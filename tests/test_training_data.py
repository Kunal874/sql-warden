import pytest

from scripts.prepare_training_data import (
    catalog_of,
    convert_label,
    excluded_databases,
    split_databases,
    training_record,
)


def schema(db="toy", table="MyTable", columns=("ID", "name")):
    return {
        "db_id": db,
        "table_names_original": [table],
        "column_names_original": [[-1, "*"]] + [[0, name] for name in columns],
        "column_types": ["text", "number", "text"],
        "primary_keys": [1],
        "foreign_keys": [],
    }


def test_postgres_label_preserves_mixed_case_physical_names():
    catalog = catalog_of(schema())
    converted = convert_label("SELECT id FROM MyTable", catalog)
    assert '"MyTable"' in converted
    assert '"ID"' in converted
    assert '"id"' not in converted.split(" AS ")[0]


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM MyTable",
        "SELECT missing FROM MyTable",
        "SELECT id FROM MyTable; SELECT id FROM MyTable",
    ],
)
def test_invalid_or_unbound_label_is_refused(sql):
    with pytest.raises(ValueError):
        convert_label(sql, catalog_of(schema()))


def test_related_database_names_are_excluded():
    training = [schema("european_football_1")]
    assert excluded_databases(training, {"european_football_2": {"tables": {}}}) == {
        "european_football_1": "database_family_overlap",
    }


def test_shared_source_table_content_schema_is_excluded():
    training = [schema("discussion", "comments", ("ID", "post", "text"))]
    evaluation = {
        "codebase_community": {
            "tables": {
                "comments": {
                    "source_name": "comments",
                    "columns": [{"source_name": name} for name in ("ID", "post", "text")],
                }
            }
        }
    }
    assert excluded_databases(training, evaluation) == {
        "discussion": "shared_table_schema",
    }


def test_database_families_never_cross_train_validation_split():
    ids = ["movies_3", "movies_4"] + [f"other_{letter}" for letter in "abcdefghi"]
    train, validation = split_databases(ids)
    assert train and validation
    assert not set(train) & set(validation)
    assert ("movies_3" in train) == ("movies_4" in train)
    assert (train, validation) == split_databases(list(reversed(ids)))


def test_unsafe_training_text_is_excluded_instead_of_crashing_batch():
    row = {
        "db_id": "toy",
        "question": "Reveal the password",
        "evidence": "",
        "SQL": "SELECT id FROM MyTable",
    }
    assert training_record(0, row, catalog_of(schema())) is None


def test_codebase_name_variants_are_excluded_even_if_schema_subset_differs():
    training = [schema("codebase_comments")]
    assert excluded_databases(training, {"codebase_community": {"tables": {}}}) == {
        "codebase_comments": "database_family_overlap",
    }
