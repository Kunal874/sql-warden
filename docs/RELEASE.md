# Release checks (G7)

Status: local checks done; nothing created, pushed or published. G7.3 needs Kunal's
explicit approval of the items in the release preview below.

## G7.1 — clean clone

2026-10-11, commit 704a984 cloned into an empty scratch directory: `uv sync --locked`
then `uv run pytest -q` passed 882 with 475 database-only skips. Tests that need the
ignored local data or credentials skip cleanly. Repeat on the final release commit.

## G7.2 — history, secrets and licenses

- History (2026-10-11, all refs): 83 commits; every author and committer is
  `Kunal <kunalchandrakar2005@gmail.com>`. No `Co-Authored-By`, `Signed-off-by`,
  generated-by line or assistant name in any commit message.
- Secrets: every blob in the full history (601) was searched for the 34 exact local
  secret values from the ignored `.env*` files (names reported, values never printed)
  and for private keys, AWS/GitHub/OpenAI/Hugging Face/Groq token shapes, hex
  password assignments and credential-bearing Postgres URLs. None found.
  Limitation: no verified scanner (gitleaks, trufflehog) is installed; installing one
  needs approval. This targeted search is not equivalent to a full scanner.
- Runtime dependency licenses: Python distributions MIT, BSD, Apache-2.0, PSF-2.0 and
  MPL-2.0 (used unmodified); web production packages MIT, ISC and BSD-3-Clause.
- Data and models: BIRD Mini-Dev and the Arcwise corrections are CC BY-SA 4.0 and are
  attributed in the README; raw data is not in Git. Arctic-Text2SQL-R1-7B and
  Qwen2.5-Coder are Apache-2.0; weights are not redistributed.
- Project code license: not chosen yet (owner decision below).

## G7.3 — release preview (needs approval)

| Decision | Recommendation | Why |
| --- | --- | --- |
| Repository | `sqlwarden` under Kunal's GitHub account | matches the project name |
| Visibility | public | portfolio evidence; no secrets or raw data in history |
| Code license | MIT or Apache-2.0 | permissive, compatible with all dependencies |
| Branch | push `feat/foundation` as `main` | history is linear and attributed to Kunal |
| Public site | static Benchmark/Attack Lab on GitHub Pages (D-077) | INR 0, no third-party model |
| Live Ask | local laptop demo only | hosted path needs accounts and new code (DEPLOY) |

After approval: create the repository, add the remote, push, confirm CI on GitHub,
build `npm run build:static` plus `python -m scripts.export_static_site`, publish
`web/dist-static`, then run `scripts/smoke_g4_local.py` against the local demo and
check the public pages.
