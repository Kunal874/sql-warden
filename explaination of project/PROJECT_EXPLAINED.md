# SQLWarden explained in simple English

Last updated: 2026-10-12.

This is your learning notebook for the project. It will be updated after every
completed subtask and group. It explains what was built, why it matters, how it
was checked, and the new words used along the way. Future features are marked
as future work, not described as finished.

## 1. What are we building?

SQLWarden will let a person ask a question about a database in normal language.
For example: "How many schools are in this database?"

An AI model will suggest a database query. The program will check that query,
run it with strict limits and a restricted login, and show the result. If the
question is unclear, it can ask a follow-up question. If it cannot answer safely,
it should say so instead of guessing.

The important idea: AI suggests an answer, but AI does not decide its own
permissions. Real code and database permissions must enforce the rules.

This is a portfolio project that you can demonstrate and explain in interviews.
It is not a finished public service yet.

## 2. What actually works now?

- The Python project installs using its saved dependency versions.
- A separate PostgreSQL database runs on your laptop.
- Different datasets have different restricted database logins.
- California Schools plus ten more real datasets have been loaded and checked.
- The first local Qwen model has answered six small test requests on the GPU.
  Those were simple text/format checks, not database questions.
- Tests check the imported values, database permissions and setup behavior.
- A SQL guard checks query structure and allowed tables without connecting
  to a database or loading an AI model.
- Small handwritten allowed queries have passed that guard and run with the
  restricted database login and short time limits. One AI-generated query has
  now also passed the same guarded path and returned the expected school count.
- Answer-size checks now handle row, byte and cell limits without returning
  a partial answer as a complete answer. The guarded runner now also passes
  real database tests for timeouts, cancellation and recovery.
- The answer checker compares two complete database answers using the saved
  rule. Failed or oversized answers cannot be marked correct. Its final review
  is complete; it reused existing Python tools without adding a package.
- The local AI connection code now passes 67 checks using fake replies. It
  can make only one limited SQL suggestion and refuses unexpected model settings.
- The E0 experiment runner now has safer restart files for future runs. It can
  save a run fingerprint and a line-by-line record stream without putting prompts,
  SQL text, answer rows or passwords into tracked files.
- The latest full configured checkpoint has 1,251 passing tests and 3 expected
  skips after the final E0 review-fix pass. The ten-dataset release matrix alone
  has 292 real PostgreSQL checks.
- The offline answer-file checker and small download tool pass 49 checks.
  The four approved files match their saved fingerprints. Their summary lists
  missing items and changed wording; it does not contain the answer text.
- All 11 source databases and both sets of 75 column-description files are local.
  The ten previously missing datasets are now in PostgreSQL: 72 tables and
  3,868,173 rows. This proves checked loading, not that every question has the
  correct answer or that every SQLite query behaves identically.
- The corrected answer pool is now selected for C1. It has 424 verified questions.
  The project saved only IDs and summary labels, not private question text, SQL,
  answer cells or credentials.

The first narrow AI question-to-database flow works for one checked question.
The first local E0 evaluation is now corrected and recorded. The G1 local agent
core is implemented through schema retrieval, prompts, voting, clarification seams
and command-line loop settings. G2 has now recorded guard, cost, direct database
permission, tenant-row-security, untrusted-data, attack-suite and SECURITY
evidence through G2.9. The website and public release are not finished. G0's
numbered checklist is complete except for the optional interview drill.

Where we are: 12 of the 12 numbered foundation tasks are complete. The query
guard, limited runner, answer checker and first AI command are checked and
reviewed. This is not the whole project's progress percentage: the agent,
experiments, website and release still come later. The first small working
demonstration, corrected E0 run, C2 model choice and G1 core implementation are
complete locally. G2.1 through G2.9 are complete locally. G3.1 is now complete
locally. G3 is now complete locally; website and release still remain.

Update 2026-10-11: G4 (the local website) is complete and works with the real
model and database. G3's experiment *plan* was frozen earlier, but most of the
experiments themselves (E1-E8) had not been run; running them is the next step.

You approved the answer-checker plan. Its small comparison function passes
60 unit checks and 17 real database checks. Its independent review found no
actionable issues and repeated all 60 unit checks successfully.
You approved the three-part AI command-line plan and its two software additions.
All three parts' code and database checks pass, and the single real question
worked. Model unload, independent review and verified corrections are complete.
You approved the next two-part data-work plan. Its offline checker is built
and checked, and the four approved small source files have been saved and checked.
The independent final review is complete. It found one time-limit gap, now fixed
and checked. No extra model test or database import ran.
The three-part source-preparation batch and its independent review are complete.
The four-part native-import implementation and its one final read-only review
are complete. Source key problems are visible, not silently repaired.

## 3. Completed work, one step at a time

### G0.1 — Check the laptop and agree on the basics

What was done: checked the available software, disk space, graphics card,
memory and local connection ports. Confirmed your Git identity, permission to
install missing tools, and a weekly budget of 15–20 hours.

Why: the project needs to fit your laptop and your time. We should discover
problems before downloading large files or building a lot of code.

Checked: Python 3.12 is available; Docker and uv already existed in local
locations; native Ollama was installed. Your graphics card has about 8 GB of
graphics memory. The existing PostgreSQL 17 service was left alone.

### G0.2 — Set up the project and its saved history

What was done: created the local Git repository and the project's instruction,
progress and decision files. Added rules that keep passwords, model files,
downloaded datasets and temporary output out of Git.

Why: Git lets you see exactly what changed. Written progress lets the next
session continue without starting everything again.

Checked: commits use your confirmed name and email for both author and committer.
No remote is configured. Creating a local commit does not upload it to GitHub.

### G0.3 — Build a small, tested Python foundation

What was done: created the Python package and saved dependency versions. Added
checks for query limits, such as maximum rows, bytes and time.

Why: even a query that only reads can use too much memory or take too long.
These limit values will be used by the query runner later.

Checked: the first 40 automated tests passed. They check real limit behavior,
including rejecting bad values. A limit definition is not the same as an
implemented query runner; the runner is still future work.

### G0.4 — Build the first database permission boundary

What was done: started a separate PostgreSQL 16 database in Docker, accessible
only from this laptop. Created two small made-up datasets for permission tests.
Each reader can read only its own dataset. A separate application login can
write only to application tables. The setup administrator is kept separate.

Why: telling an AI "do not change data" is not enough. The database itself
must refuse actions that its runtime login is not allowed to perform.

Checked: tests connect directly to the database, without a SQL guard, and try
forbidden actions. They check writes, access to other datasets, changing roles,
temporary tables and selected risky functions. A later review found an unused
large-object feature that still allowed writes; its permissions were removed
and the tests were rerun.

The database's saved data volume and passwords were preserved. These checks
prove the tested cases, not that every possible database attack is solved.

### G0.5a, source preparation — Choose and verify one real dataset

What was done: downloaded a particular BIRD Mini-Dev release and its question
files. Recorded file sizes, source versions and SHA-256 fingerprints. Selected
only California Schools and its descriptions, rather than importing every
database immediately.

Why: one small real database is enough to build the first useful version.
Recorded fingerprints help detect changed or damaged source files.

Checked: both question files have 500 matching unique question IDs. There are
some wording differences across the full release, and those differences are
recorded. The 30 selected California questions have no question/evidence
wording differences between the checked dialect files.

Downloaded files stay local and are not committed. Reference SQL has not been
run or sent to an AI model.

### G0.5a, Task 1 — Extract only the needed native data

What was done: built a reader that keeps only the data rows for schools, frpm
and satscores from the verified PostgreSQL source. It does not execute the
downloaded SQL script. It checks table names, column order, file limits,
fingerprints and whether any required data block is missing or repeated.

Why: a downloaded setup script can contain administrator commands and data
for unrelated databases. We want the selected data, not permission to run all
the commands in that script.

Checked: failure tests reject damaged, oversized or incomplete inputs without
publishing a partly extracted result. Existing files are not overwritten.

### G0.5a, Task 2 — Import with a separate restricted reader

What was done: created the California tables from checked column information
and loaded only the selected native data. Created a separate California reader
and a private credential file. The setup steps use one database transaction.

Why: native PostgreSQL values can differ from SQLite values. Keeping the native
types and values avoids quietly changing the dataset just to make it load.
Keeping setup and runtime credentials separate stops the normal program from
using an administrator login.

Checked: the imported tables contain 17,686 schools rows, 9,986 frpm rows and
2,269 satscores rows. Keys and relationships are valid. The California reader
can read its data but is denied the tested writes and unrelated tables. Other
runtime readers cannot read California. Repeating the import refuses the
existing target instead of resetting it.

### G0.5a, Task 3 — Check real content and save its history

What was done: compared all imported typed values with the native source, not
just the number of rows. Recorded column types, keys, missing-value counts,
data fingerprints and source versions in a small manifest. Connected all 89
column descriptions to their matching columns.

Why: two tables can have the same number of rows but different values. Counting
alone is not a reliable import check.

Checked: changing one value without changing the row count is detected by the
content checker. The test change is rolled back. Four description names had
extra spaces; only those description-name spaces were trimmed, with exact
matches recorded. Source data, SQL names and question labels were not changed.

This checks the import. It does not prove that SQLite and PostgreSQL always
return the same answer, or measure how accurate an AI model is.

### G0.5a, final review fixes — Close two remaining gaps

What was done: removed runtime access to the unused postgres and template1
databases. Their permissions are separate from the sqlwarden database's
permissions. Also made California-specific tests wait for California setup
instead of trying to run too early.

Why: a restricted login should not escape into another database with different
permissions. First-time setup should work before a real dataset is imported.

Checked: nine new tests first failed, then passed after the fixes. All four
runtime logins are denied connections to both unused databases. The complete
suite has 158 passing tests. Without the separate California environment,
California tests skip; when that environment is supplied, missing setup fails.

The data volume, existing rows and credentials remain intact. The original
PostgreSQL 17 service was not changed. Work is saved locally through commit
15616d4. Nothing has been pushed or published.

### G0.6a — Check the first AI model on your laptop

What was done: downloaded the selected Qwen model once and checked its exact
file fingerprints. Made a local model setting with a small 2,048-token working
space and a short answer limit. Asked only tiny test questions, such as returning
a fixed word or giving 2+3 in a simple JSON object. No database data, passwords
or reference answers were sent to it. No SQL was executed.

Why: before building the question-answering flow, we need to know whether the
model actually runs on this laptop and which response features work.

Checked: the first request reached its 60-second limit during startup/first use.
The model did load. After it was ready, all six small checks succeeded: ordinary
text, two JSON formats, two requests with the same seed, and a two-token output
limit. The warmed short text reply took about 3.8 seconds. This is not an
accuracy score or a promise about future database queries.

Ollama reported that the model ran entirely on the GPU; no CPU fallback was
needed for this small test. Its own reported GPU memory was about 4.3 GiB.
After testing, the model was unloaded to release that memory, so you can use
Chrome and your other programs normally. The downloaded model file stays on disk
for the next run. The startup timeout is recorded, not hidden.

Technical measurements and limitations are in [MODELS](../docs/MODELS.md).

### G0.7a preparation — Plan the first SQL safety check

What was done: read the saved build rules and wrote a step-by-step plan for the
SQL guard. This will be the code that checks a proposed query before it can run.
Also read the official BIRD answer-checking code and saved its exact version and
file fingerprints. The downloaded code was only read, not run.

Why: safety checks must come before connecting AI answers to the database. The
answer checker must follow its published rules, not rules chosen to improve a score.

Checked: all 158 existing tests still pass. The scoring source ignores repeated
rows when comparing answers; later result voting needs separate rules that keep
repeats. No AI model was loaded, no new package was installed, and no new SQL
guard was built in this preparation step.

At that preparation checkpoint, the plan and proposed SQLGlot addition still
needed your review. You approved them on 2026-10-04. The limited query runner,
answer checker and AI-connected demo come afterward; G0.7a is not finished.

### G0.7a, guard Task 1 — Build the query safety checker

What was done: installed the exact approved SQL-reading package and checked
its downloaded fingerprint. Built a checker that reads a query's structure,
looks inside its small named queries and nested queries, and checks which real
tables they use. It refuses writes, unreviewed functions and forbidden tables.

Why: a query starting with SELECT can still hide a forbidden action. Looking
for a word such as DROP is not enough: that word might just be a harmless
comment or text value. The checker reads the structure instead.

Checked: wrote tests before the checker and saw them fail because it was
missing. Now all 184 guard checks pass. They include quoted names, hidden
tables, unknown features and exact size boundaries. Accepted SQL is returned
unchanged; rejected SQL is not returned for execution. All 342 project tests
pass, including the existing 67 real database checks.

The checker refuses queries it cannot understand. It limits query size and
the size/depth of the structure it reads. Errors give a short category rather
than repeating private input. Two extra test assumptions were corrected after
reading the approved rules and parser API; the safety rules were not expanded.

This step checks SQL without running it. The next step checks a few handwritten
allowed queries with the real restricted database login. The limited runner,
answer comparator and AI-to-database flow are still unfinished.

### G0.7a, guard Task 2 — Check allowed queries with the real database

What was done: tested a small set of handwritten queries with the guard, then
ran the accepted text using the restricted California reader. Each test checks
the real login and sets a read-only transaction, a five-second query limit and
a half-second lock-wait limit. Checked counts, small joins, named queries,
allowed calculations and type conversions.

Why: a parser is not PostgreSQL. The guard can understand a query while the
database rejects a missing column or invalid type. Real checks tell us whether
our permitted examples work with the actual database and login.

Checked: all 56 new database tests pass. The known school count is 17,686.
Every allowed function and type has a small test. Also checked the database's
built-in function/operator/type definitions. Their reviewed implementations
are built-in routines, not custom functions from another schema. One test's
catalog lookup used a type alias rather than its stored name; that test lookup
was corrected. Permissions, source data and the guard policy were not changed.

The full project now has 398 passing tests. Without the private database test
files, 275 pass and 123 database checks skip; with setup only, 318 pass and 80
skip. With both files, all 398 run and pass. Skipped tests are not called passed.

The guard and database permissions do different jobs. The guard decides which
query shapes and tables we permit. PostgreSQL permissions refuse things the
login must not access even if the guard has a bug. The read-only transaction
adds another protection. We need all of them, plus the future result/time limits.

This is not the AI question-answering flow or an accuracy score. The limited
runner and answer checker still come next, after this increment's final review.

### G0.7a, guard final review — Fix unusual input and protect logs

What was done: one independent read-only review found two real problems. Two
unusual function calls could crash the SQL reader. A wrongly formed named query
could put its text into a warning log; one unused version was even accepted.

Why: a safety check must refuse input it cannot understand. It must not crash
or copy private query text into its error messages and logs.

Checked: wrote tests that showed both problems before fixing them. The SQL
reader now turns these crashes into a short rejection category. Malformed named
query bodies are refused before the code that produced the warning runs. Good
named queries and small VALUES examples still pass, with no SQL rewriting.
The original parser warning protection was useful, but did not cover this second
warning path. We did not silence the computer's logging or change database rights.

All 193 guard tests now pass. The complete project has 407 passing tests,
including 123 real database checks; the 56 guard-to-database checks still pass.
Without private database test files, 284 pass and 123 skip. With setup only,
327 pass and 80 skip. With both files, every test runs and passes.

Your learning notebook, progress and decisions were updated. The code stays in
your local Git branch; nothing was uploaded to GitHub. The review's limitations
are written down rather than treated as proof. The imported data and passwords
were not changed, and no AI model was loaded for this work.

This finishes the first query safety checker, not the whole foundation group.
The limited query runner and answer checker must come before running AI SQL.

The technical [guard plan](../docs/superpowers/plans/2026-10-03-minimum-sql-guard.md)
and [scoring-source record](../docs/EX_COMPARATOR.md) hold the exact details.

### G0.7a, executor preparation — Plan the limited query runner

What was done: wrote and checked the next implementation plan. The runner will
use our existing query guard and the restricted California Schools login.
There is no new package, download or AI model load for this preparation.
The runner itself has not been built yet.

Why: a query can be allowed to read and still take too long or produce a huge
answer. The guard checks what is allowed; the runner will limit time and output.
If only part of the answer fits, it must not pretend that part is the full answer.

The plan has three parts: test the answer-size rules, build the guarded runner,
then check it with the real database. It plans for timeouts, cancelled work,
wrong settings, private error messages and reusing a connection after failure.
No AI SQL will run until the runner and answer checker also pass their checks.

