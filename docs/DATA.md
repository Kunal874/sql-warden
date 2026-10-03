# SQLWarden data provenance

Checked on 2026-10-03. G0.5a is in progress: the selective native import is verified;
the compact provenance artifact is being completed. Model execution has not happened. This is not an evaluation
result or a completed conversion-validity manifest.

## Sources and selected release

The [official Mini-Dev README](https://github.com/bird-bench/mini_dev/tree/abd11b6db92a1c9f809b32f7564c7c71b34d67f0)
identifies Hugging Face as canonical for labels and links the corresponding
[database package](https://drive.google.com/file/d/13VLWIwpw5E3d5DUkMvzw7hvHE67a4XkG/view).
The package response identifies `minidev_0703.zip`, last modified 2025-07-03.
Its download URL is not revision-addressed, so reuse is pinned by SHA-256 below.
The older Aliyun package has a 2024 modification date and was not used.

Label source: [birdsql/bird_mini_dev](https://huggingface.co/datasets/birdsql/bird_mini_dev/tree/f65faf4ae3b638c1fa6df1d3370c8d92c8366301),
revision `f65faf4ae3b638c1fa6df1d3370c8d92c8366301`.
The maintainers declare [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Keep these provenance and license references; raw data is not committed or published.
This is the 500-item, 11-database Mini-Dev track, not the later CRUD/LiveSQLBench track.

Downloaded raw artifacts remain immutable and ignored under `data/raw/`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| minidev_0703.zip | 799944582 | aeb211c0e39010bbdae3838bb5e8bd27dc446ed77495b1709f85ccc9bf67f2be |
| mini_dev_sqlite.json | 278513 | 88ceb0710163cae46a256ecea8f0a8c98286599530b60587fda5c3cfe57d45d2 |
| mini_dev_pg.json | 283551 | 7fa740ef9225389cff6c34432120e8325d0ca3008d73db1ae38731234bc10da7 |

Pinned label download URLs:

- https://huggingface.co/datasets/birdsql/bird_mini_dev/resolve/f65faf4ae3b638c1fa6df1d3370c8d92c8366301/data/mini_dev_sqlite-00000-of-00001.json
- https://huggingface.co/datasets/birdsql/bird_mini_dev/resolve/f65faf4ae3b638c1fa6df1d3370c8d92c8366301/data/mini_dev_pg-00000-of-00001.json

The official package download used:
https://drive.usercontent.google.com/download?id=13VLWIwpw5E3d5DUkMvzw7hvHE67a4XkG&export=download&confirm=t

## First database: california_schools

Archive inspection found 246 entries, with 3539193972 bytes expanded in total.
The full package was downloaded, but only the small California Schools source
and its metadata were extracted. About 63 GB was free on D: before download;
the archive plus this selection uses under 1 GB. Other databases and the large
SQL dumps were not extracted. Subsequently, the native extractor selected only
three COPY data blocks under `data/bird_california/native/`.

The extractor validates the archive checksum, selects exact source member names,
writes only fixed local filenames, rejects duplicate/missing/symlink/encrypted
members and oversized data, and publishes the result only after successful
extraction. It refuses to overwrite an existing selection. Unselected archive
paths, including traversal-shaped paths, are never used as filesystem targets.

Local selection: `data/bird_california/`; its generated `manifest.json` records
source members, sizes and hashes. Source members are under
`minidev/MINIDEV/dev_databases/california_schools/`, except `dev_tables.json` under
`minidev/MINIDEV/`.

| Selected file | Bytes | SHA-256 |
| --- | ---: | --- |
| california_schools.sqlite | 11116544 | c0903eec662e63068fd1d14403d3d6c1d473287fc10c4356333ea58f878db983 |
| schools.csv | 11957 | f18d96abf47892e4bd8094dd47d6978ea6bbc11821eccdf91f3f54dd1685979f |
| satscores.csv | 1057 | a44145158100894387d05a96987c487e3c83742892b13127b486de309bb8f138 |
| frpm.csv | 1651 | f2c3fa53a02c5d711866a192f580c6a545389192a096441767f40d72ffa41334 |
| dev_tables.json | 158301 | 48aa9febe7282d1690f3ed1f222dc040c182df83812ba4e9bee956084d99c8ff |

Read-only SQLite checks: integrity_check returned `ok`; foreign_key_check returned
no violations. CSV descriptions decode as UTF-8 with optional BOM and have
original_column_name, column_name, column_description, data_format and
value_description fields. Description counts match table column counts.

| Table | SQLite rows | Columns / descriptions | Source relationships |
| --- | ---: | ---: | --- |
| schools | 17686 | 49 | primary key CDSCode |
| frpm | 9986 | 29 | primary key CDSCode; references schools.CDSCode |
| satscores | 2269 | 11 | primary key cds; references schools.CDSCode |

## Native PostgreSQL source: inspected, not executed

The package contains `minidev/MINIDEV_postgresql/BIRD_dev.sql`, a flat `public`
schema dump made by PostgreSQL 14.12. It also contains source-owner changes,
session settings and unrelated datasets. Do not execute it wholesale against
SQLWarden. The source was streamed read-only for COPY-block hashes and counts;
only the selected table definitions were reviewed.

Dump bytes: 1001882533. Dump SHA-256:
`31b1da211849d24a57c9af7636da46a5b82fc8a3ca1542bb3ebd8775e9a31cec`.
The largest observed source line was 52856 bytes.

Hash scope below: each selected COPY block's data lines, including LF endings,
excluding its COPY header and terminating `\.` line. These blocks were hashed
in memory, then extracted by the tested native-data helper. Their actual bytes,
counts and SHA-256 values match this table. The three blocks are now imported into
the isolated `california_schools` schema under `warden_owner`, with a separate
`warden_sandbox_california_schools` SELECT-only login. All rows match a setup-only
typed source replay in both directions using duplicate-preserving EXCEPT ALL.
Changing one value without changing its count is detected, and the probe rolls back.

| Native block | Rows | Data bytes | SHA-256 |
| --- | ---: | ---: | --- |
| schools | 17686 | 7728755 | f6f4de19738417ed5bd27d1d2e7935aa3e2b4319a2c366542560514671f38b6a |
| frpm | 9986 | 2481961 | 504bc2f6a66e9dfff6c9f04bb6078bcab6196c966b8d992575f88d9ad618f316 |
| satscores | 2269 | 197389 | 549f79e4b98bb0660dd9024271e3787ea83cf875fccc8e7a547c38c419a79c0f |

Reviewed native types are text, bigint, real and date. Ordinary identifiers are
lowercase; quoted names with spaces/case remain unchanged. Native `real` is not
SQLite's 64-bit REAL, and the unquoted native names are not the source SQLite's
case-preserved names. Equal counts alone do not establish semantic equivalence.

Recommended next import: extract only these native data blocks; load them through
asyncpg's COPY-data interface into owner-reviewed table definitions in
`california_schools`, with a new dataset-specific restricted login. Never execute
archive-provided SQL or its owner/session commands. Preserve native types and
identifier behavior. Validate content, keys, dates/numerics and privileges before
generated SQL. The [implementation plan](superpowers/plans/2026-10-03-bird-native-import.md)
was approved by Kunal's proceed on 2026-10-03; execution is in progress.

## Label alignment: observed differences matter

Both canonical files have 500 unique question IDs across the same 11 database
IDs. Match by question ID plus verified db_id; never by list position.
The db_id and difficulty agree for all 500 matched items. Question text differs
for IDs 937 and 964. Evidence differs for IDs 1476, 1498, 1524, 1526, 1175, 964,
988, 765, 682 and 402. Thus the two dialect files do not have identical inference
inputs across the full release. No changes were made to the source labels.

California Schools has 30 items in each file, with no question/evidence differences
in that subset. Its sorted IDs are:

`5, 11, 12, 17, 23, 24, 25, 26, 27, 28, 31, 32, 36, 37, 39, 40, 41, 45, 46, 47, 48, 50, 62, 72, 77, 79, 82, 83, 85, 87`.

| Database | Items in each dialect |
| --- | ---: |
| california_schools | 30 |
| card_games | 52 |
| codebase_community | 49 |
| debit_card_specializing | 30 |
| european_football_2 | 51 |
| financial | 32 |
| formula_1 | 66 |
| student_club | 48 |
| superhero | 52 |
| thrombosis_prediction | 50 |
| toxicology | 40 |

Corrected Arcwise labels, schema corrections, gold execution/conversion validity,
split freezing and C1 decisions remain pending. No benchmark score, PostgreSQL
gold-validity rate, ambiguity label or native/SQLite equivalence is claimed.
