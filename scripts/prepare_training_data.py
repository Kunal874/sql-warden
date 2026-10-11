"""Freeze structurally checked, execution-unverified PostgreSQL training records."""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope

from sqlwarden.guard import DatasetPolicy, guard_sql
from sqlwarden.prompts import PromptError, build_generation_prompt, template_sha256
from sqlwarden.schema import SchemaCatalog, SchemaError, quote_identifier

ROOT = Path(__file__).resolve().parents[1]
TYPES = {
    "integer": "BIGINT",
    "real": "DOUBLE PRECISION",
    "text": "TEXT",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "blob": "BYTEA",
    "number": "DOUBLE PRECISION",
    "time": "TIMESTAMP",
    "boolean": "BOOLEAN",
    "others": "TEXT",
}


def family(db_id: str) -> str:
    name = re.sub(r"_\d+$", "", db_id).casefold()
    if name.startswith("codebase_"):
        return "codebase"
    if name in {"movie", "movies"} or name.startswith("movie_"):
        return "movie"
    return name


def catalog_of(source: dict) -> SchemaCatalog:
    tables = {
        name: {"columns": [], "primary_key": [], "foreign_keys": []}
        for name in source["table_names_original"]
    }
    columns = source["column_names_original"]
    table_names = source["table_names_original"]
    for (table_index, name), dtype in zip(columns, source["column_types"], strict=True):
        if table_index >= 0:
            tables[table_names[table_index]]["columns"].append({"name": name, "type": TYPES[dtype]})
    for key in source["primary_keys"]:
        for index in key if isinstance(key, list) else [key]:
            table_index, name = columns[index]
            tables[table_names[table_index]]["primary_key"].append(name)
    for left, right in source["foreign_keys"]:
        table_index, name = columns[left]
        reference_index, reference_column = columns[right]
        tables[table_names[table_index]]["foreign_keys"].append(
            {
                "columns": [name],
                "references": (
                    f"{quote_identifier(table_names[reference_index])}"
                    f"({quote_identifier(reference_column)})"
                ),
            }
        )
    return SchemaCatalog.from_mapping(source["db_id"], {"tables": tables})


def convert_label(sql: str, catalog: SchemaCatalog) -> str:
    schema = {
        table.name: {column.name: column.type for column in table.columns}
        for table in catalog.tables
    }
    native = {table.name.casefold(): table for table in catalog.tables}
    try:
        parsed = sqlglot.parse(sql, read="sqlite")
        if len(parsed) != 1 or not isinstance(parsed[0], exp.Query):
            raise ValueError("read-only query required")
        tree = qualify(
            parsed[0],
            dialect="sqlite",
            schema=schema,
            identify=True,
            quote_identifiers=True,
            validate_qualify_columns=True,
        )
        # SQLite qualification folds names; restore physical case before PostgreSQL quoting.
        for scope in traverse_scope(tree):
            for column in scope.columns:
                ancestor = scope
                source = None
                while ancestor is not None and source is None:
                    source = ancestor.sources.get(column.table)
                    ancestor = ancestor.parent
                if isinstance(source, exp.Table) and source.name.casefold() in native:
                    names = {
                        item.name.casefold(): item.name
                        for item in native[source.name.casefold()].columns
                    }
                    if column.name.casefold() in names:
                        column.set(
                            "this", exp.Identifier(this=names[column.name.casefold()], quoted=True)
                        )
        for table in tree.find_all(exp.Table):
            if table.name.casefold() in native:
                table.set(
                    "this", exp.Identifier(this=native[table.name.casefold()].name, quoted=True)
                )
        converted = tree.sql(dialect="postgres", unsupported_level=sqlglot.ErrorLevel.RAISE)
        decision = guard_sql(
            converted,
            DatasetPolicy(catalog.db_id, frozenset(table.name for table in catalog.tables)),
        )
        if not decision.accepted:
            raise ValueError("converted label refused by guard")
        return converted
    except (sqlglot.errors.SqlglotError, KeyError, TypeError) as error:
        raise ValueError("label conversion refused") from error


def excluded_databases(training: list[dict], evaluation: dict) -> dict[str, str]:
    families = {family(db_id) for db_id in evaluation}
    tables = set()
    for database in evaluation.values():
        for name, table in database["tables"].items():
            columns = tuple(sorted(column["source_name"].casefold() for column in table["columns"]))
            if len(columns) >= 3:
                tables.add((table.get("source_name", name).casefold(), columns))
    excluded = {}
    for source in training:
        db_id = source["db_id"]
        if family(db_id) in families:
            excluded[db_id] = "database_family_overlap"
            continue
        for index, name in enumerate(source["table_names_original"]):
            columns = tuple(
                sorted(
                    column.casefold()
                    for table_index, column in source["column_names_original"]
                    if table_index == index
                )
            )
            if (name.casefold(), columns) in tables:
                excluded[db_id] = "shared_table_schema"
                break
    return excluded


