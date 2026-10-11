import pytest

from sqlwarden.schema import SchemaCatalog, SchemaError


def _schema():
    return {
        "tables": {
            "schools": {
                "description": "school directory",
                "primary_key": ["cdscode"],
                "foreign_keys": [],
                "columns": [
                    {"name": "cdscode", "type": "TEXT", "description": "school identifier"},
                    {"name": "school", "type": "TEXT", "description": "school name"},
                    {"name": "county", "type": "TEXT", "description": "county name"},
                ],
            },
            "satscores": {
                "description": "test score facts",
                "primary_key": [],
                "foreign_keys": [{"columns": ["cdscode"], "references": "schools.cdscode"}],
                "columns": [
                    {"name": "cdscode", "type": "TEXT", "description": "school identifier"},
                    {"name": "avgmath", "type": "INTEGER", "description": "average math score"},
                ],
            },
        }
    }


def test_catalog_serializes_keys_descriptions_and_bounded_untrusted_samples():
    catalog = SchemaCatalog.from_mapping(
        "california_schools",
        _schema(),
        samples={("schools", "school"): ["Alpha Academy", "Beta High", "Gamma " * 80, "extra"]},
    )

    rendered = catalog.serialize(catalog.scope_all(), max_bytes=4096)

    assert "table schools -- school directory" in rendered
    assert "column schools.school TEXT -- school name" in rendered
    assert "primary key schools(cdscode)" in rendered
    assert "foreign key satscores(cdscode) -> schools.cdscode" in rendered
    assert "untrusted samples schools.school:" in rendered
    assert "extra" not in rendered
    with pytest.raises(SchemaError, match="schema budget"):
        catalog.serialize(catalog.scope_all(), max_bytes=20)


def test_bm25_retrieval_keeps_relevant_scope_small_and_deterministic():
    catalog = SchemaCatalog.from_mapping("california_schools", _schema())

    scope = catalog.retrieve("highest average math score by school", top_k=2)
    rendered = catalog.serialize(scope)

    assert scope.column_count == 2
    assert "column satscores.avgmath" in rendered
    assert "column schools.school" in rendered
    assert catalog.retrieve("highest average math score by school", top_k=2) == scope


def test_catalog_refuses_bad_inputs_without_partial_schema():
    with pytest.raises(SchemaError):
        SchemaCatalog.from_mapping("", _schema())
    with pytest.raises(SchemaError):
        SchemaCatalog.from_mapping("db", {"tables": {}})
    with pytest.raises(SchemaError):
        SchemaCatalog.from_mapping(
            "db", {"tables": {"bad": {"columns": [{"name": "", "type": "TEXT"}]}}}
        )


def test_serialized_identifiers_are_written_as_postgresql_requires():
    catalog = SchemaCatalog.from_mapping(
        "db",
        {
            "tables": {
                "Order Lines": {
                    "description": "",
                    "primary_key": ["id"],
                    "foreign_keys": [{"columns": ["user"], "references": "users.id"}],
                    "columns": [
                        {"name": "id", "type": "BIGINT"},
                        {"name": "Academic Year", "type": "TEXT"},
                        {"name": "user", "type": "TEXT"},
                        {"name": 'odd"name', "type": "TEXT"},
                    ],
                }
            }
        },
    )

    rendered = SchemaCatalog.serialize(catalog.scope_all())

    assert 'table "Order Lines"' in rendered
    assert 'column "Order Lines".id BIGINT' in rendered
    assert 'column "Order Lines"."Academic Year" TEXT' in rendered
    assert 'column "Order Lines"."user" TEXT' in rendered
    assert 'column "Order Lines"."odd""name" TEXT' in rendered
    assert 'foreign key "Order Lines"("user") -> users.id' in rendered