Checked: all 407 existing tests passed again, including 123 real database tests.
The code-style checks pass. The database is healthy and no model is loaded.
The proposed code examples were checked for valid Python syntax only; this
does not prove the future runner works. No imported data or password changed.

Read the technical [runner plan](../docs/superpowers/plans/2026-10-04-bounded-sql-executor.md).
The planning skill requires your review of this new plan before coding begins;
the previously selected single-worker approach stays the same.

### G0.7a, executor Task 1 — Build the answer-size rules

What was done: added the first part of the runner. It counts rows, text bytes
and individual cell size. If the answer is too large, it throws away the
unfinished answer and returns a short reason. It also checks the database's
rough work estimate against the approved starting limits.

Why: two answers can have the same first rows but different rows later.
We must not call them equal just because their first page matches. Missing
values and an empty answer can also be correct, so those are not automatic errors.

Checked: tests first showed the missing module and new settings. After building
this part, all 88 answer/plan/config checks passed. The full project now has
455 passing tests, including 123 checks with the real database. The code-style
checks pass. These are still pure budget rules, not a running AI-to-database flow.

No new package or model was installed or loaded. Your data and passwords were
not changed. Next is wiring these rules to one restricted database connection.

### G0.7a, executor Task 2 — Build the guarded query runner

What was done: connected the safety checker and size rules into one small
runner. It first checks the query, then uses only the restricted California
Schools login. It checks the actual login and time settings, asks the database
for a rough work estimate, and collects the answer one row at a time.

Why: a caller must not be able to skip the checker or choose a powerful login.
The runner must also finish on time, reject an oversized answer without keeping
its first rows, and hide private database error messages.

If work is cancelled or fails, the runner closes that connection immediately.
For normal completion it rolls back the temporary work and returns the connection
for reuse. Real tests must still prove that the database stops the cancelled
work and that the next query gets a working connection.

Checked: the new tests first found the missing runner. All 94 simulated runner
checks now pass, including waiting, cancellation, errors, wrong settings and
pool opening/closing. The full suite has 511 passes, including 123 earlier
real-database checks. Those earlier checks do not prove this new runner yet.
No AI SQL, new package, data change, password change or model load occurred.

Next: run the planned handwritten checks through this runner on real PostgreSQL.

### G0.7a, executor Task 3 — Check the runner with real PostgreSQL

What was done: ran 18 new checks using the real restricted login and our real
school data. Checked complete answers, empty answers, missing values, duplicate
column names, ordering and exact size limits. Large answers return no first-page
prefix. Queries rejected by the guard still do not run.

We also made a bounded handwritten query run long enough to cancel it. The test
watched the database process disappear, then confirmed that the same pool could
run the next query. A separate short timeout test also recovered. Temporary
time settings reset and no transaction was left open after normal release.

One full run found a test-setup issue: its very short waiting limit also applied
while making the first database connection. The test now separates opening the
connection from waiting for an occupied slot. The actual runner's limits were
not increased. The corrected waiting test passed five repeated runs.

That failed test also printed a private test password through a library error
report. With your approval, only that test-login password was replaced. The new
password works, the old one is rejected, and permissions were not changed.
Future test output uses short failure lines to avoid dumping connection details.
Passwords remain in ignored local files, never in Git or AI prompts.

Checked after the fix and rotation: all 18 runner database checks pass, and the
full suite has 529 passes with no skipped tests. Of these, 141 use real PostgreSQL.
The package lock and code-style checks pass. Your data and other passwords are
unchanged, no model is loaded, and nothing has been uploaded.

This finishes the runner's three build/test subtasks. One final read-only review
comes next. The answer checker and command-line demonstration are still needed
before the AI can safely run a database query.

### G0.7a, executor final review — Check the finished runner once more

What was done: an independent read-only review checked the finished runner,
its plan and tests. It found no concrete issue to fix and ran all 144 focused
runner/settings checks successfully. It did not use your passwords or load a model.

I then reran the full project tests: all 529 passed, including 141 checks using
real PostgreSQL. The code-style and saved-package checks also passed. The database
is healthy and the model remains unloaded. Your rotated test password works,
and the previous one is no longer valid.

What this does not prove: answer-size limits are not a guarantee that the program
can never use too much memory. Work estimates can be wrong. Database administrator
logs have their own rules. Other datasets, the answer checker, AI loop and website
still need their own checks. These limits are recorded in the technical decisions.

The code stays on your existing local branch. Nothing was uploaded, merged or
deleted. The project reused its existing checker and database packages instead
of adding new ones. The final review completes the limited runner, not the whole
foundation group. Next is the answer checker, then the first command-line demo.

### G0.7a, answer-checker preparation — Plan how to check an answer

What was done: wrote the next two-part plan. First, build a small answer checker.
Then, check it using small handwritten queries on the real database. The checker
will use the complete answers from our existing runner, not just the first page.
No new package, AI model load or database change was needed for this preparation.

Why: we need a clear rule before saying an AI answer is correct. I rechecked the
saved BIRD rule: row order and repeated copies of a row do not matter, but the
order of values inside a row does. For example, rows [1, 2] and [2, 1] are not
the same two-column answer. Close-looking numbers will not be rounded into a match.
An empty answer can be correct. A failed or oversized answer cannot count as correct.

If the reference answer fails, the checker will flag it as not ready for scoring.
That does not mean deleting the question or changing the number of test questions.
Those decisions belong to the later fixed benchmark rules. The reference answer
must never be shown to the AI while it is answering or fixing a query.

Checked: the original comparison files still have their saved fingerprints.
The three planned Python examples pass syntax and code-style checks without being
run. The plan contains 60 future unit checks and 17 future real-database checks;
these have not passed yet because the checker has not been implemented.
All 529 existing project tests passed again, including 141 real database checks.
Without private test configuration, 388 passed and 141 skipped; with setup only,
431 passed and 98 skipped. No AI SQL or benchmark question was run.

Read the [answer-checker plan](../docs/superpowers/plans/2026-10-04-ex-comparator.md).
The writing-plans skill requires your review of this new plan before implementation.
The already selected single-worker approach stays the same. This completes only
the preparation subtask, not the checker or the foundation group.

### G0.7a, answer-checker Task 1 — Build the small comparison function

What was done: built the checker you approved. It receives two complete answers
from the runner and returns only a match, mismatch or short failure category.
It does not ask an AI model, run a query, read a password or show the reference rows.
The project reused its existing answer type and Python's built-in sets; no new
package was needed.

Why: different SQL text can produce the same answer. We must check the results
using the saved rule, not guess from the query text. Repeated rows and row order
are ignored; column positions matter. Empty answers and missing values can be
correct. Very close numbers are not rounded into a match.

A failed or oversized prediction gets zero, even if its first rows would match.
A failed reference gets a "reference not usable" marker, not a permission to
delete that question. The later benchmark rules will handle it openly. This
checker is not the future voting rule and does not calculate an AI accuracy score.

Checked: wrote the tests first and saw them fail because the checker did not
exist. After building it, all 60 unit checks passed. They cover complete/failed
answers, repeated/order-swapped rows, column positions, missing values, numbers,
dates and safe failure output. The whole project without private database test
files has 448 passing tests and 141 skips. Style/format checks pass. The 17 planned
real-database checks and one independent final review come next, without needing
another approval from you. No AI-generated SQL has run.

New term: **immutable result** means the returned record cannot be changed in
place after the checker creates it. It holds just a score and short reason, not
the full reference answer or a private error message.

### G0.7a, answer-checker Task 2 — Check real database answers

What was done: added and ran all 17 planned checks on the real PostgreSQL
database using the existing restricted login and runner. These were fixed test
queries, not SQL from SQLWarden's Qwen model. No benchmark question or reference
query was run.

Why: a small Python example can pass while the real database returns a different
kind of value. We checked real numbers, dates, text, missing values and empty
answers. Repeated rows and row order behave as planned; swapping column values
does not match. Close numbers are not rounded into a match, and dates are not
secretly compared as text.

The tests also force an oversized answer and an ordinary query error on each
side. A bad prediction is not correct. A broken reference gets flagged, not
quietly removed. After a failed query, the same runner can answer the next query.
Private error-canary text does not appear in the returned messages or captured logs.
An attempted DELETE is rejected by the guard; the database does not run it.

Checked: all 17 real checks passed. The full project now has 606 passing tests,
including 158 real PostgreSQL checks, with no skips when both private test files
are supplied. Without them, 448 pass and 158 skip; with setup only, 491 pass and
115 skip. The saved-package, style and format checks also pass. No new package,
model load, password, permission or imported-data change was needed.

These are checks of code behavior, not an AI accuracy score. One final independent
read-only review of both checker tasks comes next. The AI command-line demo,
later benchmark rules, voting, website and release are still unfinished.

### G0.7a, answer-checker final review — Finish and record the checks

What was done: an independent, read-only code review checked both completed
checker tasks against the approved plan. It found no actionable issues and ran
all 60 unit checks successfully. No code correction or second review was needed.
The full project tests were also run again: 606 passed, including 158 real
database checks, with no skips. The reviewer repeated the small unit checks,
not the real database tests; these are two different kinds of evidence.

Why: building something and checking it against its rules are different jobs.
The review also records what we have not proved. The checker expects complete
answers from our trusted runner; it cannot make a broken reference answer valid
or decide which benchmark questions to remove. It is not the future voting rule.
Later AI wiring must keep reference answers away from the model and keep its
own time and memory limits. Passing tests is not an AI accuracy score.

Saved: both checker tasks are committed under your Git identity. The learning
notes, exact checks and review limits are recorded. Everything stays in the local
project; nothing was uploaded to GitHub or deleted. The guard, runner and checker
are now complete, but the command-line AI demonstration is still not built.
The next step is to prepare its separate plan for your review.

New term: **read-only code review** means checking the code and evidence without
changing project files, passwords or data. It gives another check, not a promise
that every possible problem has been found.

### G0.7a, AI demo preparation — Plan the first question-to-database flow

What was done: wrote and checked a three-part plan. First, build the small piece
that talks to the existing local Qwen model. Second, connect it to a command-line
tool that accepts one question and uses the already tested guard and query runner.
Third, check that flow with the real database, then try just one real model question.
Nothing in that new plan has been built or run yet.

Why: the model must not get extra permissions just because it writes the SQL.
The first demo will use the same restricted login, query checks and answer-size
limits as the handwritten tests. It has no "run any SQL" switch or unlimited
retry. One successful answer would show the pieces work together; it would not
prove the AI answers most questions correctly.

The first model prompt will describe only four columns of the schools table.
It is like giving someone a small, clear map for one exercise, not the full map
of the database. The proposed question is "How many rows are in the schools
table?" The model will not be told the expected answer or the database password.

The plan proposes two packages, openai and httpx. A package is reusable software.
The first gives a standard way to send model requests; the second carries those
requests. Despite the openai package name, this plan sends the prompt only to
Ollama on your laptop, not a paid online service. They are not installed yet.
Their actual versions and behavior will be checked after your approval.

The demo would also get its own private runtime settings file. A setup-only
helper would copy just the existing restricted password into that new file,
without changing the password or copying administrator settings. It will refuse
to overwrite an existing file. No new settings file was created, and no password
was copied or shown in this step. Existing private settings were used only for tests.

Checked: all eight Python examples in the plan have valid syntax, and the six
planned files pass static style checks. This is checking the instructions, not
running the future feature. The existing project still passes 606 tests, including
158 real database checks. No new model question or AI-written SQL was run.

Next: review the [AI demo plan](../docs/superpowers/plans/2026-10-04-safe-local-cli.md).
After approval, build and test its three small parts one at a time. The foundation
is still 6 of 12 numbered tasks complete; the rest of the agent, experiments and
website are not finished. The plan keeps the demo small and reuses existing code.

### G0.7a, AI demo Task 1 — Build the limited local AI connection

What changed: added the approved OpenAI SDK and HTTPX packages. Here the SDK
talks only to Ollama on your laptop; it does not send your question to OpenAI.
The code checks the exact saved Qwen model and allows one SQL suggestion.
It allows one short model startup request if needed, then one answer request,
with time and size limits. It never receives a database password or an answer key.

Checked: wrote tests before the code. All 37 AI-connection checks pass with fake
HTTP replies, so these tests did not load a model. The full suite passes 643 tests,
including 158 real database checks. One existing stop-query timing check failed
once, then passed alone, with its whole group and with the full suite; we did
not change its time limit, and have not proved why that first timeout occurred.

Why it matters: a model name alone is not enough. We also check its fingerprint
and small context limit. Unexpected inherited SDK settings are refused before
connecting, because they could put extra private information in a request.

New words: **transport** is the part that carries a request to another program.
**JSON** is a structured text format; here we accept exactly one field called sql.
**Retry** means trying again after a problem; this demo does not automatically
retry. **Cleanup confirmation** means the HTTP connection closed; it does not
mean the model stopped using the graphics card. We check that separately later.

### G0.7a, AI demo Task 2 — Connect the question to the safe runner

What changed: added the sqlwarden terminal command. It checks your question
and settings first, asks the local model once, checks the suggested SQL and
uses the existing restricted database runner. A separate setup helper will
make a private runtime settings file; it never gives the runtime an admin login.
The real settings copy and real AI question have not happened yet.

Checked: 39 command-flow tests pass, alongside the 37 AI-connection tests.
The whole suite without private settings passes 524 checks and skips the 158
real database checks. The full configured suite also passes all 682 checks.
Help commands work without contacting a model or database.
Tests cover bad questions/settings, dangerous SQL, cancellation, empty answers,
missing values, oversized answers, and errors without private information.

In simple words: **one candidate** means the AI offers one possible query, not
several answers voting together. **Answered** means the permitted query ran and
returned its whole result; it does not prove the AI understood your question.
**Blocked** means a safety check refused it. **Failed** means another limit or
problem prevented an answer. There is no made-up confidence or accuracy number.
The **preview** shows at most 20 rows only after the whole bounded answer is
received. It is a display shortcut, not a partial answer treated as complete.
Token usage stays unavailable when the model does not report it.

### G0.7a, AI demo Task 3 — Try one real question safely

What happened: tried the agreed question, "How many rows are in the schools table?" The local
AI suggested a query; the guard allowed it; the restricted runner executed it.
It returned the expected count, 17,686. The entire command took 11.387 seconds,
including startup and database work. There was one startup request and one AI
answer request, with 89 input tokens and 18 output tokens reported by the model.
We did not try again, change the prompt or send the expected answer to the AI.

Before that: all seven real database command checks passed, then the whole
689-test suite passed. Afterward it passed again, including 165 real database
checks. A private runtime file holds only the existing restricted password;
it was copied with your approval and is never uploaded or shown.

An unload command was blocked by the tool before it ran. We are checking the
model's automatic expiry instead; closing the connection is not proof the
graphics memory is free. At 22:35:16, Ollama reported no loaded models, so
automatic unload is confirmed. The final review is next.

What this proves: our first small path works from an English question to a
limited real database answer. What it does not prove: that the AI answers other
questions correctly, that it is safe against every attack, or that the project
is finished. An **acceptance check** means a particular agreed demonstration
passed. A **benchmark** tests a frozen collection fairly and reports measured
results; we have not done that yet. **Keep-alive** means Ollama temporarily
keeps the model ready; it has a finite expiry rather than staying loaded forever.

### G0.7a, AI demo final review — Close two unusual reply gaps

What changed: a separate read-only reviewer checked this three-part change once
and repeated 76 small tests. It found two real problems in how unusual replies
were accepted. We checked the findings, wrote tests that failed first, fixed
them, and then watched the full suite pass all 719 tests. There were no critical
findings or small issues left for later, and no second AI question was asked.

First problem: if one token count was missing or wrong, the program forgot the
other count too. A known oversized count could then slip past its check. Each
count is now checked separately; we keep valid numbers and mark missing ones
unavailable. Second problem: a reply could have the wrong sender label or badly
shaped tool/refusal fields. Now it must be an assistant reply with permitted
fields before its SQL can reach the database runner. The SQL guard stayed active
even before these fixes; the findings were not a proven permission bypass.

New words: a **message role** says who a message is from, such as user or
assistant. A **message envelope** is the wrapper around its text, including that
role and any tool/refusal fields. A **refusal** says the model did not provide an
answer. A **malformed field** has the wrong shape, such as a number where a list
is required. Checking the wrapper matters as well as checking the SQL inside.

