"""Seeded messy-schema transformation for E4: cryptic names over the same data.

The model sees only messy names. Its SQL is translated back to the real names before
the guard and the restricted executor see it, so every security check is unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256

from sqlglot import exp, parse_one

from sqlwarden.schema import RESERVED, ColumnDoc, SchemaCatalog, TableDoc, quote_identifier

SEED = 20261011
WORD = re.compile(r"[A-Za-z]+|[0-9]+")


@dataclass(frozen=True, slots=True)
class MessyMapping:
    tables: dict[str, str]
    columns: dict[str, str]

    def reverse(self) -> MessyMapping:
        return MessyMapping(
            {messy: name for name, messy in self.tables.items()},
            {messy: name for name, messy in self.columns.items()},
        )


def build_mapping(catalog: SchemaCatalog, *, seed: int = SEED) -> MessyMapping:
    used: set[str] = set()

    def cryptic(prefix: str, name: str) -> str:
        stem = "".join(word[:3] for word in WORD.findall(name)).lower()[:10] or "x"
        for length in range(3, 12):
            suffix = sha256(f"{seed}:{catalog.db_id}:{prefix}:{name}".encode()).hexdigest()
            messy = f"{prefix}{stem}_{suffix[:length]}"
            if messy not in used and messy not in RESERVED:
                used.add(messy)
                return messy
        raise ValueError("messy name collision")

    tables = {table.name: cryptic("t", table.name) for table in catalog.tables}
    names = sorted({column.name for table in catalog.tables for column in table.columns})
    return MessyMapping(tables, {name: cryptic("c", name) for name in names})


def messy_catalog(catalog: SchemaCatalog, mapping: MessyMapping) -> SchemaCatalog:
    lookup = {name.casefold(): messy for name, messy in mapping.tables.items()}
    column_lookup = {name.casefold(): messy for name, messy in mapping.columns.items()}

    def reference(text: str) -> str:
        table, _, column = text.partition(".")
        return f"{lookup.get(table, table)}.{column_lookup.get(column, column)}"

    tables = []
    for table in catalog.tables:
        tables.append(
            TableDoc(
                mapping.tables[table.name],
                _scrub(table.description, mapping),
                tuple(mapping.columns[key] for key in table.primary_key),
                tuple(
                    (tuple(column_lookup.get(key, key) for key in keys), reference(target))
                    for keys, target in table.foreign_keys
                ),
                tuple(
                    ColumnDoc(
                        mapping.tables[table.name],
                        mapping.columns[column.name],
                        column.type,
                        _scrub(column.description, mapping),
                        column.samples,
                    )
                    for column in table.columns
                ),
            )
        )
    return SchemaCatalog(catalog.db_id, tuple(tables))


def translate(sql: str, mapping: MessyMapping) -> str:
    """Rename table and column identifiers; aliases and CTE names are untouched."""
    tree = parse_one(sql, read="postgres")
    for table in tree.find_all(exp.Table):
        renamed = _lookup(table.args.get("this"), mapping.tables)
        if renamed:
            table.set("this", _identifier(renamed))
    for column in tree.find_all(exp.Column):
        renamed = _lookup(column.args.get("this"), mapping.columns)
        if renamed:
            column.set("this", _identifier(renamed))
        qualifier = _lookup(column.args.get("table"), mapping.tables)
        if qualifier:
            column.set("table", _identifier(qualifier))
    return tree.sql(dialect="postgres")


def leaked_names(text: str, catalog: SchemaCatalog) -> int:
    """Distinctive original identifiers (not plain lowercase words) still in the text."""
    names = {table.name for table in catalog.tables} | {
        column.name for table in catalog.tables for column in table.columns
    }
    distinctive = [name for name in names if not re.fullmatch(r"[a-z]+", name)]
    return sum(1 for name in distinctive if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text))


def _lookup(node, names: dict[str, str]) -> str | None:
    if not isinstance(node, exp.Identifier):
        return None
    # PostgreSQL folds unquoted identifiers to lower case; quoted ones match exactly.
    return names.get(node.this if node.quoted else node.this.lower())


def _identifier(name: str) -> exp.Identifier:
    return exp.to_identifier(name, quoted=quote_identifier(name) != name)


def _scrub(text: str, mapping: MessyMapping) -> str:
    names = sorted(mapping.columns.items() | mapping.tables.items(), key=lambda i: -len(i[0]))
    for name, messy in names:
        if not re.fullmatch(r"[a-z]+", name):
            text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", messy, text, flags=re.I)
    return text
