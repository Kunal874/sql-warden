# BIRD EX source reference

Source checked on 2026-10-03 for G0.7a preparation and rechecked on 2026-10-04.
The comparator is implemented and passes actual native checks; final review is next.
No gold execution, benchmark freeze or aggregate accuracy score exists yet.
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

## Preparation update (2026-10-04)

This records the pre-approval preparation snapshot; current evidence follows below.

Both pinned source files were fetched into memory again and their byte lengths
and SHA-256 hashes match the table above. No source was saved, executed or vendored.
The equality rule is unchanged. Synthetic Python probes confirm native numeric
equality, precise decimal/binary-float differences, adjacent-float differences,
date/text differences and Python's shared-versus-distinct NaN identity behavior.

The [two-task implementation plan](superpowers/plans/2026-10-04-ex-comparator.md)
is prepared and self-reviewed, awaiting Kunal's review. It reuses the executor's
complete typed QueryResult rather than its JSON budget representation. Proposed
fixed outcomes are match=1, mismatch=0, unsuccessful prediction=0, prediction
comparison error=0, and invalid reference=None. Invalid reference is a signal for
the future frozen validity manifest, not an automatic exclusion or denominator
change. Pending/interrupted jobs remain the future job runner's responsibility.
This offline function will expose no rows or raw diagnostics and perform no I/O.

All three Python examples parse and pass snippet lint/format checks; the proposed
absent module is explicitly classified as first-party only for snippet lint.
AST inspection counts 60 proposed units and 17 proposed real controls. All 24
successful-pair SQL inputs pass the existing pure guard. None of those new tests,
modules or SQL controls was executed. Existing suite verification is recorded in
PROGRESS; it does not establish comparator acceptance. No implementation, new
dependency, gold execution, model inference or benchmark score exists yet.

Residual boundary: ok means complete only when produced by the trusted executor;
the Python dataclass itself is not an unforgeable completion token. Sets require
additional memory, and arbitrary internal Python objects are not sandboxed.
Future voting needs separate duplicate-preserving semantics. Do not expose these
constructors, gold rows or a reference loader to model/request-controlled code.

## Implementation: Task 1 (2026-10-04)

Kunal's "yes do it" approved the written plan. `sqlwarden.comparator.compare_ex`
now consumes the existing complete typed QueryResult objects, independently
reproducing the pinned row-tuple set equality without sorting or normalization.
The frozen/slotted EXComparison record contains only score and fixed reason:

| Condition, reference checked first | score | reason |
| --- | --- | --- |
| Unsuccessful/malformed reference | None | gold_invalid |
| Unsuccessful/missing prediction | 0 | prediction_failed |
| Malformed/unhashable prediction rows | 0 | comparison_error |
| Equal complete row sets | 1 | match |
| Unequal complete row sets | 0 | mismatch |

There is no database/model I/O, SQL/file/env loader, gold-row output or raw error
message. Column names and sizing bytes are metadata, not comparison inputs.
Non-ok statuses are checked even when a synthetic fixture retains a matching
prefix. Reference failure cannot authorize dropping an item; C1/G0.7's frozen
manifest owns that decision. Do not call this function for pending jobs or use
it for the future online vote.

Observed RED: the new unit file failed collection because the comparator module
did not exist (0.39s). After the small implementation, all 60 units passed (0.19s).
Full no-env suite: 448 passed, 141 skipped (2.24s); lint/20-file format pass.
The new native tests and single final review have not run yet. Unit checks do not
establish PostgreSQL acceptance or an official benchmark score. Trusted-constructor,
native-type adaptation and set-allocation residuals above still apply.

## Native acceptance: Task 2 (2026-10-04)

All 17 comparator integration controls pass on actual PostgreSQL (2.19s), using
only the existing fixed California reader/executor for handwritten test SQL.
They cover the known schools count, order/duplicate handling, swapped columns,
empty outputs of different widths, NULL, native Decimal/int and date/text values,
distinct NaN objects and adjacent floats. They also verify overflow and engine
failure on either side, guard-denied prediction, fixed private output and a
successful next query from the same pool after failure. No reference/generation
benchmark item, new login, SQL rewrite or privilege change was needed.

Full configured suite: 606 passed, zero skips (15.36s), including 158 actual
PostgreSQL tests. Without private configuration: 448 passed / 158 skipped (2.12s);
setup only: 491 passed / 115 skipped (3.70s). Locked sync, lint/21-file format and
whitespace checks pass. Original inputs, dependency files and existing runtime
modules remain unchanged. The single final read-only review is pending.

This proves the bounded native handoff for these controls, not official dataset
scores, conversion validity, a frozen exclusion manifest or inference isolation.
The trusted-result/offline/set-allocation limitations remain; no aggregate metric,
voting comparator, cache loader or model/CLI path has been implemented here.
