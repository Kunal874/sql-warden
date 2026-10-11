from scripts.messy_schema import build_mapping, leaked_names, messy_catalog, translate
from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql
from sqlwarden.schema import BARE_IDENTIFIER, SchemaCatalog


def _catalog():
    return SchemaCatalog.from_mapping(
        "california_schools",
        {
            "tables": {
                "schools": {
                    "description": "",
                    "primary_key": ["cdscode"],
                    "foreign_keys": [],
                    "columns": [
                        {"name": "cdscode", "type": "TEXT", "description": "school id"},
                        {"name": "County", "type": "TEXT", "description": "County of the school"},
                    ],
                },
                "frpm": {
                    "description": "",
                    "primary_key": ["cdscode"],
                    "foreign_keys": [{"columns": ["cdscode"], "references": "schools.cdscode"}],
                    "columns": [
                        {"name": "cdscode", "type": "TEXT", "description": "school id"},
                        {
                            "name": "Enrollment (K-12)",
                            "type": "BIGINT",
                            "description": "Same as Enrollment (K-12) in the report",
                        },
                    ],
                },
            }
        },
    )


def test_mapping_is_seeded_unique_and_bare():
    first, second = build_mapping(_catalog()), build_mapping(_catalog())
    assert first == second
    names = list(first.tables.values()) + list(first.columns.values())
    assert len(names) == len(set(names))
    assert all(BARE_IDENTIFIER.fullmatch(name) for name in names)
    assert first.columns["cdscode"] != "cdscode"


def test_messy_catalog_hides_distinctive_original_names_and_keeps_keys():
    catalog = _catalog()
    mapping = build_mapping(catalog)
    text = SchemaCatalog.serialize(messy_catalog(catalog, mapping).scope_all())

    assert leaked_names(text, catalog) == 0
    assert leaked_names(SchemaCatalog.serialize(catalog.scope_all()), catalog) > 0
    assert mapping.columns["Enrollment (K-12)"] in text
    assert f"-> {mapping.tables['schools']}.{mapping.columns['cdscode']}" in text


def test_round_trip_translation_restores_guarded_original_sql():
    mapping = build_mapping(_catalog())
    original = (
        'SELECT T1."County", MAX(T2."Enrollment (K-12)") FROM schools AS T1 '
        'JOIN frpm AS T2 ON T1.cdscode = T2.CDSCODE GROUP BY T1."County"'
    )

    messy = translate(original, mapping)
    restored = translate(messy, mapping.reverse())

    assert "Enrollment" not in messy and "schools" not in messy
    assert mapping.columns["Enrollment (K-12)"] in messy
    assert 'T1."County"' in restored and 'T2."Enrollment (K-12)"' in restored
    assert "T2.cdscode" in restored and "FROM schools AS T1 JOIN frpm AS T2" in restored
    assert guard_sql(restored, CALIFORNIA_POLICY).accepted
