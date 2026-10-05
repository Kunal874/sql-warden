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

Corrected Arcwise intake and offline manifest are now checked below. Schema corrections, gold execution/conversion validity,
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
76,445 bytes by recursive Git tree metadata. At this earlier intake checkpoint,
contents were not parsed/applied; the dated preparation below now records content
inspection. Neither inspection establishes physical-table changes or value correctness.

The [two-task intake plan](superpowers/plans/2026-10-05-corrected-label-intake.md)
was approved by Kunal on 2026-10-05. Both tasks' code/actual acceptance are checked;
40 label tests and 9 fake-network tests pass, sole final review complete.
Only the four pinned resources (645140 content bytes) were saved in this
increment. No source SQL, SQLite gold,
PostgreSQL gold or model request ran during this inspection. Conversion survival,
validity/exclusion policy, primary labels, ambiguity labels, family splits and C1
remain undecided. No benchmark denominator or score has been changed.

Task 1 accepts integer original IDs and strictly decimal corrected string IDs,
rejects duplicate keys/IDs and malformed or unreviewed fields, and verifies exact
local byte/hash pins before reporting. It matches by numeric ID and separately
records database mismatches; identity alignment is not semantic alignment.
Output contains aggregate counts and difference IDs, not question/evidence/SQL
values. original_* anchors remain observational. Actual correction bytes are now
saved and accepted through the scripts below; no gold SQL has been executed.

## Actual pinned offline correction acceptance (2026-10-05)

Ran uv run python -m scripts.fetch_labels once, without an env file, after fake
controls and read-only absent/ignored-destination/disk/pin checks. All four
resources above passed exact size/SHA-256 before publishing the new ignored
data/corrections/arcwise-fe766045 directory; all four were rechecked offline.
Original raw label files were reused unchanged. No redirects, proxy inheritance,
source SQL execution, retry/repin or overwrite; task-owned temporary staging
was cleaned by its context manager, not any prior artifact.

The first strict parse identified evidence null at IDs 1507/1528 in both corrected
sets. Read-only shape checks and a failing regression established the cause.
Permit null only for corrected evidence and retain it exactly; original evidence
remains string-only. Do not normalize null to empty, omit rows or infer an input
policy. All other present text fields are strings. Source pins are unchanged.

The [compact alignment manifest](label-alignment-manifest.json) records actual
pins/URLs/license, observed bytes, check date/procedure and acceptance Git state
(64f51e4 plus dirty Task 2/schema-support changes, before its commit). It includes
all difference/mismatch IDs, original database/difficulty counts and four
undecided states. No raw question/evidence/SQL values are in the manifest.

All planned actual assertions pass: 500 originals per dialect, 498 corrections
each, missing 119/120 only, no unexpected/db/difficulty mismatch; question/evidence
differences 81/86 and 147/152, corrected-pair union 148. Original difficulty counts
148 simple/250 moderate/102 challenging. Anchor mismatch counts are 81/86 for
SQL-only and 81/79 for full; these do not verify provenance of baseline rewrites.
Gold execution/conversion survival, descriptions/imports, primary labels, ambiguity
policy, exclusions, family splits and C1 remain unfinished. G0.5 is not complete.

Sole final review of 399efed..676428f verified the six distinct source pins and
fresh report/manifest equality. One Important body-deadline gap was reproduced
test-first and fixed by unbuffered HTTPX raw iteration; byte/hash rules unchanged.
No corruption or refetch: the acquired files and their acceptance record remain
valid. Final combined tests 49 passed, configured full suite 768/zero skips,
including 165 actual PostgreSQL checks; no gold SQL or new corpus validity claim.
Cooperative bounds do not promise hard interruption inside DNS/TLS/header/file
operations or crash durability; Windows/trusted-local-filesystem workflow only.

## Full-source read-only preparation (2026-10-05)