def split_databases(db_ids: list[str], *, seed=42) -> tuple[list[str], list[str]]:
    families = sorted({family(db_id) for db_id in db_ids})
    if len(families) < 2:
        raise ValueError("at least two database families required")
    random.Random(seed).shuffle(families)
    validation_families = set(families[: max(1, round(len(families) * 0.1))])
    return (
        sorted(db_id for db_id in db_ids if family(db_id) not in validation_families),
        sorted(db_id for db_id in db_ids if family(db_id) in validation_families),
    )


def text_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).casefold().encode()).hexdigest()


def training_record(index: int, row: dict, catalog: SchemaCatalog) -> dict | None:
    converted = convert_label(row["SQL"], catalog)
    evidence = row.get("evidence", "").strip()
    question = (evidence + "\n" if evidence else "") + row["question"].strip()
    try:
        messages = build_generation_prompt(question, catalog.serialize(catalog.scope_all()))
    except (PromptError, SchemaError):
        return None
    return {
        "source_index": index,
        "db_id": row["db_id"],
        "messages": messages,
        "completion": f"<think></think>\n<answer>\n```sql\n{converted}\n```\n</answer>",
    }


def main() -> None:
    from scripts.validate_gold import load_tracks

    directory = ROOT / "data/training"
    manifest = json.loads((ROOT / "docs/training-source-manifest.json").read_text(encoding="utf-8"))
    for name, key in [
        ("train-tables.json", "schema_sha256"),
        ("filtered-train.jsonl", "annotation_sha256"),
    ]:
        if hashlib.sha256((directory / "source" / name).read_bytes()).hexdigest() != manifest[key]:
            raise ValueError("source fingerprint mismatch")
    schemas = json.loads((directory / "source/train-tables.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (directory / "source/filtered-train.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    audit = json.loads((ROOT / "docs/source-audit-manifest.json").read_text(encoding="utf-8"))
    excluded = excluded_databases(schemas, audit["databases"])
    catalogs = {source["db_id"]: catalog_of(source) for source in schemas}
    eval_questions, eval_sql = set(), set()
    for track in load_tracks(ROOT / "data").values():
        for row in track.values():
            eval_questions.add(text_hash(row.get("question", "")))
            eval_sql.add(text_hash(row["SQL"]))
    prepared, counts, seen_questions = [], Counter(), set()
    for index, row in enumerate(rows):
        db_id = row["db_id"]
        if db_id in excluded:
            counts[excluded[db_id]] += 1
            continue
        question_hash, sql_hash = text_hash(row["question"]), text_hash(row["SQL"])
        if question_hash in eval_questions or sql_hash in eval_sql:
            counts["evaluation_text_overlap"] += 1
            continue
        if question_hash in seen_questions:
            counts["duplicate_training_question"] += 1
            continue
        try:
            record = training_record(index, row, catalogs[db_id])
        except ValueError:
            counts["conversion_or_guard_refused"] += 1
            continue
        if record is None:
            counts["prompt_refused"] += 1
            continue
        seen_questions.add(question_hash)
        prepared.append(record)
    train_dbs, validation_dbs = split_databases(sorted({row["db_id"] for row in prepared}))
    train, validation = [], []
    for record in prepared:
        (train if record["db_id"] in train_dbs else validation).append(record)
    output = directory / "prepared"
    output.mkdir()
    for name, records in [("train", train), ("validation", validation)]:
        with (output / f"{name}.jsonl").open("x", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    report = {
        "seed": 42,
        "source_count": len(rows),
        "prepared_count": len(prepared),
        "train_count": len(train),
        "validation_count": len(validation),
        "train_databases": train_dbs,
        "validation_databases": validation_dbs,
        "excluded_databases": excluded,
        "excluded_rows": dict(counts),
        "label_validity": "structurally qualified and guard accepted; execution-unverified",
        "schema_types": "mapped from SQLite metadata; not imported PostgreSQL types",
        "leakage_checks": (
            "database families, shared source table schemas, exact normalized question/SQL overlap"
        ),
        "limitations": (
            "no training database row-content comparison; pretraining contamination unknown"
        ),
        "prompt_sha256": template_sha256("generate"),
        "train_sha256": hashlib.sha256((output / "train.jsonl").read_bytes()).hexdigest(),
        "validation_sha256": hashlib.sha256((output / "validation.jsonl").read_bytes()).hexdigest(),
    }
    with (ROOT / "docs/training-data-manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
