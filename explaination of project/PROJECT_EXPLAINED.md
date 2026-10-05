# SQLWarden explained in simple English

Last updated: 2026-10-05.

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
- One real dataset, California Schools, has been loaded and checked.
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
- The latest verified code checkpoint has 768 passing tests, including 165
  tests that connect to the real local PostgreSQL database.
- The offline answer-file checker and small download tool pass 49 checks.
  The four approved files match their saved fingerprints. Their summary lists
  missing items and changed wording; it does not contain the answer text.

The first narrow AI question-to-database flow works for one checked question.
The full agent, evaluation scores, website and public release are not finished.
G0, the foundation group, is still in progress. Model unload, final review and
its two test-first corrections are complete. The first small demo is finished.

Where we are: 7 of the 12 numbered foundation tasks are complete. The query
guard, limited runner, answer checker and first AI command are checked and
reviewed. This is not the whole project's progress percentage: the agent,
experiments, website and release still come later. The first small working
demonstration is complete; data checks come next before expanding the agent.

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

## 6. What comes next?

G0.6a's first model smoke and G0.7a's guard, including real-database checks and
final review fixes, are complete. You approved the runner plan, and its answer-size
rules, guarded workflow, real recovery tests and final review are complete.
The answer checker and its independent final review are also complete. It passes
60 pure and 17 real database checks. The separate plan for a small command-line
question-to-database demonstration is approved. Its local AI connection is now
checked, and the safe command passes its flow and real database tests. Its sole
live question returned the expected answer; model unload, final review and its
verified parsing fixes are complete. Next we resume the remaining foundation:
datasets and validity decisions, the second model, then split/evaluation/model
choices. You approved the two-task correction-intake plan; its first checker
and the four-file intake and their final review are complete. Next comes the
remaining descriptions/layout/import and answer-validity work. The three-task
offline source-preparation batch has now unpacked the fixed sources, saved the
small descriptions and audited real layouts; its sole final review is next.
Source key problems are recorded, not repaired. Next is a separate reviewed
import/content/conversion plan. This intake uses existing software and does not change the database
or run the model. Each relevant new permission outside that scope needs review.
The rest of the data, agent loop, website, broader attack suite and release come later.

## 7. How this notebook will be kept up to date

After each fully completed subtask or group, add what changed, why it matters,
the checks that actually ran, and an easy explanation of new terms. Keep earlier
entries so you can see how the project grew. Update the current-status section
and never label an unfinished feature as completed.

Technical evidence remains in [PROGRESS](../docs/PROGRESS.md),
[DECISIONS](../docs/DECISIONS.md) and [DATA](../docs/DATA.md). This notebook is the
simple-English explanation, not a replacement for those exact records.