[Source-release pins](source-release-pins.json) record actual streamed fingerprints
from clean fc71084: archive 799944582 bytes, native dump 1001882533 bytes, metadata
158301 bytes; 11 SQLite files (1493287936 bytes), 75 original description CSVs
(76887 bytes), and 75 corrected CSVs (76445 bytes). All SQLite archive members were
hashed without extracting/deserializing them. Exact member/output paths exclude
__MACOSX forks and preserve filename case differences such as original Budget.csv
versus corrected budget.csv. No raw prose, data cells or SQL is in this metadata.

Read-only native CREATE/COPY inspection found 75 unique tables, 798 ordered columns,
3898114 COPY data lines and 1001771589 COPY data bytes; all header/definition columns
match. Types: BIGINT 366, TEXT 329, REAL 73, DATE 19, TIMESTAMPTZ 11. The latter occur
in codebase_community and require later conversion/timezone decisions. These are
native dump observations, not verified physical SQLite or imported PostgreSQL rows.

Fetched all 75 fixed-revision corrected CSVs into memory only; checked Git blob
SHA-1/size and computed SHA-256, then strictly parsed headers/column names. After
existing pg_name mapping and description-only padding removal, corrected rows
cover all 798 native columns with no missing/extra/duplicate identities. This is
name coverage, not semantic correctness or a chosen runtime description policy.
Original CSVs contain 799 records: constructors in formula_1 has an extra padded
wins description absent from the native table; retain/report it rather than attach
it to another column. 89 original padded-name records were observed, including
that unmatched record. Both financial/account files have a sixth unnamed header
field with nonempty text at one-based data row 3; record it, preserve raw files,
and do not silently erase it or present it as a verified named-column description.

Strict UTF-8 failed for four original files: formula_1/qualifying.csv,
european_football_2/Team_Attributes.csv, european_football_2/Player_Attributes.csv,
and student_club/Budget.csv. Three corrected files retain the encoding issue
(the two European files and student_club/budget.csv); corrected qualifying is UTF-8.
Strict cp1252 parses these bytes and is a pinned local interpretation, not an
upstream charset declaration or an automatic fallback. Other originals/corrections
are UTF-8-sig. Source bytes/pins remain unchanged.

Kunal reviewed and approved the [three-task source preparation plan](superpowers/plans/2026-10-05-full-source-preparation.md).
It will extract 87 fixed members into a new ignored release, acquire 75 corrected
CSV files once and audit actual SQLite layouts/counts/keys/descriptions offline.
Expanded footprint 1493523124 + 76445 bytes, plus 1 GiB extraction reserve; fresh
preparation D: free 46325698560 bytes, RAM free 1167319040 bytes. Native dump is streamed,
not copied into another 1 GB tree. Physical layout/count equality, content/type
conversion equivalence, remaining PostgreSQL imports, gold validity, primary labels/
descriptions, ambiguity/splits and C1 remain unperformed. No benchmark score.

## Full-source batch Task 1 — actual extraction (2026-10-05)

After the approved tests-first extraction controls passed (16 tests), ran
uv run python -m scripts.prepare_sources once without private env settings.
Destination was absent/ignored; D: free 46325235712 bytes. Extracted exactly 87
fixed members into data/source-release/minidev-0703: 11 SQLite files, 75 original
description CSVs, dev_tables.json; total 1493523124 bytes. Rechecked every saved
size/SHA-256 and exact file count. No source SQL executed, no database import,
no existing California/raw/correction artifact changed. Only newly owned staging
was cleaned normally. Physical SQLite/layout/count checks remain Task 3.

Expected missing-module RED, then 16 GREEN; no-env full suite 619 passed/165
skipped (5.90s), ruff/format checks pass. One unused fixture import removed and
planned mechanical formatting applied; no pin/control changes. The extractor
refuses this existing destination and must not be rerun automatically.

## Full-source batch Task 2 — actual corrected descriptions (2026-10-05)

Ran uv run python -m scripts.fetch_descriptions once without private env settings
after 29 combined extraction/network controls passed. New destination was absent
and ignored. Saved the 75 fixed-revision sources into
data/description-corrections/arcwise-fe766045; total 76445 bytes. Every saved size/
SHA-256 was checked again offline. No redirects, retries, proxy/auth inheritance,
repinning, overwrites or extra files; previous label/license sources unchanged.