The new tests use fake replies only: 30 additional cases, with 27 failing before
the fixes and all 30 passing afterward. Client/command checks now total 106;
165 of the 719 full checks connect to real PostgreSQL. The earlier live demo
record is preserved exactly, including its original code checkpoint. We did not
quietly repeat it on the corrected code and call that a new measured result.

Decisions and limits kept, in the order made (full technical record: D-031):

1. Used your existing project folder. Cost: no extra isolation from other local edits.
2. Wrote all AI-connection tests before its code. Cost: only the plan's test order changed.
3. Wrote all command tests before its code. Cost: again only the test order changed.
4. Refused inherited private SDK settings. Cost: this command cannot run with those settings present.
5. After the tool blocked the unload command, observed automatic expiry instead. Cost: graphics memory stayed occupied longer; no explicit stop time was measured.
6. Reviewed all three new task commits, not older completed components. Cost: an old defect could escape this particular review.
7. Kept your local branch without merging/uploading. Cost: integration and publication wait for later approval.
8. Kept this plan's ignored temporary notes. Cost: a small amount of extra local disk space.
9. Accepted earlier completed component reviews, checking their connection points here. Cost: no new full inspection of their internals.
10. Used the recorded real-database/live evidence, labelled separately from the reviewer's tests. Cost: the reviewer did not independently repeat those real runs.
11. Left the earlier timing failure honestly unexplained. Cost: that intermittent test timeout might return; no limit was relaxed.
12. Kept the small text-byte rule, not an exact tokenizer. Cost: it cannot promise every prompt avoids model truncation.
13. Kept cooperative time/size limits, not hard process or memory isolation. Cost: work or allocations may outlive those logical limits.
14. Trusted local Ollama without locking out other programs. Cost: privileged concurrent changes can undermine a checked model configuration.
15. Assumed a trusted local folder for the password copy. Cost: a hostile local administrator could interfere with private files.
16. Supported a fresh one-question command, not shared concurrent library use. Cost: shared use could mix cleanup information or change other SDK logging.
17. Checked reply fields that affect execution, not unused IDs/timestamps/indexes. Cost: malformed unused metadata can pass.
18. Kept the demo narrow. Cost: full schema, accuracy, retrieval, repairs, voting, website and hosting are still future work.

G0.7a, the first safe end-to-end slice, is now complete. G0 itself is not:
remaining datasets/validity, the second model and fair measured evaluation still
come next. This is 7/12 foundation checklist items, not 58% of the whole project.
Everything stays local, with passwords outside Git and no active model loaded.

### G0.5, preparation — Check which corrected answers belong together

What was done: checked the existing download and looked at the correction
source without changing the database. Wrote the next small implementation
plan. This finishes preparation only; the new checker is not built yet.

Why: a benchmark is like an exam for the AI. Before marking its answers, we
need to know that the exam questions and the answer key refer to the same
items. If the answer key itself changed, that must be visible.

What we found:

- The original download already contains all 11 database files. We do not
  need to download that big archive again.
- Each corrected answer set has 498 items. The original has 500. Items 119
  and 120 are absent from both corrected sets.
- Item numbers are stored as text in the corrections and as numbers in the
  original. The items are also in a different order. Match their item number,
  not their place in the list.
- The set called SQL-only still has question or hint text different from
  our original copy on 141 items. The other set differs on 229 items.
- A wording change does not automatically mean the old question was unclear.
  Some differences may come from which earlier copy was corrected. We have
  not decided which answers or ambiguity labels to use.
- The source also lists 75 corrected column-description files. We counted
  the files, but have not applied their descriptions or changed any tables.

Checked: the existing archive and original answer files still match their
saved fingerprints. The unchanged project passed 719 tests again, including
165 checks using the real PostgreSQL database, with no skipped tests. No AI
model request or gold-answer query ran in this preparation.

Next plan: build an offline checker, then save only four small pinned
correction and license files, about 645 KB in total. The checker will list
missing items and changed text. It will not run their SQL or tell the AI the
answer key. It will not silently pick a new exam or change its score.

Your approval of the earlier AI command-line plan has already been used.
The Handoff requires you to review this new data-work plan before its code
or saved correction files are created. This is a required review checkpoint,
not a request to repeat completed work. We remain at 7 of 12 foundation tasks;
the full foundation group is not finished.


### G0.5, correction Task 1 — Build the offline answer-file checker

What was done: built a small program that checks file fingerprints, then reads
the answer files and pairs items by their number. It refuses repeated numbers,
repeated JSON fields, wrong kinds of values and files that exceed their limits.
It lists missing items and changed wording using item numbers only.

Why: the answer key must be checked before we use it to judge the AI. Finding
the same item number and database name does not prove its wording or answer is
correct. This checker does not run SQL, ask the model or choose our answer key.
The full answer text stays out of the saved summary and the future AI prompt.

Checked: all 39 new checks pass. The full run without private database settings
passed 593 tests and skipped 165 database tests. We have not rerun those real
database checks yet in this task. One very large test first failed because
Windows could not store its huge test name. Giving it a short name fixed that;
the large input and the file-size rule stayed exactly the same.

New words: a parser turns stored text into values a program can use. JSON is
one common way to store lists and named fields. A duplicate field repeats the
same name; different readers might disagree about which value to keep, so we
refuse it. A difference report lists changes; it is not an exam score.

Next: save only the four approved correction/license files, check their exact
fingerprints and record actual item differences. We have not saved those files
in this task. The final review and the rest of the foundation still remain.

### G0.5, correction Task 2 — Save and check the small approved answer files

What was done: saved the two correction files and their README/license in a
private-to-this-project folder that Git ignores. Total new source content is
about 645 KB. The tool accepts only the four saved URLs and fingerprints,
refuses an existing folder, and shows the final folder only when all files pass.

Why: an incomplete or changed answer key must not look ready for use. We also
need a small record of where the answer files came from and which checks passed.
That record contains item numbers and counts, not the full answer text.

What we found: both correction sets have 498 items, missing 119 and 120 from
the original 500. The database names line up. Their question/hint wording
differs from the original on 141 and 229 items. Between the correction sets,
148 items have different question or hint text. None of these counts is an
AI accuracy score or a decision that those questions are ambiguous.

Two corrected items, 1507 and 1528, store their hint as null. Null means no
value was supplied; it is not automatically the same as an empty string.
The checker initially refused this format. A new test failed first, then
passed after supporting null only for corrected hints and keeping it unchanged.
We did not edit the source files, remove items or choose a new exam policy.

Checked: 40 answer-file checks and 8 fake-download checks pass. The real files
passed all fingerprints and expected alignment checks. The full project passed
767 tests, with no skips, including 165 real PostgreSQL checks. Without private
database settings, 602 passed and 165 were skipped. No AI request or gold-answer
SQL ran; the database tests checked the already built project controls.

New words: staging is a temporary work area before files are marked ready.
All-or-nothing publication means either the whole checked folder appears or
none of it does. Identity alignment means item numbers and database names agree;
it does not prove the question or SQL answer is correct. A null hint stays a
null hint until we explicitly decide how a later experiment should use it.

Next: one fresh final review of these two tasks, then remaining descriptions,
database imports and conversion/answer-validity work. Foundation stays at 7 of
12 tasks because this finishes only one part of the larger data task.

### G0.5, correction final review — Check time even when bytes arrive slowly

What was done: one fresh reviewer checked the two completed tasks without
changing files or running models. The source summary still matches the real
files, all fingerprints pass, and the corrected hints keep their original values.

The reviewer found one problem: the download library waited to collect 4096
bytes before our code checked the time. Very slowly arriving bytes could keep
that wait going. We first made a fake stream reproduce this, then changed the
loop to check time after each delivered chunk. The fake test now stops at 120
simulated seconds instead of waiting through 1000. No long real download was
needed, and the four already checked source files were not downloaded again.

Checked: 49 answer-file/download checks pass. The full corrected project passed
768 tests, with zero skips, including 165 real PostgreSQL checks. Without private
database settings, 603 passed and 165 were skipped. The review and its one fix
pass are complete; no second review was needed and no minor finding is deferred.

New words: a chunk is a small piece of incoming data. Buffering means collecting
pieces before passing them on. An inactivity timeout notices a gap with no bytes;
it does not notice a slow stream that keeps delivering bytes. A cooperative
deadline works when our code can check time. It is not a promise that Windows
will forcibly stop every blocked operation at that exact instant.

Limitations kept visible: matching item numbers is not proof the SQL answer is
right; we still have not chosen corrected answers, experiment splits or ambiguity
rules. Only one database has a verified import. This local file workflow does
not promise protection from an administrator changing files or crash durability.
These are recorded limits, not claims that the remaining features are finished.

Result: both approved data-intake tasks and their final review are saved locally
under your Git identity. Progress remains 7 of 12 foundation tasks. Next comes
the separate description/layout/import plan and later answer-validity decisions.
No upload, model test, credential change or new database import happened here.

### G0.5, full-source preparation — Check the files before loading more databases

Finished three preparation checks together: counted and fingerprinted the complete
source files, inspected the native database table descriptions, and checked all
75 corrected description files in memory. We found 75 tables with 798 columns.
The corrected description names cover those columns. This does not prove the
written descriptions or answers are correct.

We found details that could otherwise cause mistakes. Some old files use a
different text encoding. Many old column-description names have spaces around
them. One old description names a column that is not in the native table.
One file has extra text under an empty heading. We recorded these facts instead
of silently throwing them away or pretending they are verified corrections.

You reviewed and approved one batch containing three implementation tasks:
safely unpack the source databases, save the small fixed-version description
files, then inspect the real SQLite layouts, row counts and keys. I will do those
in order without asking to continue after each one. This preparation did not load
another database, change a password or run the AI.

Checked now: the existing full project passed 768 tests, zero skips, including
165 real PostgreSQL checks. The proposed code in the plan passes syntax checks
only; it is not yet implemented or tested. Foundation progress remains 7 of 12
top-level tasks, with the new preparation/review steps checked inside G0.5.

New words:

- **Layout:** the list of tables and columns in a database.
- **Encoding:** the rule a file uses to turn bytes into readable letters.
  Using the wrong rule can make accented characters unreadable.
- **CSV:** a simple table saved as text, usually with commas separating fields.
- **SQLite:** a database stored in one file. Reading that file is not the same
  as importing its contents into our PostgreSQL server.
- **COPY block:** a section of the PostgreSQL source containing table rows.
  We counted and fingerprinted it; we did not run its surrounding SQL.
- **Timestamp with time zone:** a date and time that also needs a clear time-zone
  interpretation. We must check conversions before claiming equal answers.

### G0.5, source batch Task 1 — Unpack only the files we need

Finished: unpacked all 11 SQLite databases, 75 original description files and
one table-list file into a separate private folder. That is 87 files, about
1.5 GB. The old California import and original download stayed unchanged.
Every saved file matched its recorded size and fingerprint after extraction.

We wrote the failure tests first. They check missing or repeated files, unsafe
paths, symbolic links, changed bytes, lack of disk space and time limits. All
16 checks pass. The whole project without private database settings passed
619 tests; 165 database checks were skipped in that run, not counted as passes.
The actual SQLite layouts and row counts still belong to Task 3.

New words: extraction means unpacking a compressed file. Staging is a temporary
work area: the final folder appears only after all selected files are checked.
A symbolic link points to another location instead of containing the expected
file, so we reject it here. These checks are for our fixed local sources; they
do not claim protection against someone with administrator access changing files.

### G0.5, source batch Task 2 — Save the checked column descriptions

Finished: saved all 75 corrected description files from the reviewed version.
Together they use only about 76 KB. Every file's saved bytes match its recorded
fingerprint. The existing answer files and license notes stayed unchanged.

The program refuses unexpected addresses, redirects, changed files and slow
bodies. It checks the whole batch before exposing the final folder. All 29
combined unpack/download checks pass. We deliberately removed a time check for
one fake test: it waited until 1000 simulated seconds. Restoring the check stopped
it at the first late chunk, 181 seconds. No real slow download was needed.

An early failure was in our fake network responses, not the downloaded sources:
the fake had already consumed its own bytes. We corrected it to act like a real
stream. The whole project passed 632 tests without private database settings;
165 database checks were skipped. Task 3 will now inspect actual source layouts.

New words: a redirect tells a program to use a different address. We refuse it
for these fixed sources. A mock is a small fake used in a test, such as a fake
download; it must behave like the real boundary or it can hide mistakes.

### G0.5, source batch Task 3 — Check the real tables and keep problems visible

Finished: opened all 11 source databases read-only and checked 75 tables and
798 columns. Their 3,898,114 rows match the row counts in the native source,
table by table. All source fingerprints still match. The column-description
checks also passed, while retaining the old extra column description and text
under the unnamed heading. No source file or PostgreSQL import was changed.

The audit found real source problems. Three databases report 955 foreign-key
violations altogether. That does not necessarily mean 955 different bad rows.
European Football has a broken foreign-key definition, so SQLite cannot count
its violations. You approved recording that count as unavailable, not zero,
and finishing the other checks. We wrote a failing example first, then added
this exact handling. Other errors still stop the audit. We did not repair data.

Checked: 54 new batch checks pass. The complete configured project passed
822 tests, zero skips, including 165 real PostgreSQL checks. Without private
settings, 657 passed and 165 were skipped. The three implementation tasks are
checked; the batch's one independent final review comes next.

New words: a primary key identifies a row. A foreign key says a value should
refer to a row in another table. A unique key says that the referenced value
cannot be repeated; a foreign-key definition needs an appropriate parent key.
Null here means the count is unavailable; it is not a count of zero. Matching
row counts do not prove matching values or correct AI answers.

Progress: three source-preparation subtasks finished in this batch. The top-level
foundation checklist remains 7 of 12, because remaining imports and answer-
conversion checks are not finished. This is not an overall-project percentage.

### G0.5, source batch final review — Finish the preparation and save the next step

Finished: an independent reviewer checked all three tasks and the saved report.
It found no issues needing correction and repeated all 54 batch tests successfully.
The report matches the actual audit; only the date and file-history details were
added to the copy in our documentation. No source file was downloaded or audited
again, and no model was run. The three tasks are saved under your Git identity.

This review does not mean every source is healthy. The broken key definition and
955 violation records are still visible. We have not loaded ten more databases,
proved matching values/answers, or selected which descriptions the AI will use.
The next step is to prepare a separate import and conversion plan for review.

Final checks: the whole project passed 822 tests, with no skips, including 165
real local PostgreSQL checks. Without private database settings, 657 passed and
165 were skipped. The code-style and saved-package checks also passed.

New words: an independent review is a second set of eyes checking the finished
work. A limitation states what a check cannot prove. A handoff is a saved note
showing what finished and where to resume, so completed work is not repeated.
A local commit saves history on your laptop; it does not upload the project.

Progress: three preparation subtasks plus their final review are complete.
Foundation progress stays 7 of 12 top-level tasks; the later agent, experiments,
website and release are still ahead. Everything stays local, with no new import,
password change, benchmark score or publication in this batch.

### G0.5, next import preparation — Get ready to load the other ten databases

Finished now: checked the next import targets without changing the database.
Only California is loaded. The other ten datasets contain 72 tables and about
3.87 million rows. Their copied row files will need about 991 MB of extra space.
There is enough checked disk space for this bounded plan.

Checked the source primary keys: none of the 72 declared keys had missing or
repeated key values. Three tables have no declared primary key, so we must not
invent one. The date-and-time columns use text or empty values, but we have not
proved what time zone they mean. The earlier broken relationships remain visible.

I prepared one four-part plan: unpack only the remaining row files; build a
small setup importer and separate reader passwords; check toxicology first;
then load and check the other nine in order. It reuses our existing code and
packages. No database or password was changed during this preparation.

One important choice needs your review: keep every source row and record foreign
keys without enforcing them on the ten new imports. Enforcing all the broken
links would fail; deleting rows to make them pass would change the dataset.
California's existing key rules will stay unchanged. This is a proposal, not a
choice already made for you.

Checked: the current project passed 822 tests, including 165 real PostgreSQL
checks, with no skips. Without private settings, 657 passed and 165 were skipped.
The eight pieces of proposed Python code pass grammar checks only; they have
not been implemented or run. Code-style and saved-package checks passed.

New words: a representative sample is a few rows checked in detail; it cannot
prove every row is identical. UTC is a common reference time zone. Float4 is a
database number type that stores fewer digits, so values may be rounded. A
conversion check must notice such differences rather than hide them for a score.

