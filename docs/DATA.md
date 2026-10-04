# SQLWarden data provenance

California import checked on 2026-10-03; correction-source inspection added
2026-10-05. G0.5a is complete for California Schools: selective native
import, content/types/keys, descriptions and direct privileges are verified.
One guarded local model-driven question ran on 2026-10-04, documented separately
in [CLI_SMOKE.md](CLI_SMOKE.md). This is not an evaluation
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

## Native PostgreSQL source: selected COPY data only

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

Import method: extract only these native data blocks; load them through
asyncpg's COPY-data interface into owner-reviewed table definitions in
`california_schools`, with a new dataset-specific restricted login. Never execute
archive-provided SQL or its owner/session commands. Preserve native types and
identifier behavior. Validate content, keys, dates/numerics and privileges before
generated SQL. The [implementation plan](superpowers/plans/2026-10-03-bird-native-import.md)
was approved by Kunal's proceed on 2026-10-03 and all three tasks are verified.

The small [import manifest](california-import-manifest.json) records the actual
import Git state, source hashes, full column/type/key mapping, ordered native
content fingerprints and per-column NULL counts. Fingerprints were streamed using
the restricted reader, in primary-key order with COLLATE C and fixed native output
settings. They are not the raw TSV hashes or SQLite-equivalence claims.

| Table | Ordered native COPY SHA-256 |
| --- | --- |
| schools | 34e8f4ca65a612a43dc8cc4040091eb37eae2bf70b02a937c7d26a5fe0df7dae |
| frpm | 1309104cd94cc85c790f93518d63ac5be05177dda0e5c3d63110fa52ce0c41ca |
| satscores | 4fa59c2fd521124791ff36e219559d53eabe5765e658108b6f9b1abc84b0ef24 |

All 89 descriptions map uniquely to native columns. Four frpm description names
have whitespace padding: School Code, District Name, School Type and
Percent (%) Eligible Free (Ages 5-17). Only description-name padding was trimmed;
the exact aliases are recorded in the manifest. Source bytes, quoted SQL names,
labels and benchmark definitions are unchanged.

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

Persisted corrected Arcwise intake (approved, Task 2 next), schema corrections, gold execution/conversion validity,
split freezing and C1 decisions remain pending. No benchmark score, PostgreSQL
gold-validity rate, ambiguity label or native/SQLite equivalence is claimed.

## Remaining G0.5 — read-only correction intake preparation (2026-10-05)

The existing 799,944,582-byte archive was freshly SHA-256 verified against its
pin above. Its central-directory inventory still has 246 entries, expanded
3,539,193,972 bytes, including all 11 original SQLite files (1,493,287,936 bytes
total). No further database was extracted or loaded. D: reported 46,331,715,584
free bytes at inspection; this is not a PostgreSQL import-size estimate.

Read the corrected source over HTTPS into memory only; no new correction corpus
was saved locally. Pin the inspected revision
fe766045c55b6875a43b30e9ac7683df5582f8cf (upstream commit dated 2026-08-27).
The [revision README](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/README.md)
names Arcwise-Plat-SQL and Arcwise-Plat. The full filename below is an upstream
filename, not permission to rename or revise the historical planning inputs.
The [revision license](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/LICENSE)
declares CC BY-SA 4.0.

| Resource at that revision | Observed bytes | SHA-256 |
| --- | ---: | --- |
| data/arcwise_plat_sql_only_with_diff.json | 287718 | e7bf76408f99266506ea558d84982c69422e5db3dfecab5f08a3a8d3900e8395 |
| data/arcwise_plat_full_with_diff.json | 332246 | baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8 |
| README.md | 5038 | 7aefaba8da2792a8edde1cb534dde1f89c3228e87ac5b923838ba68bb56cf0f5 |
| LICENSE | 20138 | 28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5 |

Source files: [SQL-only](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/data/arcwise_plat_sql_only_with_diff.json),
[question/evidence corrections](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/data/arcwise_plat_full_with_diff.json).
Exact ID-keyed in-memory inspection against the pinned canonical SQLite labels:

| Observation | SQL-only | Full |
| --- | ---: | ---: |
| Items / unique numeric IDs | 498 / 498 | 498 / 498 |
| Missing original IDs | 119, 120 | 119, 120 |
| Unexpected IDs / database mismatches | 0 / 0 | 0 / 0 |
| Question text differences | 81 | 147 |
| Evidence text differences | 86 | 152 |
| Either question or evidence differs | 141 | 229 |
| SQL text differences (not result comparisons) | 180 | 215 |
| original_SQL metadata fields | 83 | 134 |
| original_question metadata fields | 0 | 88 |
| original_evidence metadata fields | 0 | 98 |

IDs in the correction JSON are decimal strings; canonical IDs are integers.
Correction order starts with thrombosis_prediction; matching lists by position
would be wrong. All 11 database identities are represented. Only financial has
a count change: 30 corrected items versus 32 original. SQL-only has one optional
difficulty field, ID405 moderate, matching canonical. Other difficulty values
must come from the verified original ID mapping, not list order.

Between the two corrected sets, 88 question fields and 98 evidence fields differ,
148 IDs in their union. These are literal text differences; no trimming,
case-folding, fuzzy matching, semantic classification or ambiguity-label inference
was made. In particular, SQL-only is not text-identical to our pinned canonical
BIRD release. Its upstream preservation statement is not evidence that those
141 original-to-SQL-only text differences are zero. C1 must review baseline drift
and anchors before selecting question/ambiguity policies.

The [corrected schemas directory](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/tree/fe766045c55b6875a43b30e9ac7683df5582f8cf/data/schemas)
has Git tree 9cf49139c686a1156491f1859c0a75c91e257897: 75 CSV description files,
76,445 bytes by recursive Git tree metadata. Contents were not parsed/applied;
this inventory does not establish physical-table changes or correct column
mapping. Schema-description inspection remains required separately.

The [two-task intake plan](superpowers/plans/2026-10-05-corrected-label-intake.md)
was approved by Kunal on 2026-10-05. Task 1's strict offline checker is implemented
and passes 39 synthetic checks; Task 2's acquisition/actual acceptance is next.
Only the four pinned resources (645,140 content bytes) may be saved in this
increment. No source SQL, SQLite gold,
PostgreSQL gold or model request ran during this inspection. Conversion survival,
validity/exclusion policy, primary labels, ambiguity labels, family splits and C1
remain undecided. No benchmark denominator or score has been changed.

Task 1 accepts integer original IDs and strictly decimal corrected string IDs,
rejects duplicate keys/IDs and malformed or unreviewed fields, and verifies exact
local byte/hash pins before reporting. It matches by numeric ID and separately
records database mismatches; identity alignment is not semantic alignment.
Output contains aggregate counts and difference IDs, not question/evidence/SQL
values. original_* anchors remain observational. No real correction bytes have
been saved/accepted through this script yet, nor has any gold SQL been executed.
