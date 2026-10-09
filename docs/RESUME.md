# Resume evidence

Use these only with the local-development qualifier; this is not an official benchmark or public leaderboard score.

- Built a local read-only text-to-SQL evaluation slice with guard checks, restricted PostgreSQL execution and compact tracked metrics that exclude raw prompts, SQL, rows and credentials.
- Arctic measured 22/100 exact matches on the frozen development slice; Qwen measured 3/100 under its smaller context window.
- Added phase metrics: Arctic parse 0.89, guard 0.74, execution 0.62; paired Arctic-Qwen delta 0.19 on 100 matched development questions.