Where we are: foundation progress is still 7 of 12 top-level tasks. This next
plan is ready for review, not executed. Finishing G0 also needs answer-conversion
checks, your label-policy decision, the second-model check, a frozen question
split, real smoke scores and your final model/speed choice. I will batch routine
work but cannot replace those required decisions with guesses.

## 4. AI words in normal language

These explain the project vocabulary. A definition here does not mean the
feature has already been implemented.

### AI, LLM and model

- **AI (artificial intelligence):** software that uses learned patterns to do
  tasks such as understanding text or suggesting an answer. It can be wrong.
- **LLM (large language model):** a kind of AI trained on lots of text. It reads
  text and produces more text; that ability can also be used to suggest SQL.
- **Model:** the trained system used to produce answers. Qwen is the first
  model family selected for this project; its first local smoke test is complete.
- **Weights / parameters:** the learned numbers inside a model. They store
  patterns learned during training, not a verified list of facts.
- **7B:** roughly seven billion model parameters. It is a size label, not an
  accuracy score or a seven-gigabyte download size.
- **Training:** changing a model's learned numbers using examples.
- **Inference:** using an already trained model to produce an answer.
- **Fine-tuning:** doing more training for a narrower task. It is an optional
  later project stage, not something already done here.

### Running a model on this laptop

- **Local model:** a model running on your own computer instead of sending
  the prompt to a hosted model service.
- **Ollama:** the local program that loads a model and accepts requests for
  answers. Installing Ollama does not automatically download a model.
- **GPU:** the graphics chip. It can also speed up model calculations.
- **VRAM:** the GPU's working memory. Some is already used by other programs;
  an 8 GB GPU does not always have 8 GB free.
- **RAM:** the computer's main working memory. It is separate from VRAM and
  separate from the space used to save files on disk.
- **CPU offloading:** running part of the model on the main processor when
  it does not all fit on the GPU. This can make answers slower.
- **Quantization / Q4:** storing many model numbers in a smaller form to use
  less memory. Q4 uses roughly four-bit storage for many weights; not every
  value uses exactly four bits. Answer quality can differ from the full model.
- **GGUF:** a file format used by many local model runners to store model
  weights and metadata. It is a format, not a separate AI model.
- **Model digest:** a fingerprint identifying a particular model package.
  Saving it helps notice if a model name later points to different contents.

### Talking to a model

- **Prompt:** the instructions and information sent to the model.
- **Prompt template:** the pattern used to arrange instructions and chat
  messages into the format expected by that model.
- **Token:** a small piece of text processed by the model. It might be a
  word, part of a word or punctuation; it is not always one whole word.
- **Context window:** the amount of text the model can work with in one
  request. Instructions, schema information and the answer use this space.
  This is not permanent memory of every earlier conversation.
- **Temperature:** a setting that changes how much variation is allowed
  when choosing output tokens. A low setting does not guarantee correctness.
- **Seed:** a number used to initialize random choices. It can help repeated
  tests, but the same seed does not guarantee identical answers everywhere.
- **Structured output / JSON:** an answer in a machine-readable shape, such
  as named fields. A valid shape does not mean the contents are correct.
- **Hallucination:** a confident-looking answer that is wrong or invented,
  such as SQL referring to a column that does not exist.
- **Smoke test:** a small check that something starts and responds. It is
  not a full accuracy test or proof that it works for every question.
- **SDK (software development kit):** a toolbox of ready-made code for talking
  to a system. An SDK's brand name does not decide where a request is sent.
- **Model client:** the part of our program that sends a request to the model
  and reads its reply. It does not give the model database permissions.
- **Schema capsule:** a small description of chosen tables and columns. This
  demo's capsule is not the full database description or a search system.
- **Warmup / preload:** loading the model into working memory before asking a
  question. It can take time and is counted separately from a question attempt.
- **Output cap:** a maximum answer size. If an answer stops because it hits the
  cap, we must not pretend the incomplete text is a complete SQL query.
- **Token usage:** the number of text pieces reported for the input and output.
  If that number is missing, `null` means "we do not know," not "it used zero."
- **Attempt budget:** the maximum number of requests we allow. Starting one
  attempt does not mean the server finished it or produced a correct answer.

### How the future SQLWarden agent will work

- **Text-to-SQL:** turning a normal-language question into a SQL query.
- **Agent:** a program that uses a model plus tools and rules to complete a
  task. SQLWarden will use one plain Python flow, not a team of runtime agents.
- **State machine:** a program that moves through named steps with clear
  rules for what may happen next and when it must stop.
- **Schema linking:** finding which tables and columns the question refers to.
- **Retrieval:** selecting useful information before asking the model to answer.
- **RAG (retrieval-augmented generation):** giving a model retrieved information
  so it can use that information while answering. Here that means database
  structure and descriptions; it does not train new model weights.
- **BM25:** a word-based method for ranking matching information. It is the
  planned starting method for finding useful columns.
- **Embedding:** a list of numbers representing text for similarity searches.
  This is a common AI term, but embedding-based retrieval is not currently
  part of the implemented project.
- **Candidate:** one proposed SQL query. The agent may later try a fixed
  number of candidates, rather than trying forever.
- **Repair loop:** making a limited new attempt after a query fails a check.
  The model receives a safe error summary, not database secrets.
- **Result voting:** grouping candidates that produce the same complete
  result. Different SQL text can still produce the same answer.
- **Agreement score:** how many requested candidates support the largest
  result group. Agreement is not a proven probability that the answer is right.
- **Clarification:** asking the user a follow-up question when their meaning
  is unclear instead of secretly choosing an interpretation.
- **Abstention:** refusing to guess when the system cannot give a reliable
  answer. This must be reported honestly, not counted as a correct answer.
- **Cache:** saved output that can be reused. Replaying cached text is not
  the same as measuring a new live model response.
- **KV cache / prompt cache:** saved intermediate model calculations that can
  make repeated input faster. This is different from replaying a saved answer.
  The small model tests used this built-in Ollama optimization.

### Measuring results fairly

- **Dataset:** a collection of data used for development or testing.
- **BIRD Mini-Dev:** the public collection of databases and question/reference
  pairs selected for this project. The checked release has 500 questions in
  11 databases; only one database is imported so far.
- **Gold / reference SQL:** the provided query used by an offline checker.
  References can contain mistakes. They must not be shown to the model while
  it is answering the test question.
- **Evaluation:** checking actual outputs against a fixed test method.
- **EX (execution accuracy):** checking whether the generated query produces
  the expected result under the chosen comparison rules. No EX score exists yet.
- **Comparator / answer checker:** code that decides whether two complete
  answers match under a specific rule. It is not another AI model.
- **Reference failure / gold validity:** the supplied answer can fail too.
  We must check it and record the reason before measuring the AI's answers.
- **Denominator:** the number of test questions a rate is measured over.
  Quietly removing failed questions can make a score look better than it is.
- **Baseline:** a simple starting version used for comparison with later changes.
- **Ablation:** changing one part to measure its effect. Turning off security
  controls is allowed only in the separately controlled disposable attack setup.
- **Held-out data:** test questions not used to tune the system's settings.
- **Data leakage:** letting answer information reach the model or tuning process
  when it should be reserved for checking. This can make scores misleading.
- **Latency:** how long a request takes. A faster answer is not automatically
  a more accurate answer.
- **Token usage:** how many input and output tokens a request used. Missing
  usage information is unknown, not zero.
- **Budget / limit:** a maximum amount of time, output or attempts allowed.
  Limits stop the system from continuing without a clear stopping point.

### Words from the corrected-answer preparation

- **Stable ID:** an item's saved number. It stays useful even when a list is
  rearranged. Matching the first item to another first item is not reliable.
- **Pinned release:** a specific saved version, checked by its fingerprint.
  We do not silently switch to a newer file if its contents change.
- **Alignment:** checking that records refer to the same item and database.
  Matching numbers alone does not prove the question or answer is correct.
- **Baseline drift:** the older copy used as a starting point differs from
  our copy. A correction can contain changes inherited from that older copy.
- **Conversion validity:** checking that an answer query has the same meaning
  and result after moving it to another database system. We have not checked
  this yet for the corrected answers.
- **Ambiguity label:** a mark saying a question has more than one reasonable
  meaning. Different wording alone is not enough evidence for that mark.
- **Offline checker:** a separate program used to inspect the exam's answer
  key. It does not send the key to the AI that is taking the exam.

## 5. Database and coding words used so far

- **Database:** an organized store of information that can be queried.
- **SQL:** the language used to ask a database for information or change it.
  SQLWarden is intended to support only permitted read queries.
- **Table, row, column:** a table is like a sheet; a row is one record;
  a column is one field, such as a school name.
- **Schema:** a named group of tables inside PostgreSQL. It is also often
  used to mean the description of a database's tables and columns.
- **Type:** the kind of value a column holds, such as text, a whole number,
  a decimal-like floating-point number or a date.
- **NULL:** a missing or unknown value. It is not always the same as zero
  or an empty piece of text.
- **Primary key:** the column or columns that uniquely identify a row.
- **Foreign key:** a rule connecting values in one table to matching rows
  in another table.
- **Read-only login:** a database identity that is allowed to read the
  permitted data but not modify it.
- **Privilege:** a real permission enforced by the database, such as
  permission to read a table or connect to a database.
- **Administrator / bootstrap login:** a powerful identity for initial setup.
  It must not be used by the normal runtime or included in model prompts.
- **Credential:** a login secret, such as a password. Credentials are kept
  in private local environment files, not in Git or this notebook.
- **Transaction / rollback:** a transaction groups database changes together.
  A rollback undoes its changes if the group is not committed.
- **Docker container:** an isolated way to run the database software locally.
  It is useful separation, not a guarantee against every security problem.
- **Volume:** the saved database storage. Restarting a container should not
  delete this data. We have preserved the project's named volume.
- **SQL guard:** code that checks the structure of a proposed query before
  execution. The first guard now works in tests; prompt instructions cannot replace it.
- **Parser / AST (syntax tree):** a parser reads SQL and makes a structured map
  of its parts. This lets us see a real command instead of guessing from words.
  Parsing alone does not prove a query is allowed or will run successfully.
- **SQLGlot:** the Python package that reads SQL into that tree. Its exact approved
  version is now installed. It is not the database itself.
- **Allowlist:** a written list of things the program permits. A thing missing
  from the list is not automatically allowed just because it looks harmless.
- **Fail closed:** if a safety check cannot understand or verify something, it
  refuses instead of guessing that it is safe.
- **Identifier / quoted name:** the name of a table, column or alias. PostgreSQL
  makes ordinary English capital letters lowercase in unquoted names. A name
  inside double quotes keeps its exact spelling, so "Schools" differs from schools.
- **Alias:** a temporary short name used inside one query. It does not give
  permission to read a different table.
- **Immutable:** a value that cannot be changed after it is created. The guard's
  table policy is fixed, so a later step cannot quietly change that same object.
- **Stable error category:** a short label, such as table_not_allowed, that the
  program can handle without receiving private query text or an internal traceback.
- **Exception / traceback:** an exception is a problem that interrupts normal
  code. A traceback lists the internal steps where it happened. The guard turns
  the known parser errors into short labels instead of giving that internal list.
- **Log:** a record a program writes to help diagnose problems. Private query
  text should not be copied into these records by the safety checker.
- **Regression test:** a saved test for a bug, so the same bug is noticed if it
  returns later. We first watched these new tests fail, then pass after the fixes.
- **Canary:** made-up recognizable text used in a test. Here it let us notice
  a logging leak without using a real password or private query value.
- **CTE / SQL scope:** a CTE gives a name to a small query inside a bigger query.
  Scope is where that name is valid. The same name elsewhere does not give that
  other place permission to read an unrelated table.
- **Operator / cast:** an operator is a symbol such as + or =. A cast converts
  a value to another type. Both can use database functions, so they also need review.
- **Overload:** the same function name with different kinds of input. For example,
  adding whole numbers can use a different routine from adding floating-point numbers.
- **Catalog:** PostgreSQL's own description of its tables, functions and types.
  The tests can inspect this metadata; that does not allow reading other datasets.
- **Read-only transaction:** a group of database work where writes are refused.
  It does not make every possible reading function safe by itself.
- **Search path:** the order PostgreSQL uses to find an unqualified name. Putting
  built-in functions first helps name lookup; it is not a permission boundary.
- **Tuple / set / multiset:** a row tuple keeps values in column order. A set
  keeps each distinct row once; a multiset also keeps how often a row repeats.
  The inspected BIRD EX rule uses sets, not multisets.
- **Float / decimal:** a float stores an approximate number using binary digits.
  A decimal can store an exact base-10 value. Two displayed numbers can look the
  same but differ inside the computer; the planned checker will not hide that.
- **NaN (not a number):** a special numeric value, not a blank or missing value.
  Ordinary NaN values do not equal each other. Python's containers can still
  recognize the very same NaN object; the checker must preserve the saved rule.
- **Sandbox / restricted executor:** the controlled place where permitted
  queries will run with strict permissions and time/output limits.
- **Connection pool:** a small set of database connections kept ready for reuse.
  This runner uses at most one, rather than opening unlimited links.
- **Cursor:** a way to collect an answer gradually, instead of loading all rows
  into the program at once. Our runner requests one row at a time.
- **Rollback:** end a transaction without keeping its changes. Here it also
  clears temporary query settings before the connection is reused.
- **Budget / deadline / timeout:** a budget is a maximum amount allowed, such as
  rows, bytes or time. A deadline is the latest finishing time. A timeout means
  the time limit was reached, not that the database returned a correct answer.
- **Overflow / complete result:** overflow means an answer exceeded a limit.
  A complete result contains the whole answer. A matching first page does not
  prove that two complete answers are equal.
- **Cap-plus-one:** ask for one extra row to check whether more rows exist.
  If the limit is two and a third row appears, the result is too large.
- **UTF-8 / byte size:** UTF-8 turns text into computer bytes. A Hindi character
  or emoji can use several bytes; counting letters is not enough. The planned
  result budget also counts column names and the brackets around the data.
- **EXPLAIN / estimated cost:** EXPLAIN asks PostgreSQL what work it expects
  a query to need. Its cost is a rough work estimate, not money or accuracy.
  Estimates can be wrong, so time limits are still needed.
- **Cancellation:** stopping work because the caller asks to stop. The planned
  runner must release its database resources, not just stop showing output.
- **RLS (row-level security):** database rules that can restrict individual
  rows to the correct user or tenant. Tenant RLS is not implemented yet.
- **API / endpoint:** an API is a way programs talk to each other; an endpoint
  is one address for a particular operation. A loopback address, such as
  127.0.0.1, points back to this computer.
- **SDK:** a ready-made software kit for calling another program's API.
- **CLI:** a program used by typing commands in a terminal rather than clicking.
- **uv:** the tool used to manage this project's Python environment and packages.
- **Dependency / lock file:** a dependency is another package our code needs.
  The lock file records exact package versions for repeatable installation.
- **Hash / SHA-256:** a fingerprint of file contents. It helps detect changed
  bytes; a matching hash alone does not prove the source is trustworthy.
- **Pinning:** saving the exact version or fingerprint we used instead of
  relying on a name like "latest" that may change later.
- **Manifest / provenance:** a small record of what was used and where it came
  from, including versions, fingerprints and important checks.
- **Unit test / integration test:** a unit test checks a small piece of code;
  an integration test checks it with a real system such as PostgreSQL.
- **Git repository / commit:** a repository stores project files and their
  history. A commit is a saved change in that history, not an automatic upload.

### Remaining import batch — Task 1 complete (2026-10-05)

You said “move forward”, so the four-part import batch is approved. I will not
ask for routine reviews. Important new decisions will still be questions.
I saved the data for 72 tables from the ten remaining datasets, almost 1 GB.
Every saved file matches its recorded fingerprint. The first California dataset
was not copied again, and the database has not changed yet.

The tool reads only COPY data, not the commands around it. It first saves into
a temporary folder; the completed folder appears only after every check passes.
It refuses changed files, insufficient space and an existing completed folder.
61 extraction/source checks passed; the full no-secret test run passed 668
tests and skipped 165 checks that need private database settings.

**COPY payload** means table rows in a format PostgreSQL can read quickly.
**Staging** means preparing privately before declaring the result ready.
**Unenforced foreign key** means a recorded relationship between two tables is
not made a database rule. Some source relationships are defective. We preserve
the rows and record those defects instead of quietly deleting or repairing data.
This does not prove every query will give the same answer as SQLite.
Next: test and build the fixed importer, then create its private login file.