Initial five fake-stream failures were fixture defects: HTTPX content= responses
were already consumed, unlike stream=ByteStream responses. Isolated flags and
installed source established the cause; changed fixtures only. Strengthened late-
body fixture to prove a third late chunk is never consumed: removing the body
deadline check failed at logical 1000s (0.15s), restoration passed at 181s. Bounds
remain cooperative/180s aggregate, 20s max per HTTP I/O, 32768-byte per-source cap.
Combined 29 GREEN (0.21s), no-env full 632 passed/165 skipped (5.56s), lint/35-file
format pass. Actual persisted description mapping/layout acceptance remains Task 3.

## Full-source batch Task 3 — actual layout/count/description audit (2026-10-05)

[Audit metadata](source-audit-manifest.json) records actual acceptance: 11 immutable
read-only SQLite databases, 75 tables/798 ordered columns, 3898114 SQLite rows;
all per-table counts equal pinned native COPY counts. Full dump/75 CREATE definitions/
COPY blocks match pins and metadata; no dump SQL executed. 72 tables declare a
primary key; 105 foreign-key component records retained. Source type pairs exactly:
INTEGER->BIGINT 366, TEXT->TEXT 329, REAL->REAL 73, DATE->DATE 19,
DATETIME->TIMESTAMPTZ 11. These are declarations, not typed value equivalence.

The first actual audit failed without publishing: European Football's
Team_Attributes references Team.team_fifa_api_id without a required unique key;
Team's unique index is only on team_api_id. Read-only isolation verified its
seven table layouts/222796 rows separately. Kunal explicitly approved recording
only this SQLite schema-mismatch class as status schema_mismatch/count null.
Actual violation count is unavailable, not zero. Other SQLite errors still fail.
New real malformed-FK fixture observed RED; approved handling is GREEN, unrelated
interruption remains fatal. No source constraint/data repair or pin relaxation.

Ten FK checks completed: formula_1 779, card_games 88, codebase_community 88 violation
records; the other seven completed counts zero. European count uncheckable. These
955 records are not necessarily 955 distinct rows. Constraint validity is not
established; later import/key policy must explicitly consider these source issues.

One successful audit acceptance after the approved amendment saved an ignored
manifest. Reviewed metadata was copied with apply_patch to docs, with date, dirty
Task 3 Git state and exact source-pins hash. Original descriptions 799 records,
extra wins only; corrected 798 complete column matches. 89 original padding records
and populated unnamed financial/account row 3 in both sources preserved as
observations, not adopted runtime prose. Four/three encoding exceptions explicit.

54 batch controls pass (0.46s); no-env full 657 passed/165 skipped (5.81s), configured
822 passed/zero skips (16.75s), including 165 actual PG. Locked 27 packages, lint/
37-file format pass. No new PostgreSQL import, model/gold query or secret action.
Typed content/result equivalence, validity/exclusions, primary descriptions/labels,
ambiguity/splits and C1 remain unfinished. G0.5 remains incomplete; no benchmark score.

## Full-source batch final review (2026-10-05)

All three tasks committed at 8a37707/e4433ab/04817bf. Sole independent read-only
review of 6be261c..04817bf found no Critical, Important or Minor issues and repeated
54 batch controls (0.94s). It compared the saved documentation manifest with the
actual ignored report: identical audit fields, only four execution/provenance
additions. Source-pins fingerprint, all 75 native block pins and recorded totals
match. Parent independently confirmed those metadata relationships. No fresh
acquisition/extraction/audit, SQL, PostgreSQL import, credentials or inference.

This accepts the approved preparation scope only. The 955 source FK violation
records and European uncheckable FK count remain source issues, not waived or
repaired constraints. Matching layout/counts is not typed-content, timezone or
query-answer equivalence. Description meanings/primary selection, remaining
imports and new restricted-role security checks require the next reviewed scope.
D-040 records all retained review limits and costs; no deferred minors.

