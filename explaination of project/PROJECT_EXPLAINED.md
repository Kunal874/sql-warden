# SQLWarden explained in simple English

Last updated: 2026-10-04.

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
  restricted database login and short time limits. No AI output was run.
- Answer-size checks now handle row, byte and cell limits without returning
  a partial answer as a complete answer. The guarded runner is now built and
  passes simulated tests; its real database recovery tests are next.
- The latest completed code checkpoint has 511 passing tests, including 123
  tests that connect to the real local PostgreSQL database.

The AI question-answering flow, fully verified runner, evaluation
scores, website and public release are not finished yet. G0, the foundation group,
is still in progress. No AI-generated SQL has been executed.

Where we are: 6 of the 12 numbered foundation tasks are complete. Inside the
next task, the query guard is finished and the guarded runner passes simulated
checks. Real runner checks are next. This does not mean half the project is done: the agent,
experiments, website and release still come later. We are building the first
small working demonstration before expanding.

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
rules and guarded workflow are built. Next are the real database recovery tests
and one final runner review.
After that come the answer checker and a small command-line
question-to-database demonstration. The rest
of the data, agent loop, website, broader attack suite and release come later.

## 7. How this notebook will be kept up to date

After each fully completed subtask or group, add what changed, why it matters,
the checks that actually ran, and an easy explanation of new terms. Keep earlier
entries so you can see how the project grew. Update the current-status section
and never label an unfinished feature as completed.

Technical evidence remains in [PROGRESS](../docs/PROGRESS.md),
[DECISIONS](../docs/DECISIONS.md) and [DATA](../docs/DATA.md). This notebook is the
simple-English explanation, not a replacement for those exact records.