### Remaining import batch — Task 2 complete (2026-10-05)

The importer is built and checked. It accepts only the ten approved datasets
and the dedicated local database. It will refuse to overwrite a dataset that
already exists. Each dataset has its own private password, saved outside Git.
None has been added to the database yet, and the AI cannot use setup passwords.

Before saving an import, the tool checks every native row and compares a few
real SQLite rows. A mismatch must cancel the import. This is stronger than just
counting rows, but it is not yet proof that every SQLite query keeps its answer.
32 new checks pass. The full private-settings run passed 865 tests. Two earlier
runs hit an existing cancellation timeout; isolated checks and the fresh full
run passed. I did not increase its limit or claim the timing problem was fixed.

**Transaction** means a group of changes that is saved together or cancelled.
**Primary key** is the column or columns that uniquely identify a row.
**Multiset comparison** checks values and how many times each row appears.
**Representative sample** checks a few chosen rows, not every source value.
Next: import the small toxicology dataset and test its real read permissions,
blocked writes, cancelled imports and changed-value detection.

### Remaining import batch — Task 3 complete (2026-10-05)

The first new dataset, toxicology, now has four real database tables and 36,922
rows. Every native row matches, and 12 chosen SQLite rows also match. Its own
login can read it but cannot write, read other protected tables or take another
role. These are real database checks, not just pretend connections.

22 checks passed. I deliberately interrupted a two-table test import after its
first table; neither its schema nor its login remained. Another test changed a
value without changing the number of rows. The content checker noticed it, and
the test rolled the change back. None of those test changes remain saved.

**Isolation** means one dataset login cannot use another dataset's permissions.
**Default grant** means permissions automatically applied to future tables.
**Atomic import** means one dataset is saved completely or not saved at all.
The batch is not all-or-nothing: completed datasets stay if a later one fails.
The next nine imports will run one at a time. Query-answer conversion and model
evaluation are still later work; these import checks are not an accuracy score.

### Remaining import batch — seven more imported; Task 4 paused (2026-10-05)

Eight new datasets are saved, with 57 tables and 2,904,731 rows. Together with the
earlier California dataset, 9 of 11 datasets are loaded. Every saved native row
matched, and 171 selected SQLite rows matched. The completed datasets and old
boundaries passed 1,083 tests. 74 checks for the missing datasets are not counted
as successes. This is progress on data loading, not completion of all G0.

Codebase Community hit a real timestamp difference. Its import was cancelled
and left no tables or login. European Football was not attempted after that.
I checked all 11 timestamp columns without changing anything. 882,084 non-empty
cells have the same clock time, but the native file says UTC+08 and SQLite does
not say which timezone it means. 226,789 empty cells match.

**Timezone** tells us which place's clock a time belongs to. 8 AM at UTC+08 is
midnight at UTC. Equal clock numbers do not always mean the same instant.
**Wall clock** is the displayed time before interpreting its timezone.
I asked one important question: may this dataset's import sample check use
UTC+08, with new tests and one retry? This would preserve all source/native
values and would not change gold SQL or benchmark rules. Until you answer,
the strict existing comparison stays. Tasks 1–3 are finished; Task 4 and its
final independent review are not. G0 still needs conversion and model work.

### Important timestamp choice — approved and tested (2026-10-05)

You approved UTC+08 for Codebase's sample comparison and one import retry.
I added five checks before changing code. They first failed, then passed.
Only Codebase's timezone-unspecified times use this rule; already specified
timezones keep their meaning, and all other datasets keep their existing rule.
No source rows or stored native values are rewritten. The accuracy benchmark
and gold SQL are unchanged. Next comes the one approved retry and last import.

### Remaining import batch — Task 4 complete (2026-10-08)

Codebase Community succeeded on its one real retry. European Football then
succeeded. The ten new datasets now contain 72 tables and 3,868,173 rows. Every
native table was compared as a complete bag of typed rows, and 216 selected
SQLite rows also matched. The database kept 69 checked primary keys.

The real database test matrix passed 292 checks. It includes 90 ordered login
pairs: each dataset login was tested against every other new dataset and was
blocked from reading it or taking its role. The complete configured project run
passed 1,162 tests with no skips. The offline run passed 705 tests and skipped
457 checks that deliberately need private local database settings.

European Football has a broken relationship definition in its original source.
We record that as “schema mismatch” with no numeric count. We do not pretend it
has zero problems. Foreign-key relationships for these ten imports are saved as
information but are not installed as database rules, so no bad source row was
silently deleted or repaired.

**Bag / multiset:** all rows are compared including duplicates; order does not
matter, but the number of repeated rows does.
**Cross-dataset isolation:** a login for one dataset cannot read or impersonate
another dataset's login.
**Schema mismatch:** a source relationship is defined in a way the database
cannot safely enforce or count. “Unknown” is different from zero.
**Regression suite:** a large group of old and new tests rerun together to check
that new work did not break earlier behavior.

The import group is not the whole data milestone. We still need to check which
official questions and answers survive conversion, choose the main descriptions
and labels, and make the C1 ambiguity decision. Model comparison and scoring are
also later work.

### Remaining import batch — final review complete (2026-10-08)

A fresh reviewer checked the whole four-part import change without editing it.
It reran 80 real database checks and 19 smaller importer/time checks, rebuilt the
metadata summary and matched every dataset/table and file fingerprint. It found
no serious or important problem. One small progress checkbox still said the
already-approved import policy needed approval; that checkbox is now corrected.

**Read-only review:** inspection and tests that do not change project files or
database data. **Scope:** the exact work a check covers. Passing import tests does
not automatically prove model accuracy, every possible database attack, or the
meaning of official answers; those stay at their later checkpoints.

### Gold-answer validator built (2026-10-08)

The next G0 part now has a safe checker. It can run one official answer query on
the original SQLite database and its converted query on the matching restricted
PostgreSQL database, then compare the complete answers. It does not save the SQL,
answer cells, questions or passwords in its report. It records only the question
number, dataset and a short result such as matched, different, timed out or too
large.

The checker refuses changed input files, write statements and multiple statements.
It opens SQLite as an unchangeable read-only file and uses only the matching
dataset login for PostgreSQL. Each query is limited to 10 seconds, 100,000 rows,
16 MiB total and 1 MiB for one cell. The comparison ignores row order but keeps
duplicate rows and value types. Its focused checks passed 17 tests; one optional
Windows symlink check was skipped because this account cannot create a test link.
The full offline project run passed 722 tests and skipped 458 database-only checks.

**Gold answer** means the trusted reference query used to decide whether a model's
answer is correct. **Transpilation** means translating SQL syntax from one database
language to another without manually rewriting the intended answer. **Canonical
form** means converting values into one exact comparison format; for example, a
number remains a number and is not silently treated as text. **Atomic file write**
means the final report appears completely or not at all, so an interrupted run
cannot look finished.

This finishes the checker itself, not the gold-validity decision. The next step is
to run it on the real pinned questions and use the measured corrected-label survival
rate for C1.

### Real gold check reached an important choice (2026-10-08)

The checker ran across all 11 databases. The original converted answers matched
439 of 500 questions. The full corrected set has 498 available questions, but only
365 produced exactly the same complete answer in SQLite and PostgreSQL: 73.29%.
That is below the 95% safety line chosen before seeing results, so I did not quietly
pick a dataset, freeze a split or start scoring models.

For the 133 aligned corrected questions that did not pass, 75 refer to a table,
column or function PostgreSQL cannot find after automatic translation; 52 run but
return a different exact answer; two time out; and four have other database/data
errors. Two more question IDs are missing from the correction source. No query,
answer or source data was edited to improve these numbers.

**Survival rate** is the share of converted reference questions that still produce
the same answer after moving database systems. **Undefined object** means the
translated query names a function, table or column that PostgreSQL cannot resolve.
**Precommitted threshold** means the pass line was written down before measuring,
which prevents changing the rule merely because the result is inconvenient.

C1 now needs a real product choice: use the smaller 365-question corrected pool;
use the larger 439-question original verified pool and keep corrections only for
research; or first do a separate manual/adaptation review of the 133 corrected
failures. Work stops at this choice because each option changes what later model
scores mean.

### Corrected-answer recovery finished (2026-10-08)

You chose to review the failures first. I added automatic, tested translations for
renamed PostgreSQL tables and columns, reserved words, dates, SQLite number behavior
and aggregate functions. These rules recovered 59 more corrected questions, taking
the exact pass count from 365 to 424 of 498, or 85.14%. The original source SQL was
never edited and the answer checker was not made looser.

There are 58 remaining questions that run but return an exactly different answer.
Another 18 either fail or time out. Even if all 18 were repaired, the best possible
total would be 442, still below the 473 needed for 95%. Twenty-three of the 58 become
similar only if numbers are rounded to six decimal places, but rounding is forbidden
by the rule written before testing.

**Dialect adaptation** is a documented translation rule for a known difference
between SQLite and PostgreSQL. **Ceiling** means the highest possible result even if
all repairable failures were fixed. The recovery proves that more syntax fixes alone
cannot reach the safety line. The honest remaining choice is between 424 verified
corrected questions and 439 verified original questions, unless you deliberately
change the exact-comparison method. I recommend the corrected pool because it keeps
the reviewed corrections without hiding failures.

### Second local AI model installed and checked (2026-10-08)

The Arctic Text2SQL 7B model is now installed locally. The exact 4.68 GB file was
checked against its expected digital fingerprint before Ollama accepted it. The
downloader keeps at least 12 GiB free, can safely resume an interrupted transfer,
and will not replace a different existing file.

I tested Arctic with an invented `planets` table, not project data. Two identical
requests produced the same small SQL answer. A third request proved the four-token
output limit stops generation. The first call took 8.718 seconds while loading;
the warm call took 0.360 seconds. Ollama showed the requested 8,192-token context
and about 5.13 GB of GPU memory. The model was unloaded afterward.

**Quantization** means storing model numbers in a smaller format so the model fits
on ordinary hardware; Q4_K_M is the selected four-bit format. **Model digest** is
Ollama's fingerprint for the complete local model package. **Context window** is
how much prompt text the model can consider at once. This smoke proves the model can
load and make a tiny SQL-shaped answer; it does not prove benchmark accuracy.

### Executor now supports every fixed dataset safely (2026-10-08)

The safe SQL runner no longer works only for California Schools. It now has a fixed
list of all 11 loaded datasets and their table names. When the program is told a
dataset ID, it chooses the matching restricted database login and search path by
itself. The user, model and generated SQL still cannot choose a role or switch to a
different dataset.

The old California function still exists, so the earlier CLI and tests keep working.
For the new path, I added checks for every real local dataset login. Each one can
read its own tables through the guarded executor. Each one is blocked from reading
the app schema, running writes and using `SET ROLE`. I also kept the older complete
result-size and timeout checks.

Checks that actually ran: 355 focused pure checks passed; 321 real PostgreSQL
executor/release checks passed; the full offline suite passed 746 tests and skipped
470 database-only tests; the full configured suite passed 1214 tests and skipped 2.
Ruff lint and format also passed.

**Dataset policy** means the trusted list of tables that one dataset is allowed to
query. **Search path** means the database lookup order for unqualified table names;
here it is set to `pg_catalog` first and then exactly one dataset. **Restricted
login** means a database user that can only read its own dataset and cannot become
another user.

This does not finish G0 by itself. The corrected answer-pool choice is now handled
below, but model evaluation cannot start until the split/E0 inputs are frozen.

### Corrected answer pool chosen and frozen (2026-10-08)

You chose the corrected option for C1. That means future local evaluation will use
the 424 questions whose corrected SQL produced the exact same answer after being
adapted to PostgreSQL. The project now has a small tracked manifest with those
question IDs, database IDs, difficulty labels and simple ambiguity labels.

Corrected descriptions are now the main column descriptions for evaluation.
Original descriptions are still kept as alternate reference material. The 58 exact
answer mismatches and 18 failed/excluded questions are not hidden; they are simply
not in this verified pool. No score has been run yet.

Checks for this subtask: the manifest builder has focused tests for corrected-pool
counts, evidence fingerprints, no raw payload text, and stable relative evidence
paths. The focused gold tests passed 31 checks with 1 expected skip. The full
offline suite passed 749 checks and skipped 470 database-only checks. The full
configured suite passed 1217 checks and skipped 2 expected checks. Ruff lint and
format passed.

**Benchmark pool** means the fixed set of questions used for measurement.
**Primary label** means the answer SQL we treat as the reference for this project.
**Alternate description** means older text we keep for comparison, but do not use
as the main input. **Ambiguity candidate** means the original and corrected wording
are literally different, so the item may be useful later for testing clarification.
**Negative control** means the wording did not change, so it helps compare against
the ambiguity candidates.

### E0 split and protocol frozen (2026-10-08)

I added the rule for the first local evaluation split. From the 424 verified
corrected questions, 100 are now the development set and 324 are held out for
later. The split is saved in a small protocol file with IDs and hashes only. It
does not contain the natural-language questions, SQL, answers or secrets.

The split uses a fixed seed, so the same input produces the same IDs every time.
It also tries to keep the mix of databases and difficulty levels balanced. If we
later add groups of related variants, the splitter keeps each group together so a
near-duplicate does not leak between development and held-out sets.

Checks for this subtask: the protocol tests first failed because the module did
not exist. After implementation, 4 focused tests passed. The full offline suite
passed 753 checks and skipped 470 database-only checks. The full configured suite
passed 1221 checks and skipped 2 expected checks. Ruff lint and format passed.

**Development set** means the questions used while tuning choices. **Held-out
set** means questions kept aside to check later whether the project generalizes.
**Seed** means a fixed number that makes a random-looking split repeatable.
**Bootstrap interval** means estimating a score range by repeatedly resampling
the measured answers; it helps report uncertainty instead of just one number.

### First two-model E0 measurement finished (2026-10-09)

I ran the first local evaluation on the 100-question development set. Both models
used the same frozen questions, the same checked database logins, the same SQL
guard and the same exact answer checker. This was single-shot: no repair, no vote,
no retrieval helper and no hidden retry.

Arctic answered 22 out of 100 exactly after the final review fix pass. Qwen
answered 3 out of 100 exactly. Qwen's
main problem was not only wrong SQL: 86 questions were stopped before a model call
because the full database schema plus reserved answer space did not fit inside the
small 2048-token Qwen alias. Arctic used more GPU memory but handled the full-schema
prompt better.

The compact result file is saved as `results/E0_smoke/summary.json`. It includes
counts, speed, token totals and peak GPU memory. The detailed per-question raw files
are ignored and not committed. The tracked summary does not include prompts,
generated SQL, answer rows, gold SQL or credentials.

Initial checks for this subtask: 13 focused E0 tests passed. The full offline
suite passed 766 checks and skipped 470 database-only checks. The full configured
suite passed 1234 checks and skipped 2 expected checks. After the final review
found the stricter comparator/provenance gaps, the corrected fix-pass checks passed
57 focused checks with 2 expected skips, 783 full offline checks with 471 skips,
and 1251 full configured checks with 3 skips. Ruff lint and format passed. Ollama
reported no model still loaded after the clean rerun.

**EX** means exact match: the generated query's complete answer matched the frozen
reference answer exactly. **Prompt budget** means the model input plus reserved
output space would not fit into the chosen context window, so the program refused
to call the model. **p95 seconds** means 95% of measured calls were at or below
that time. **Peak VRAM** means the largest GPU-memory amount Ollama reported for
that model during the run.

### C2 model choice and first G1 provider/cache slice (2026-10-09)

I used the E0 results to choose the next local SQL model. Arctic is now the main
full-schema SQL-generation model for the next agent work, because it handled the
full database schema and got 22 exact answers out of 100. Qwen is not removed, but
it is not the full-schema SQL model right now because 86 of the 100 questions did
not fit into its small 2048-token context. Qwen can still be used for the already
tested safe local command-line/helper path, and we can test a different Qwen setup
later if needed.

I also started G1.1. I added a small provider contract and a small disk cache. The
provider contract records which local model is being called, which exact model
digest/template is expected, the input settings and the rule that there are no
hidden retries. The outcome record stores only safe summary information such as
status, token counts when available, cache-hit status and a hash of the content.
The cache writes JSON files atomically, refuses overwriting an existing cache file,
and refuses secrets or gold answers.

The old safe CLI still behaves the same. It now gets its local Ollama URL and retry
settings from the shared provider code, so future G1 work can reuse one checked
contract instead of hard-coding it again.

