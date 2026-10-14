# Using SQLWarden on your laptop

Verified locally on 2026-10-14. Open http://127.0.0.1:8000/#ask while the
local server is running. This is the live app, not the static evidence build.

## Your first question

1. Open **Ask**.
2. Select **california_schools** in Dataset.
3. Enter **How many schools are in Alameda county?** in Question.
4. Click **Ask** once and wait. The trace shows progress; Cancel stops a run.

Our actual live run took 56.19 seconds and displayed:

```sql
SELECT COUNT(*)
FROM schools
WHERE county = 'Alameda'
```

| count |
| --- |
| 761 |

Explanation: `Returned 1 row with columns count. 2 of 3 candidates agreed on
this result.` Agreement: **2/3**. A separate restricted database query also
returned 761. This means 761 records in the imported dataset, not a current
census of schools. A later generation can produce different SQL or disagree.

## What to give as input

Give an ordinary English question about the selected dataset. You do not need
to write SQL or supply credentials. Questions are limited to 500 characters.
Name the thing to count/list, filters, desired columns and sorting when relevant.
Prefer small results. You cannot upload your own database through this app.

Try these next on california_schools. These are suggested exercises; only the
Alameda count above was tested in this session.

| Question | Expected result shape |
| --- | --- |
| How many records are in the schools table? | One row containing a count |
| List 10 school names and cities in Alameda county, ordered by school name. | Up to 10 rows, name and city columns |
| Show the five counties with the most schools and their school counts, ordered from highest to lowest. | Five county/count rows |
| How many schools in Alameda county have a charter value of 1? | One filtered count |

Avoid vague questions such as “best schools” without defining best. A clearer
question names a measured column, direction and count, for example the highest
average SAT reading scores in the SAT table. Some complex questions may fail or
receive no answer; the model is not always correct.

Available datasets: california_schools, card_games, codebase_community,
debit_card_specializing, european_football_2, financial, formula_1, student_club,
superhero, thrombosis_prediction and toxicology. Choose the matching dataset
before asking; a school question belongs to california_schools.

## Reading the screen

The app retrieves relevant schema, generates three SQL candidates, checks SQL,
estimates cost and executes allowed queries with restricted dataset credentials.
It can attempt one repair per candidate and votes on complete results.

- **Trace:** progress such as retrieval, generation, guard, execution and vote.
  It records decisions, not private model reasoning.
- **Answer:** SQL, result table, factual explanation and agreement count.
  The explanation describes rows and agreement; it is not a detailed AI analysis.
- **Agreement 2/3 or 3/3:** how many candidate results matched. It is not a
  67% or 100% probability of correctness. Matching answers can still be wrong.
- **One result row:** a COUNT query returns one row containing a number;
  it does not mean there is only one school.
- **NULL:** the database value is missing. Empty results can be valid.
- **Preview:** the UI shows at most 50 rows. A larger complete result is labelled
  as a truncated preview. Execution separately caps results at 1,000 rows and
  2 MiB; exceeding a limit does not produce a silently accepted partial answer.
- **Needs clarification:** choose the intended option or type what you meant
  (up to 200 characters), then Reply. One clarification reply is allowed; it
  expires after 10 minutes. Clarification can occur after disagreement.
- **Abstained:** the system did not reach sufficient agreement. Rephrase clearly
  and submit a new question.
- **Blocked:** SQL was refused by a control. Ask for a supported read-only query.
- **Failed / timeout:** no completed answer. Check services, free memory or try a
  simpler question. Model generation may take tens of seconds; the agent stage
  has a 120-second total deadline, and the API has a separate 300-second deadline.
- **Cancelled / interrupted / expired:** start a new question when ready.
- **Overload / rate limited:** wait before retrying; avoid repeated clicks.

The database statement timeout is five seconds. Model time is additional.
The observed 56 seconds is one laptop run, not a promised response time.

## Other pages

**Attack Lab** shows saved attack evidence, observed blocking layers and a threat
filter. Browsing it does not run a new live attack or disable security controls.

**Benchmark** shows saved development and held-out measurements, accuracy,
coverage, comparisons and latency. EX means the generated query result matched
the reference under the evaluation comparator. Coverage means how often the
system answered. These are project measurements, not official BIRD scores.
The live app uses Arctic 7B for SQL. The separately evaluated fine-tuned 1.5B
model did not replace the live default.

## Restart on this existing installation

Open PowerShell in D:\PROJECTS\SQLWARDEN:

```powershell
uv sync --locked
docker compose --env-file .env.setup up -d --wait
uv run --env-file .env.web uvicorn sqlwarden.runtime:create_runtime_app --factory --host 127.0.0.1 --port 8000
```

Leave that terminal running, then open http://127.0.0.1:8000/#ask.
Ollama must be running too. The required pinned aliases are already installed.
Do not rerun dataset imports or credential initialization. `.env.web` already
exists; do not rerun the one-time preparation script against it.

If frontend source changes, rebuild before launching:

```powershell
Set-Location D:\PROJECTS\SQLWARDEN\web
npm ci
npm run build
Set-Location D:\PROJECTS\SQLWARDEN
```

Health: http://127.0.0.1:8000/api/health. Readiness:
http://127.0.0.1:8000/api/ready. `model_unavailable` means check Ollama and pinned
models; `database_unavailable` means check the PostgreSQL container. Reload the
page after services recover. Free memory by closing unused apps before inference.
If port 8000 is occupied by this demo, use the existing app instead of starting
another copy. Restarting the API loses its in-memory runs; ask again.

For a terminal-only alternative using the existing `.env.runtime`:

```powershell
uv run --env-file .env.runtime sqlwarden ask --db california_schools --loop --candidates 3 --repairs 1 "How many schools are in Alameda county?"
```

The CLI supports california_schools and prints a result as JSON. The browser is
the easiest route for all 11 datasets and interactive clarification.

## Stop safely

A foreground API stops with Ctrl+C. This session instead started a hidden
background server: launcher PID 17328, API PID 18528. To stop that exact API,
first verify its command line still belongs to this SQLWarden server:

```powershell
Get-CimInstance Win32_Process -Filter "ProcessId = 18528" | Select-Object ProcessId, CommandLine
# Only after confirming the displayed command is this SQLWarden API:
Stop-Process -Id 18528
```

PIDs are session-specific and can be reused; do not reuse this stop command for
a later session without checking. If no longer using the model, its scoped
unload command is:

```powershell
ollama stop sqlwarden-arctic-text2sql-r1-7b-q4km-ctx8192:smoke-v1
```

To stop this project's database while preserving its data:
`docker compose --env-file .env.setup stop`. Never add `--volumes` or prune volumes.
Do not use `.env.setup` to launch the API or CLI and do not paste passwords into
questions. Questions and inference stay local with this configuration.
