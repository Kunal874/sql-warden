"""Small schema catalog and lexical retriever for the local agent loop."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

MAX_SAMPLE_VALUES = 3
MAX_SAMPLE_BYTES = 160
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
BARE_IDENTIFIER = re.compile(r"[a-z_][a-z0-9_]*")
# PostgreSQL reserved key words (docs appendix C) that must be quoted as identifiers.
_RESERVED_WORDS = (
    "all analyse analyze and any array as asc asymmetric authorization binary both case cast "
    "check collate collation column concurrently constraint create cross current_catalog "
    "current_date current_role current_schema current_time current_timestamp current_user "
    "default deferrable desc distinct do else end except false fetch for foreign freeze from "
    "full grant group having ilike in initially inner intersect into is isnull join lateral "
    "leading left like limit localtime localtimestamp natural not notnull null offset on only "
    "or order outer overlaps placing primary references returning right select session_user "
    "similar some symmetric system_user table tablesample then to trailing true union unique "
    "user using variadic verbose when where window with"
)
RESERVED = frozenset(_RESERVED_WORDS.split())


class SchemaError(ValueError):
    """Stable refusal for invalid or over-budget schema material."""


@dataclass(frozen=True, slots=True)
class ColumnDoc:
    table: str
    name: str
    type: str
    description: str = ""
    samples: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TableDoc:
    name: str
    description: str
    primary_key: tuple[str, ...]
    foreign_keys: tuple[tuple[tuple[str, ...], str], ...]
    columns: tuple[ColumnDoc, ...]


@dataclass(frozen=True, slots=True)
class SchemaScope:
    db_id: str
    tables: tuple[TableDoc, ...]
    column_count: int
    score_floor: float


@dataclass(frozen=True, slots=True)
class SchemaCatalog:
    db_id: str
    tables: tuple[TableDoc, ...]

    @classmethod
    def from_mapping(
        cls,
        db_id: str,
        schema: dict[str, Any],
        *,
        samples: dict[tuple[str, str], list[Any]] | None = None,
    ) -> SchemaCatalog:
        if type(db_id) is not str or not db_id:
            raise SchemaError("schema db refused")
        try:
            source_tables = schema["tables"]
        except (KeyError, TypeError):
            raise SchemaError("schema invalid") from None
        if type(source_tables) is not dict or not source_tables:
            raise SchemaError("schema invalid")
        sample_values = samples or {}
        tables = []
        for table_name in sorted(source_tables):
            table = source_tables[table_name]
            columns = []
            for column in table["columns"]:
                column_name = _text(column["name"], "column invalid")
                columns.append(
                    ColumnDoc(
                        table=_text(table_name, "table invalid"),
                        name=column_name,
                        type=_text(column["type"], "column invalid"),
                        description=_clean(column.get("description", "")),
                        samples=_bounded_samples(sample_values.get((table_name, column_name), [])),
                    )
                )
            tables.append(
                TableDoc(
                    name=_text(table_name, "table invalid"),
                    description=_clean(table.get("description", "")),
                    primary_key=tuple(
                        _text(value, "primary key invalid")
                        for value in table.get("primary_key", [])
                    ),
                    foreign_keys=tuple(
                        (
                            tuple(
                                _text(value, "foreign key invalid")
                                for value in foreign_key.get("columns", [])
                            ),
                            _text(foreign_key.get("references", ""), "foreign key invalid"),
                        )
                        for foreign_key in table.get("foreign_keys", [])
                    ),
                    columns=tuple(columns),
                )
            )
        return cls(db_id, tuple(tables))

    def fingerprint(self) -> str:
        return sha256(
            self.serialize(self.scope_all(), max_bytes=1_000_000).encode("utf-8")
        ).hexdigest()

    def scope_all(self) -> SchemaScope:
        return SchemaScope(
            self.db_id,
            self.tables,
            sum(len(table.columns) for table in self.tables),
            0.0,
        )

    def retrieve(self, question: str, *, top_k: int = 24) -> SchemaScope:
        if (
            type(question) is not str
            or not question.strip()
            or type(top_k) is not int
            or top_k <= 0
        ):
            raise SchemaError("retrieval input refused")
        docs = [
            (
                table,
                column,
                _tokens(" ".join([table.name, table.description, column.name, column.description])),
                set(_tokens(table.name)),
                set(_tokens(column.name)),
            )
            for table in self.tables
            for column in table.columns
        ]
        query = _tokens(question)
        if not query:
            raise SchemaError("retrieval input refused")
        df = {
            token: sum(1 for _, _, tokens, _, _ in docs if token in tokens) for token in set(query)
        }
        scored = []
        avg_len = sum(len(tokens) for _, _, tokens, _, _ in docs) / len(docs)
        for table, column, tokens, table_tokens, column_tokens in docs:
            score = 0.0
            for token in query:
                frequency = tokens.count(token)
                if frequency:
                    idf = math.log(1 + (len(docs) - df[token] + 0.5) / (df[token] + 0.5))
                    score += (
                        idf
                        * (frequency * 2.2)
                        / (frequency + 1.2 * (0.25 + 0.75 * len(tokens) / avg_len))
                    )
                if token in column_tokens:
                    score += 2.0
                if token in table_tokens:
                    score += 0.25
            scored.append((score, table, column))
        picked = sorted(scored, key=lambda item: (-item[0], item[1].name, item[2].name))[:top_k]
        selected: dict[str, set[str]] = {}
        for score, table, column in picked:
            if score > 0 or not selected:
                selected.setdefault(table.name, set()).add(column.name)
        if not selected:
            table = self.tables[0]
            selected[table.name] = {
                column.name for column in table.columns[: min(top_k, len(table.columns))]
            }
        scoped_tables = []
        for table in self.tables:
            names = selected.get(table.name)
            if names:
                scoped_tables.append(
                    TableDoc(
                        table.name,
                        table.description,
                        table.primary_key,
                        table.foreign_keys,
                        tuple(column for column in table.columns if column.name in names),
                    )
                )
        return SchemaScope(
            self.db_id,
            tuple(scoped_tables),
            sum(len(table.columns) for table in scoped_tables),
            picked[-1][0] if picked else 0.0,
        )

    @staticmethod
    def serialize(scope: SchemaScope, *, max_bytes: int = 64_000) -> str:
        if type(scope) is not SchemaScope:
            raise SchemaError("schema scope invalid")
        lines = [f"database {scope.db_id}"]
        for table in scope.tables:
            name = quote_identifier(table.name)
            suffix = f" -- {table.description}" if table.description else ""
            lines.append(f"table {name}{suffix}")
            for column in table.columns:
                column_name = f"{name}.{quote_identifier(column.name)}"
                column_suffix = f" -- {column.description}" if column.description else ""
                lines.append(f"column {column_name} {column.type}{column_suffix}")
                if column.samples:
                    lines.append(f"untrusted samples {column_name}: " + ", ".join(column.samples))
            if table.primary_key:
                keys = ", ".join(quote_identifier(key) for key in table.primary_key)
                lines.append(f"primary key {name}({keys})")
            for columns, reference in table.foreign_keys:
                keys = ", ".join(quote_identifier(key) for key in columns)
                lines.append(f"foreign key {name}({keys}) -> {reference}")
        rendered = "\n".join(lines)
        if len(rendered.encode("utf-8")) > max_bytes:
            raise SchemaError("schema budget exceeded")
        return rendered


def quote_identifier(name: str) -> str:
    """Render a name the way PostgreSQL must read it: bare only if folding cannot change it."""
    if BARE_IDENTIFIER.fullmatch(name) and name not in RESERVED:
        return name
    return '"' + name.replace('"', '""') + '"'


def _tokens(value: str) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(value.replace("_", " ")):
        folded = token.casefold()
        tokens.append(folded)
        if len(folded) > 3 and folded.endswith("s"):
            tokens.append(folded[:-1])
    return tokens


def _text(value: Any, reason: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise SchemaError(reason)
    return value


def _clean(value: Any) -> str:
    return " ".join(value.split()) if type(value) is str else ""


def _bounded_samples(values: list[Any]) -> tuple[str, ...]:
    samples = []
    for value in values[:MAX_SAMPLE_VALUES]:
        text = _clean("" if value is None else str(value))
        if text:
            encoded = text.encode("utf-8", errors="ignore")[:MAX_SAMPLE_BYTES]
            samples.append(encoded.decode("utf-8", errors="ignore"))
    return tuple(samples)