Checks for this subtask: provider/cache/LLM/CLI focused tests passed 117 checks
with 1 expected Windows symlink skip. The full offline suite passed 777 checks and
skipped 471 database-only checks. The full configured PostgreSQL suite passed 1245
checks and skipped 3 expected checks. Ruff lint, format check and whitespace check
passed.

### Final review of finish-G0/start-G1 and the E0 fix pass (2026-10-09)

A fresh read-only reviewer checked the whole finish-G0/start-G1 change. It found
no Critical issues, but it found Important problems in the first E0 evidence path.
The main problem was that the code used the stricter duplicate-preserving answer
comparison instead of the pinned EX comparison rule. That made the old Arctic
20/100 number not the exact metric we promised.

I fixed the review findings test-first. The E0 runner now uses the pinned EX
comparison, saves enough ignored raw information to safely resume or rescore, keeps
model usage even when output is invalid, has explicit per-item deadlines, keeps
complete selected descriptions instead of silently cutting them, records Git commit
and clean/dirty state, avoids Decimal rounding in the gold checker, and hardens the
small cache boundary checks. I then reran E0 from a clean commit. The new tracked
summary is Arctic 22/100 and Qwen 3/100. Old pre-fix raw records are still local
and ignored as legacy evidence, not committed.

Checks for this review-fix pass: 57 focused checks passed with 2 expected skips.
The full offline suite passed 783 checks and skipped 471 database-only checks. The
full configured PostgreSQL suite passed 1251 checks and skipped 3 expected checks.
Ruff lint, format check and whitespace check passed. The final raw records have
`git_dirty: false`, and Ollama reported no model loaded afterward.

**Final review** means a separate read-only check after the work is finished.
**Provenance** means information that proves where a result came from, like the
Git commit, model digest and data fingerprint. **Rescore** means checking old model
outputs again with a corrected scoring rule. **Dirty Git state** means files were
changed when a result was produced; for the corrected E0 run it was false.

**Context window** means how much text a model can read at once. **Provider** means
the local model service being called, here Ollama on this laptop. **Digest** means
a fingerprint that identifies the exact local model artifact. **Cache** means saved
model-call output that can be replayed exactly later. **Atomic write** means a file
is created all at once, so an interrupted write does not look like a finished cache
entry. **Hidden retry** means the software silently tries a failed model call again;
we keep this at zero so measurements count the real number of calls.

## 6. What comes next?

G0's numbered checklist is complete, except the optional interview drill. G1's
core code is implemented and committed through the first command-line loop settings.
G2 has started with the first guardrail-contract slice. The website, broader attack
suite, hosted/deployment work and release still come later. Important new
permissions outside the approved local scope will still be asked as questions.

### G1 core agent slice (2026-10-09)

I added the first real local agent core.

What changed:

- The project can now turn database schema information into a smaller schema
  “scope” for one question. It keeps table names, column names, descriptions,
  primary keys, foreign keys and a few bounded sample values.
- It has versioned prompts for four actions: make SQL, repair SQL, ask a
  clarification question and explain an already executed answer.
- It has a plain Python state machine. That means the loop is written as clear
  steps: validate, retrieve schema, generate candidates, guard SQL, execute safely,
  repair once if allowed, vote, possibly clarify, and finish.
- It has result voting. Failed candidates still count in the denominator, ties
  abstain, and one candidate is never called “high confidence”.
- The CLI now has an explicit `--loop` mode with settings for candidates, repairs
  and retrieved columns. The old safe one-candidate command still works by default.

The C3 retrieval check used the frozen 100 development questions, not the held-out
set. Top 24 retrieved columns gave mean table recall of 0.968333 and full-table
recall of 0.93. Top 32 was only slightly better, so I chose 24 columns to save
prompt space. I also chose 3 candidates and 1 repair for the first loop.

Checks: 118 focused G1/CLI/LLM tests passed after the read-only review fixes. The
full offline suite passed 795 tests and skipped 471 database-only tests. The
configured PostgreSQL suite passed 1263 tests and skipped 3 expected tests. Ruff
lint and format passed too.

New simple terms:

**Schema retrieval** means picking only the tables and columns that look relevant
to the user's question, instead of sending the whole database map every time.

**BM25** is a classic keyword-scoring method. In simple terms, it gives more points
to schema fields whose words match the question, while avoiding over-rewarding
very common words.

**Primary key** is the column or columns that identify one row in a table.

**Foreign key** is a column that points to a row in another table. It helps the
agent know how tables can join.

**Untrusted sample values** means example cell values from the database are treated
as data, not instructions. If a sample value says “ignore previous rules”, the
program must not obey it.

**State machine** means the agent can only move through allowed steps and must end
in a clear final state like answered, needs clarification, abstained or failed.

**Abstain** means SQLWarden refuses to give an answer because the candidates were
not reliable enough.

**Clarification** means asking the user one bounded follow-up question when the
agent cannot safely decide what was meant.

### G2.1/C4 guardrail contract slice (2026-10-09)

I started G2, the broader guardrails and sandbox group, with a small contract file.
This file records the security choices that were already partly inside the code:
which SQL functions are reviewed, which cast types are allowed, what the default
query limits are, and how tenant isolation should work later.

What changed:

- The guard now gets its allowed function and cast lists from one explicit contract.
- The contract records the current query caps: row limit, result-size limit,
  cell-size limit, timeouts and estimated-cost/row caps.
- The tenant design is written down before implementation: the server must choose
  separate database roles for tenants, and a user/model-supplied tenant id is not
  trusted as the security boundary.

Checks: I first wrote a test that failed because the contract file did not exist.
After adding the contract, 298 focused security/guard/executor tests passed. The
full offline suite passed 798 tests and skipped 471 database-only tests. Ruff lint
and format passed too.

New simple terms:

**Allowlist** means only the listed safe things are allowed. Anything not listed is
blocked by default.

**Cast** means converting a value from one type to another, like text to date or
integer to text.

**Cost threshold** means PostgreSQL estimates whether a query may be too expensive
before it runs. This is useful, but not perfect, so timeouts still stay enabled.

**Tenant isolation** means one user's or tenant's data should not be readable by
another tenant. SQLWarden will use separate database roles for that later instead
of trusting a changeable setting inside the SQL session.

### G2.2 guard coverage and gold-audit slice (2026-10-09)

I added a small read-only audit for the SQL guard.

What changed:

- The project now records how many guard test cases already exist.
- It also checks the 424 usable corrected gold questions against the pure SQL guard.
- The audit file stores only counts and reasons. It does not store question text,
  SQL text, answer rows, credentials or model prompts.

Result:

- Existing guard test corpus count: 148 case strings.
- Corrected usable gold items accepted by the current guard: 368.
- Corrected usable gold items blocked by the current guard: 56.
- All 56 blocked items were blocked because the query used a function that is not
  currently reviewed/allowed.

This does not change the benchmark and does not mean the blocked queries are bad.
It means SQLWarden will not run them until their functions are reviewed and allowed
on purpose.

Checks: the audit test first failed because the script did not exist. After adding
the script, 198 focused guard/audit tests passed. The full offline suite passed
800 tests and skipped 471 database-only tests. Ruff lint and format passed, and
the compact manifest was regenerated.

New simple terms:

**Guard coverage** means how many different SQL shapes the guard tests already
check.

**Safe-gold acceptance audit** means checking whether trusted reference SQL would
pass the safety guard, without running it and without changing the reference data.

**Function not allowed** means a SQL function is not on the reviewed allowlist yet,
so the guard blocks it until we intentionally review it.

### G2.3 executor error-contract slice (2026-10-09)

I added an explicit list of the stable executor error reasons.

What changed:

- The project now records which public reason strings can come out of the
  guard/executor path.
- Each reason is grouped into one status: ok, blocked, failed or overflow.
- This is for safety and clarity; it does not give the model or user any new SQL
  power.

Checks: I first wrote a test that failed because the reason map did not exist.
After adding the map, 103 focused security/executor tests passed. The full offline
suite passed 801 tests and skipped 471 database-only tests. Ruff lint and format
passed too.

New simple terms:

**Error category** means a safe label like `timeout` or `syntax_error`, instead of
showing a raw database traceback.

**Overflow** means the query may be read-only, but the answer was too large for the
configured row/byte/cell limits, so SQLWarden refuses to return a partial answer as
complete.

### G2.4 guarded EXPLAIN and cost calibration slice (2026-10-09)

I recorded how SQLWarden checks query cost before execution.

What changed:

- A compact manifest now records the default estimated-cost and estimated-row caps.
- It also records the rule that SQLWarden guards SQL before asking PostgreSQL for
  an `EXPLAIN` plan.
- The manifest says SQLWarden uses `EXPLAIN (FORMAT JSON)`, not `EXPLAIN ANALYZE`.
  That matters because ANALYZE would actually run the query.
- Real PostgreSQL checks confirm the cost and estimated-row gates still work.

Checks: the manifest test first failed because the file did not exist. After adding
the manifest, 7 focused manifest/unit executor checks passed and 2 real PostgreSQL
checks passed. The full offline suite passed 802 tests and skipped 471
database-only tests. Ruff lint and format passed too.

New simple terms:

**EXPLAIN** means asking PostgreSQL for an estimated plan before running a query.

**EXPLAIN ANALYZE** means running the query while measuring it. SQLWarden does not
use that for untrusted SQL cost checks.

**Estimated cost** is PostgreSQL's guess about query expense. It helps block risky
queries early, but it is not perfect, so timeouts still matter.

### G2.5 grant and default-grant evidence slice (2026-10-09)

I recorded the real database permission checks for all 11 restricted dataset
logins.

What changed:

- A compact manifest now lists the direct PostgreSQL tests that prove each
  dataset login is restricted.
- The tests connect as the restricted dataset users directly, not through the SQL
  guard.
- They check that each reader has no admin powers, cannot change into other roles,
  cannot write, cannot create temp tables, cannot read the app schema, cannot read
  another dataset and cannot use selected risky PostgreSQL functions.
- They also check future default grants: if a new table is created in a dataset
  schema, only that dataset's reader gets SELECT, and not INSERT.

Checks: the manifest test first failed because the manifest did not exist. After
adding it, 6 focused security-contract tests passed. The real PostgreSQL
permission checks passed 210 tests against the local database. The full offline
suite passed 803 tests and skipped 471 database-only tests. Ruff lint and format
passed too.

New simple terms:

**Grant** means permission in the database, such as permission to read a table.

**Default grant** means permission automatically given to future tables created
later.

**Direct-connection test** means the test logs into PostgreSQL as the restricted
user and tries actions directly. This proves the database itself refuses those
actions, even without help from the SQL guard.

**ACL** means an access-control list. In simple words, it is a list of who can do
what.

### G2.6 tenant RLS slice (2026-10-09)

I added a tiny tenant demo that proves PostgreSQL can hide rows for different
tenants.

What changed:

- The local setup now creates two tenant database logins.
- Both tenant logins read the same `tenant_demo.orders` table.
- PostgreSQL row-level security is enabled and forced on that table.
- Each tenant role has a policy that only shows its own row.
- Changing `app.tenant_id` inside the SQL session does not change which rows are
  visible. The database role is the real boundary.
- The existing local ignored env files got two new tenant passwords, and the
  existing local PostgreSQL database was updated with the tenant demo objects.
  The passwords were not printed or committed.

Checks: the setup test first failed because the tenant passwords were not created.
After adding setup support, that test passed. The real tenant RLS tests passed 4
checks against local PostgreSQL. The focused setup/boundary tests passed 51 tests
and skipped 2 expected checks. The full configured suite passed 1275 tests and
skipped 3 expected tests. Ruff lint and format passed too.

New simple terms:

**RLS** means row-level security. It lets PostgreSQL decide which rows a login can
see.

**Forced RLS** means even the table owner must follow the row-security rule.

**Tenant** means one customer or user group sharing the same app but needing its
data separated from other tenants.

**Database role** means the login identity PostgreSQL uses for permissions.

### G2.7 untrusted data and explanation isolation slice (2026-10-09)

I added tests and a small code change for data that looks like instructions.

What changed:

- Schema sample values are still sent as `untrusted samples`.
- A test now puts a fake instruction inside a sample value. If the model follows
  that fake instruction and tries to read the app-private table, the SQL guard
  blocks it before the database runner is called.
- The explanation step now sees only a tiny result preview: at most 3 rows, with
  long cells shortened.
- The preview is labelled as untrusted data.
- Explanation text from the model is escaped before being returned, so HTML-like
  text such as `<script>` is shown as text instead of being treated as page code.

Checks: the new tests first failed because explanation prompts did not include
bounded rows and explanation text was not escaped. After the change, the 3 focused
G2.7 tests passed.

New simple terms:

**Prompt injection** means text inside data tries to act like an instruction to
the AI.

**Escaping** means changing special characters so they display as text instead of
being interpreted as code.

**Result preview** means a small sample of answer rows given to the explanation
step, not the full result.

### G2.8 attack-suite evidence slice (2026-10-09)

I organized the existing security tests into an attack-suite evidence file.

What changed:

- A new manifest records 40 deterministic SQL attack fixtures.
- It also records 3 fake-LLM/model-mediated controls for poisoned samples,
  explanation manipulation and unsafe generated SQL.
- Each attack record says what threat it belongs to, which test fixture proves it,
  what would count as success for the attacker, which layer blocked it and which
  test is the evidence.
- The manifest records false-block evidence too: from 424 safe-gold items, the
  current guard accepts 368 and blocks 56 because their SQL functions are not yet
  reviewed.
- The layer-off E5 experiment is not run here. Instead, the manifest records the
  safety rule for later: it must use a separate disposable local Docker project
  and volume, must reject hosted targets and must not mount host directories.

Checks: the tests first failed because the attack audit module and manifest did
not exist. After adding them, the 3 attack-manifest tests passed. The focused
attack/guard/prompt tests passed 210 checks. The full offline suite passed 809
tests and skipped 475 database-only tests. Ruff lint and format passed too.

New simple terms:

**Attack fixture** means a saved test input used to check whether a defense works.

**Success predicate** means the exact condition that would mean an attack
succeeded or failed.

**False block** means SQLWarden blocks a harmless/valid query. This is safer than
allowing unsafe SQL, but too many false blocks make the tool less useful.

**Layer-off experiment** means deliberately turning off one safety layer to see
what it was protecting. That is risky, so SQLWarden only allows it later in a
disposable local setup.

### G2.9 SECURITY file slice (2026-10-09)

I added the root `SECURITY.md` file.

What changed:

- The file explains what SQLWarden is protecting right now.
- It lists the important trust boundaries: model output is not trusted, database
  roles decide permissions and gold answers stay out of prompts.
- It lists the security rules that must stay true, like guard before execution,
  restricted dataset logins, forced tenant RLS and escaped explanation text.
- It links the G2 evidence files instead of copying raw SQL, prompts, result rows
  or credentials.
- It clearly says what is not proven yet, including hosted security, universal
  prompt-injection resistance and layer-off E5 experiments.

Checks: the test first failed because `SECURITY.md` did not exist. After adding
the file, the SECURITY test passed. The security-policy resolver also found and
resolved the root policy. The final focused policy/security tests passed 10. The
full offline suite passed 810 tests and skipped 475 database-only tests. The full
configured suite passed 1282 tests and skipped 3 expected tests. Ruff lint and
format passed too.

New simple terms:

**Security policy** means a document that tells reviewers what must be protected
and what counts as a real security problem.

**Residual limitation** means a known risk or unfinished proof that remains after
the current work.

**Trust boundary** means the line between things the program trusts and things it
must treat carefully.

### G2 interview drill (2026-10-09)

Use these as simple interview practice answers.

Question 1: Why is SQLWarden safer than just telling the AI “only write SELECT
queries”?

Simple answer: because an AI instruction is only a request, not a lock. SQLWarden
uses code and database permissions as the lock. The model can suggest SQL, but the
SQL guard checks the shape first, and PostgreSQL restricted logins decide what the
query is actually allowed to read. If the model suggests unsafe SQL, the program
blocks it before execution.

Question 2: What do L3, L5 and L7 each block?

Simple answer:

- L3 is the SQL guard. It blocks unsafe SQL shapes, like writes, DDL, dangerous
  functions, catalog reads and tables outside the allowed dataset.
- L5 is least-privilege database permissions. It blocks damage even if something
  reaches PostgreSQL directly, because the dataset login cannot write, switch
  roles or read other schemas.