Fresh finishing verification: configured 822 passed/zero skips (14.20s), including
165 actual local PostgreSQL tests for existing boundaries; no-env 657 passed/
165 skipped (5.08s). Locked 27 packages, Ruff/37-file format/whitespace pass.
No new corpus content/answer or dataset-isolation claim follows from these tests.

## Remaining COPY preparation completed (2026-10-05)

Kunal approved the presented four-task batch by “move forward”. The proposed
metadata-only FK policy is now accepted for these ten new native imports;
California's enforced FKs stay unchanged. This is not source referential or gold
validity acceptance. No rows/keys/source bytes are repaired or dropped.
Task 1 extracted only checked COPY data into ignored
data/import-release/minidev-0703/native: ten datasets, 72 files, 991363484 bytes,
3868173 rows. All saved pins/table layouts rechecked; California excluded.
Staging publishes only after complete dump/archive/block and saved-file checks.
1200s cooperative budget/1MiB lines/1GiB reserve retained; no source SQL executed.
61 controlled extraction/audit/native checks pass; new 11 checks first RED
because the module did not exist. No database/credential/model/gold change yet.

## Fixed remaining importer completed (2026-10-05)

Task 2 creates only approved fixed target IDs and refuses existing objects.
New .env.datasets is ignored/setup-test-only, ten distinct restricted-only
secrets verified without printing; bootstrap/runtime/California files untouched.
No new login/schema/import yet. Full typed native comparison and bounded
SQLite first/middle/last samples run before transaction commit. Explicit REAL
float4, ISO date and UTC timestamp mapping is not full gold/SQLite equivalence.
69 remaining PKs will be enforced, new FKs metadata-only as approved.
32 new deterministic controls; full865passed/zero skips(17.71s),165realPG;
no-env700passed165skipped(8.15s), Ruff/41-file format/locked27 pass.
Existing cancellation timing failures are documented in D-043, not hidden.

## Toxicology actual import accepted (2026-10-05)

Four tables/36922rows/four enforced PKs, all pinned native typed rows plus twelve
representative SQLite rows match before commit. Source FKs retained unenforced,
their original zero-violation audit is not a full constraints/answer-validity
claim. 22 real restricted-role/rollback/content/count/type/key/default/grant
controls passed(1.29s), with21 absent-login RED checks observed before import.
docs/toxicology-import-manifest.json is reviewed metadata only with source
fingerprints/date/code state/import result; ignored evidence matches its fields.
Full SQLite equivalence/gold conversion/primary descriptions remain unchecked.
Existing California/source files/runtime untouched; no inference/gold SQL.

## Remaining import readiness — read-only preparation (2026-10-05)

Dedicated PostgreSQL 16 still contains only the California dataset and its login;
ten remaining target schemas/logins absent. Immutable, hash-checked SQLite source
PK aggregates find all 72 declared keys free of null rows/duplicate groups. Three
tables have no declared PK: thrombosis_prediction/examination and superhero/
hero_attribute, hero_power. This is not new PostgreSQL constraint acceptance.
All 11 codebase DATETIME columns store text/null only; no timezone/format/answer
meaning established. Existing source FK issues remain unchanged.

Remaining native footprint: 72 tables/709 columns/3868173 rows, 991363484 COPY
payload bytes. COPY bundle and .env.datasets not yet created. The proposed
[four-task plan](superpowers/plans/2026-10-05-remaining-native-imports.md) uses
native types/69 checked PKs, preserves all rows and retains new-dataset FKs as
unenforced metadata, with actual typed-native/representative/source/permission
checks. This foreign-key policy is a recommendation awaiting explicit review,
not an adopted import/validity policy. California's enforced FKs stay unchanged.

No new source acquisition, SQL/gold execution, database/role change, password
creation, model or benchmark action. Eight proposed blocks syntax-valid only.
Fresh unchanged suite822passes/zero skips(16.27s),165actualPG; no-env657/165skips
(5.77s); locked27/Ruff/37-file format/whitespace pass. G0.5/C1 still unfinished.
