# BIRD EX source reference

Checked on 2026-10-03 for G0.7a preparation. This pins an inspected reference;
no comparator implementation, gold execution, benchmark freeze or score exists yet.
The selected data remains the 500-item Mini-Dev track in [DATA](DATA.md).

## Exact upstream source

Repository revision: `abd11b6db92a1c9f809b32f7564c7c71b34d67f0`, the same
Mini-Dev revision already recorded in DATA. Read-only Git HEAD and GitHub's tree
agree. Source bytes were fetched into memory, not executed or vendored.

| Inspected file | Bytes | SHA-256 |
| --- | ---: | --- |
| evaluation/evaluation_ex.py | 4779 | da1bbcd4530be83692d7c650c814ea9704bb710d0c953eb75d02ccb38233cf89 |
| evaluation/evaluation_utils.py | 4314 | f6943d249caac5aeaef9bce21d43dbf29dcef85a0c965a76df032a9542f308bf |

The [EX source](https://github.com/bird-bench/mini_dev/blob/abd11b6db92a1c9f809b32f7564c7c71b34d67f0/evaluation/evaluation_ex.py#L18-L22)
compares sets of result-row tuples. Row order and duplicate counts are ignored;
column positions remain significant. Its comparison adds no floating-point
tolerance, rounding, column matching or NULL substitution. Equality follows
Python values, not extra type tags; empty row sets compare equal. The surrounding
runner assigns failure to timeouts and exceptions.

The [execution helper](https://github.com/bird-bench/mini_dev/blob/abd11b6db92a1c9f809b32f7564c7c71b34d67f0/evaluation/evaluation_utils.py#L57-L67)
fetches both complete outputs before comparison. Its connection setup and extra
drivers are not appropriate for this project's restricted asyncpg runtime. Do
not run/copy that runner or reuse its example credentials. No code LICENSE was
found in the inspected repository tree; do not assume the dataset license licenses
all software there. Retain citations when independently reproducing the rule.

## Project obligations, not source claims

- Test duplicates, ordering, column positions, NULL, floats, empty outputs and errors
  when the comparator is implemented. Preserve the inspected EX rule.
- Reject incomplete/overflowed predictions rather than comparing matching prefixes.
- Keep the duplicate-preserving comparator for future voting separate from EX.
- Gold results stay offline; no reference answer reaches generation or repair.
- C1/G0.7 still own label validity, exclusions and split freezing. This reference
  is not a changed benchmark, an official leaderboard score or a complete evaluator.