- L7 is tenant row-level security. It blocks one tenant from seeing another
  tenant's rows by using separate database roles and forced RLS policies.

Question 3: What are the biggest remaining security limitations after G2?

Simple answer: G2 proves local tested boundaries, not universal security. The
project is still not a production SaaS, the layer-off E5 experiment has not been
run, prompt injection is reduced but not magically solved, PostgreSQL cost
estimates can be wrong, some catalog metadata is normally visible, and tenant RLS
is proven only on the small synthetic tenant demo. Hosted/API/web security still
comes later.

### G3.1 E0 safer resume files (2026-10-10)

I improved the E0 experiment runner for future evaluation runs. I did not rerun
the AI models or change the saved E0 scores.

What changed:

- Future E0 runs save a small ignored `manifest.json` file for each model.
- Future E0 runs also save an ignored `records.jsonl` file with one result per
  line.
- If a run stops in the middle, resume can reuse good saved lines and ignore only
  a broken final line.
- The old per-question raw JSON files still work, so existing raw evidence does
  not need to be rewritten.
- The saved metadata still avoids prompts, generated SQL, gold SQL, answer rows
  and credentials.

Checks: the focused E0/evaluation test file passed 21 tests. The full offline
test suite passed 814 tests and skipped 475 database-only tests. Ruff lint,
format and diff checks also passed. No AI model, database query or benchmark
rerun happened.

New simple terms:

**Manifest** means a small facts file that says exactly what settings a run used.
Here it records the protocol, model identity and Git state so the program can
notice if someone tries to resume with different settings.

**Fingerprint** means a short hash made from those facts. If the facts change,
the fingerprint changes too.

**JSONL** means "JSON Lines". It is a text file where every line is its own small
JSON record. This is useful for experiments because the program can save each
answer as soon as it is finished.

**Resume** means continuing a stopped run from the saved records instead of
starting again from the beginning.

### G3 full evaluation package (2026-10-10)

I completed the rest of G3 using the already-saved E0 run records. I did not ask
the AI models new questions and I did not touch the held-out test IDs.

What changed:

- The E0 summary now separates the path into simple steps: parse, guard,
  execution and exact match.
- It reports coverage, meaning how many expected records were present.
- It reports answered-only accuracy, meaning accuracy only among questions that
  reached a database answer comparison.
- It reports paired Arctic-vs-Qwen numbers on the same 100 development questions.
- It labels 50 observed failures using compact labels like `wrong_result`,
  `guard_blocked` and `execution_failed`.
- It adds a compact dashboard file, an EVAL document, a frozen next-experiment
  matrix and resume-safe bullets.
- The README now links to the local evaluation evidence.

Important measured numbers:

- Arctic: 22 exact matches out of 100 development questions.
- Qwen: 3 exact matches out of 100 development questions.
- Arctic answered-only EX: about 35.5%.
- Qwen answered-only EX: 30%.
- Arctic beat Qwen by 19 percentage points on the matched development slice.

Checks: the focused evaluation/artifact tests passed 25 tests. The full offline
suite passed 818 tests and skipped 475 database-only tests. Ruff lint, format and
diff checks passed. No model call, database query, held-out run, push or public
release happened.

New simple terms:

**Coverage** means how much of the planned test set actually has a saved record.

**Parse rate** means how often the AI output became usable SQL text.

**Guard rate** means how often that SQL passed the safety guard.

**Execution rate** means how often the guarded SQL reached a database comparison.

**Answered-only EX** means exact-match accuracy only among questions where a
database answer was produced and compared. It is useful, but it can hide skipped
or blocked questions, so we also keep the full 100-question denominator.

**Paired comparison** means comparing two models on the exact same question IDs.

**Failure taxonomy** means short labels for why something failed.

G3 interview practice:

Question 1: Why is Arctic 22/100 not called an official benchmark score?

Simple answer: because it is a local development slice. It used a frozen 100-item
development set, which is good evidence for the project, but official claims need
the agreed held-out run, release checks and public reporting rules.

Question 2: Why report parse, guard and execution separately?

Simple answer: because one final accuracy number hides where the system failed.
If parsing failed, that is a model/output-format problem. If the guard blocked
the SQL, that is a safety boundary doing its job. If execution failed, that is a
database or SQL compatibility problem. Different failures need different fixes.

Question 3: Why keep raw SQL and prompts out of tracked files?

Simple answer: because they can contain sensitive or bulky experiment details.
The project tracks compact evidence that reviewers can use, while raw prompts,
generated SQL, gold SQL, answer rows and credentials stay out of Git.

### G4 first API/web slice (2026-10-10)

I started G4 with the safe local core instead of installing new web packages.
This is not the full FastAPI/React website yet.

What changed:

- Added a local API core that can create a run, store events, replay events and
  cancel a run.
- Run access uses a secret capability token. The program stores only a hash of
  that token, not the token itself.
- Added checks for allowed database IDs, request size, browser origin, overload
  and simple per-IP rate limits.
- Added SSE-style event formatting so a future web client can replay events.
- Added restart handling that marks unfinished runs as interrupted.
- Added three static local page artifacts: Ask, Attack Lab and Benchmark.
- Added a local smoke script that checks those pages and a fake answered API
  flow without starting a network server.

Checks: the focused G4 API/static tests passed 6 tests. The full offline suite
passed 824 tests and skipped 475 database-only tests. Ruff lint, format and diff
checks passed. No AI model, database, hosted service, dependency install, push or
publication happened.

New simple terms:

**API** means the interface the web page will call to start and watch a run.

**Bearer capability** means a secret token that gives access to exactly one run.
It is not a user account.

**Hash** means a one-way fingerprint. The server can check the token without
storing the token itself.

**SSE** means Server-Sent Events. It is a simple way for the server to stream
progress updates to a browser.

**CORS/origin** means checking which browser site is allowed to call the API.

What remains for full G4: the real FastAPI adapter/routes and React/Vite frontend
need direct dependencies. Project rules say I must ask before adding those.

### G4 complete: the real website works on this laptop (2026-10-11)

You approved the web packages (FastAPI, uvicorn, React, Vite, Recharts). G4 is
now finished locally. You can type a question in a browser page and watch the
real agent answer it, using the real model and the real database.

What changed:

- The web server (FastAPI) now runs the real agent instead of a fake one. Each
  question uses only that one dataset's read-only database login.
- The page shows each step live as it happens (retrieve, three candidates, vote).
- If the three SQL candidates disagree, a second small model (Qwen) writes a
  short "what did you mean?" question with options. You may reply once.
- Explanations are a simple fact sentence ("Returned 1 row ... 3 of 3 agreed"),
  not AI-written text. That is safer and faster.
- Three React pages: Ask, Attack Lab (which layer stopped each attack) and
  Benchmark (results from tracked files only).

Two important discoveries while testing for real:

1. **The prompt format mattered a lot.** The old agent prompts wrapped the
   question inside a JSON document. The SQL model then wrote nonsense like
   `SELECT '1'`. The research paper for this model (Arctic-Text2SQL-R1) shows
   the format it was trained with: "think step by step, then give the SQL in a
   code block", plus BIRD's hint text ("evidence"). On 20 practice questions the
   old style got 3 right; the paper-style prompt with hints got 10 right. It is
   slower (about 11 seconds per try instead of 2). This is recorded as D-075.
2. **The safety guard was blocking good queries.** 56 of the 424 correct answer
   queries were blocked because they used normal date/text functions such as
   `to_char` and `substring`. We reviewed those nine functions, proved on the
   real database that they are plain built-in functions with no side effects,
   and allowed them. Now only 3 of 424 are blocked. All 43 attack tests still
   give exactly the same result. This is D-076.

Also: column names such as `Academic Year` must be written with double quotes
in PostgreSQL. The schema text given to the model now shows the quotes, so the
model copies them correctly.

Checks that actually ran: 875 offline tests passed (475 database-only tests were
skipped in that run); 56 real database guard checks passed; the web page code
type-checks and builds. A real scripted run asked a question, got a
clarification with 3 options, replied, and got an answer in 48.6 seconds. Cancel
worked. A real browser run answered a Fresno school question with 3 of 3
candidates agreeing.

New simple terms:

**FastAPI / uvicorn**: the Python web framework and the small program that
serves it on `http://127.0.0.1:8000`.

**React / Vite**: React builds the page from small components; Vite turns the
source files into the final website files in `web/dist`.

**Heartbeat**: a tiny "still here" message sent while a long answer is running,
so the browser connection does not look dead.

**Last-Event-ID**: the number of the last update the browser saw. When it
reconnects, the server sends only the newer updates.

**Evidence (in BIRD)**: a short human-written hint that comes with each
question, for example how a rate is calculated. It is input, not the answer.

**Reasoning model**: a model trained to think in steps before giving its final
answer. It is more accurate but slower.

**False block**: when a safety check stops a query that was actually safe.

**Model swap**: unloading one model from the GPU and loading another, because
this laptop's 8 GB GPU fits only one at a time.

What is still unfinished: the big experiment set (E1-E8) has not run yet. That
is next. Deployment preparation (G5), the release (G7) and the interview drills
for G1, G4, G5 and G7 also remain.

### G5 deployment preparation and first release checks (2026-10-11)

G5 means "get ready to publish, but do not publish yet". Nothing was put online.

What changed:

- **Free hosting check.** I read the official pages of five services on
  2026-10-11. The free web servers are small and fall asleep; Hugging Face now
  charges for app containers; free databases are 1 GB; a free hosted AI model
  allows only about 1,000 requests a day and would receive the questions. So the
  recommendation (D-077) is: publish the Benchmark and Attack Lab pages as a
  static website on GitHub Pages, and keep the live Ask page as a laptop demo.
- **Container.** A Dockerfile now packages the website and the Python server.
  It runs as a normal (non-administrator) user, cannot write to its own files,
  and can only reach the local database and the local AI model.
- **CI (automatic checks).** A GitHub workflow will run the tests, lint, the web
  build and a throw-away database security test on every push. It only gets
  read permission. It will first run after the approved push.
- **Public check script.** It tries bad requests on purpose (wrong website, huge
  body, wrong password token, too many requests) and expects each to be refused.
- **Release checks.** All 83 saved commits are by you only. A search of every file
  version ever saved found none of your 34 local passwords and no key patterns.
  All software licenses are permissive (MIT, BSD, Apache, ISC).

New simple terms:

**Container / Docker image**: a sealed box with the app and everything it needs,
so it runs the same way on any computer.

**CI (continuous integration)**: a robot that runs your checks automatically each
time code is pushed.

**Static website**: a site made only of files (no live server code), so it is
free and safe to host.

**Secret scan**: searching saved history for passwords or keys that should never
have been committed.

What still needs you: choosing the public repository name, public or private,
and the code license, before anything is pushed (see docs/RELEASE.md).

### G1 interview drill (2026-10-11)

Question 1: Walk me through what happens to one question inside the agent.

Simple answer: first it finds the 24 most relevant columns with BM25 (a word-match
score) and adds their keys. Then it asks the model for three SQL candidates. Each
candidate goes through the SQL guard, a cost check and the restricted database run.
If a candidate fails, it gets one repair try with the error category. Finally the
candidates vote on their complete results. If one result wins, that is the answer;
if they tie or nothing worked, it asks one clarifying question or abstains.

Question 2: Why vote on results instead of on the SQL text?

Simple answer: two different SQL queries can mean the same thing, and two similar
queries can mean different things. Comparing the actual result tables checks what
matters. Failed candidates still count in the denominator, so "1 out of 3 worked"
is never reported as strong agreement.

Question 3: Why a plain Python state machine and not an agent framework?

Simple answer: every step, limit and stopping point is visible in about 250 lines
and covered by fake-model tests. That made it easy to bound retries, record every
attempt for the experiments, and stream each step to the web page.

### G4 interview drill (2026-10-11)

Question 1: How does the browser see progress without a second run being started?

Simple answer: `POST /api/ask` creates one run and returns a secret token. The page
then reads a Server-Sent Events stream with that token in a header. Every event has
a number; if the connection drops, the page reconnects with the last number and only
gets newer events. Reconnecting never starts new work (there is a test for it).

Question 2: What stops someone from reading another person's run?

Simple answer: each run has a random 32-byte token. The server keeps only a hash of
it and compares in constant time. Unknown runs and wrong tokens get the same 401, so
an attacker cannot even learn whether a run exists.

Question 3: What did testing with the real model teach you that fake tests did not?

Simple answer: the prompt format. With fake models everything passed, but the real
SQL model wrote placeholder queries for our JSON-shaped prompt. Switching to the
format from its paper took a 20-question probe from 3 to 10 correct. Fake tests
check control flow; only real runs check behaviour.

### G5 interview drill (2026-10-11)

Question 1: Why did you not deploy the live demo publicly?

Simple answer: the free tiers I checked on official pages were too small or would
send every question to a third-party model, and a managed database would not allow
some of my permission hardening. A static evidence site plus a local demo costs
nothing, leaks nothing and still shows the measured results.

Question 2: What makes the container safer than just running the code?

Simple answer: it runs as a normal user, its files are read-only, it has no Linux
capabilities, it has memory/CPU/process limits, it listens only on 127.0.0.1, and it
refuses to start if any setup password or a non-local model address is present.

Question 3: How do you know no secret was ever committed?

Simple answer: I searched all 601 file versions in the whole history for the exact
values of all 34 local passwords and for common key formats, and found none. I also
say clearly that this is a targeted search, not a full commercial secret scanner.

### G3 experiments finished: what the measurements say (2026-10-12)

The experiment plan from G3 has now actually run, on 100 practice ("development")
questions and 324 held-out test questions. Another Claude session ran the security
switch-off test (E5) at the same time; the two sessions agreed who did what so they
did not overwrite each other. Every run recorded the exact code version it used.

Main results, in plain words:

- **Simple was best for accuracy.** Giving the model the whole database description
  and asking once got 54.3% of held-out questions right. The full agent (pick 24
  columns, three tries, one repair, vote) got 42.9% right overall.
- **But the agent is more trustworthy when it does answer.** Using a rule chosen on
  practice questions only, it answered 61.7% of test questions and was right on 66.5%
  of those. Saying "I don't know" is better than a confident wrong answer.
- **The repair step almost never helped.** 56 of 58 repairs repeated the same mistake,
  because the repair only hears a short error category (for safety), not which word
  was wrong. That is the clearest thing to improve next.
- **Wording matters a lot.** The original BIRD wording cost 20 points on the 40 practice
  questions whose wording had been corrected. Scrambled column names cost 15 points.
- **Clarifying questions:** it asked on 44% of truly unclear questions and 15% of clear
  ones. The question options were always well formed, but answers after clarifying
  were still often wrong.
- **Security:** with every layer on, 0 of 43 recorded attacks succeeded. Switching one
  layer off at a time in a throw-away database, 27 of 29 attacks were still stopped;
  two depended on a single layer (the guard, or the time limit).

Fixes made along the way: a crash when a clear question got a clarifying question,
replay stopping when a few answers could not be cached, and questions wrongly shown
as "pending". Each fix has a test, and the affected runs were redone from clean code.

New simple terms:

**Held-out set**: questions kept locked away until the very end, so the final score
is not tuned to them.

**Ablation**: turning one feature off to see how much it really helps.

**Selective accuracy**: how often the answers are right when the system chooses to
answer, ignoring the questions it declined.

**Confidence interval**: the range the true score probably lies in; small test sets
give wide ranges.

**Positive control**: a run with every protection off, to prove the test can detect
a successful attack at all.

### G7 final interview drill (2026-10-12)

Question 1: Your full agent scored lower than the simple baseline. Why keep it?

Simple answer: because it knows when to stay quiet. End to end it is lower, but
when it answers it is right about two times in three, and every abstention is counted
as wrong in the main score, so nothing is hidden. I report both numbers and say which
setting to use for which goal.

Question 2: How do you know your security claims are not just marketing?

Simple answer: each claim points to a test or a recorded run. 43 attacks have success
rules that check the database itself, not just error messages. A disposable database
test switched layers off one at a time, and an "everything off" control proved the
attacks really work when nothing stops them. I also give the statistical upper bound,
8.2%, instead of saying "unhackable".

Question 3: What would you do next?

Simple answer: give the repair step safe, specific feedback (which column or function
was wrong), teach the guard-friendly PostgreSQL date functions in the prompt, and then
re-run the same frozen evaluation to see whether the loop finally beats the baseline.

### G6 starts with a small training check (2026-10-12)

You asked to add fine-tuning for your resume. We checked the laptop and saved a
small experiment plan. Nothing has trained yet, and no new library or model has
been installed in this step. The GPU has almost all its memory free, but normal
computer RAM has only about 1 GB free. Training will wait for at least 4 GB free.

The proposed first experiment teaches a small Qwen model using eight invented
SQL examples, for just 20 training steps. It checks whether GPU training works,
whether the learned file saves and loads again, and how much memory/time it uses.
It does not prove the model answers real database questions better.

Fine-tuning means teaching an existing AI model more examples. QLoRA keeps the
large original model compressed and teaches small extra weights. An adapter is
the file holding those extra learned weights. A training step is one update to
them. Loss is a number measuring how far the training prediction is from the
example; lower training loss alone does not mean better answers on new questions.

Next: approve the exact new training tools and limits required by C8, test the
small run, then prepare separate training/validation databases. Compare the base
model and trained model fairly. Only numbers we actually measure go on the resume.
The existing release and its evaluation results stay available.

### The training tools work on the GPU (2026-10-12)

You approved the pilot. We installed its tools in a separate Python environment,
so the working website keeps its original tools. A real small calculation on the
GPU passed both the prediction and learning directions using 4-bit numbers.
Seventeen checks cover memory/disk limits, stopping a long run, keeping private
SQL out of saved summaries, and teaching only the answer part of an example.

Forward pass means making a prediction. Backward pass means calculating how to
adjust the learned weights. Response-only labels mean the model is rewarded for
the SQL answer, not for copying the question. A lockfile records exact tool
versions so we can reproduce the experiment. The 20-step model training is next;
this successful tool check is not an accuracy improvement yet.

### Real training examples are ready to inspect (2026-10-12)

We acquired the BIRD team's 6,601 filtered question/SQL examples and 69 database
descriptions. The full database download is huge. A range request asks the server
for only a small part of a file; we needed about 49 KB of the archive to get the
schema descriptions. Four checks verify that the reader refuses oversized or
incomplete downloads. Raw training examples stay outside Git.

These answers are written for SQLite. SQLWarden uses PostgreSQL, so we must check
their conversion before choosing the training set. Acquiring examples is not
training, and it does not prove those answers execute correctly in PostgreSQL.
The first training launches stopped at the RAM check. You closed unused apps;
we will now retry with the model already downloaded.

### The first real GPU training run passed (2026-10-12)

The small Qwen model completed 20 learning updates. It trained about 1.09 million
extra weights in about 29 seconds, using at most 3.25 GB of reserved GPU memory.
We saved those weights, loaded them again and checked they were identical. The
loaded model then produced an answer. The GPU was released when the program ended.

Training loss fell from about 0.20 to 0.002 on the invented examples. That means
it learned these examples; it does not prove it answers new database questions
better. A launcher bug stopped the summary being saved after training. A new
test caught the script path problem; we fixed it and recovered the completed
record without training again.

We also spotted a training/test overlap risk: the two European Football datasets
have related names. We excluded that whole family. The remaining 6,559 labels
convert to PostgreSQL syntax, but their converted results are not verified yet.
The important choice is whether to train with that disclosed limitation or first
spend more time and disk verifying additional databases.

GPU memory reserved means memory PyTorch keeps available for reuse. Leakage
means training on examples too closely related to the final evaluation, making
the score look better than it should. Generalization means answering new cases,
instead of just remembering the training examples. Full training and E9 are next.

### The real training and validation sets are frozen (2026-10-12)

You chose converted SQL answers with a clear warning that we have not executed
them on the training databases. We screened them against known tables/columns,
the SQL guard and prompt checks. We kept 5,822 records and separated databases
before choosing examples. The final sample has 2,000 training examples from 57
databases and 128 validation examples from six different databases.

Examples longer than 2,048 tokens are excluded instead of cutting off the answer.
We excluded both European Football and Codebase evaluation families. Related movie
versions stay together. Eight complex conversion pairs were inspected within a
50-record sample; conversions remain unverified for actual answer results.

Validation means checking examples the model was not trained on. A checkpoint is
a saved point during learning. We will select the checkpoint with the lowest
validation loss, not whichever looks best on final evaluation questions. Balanced
sampling means giving each database a turn so one large database does not take
all the places. Full training will make 500 learning updates next.

### The full training runner is ready for hardware checks (2026-10-12)

The new runner reads the frozen 2,000 examples and checks their file fingerprints.
It refuses examples with no answer labels or labels that do not match the input
tokens. Every 100 updates it will save an adapter and measure loss on the separate
validation examples. The final choice uses that validation loss, with earlier
updates winning a tie. It never looks at final benchmark answers to make that choice.

The first hardware check will run two updates at the real 2,048-token length.
If memory fits, the full run gets a two-hour limit. This code step has not trained
the full dataset yet; the earlier 20-step synthetic pilot is still the completed run.

### Real schema-length training fits on the laptop (2026-10-12)

The next GPU test used two learning updates on real examples padded to 2,048
tokens. It passed save/reload and used about 6.86 GB of GPU memory. Two updates
took about 12.5 seconds including saves, so the full 500-update run is estimated
at about an hour including validation. It gets a two-hour cap.

This confirms the memory limit is workable, but it is still only a feasibility
test. Those two reported losses are training losses, not validation scores.
Full training, checkpoint selection and the real answer-accuracy comparison remain.

### Full fine-tuning finished and its saved weights passed checks (2026-10-12)

The full run made 500 learning updates on 2,000 real examples. Training,
checkpoint saves and repeated validation took about 58 minutes. The measured
training loop used at most about 6.43 GB of reserved GPU memory and released the
GPU when it ended. All 39 focused training checks pass.

Validation loss went from about 0.834 before learning to about 0.094. The best
saved version was update 400, slightly better than update 500. We selected it by
the rule written before training. Every saved adapter weight matched after loading
it again, and the loaded model produced an answer.

An important detail for the resume: the full experiment processed 2,000 examples,
but the selected version at update 400 had seen 1,600. We will describe both
accurately. Lower token loss is useful evidence of learning, but real answer
accuracy still needs the database test. Next is the original-versus-trained model
comparison, then an honest resume entry. No model weight or code has been pushed.

### The fair comparison tools are checked, but the comparison has not run (2026-10-12)

We can now run the original small model and its trained version through the same
SQL guard, restricted database login and answer checker. Both will get the same
question, full database layout, one attempt and output limit. Old Arctic tests
still use Arctic by default; we did not change your existing benchmark results.

The new runner saves completed questions and can continue after a stop. It refuses
a changed setup, repeated question IDs or a damaged saved line. It does not reuse
old AI answers. The report needs every question from both models before writing
an accuracy claim. Wrong answers and failed attempts still count. Unknown memory
use is recorded as unknown, not zero. Tracked reports will not include SQL text,
database answers or passwords.

New terms: a digest is a file/model fingerprint used to check which version ran.
A paired comparison checks the two models on the same questions. Execution
accuracy (EX) means the suggested query returned the correct database answer.
A confidence interval shows uncertainty in a measured score; it is not a promise
about future questions. A cache stores old replies; it is disabled for this test
so that each recorded question gets a fresh model attempt.

Checks: 25 focused tests passed. The full database-configured suite passed 1,455
tests with three expected skips; the no-database suite passed 983 with 475 skips.
One earlier cancellation check timed out, then passed alone and in full reruns.
Its cause is not established, so we did not claim to fix it or relax its limits.

Still unfinished: model merging/local Ollama import, the real base-versus-trained
accuracy test and the final resume comparison. The storage-limit choice is pending.
Training is already complete and will not be repeated. Nothing was pushed.

### A tiny merge check passed; your real model is still untouched (2026-10-12)

We checked the original model file against its publisher's saved fingerprint.
They match. The selected trained adapter still matches its training fingerprint.
Then we used a tiny invented model to check the installed merging tools. Its
adapter changed the answer numbers inside the model, merging kept them close,
and saving/loading preserved the merged numbers exactly. The tool also refused
an adapter containing an invalid number. This check took about 2.6 seconds.

Merging means adding the adapter's learned changes into the original model's
weights so one model file can be served. FP16 stores numbers with fewer bits;
small rounding differences can occur. NaN means "not a number"—an invalid
calculation result that must not be accepted as a usable model weight.

This was not a test of the full model's memory needs or Ollama compatibility.
No full model was merged, no file was downloaded, no GPU was used and no source
checkpoint was changed. The tiny temporary weight files were removed automatically.
The current training files use about 10.23 GiB; a full merged model would add
about 2.88 GiB, over the approved 12 GiB limit even though the disk has free space.
We are keeping that limit until the storage-choice answer arrives. Real answer
accuracy and the final resume comparison are still unfinished.

### Your resume can now describe real training work (2026-10-12)

The resume notes now contain a training bullet backed by the saved experiment.
The README and evaluation notes say training is finished but the accuracy test
is not. Five new interview answers explain what was trained, why update 400 was
selected, what the data checks did and why lower loss is not proof of better SQL.

Safe claim: a 500-update QLoRA experiment on 2,000 examples worked on your 8 GB
GPU, and the selected adapter passed save/reload checks. Be clear that the selected
version had seen 1,600 examples, not all 2,000. Do not say that it improved answer
accuracy, beat Arctic or is already running in the app. Those are still untested.

An adapter is a small set of learned changes beside the original model. Frozen
weights means the original model numbers were not trained directly. Response-only
loss means the model learned the answer part of each example, not the question
and schema. Validation helped choose a saved version; the database accuracy test
will check whether that choice actually gives better answers.

No model was retrained, converted or loaded in this documentation step. The
storage-choice answer is still needed before the real serving/comparison work.
Checks read the saved training numbers and confirmed the 57 training/six validation
database groups are separate. The old benchmark sections are unchanged. Ten
focused report/training tests passed, and the full no-database suite passed 983
tests with 475 expected skips. No database or GPU training test was repeated just
to update the notes.

### Rebuilding the old report will keep your fine-tuning notes (2026-10-12)

The old report builder would erase the new fine-tuning section because it knew
only about G3. We reproduced that in a test and fixed it. It now refreshes G3
while keeping the separate G6 notes, even when their status heading changes.
Running it twice does not add the same section twice. This is called idempotent:
repeating an operation leaves the intended result stable.

A real-file check also found a display problem: loading sorted JSON put failure
names in alphabetic order, and the report mistook the first names for the most
common failures. It now chooses the largest counts first. No accuracy score or
failure count changed. Tests used copies of your real saved reports; your result
documents were left unchanged. Twelve focused checks and 986 full no-database
tests passed, with 475 expected skips; formatting/lint passed.

All independent preparation is checked. The remaining model conversion and real
accuracy comparison needed a storage-limit choice. Your answer arrived during
this step: use up to24 GiB across the project and Ollama's cache, keeping20 GiB
free on D:. We can now proceed with the real merge and local model comparison.
We will preserve existing models/caches and will not upload or push anything.
The fine-tuning project is not fully finished yet.

### The model conversion tools are now ready (2026-10-12)

Your installed Ollama could not make Q4_K_M directly from the original model
format. You approved another local route: llama.cpp makes a GGUF file, then
compresses it for Ollama. We downloaded a fixed tool version and checked its
fingerprint. Four conversion-only packages were added; the app and Torch were
not upgraded. A tiny invented model successfully passed both tool steps.

GGUF is a model file format that Ollama can read. Quantization stores the model
numbers using fewer bits, saving memory but sometimes changing answers. Q4_K_M
is the same compression recipe we will use for both models for a fair comparison.
The tiny test used fallback compression for eight tensors because it was unusually
small; it does not prove that your real model is converted or running yet.

You permitted pausing Docker to free memory. It was stopped gracefully, without
deleting any databases; the previously running services were recorded for restart.
About5.08 GiB RAM and the GPU are free. The next step adds the selected adapter
to the original model on the GPU, saves it in small pieces, and checks loading
again. A supervisor watches time and storage limits and stops only its own job
if necessary. It will not publish success from broken or incomplete evidence.

Checks:24 focused tests passed and the full offline suite passed1010 tests, with
475 database checks skipped because they were not configured. Lint/format passed.
Real merging, Ollama serving and answer-accuracy comparison are still unfinished.
Docker will be restored before database evaluation. Nothing was uploaded or pushed.

### Your actual trained model is merged and reloads correctly (2026-10-12)

We added the selected step400 adapter to the original model. This changed the
weights, and no invalid numbers remained. Every saved weight matched the model
in memory. After unloading it and loading the saved version, its answer scores
matched exactly. It also produced a short reply to an invented, harmless prompt.
The GPU is unloaded again. The merge itself took11.7 seconds and used about
4.24 GiB of GPU memory at its peak. The original files were not changed.

A shard is one piece of a large model file: seven smaller pieces helped keep
memory use low. Logits are the model's scores for possible next words. Matching
logits here proves saving/loading preserved the model; it does not prove its SQL
answers are correct. The short generation check printed harmless configuration
warnings, recorded in the technical notes rather than hidden.

Both models still need GGUF conversion, matching compression and Ollama import.
The new bounded converter checks the planned space before starting each tool,
watches resource limits, and refuses to overwrite files.28 focused checks passed.
There is still no measured accuracy improvement. Docker remains temporarily
paused and must be restored before the real database comparison. Nothing was pushed.

### Both compressed model files were made; a fairness check caught one tiny difference (2026-10-12)

The original and trained models both converted to Q4_K_M successfully. Each
compressed file is about986 MB. Compression took about25 seconds per model.
Unlike the tiny test, the full models needed no fallback compression. The first
original model also imported into Ollama, but has not answered evaluation questions.

We checked the actual weights, not just the file names. The56 trained projection
matrices differ as expected. One other value differed by about0.000000022 because
the merge loaded it as FP16 while the converter kept the original in F32. This
is rounding, not a learned bias. For a fair comparison, we will apply exactly
that same rounding to the derived original model and check again. The original
download and trained checkpoint stay untouched; the old bytes are kept for recovery.
The first Ollama alias stays separate and will not be used in the comparison.

A bias is a small offset inside a model calculation. Numeric precision means
how accurately stored numbers represent their original values. Even very small
differences deserve checking when comparing training results. Five rounding tests
passed after first failing; full offline checks passed1019 tests, with475 skips.
Both imports, the final matching check and real SQL accuracy are still unfinished.
Docker remains paused until it is restored before database testing. Nothing was pushed.

### Both models now run locally; real accuracy testing is next (2026-10-12)

The tiny rounding difference is fixed in the derived original model, with its
previous bytes saved for recovery. The final check found only the56 trained
weight matrices differ. Both models have the same tokenizer and compression
layout. Ollama imported them as separate names, and each returned a short reply.
Its reported chat template exactly matches the pinned original template; three
small examples checked the formatting. The older pre-fix model remains separate.

A tokenizer divides text into model-readable pieces. A chat template marks who
said each message. A digest fingerprints the exact model serving configuration.
We froze matching settings: full schema, one candidate, no repair, the same
compression,8,192-token context,3,072-token answer cap and seed42. Seed means a
fixed random starting point; it is not a guarantee of identical future replies.

Docker and all five services that were running before the pause are back and
healthy. Your database volume was preserved.1,491 configured tests passed, with
three expected skips;53 focused G6/E9 tests and lint/format also passed. Files
use23.826 GiB of the approved24 GiB, while D: still has21.689 GiB free.

We tried one real development database question per model through the existing
guarded path. Both abstained: the original query exceeded the row limit, and the
trained query referred to an unknown object. Neither got a correct answer here.
Abstain means refusing to pretend an answer is usable. This is a pipeline check,
not an accuracy comparison or evidence that tuning helped. No settings were
changed based on these replies. Raw questions/SQL/rows stay out of Git.

Next: fresh100-question development tests and324 existing held-out questions
for each model, then honest accuracy/latency comparisons and resume notes.
Training and local serving are finished; evaluation and final review are not.
The historical project scores and app's default model remain unchanged. No push.

## 7. How this notebook will be kept up to date

After each fully completed subtask or group, add what changed, why it matters,
the checks that actually ran, and an easy explanation of new terms. Keep earlier
entries so you can see how the project grew. Update the current-status section
and never label an unfinished feature as completed.

Technical evidence remains in [PROGRESS](../docs/PROGRESS.md),
[DECISIONS](../docs/DECISIONS.md) and [DATA](../docs/DATA.md). This notebook is the
simple-English explanation, not a replacement for those exact records.
