# First globally prism-free complete-cap pilot

All four cases returned **UNKNOWN** at their requested 60-second limits.
The pilot produced no graph, UNSAT return, checked proof, or exclusion.
Every globally prism-free matching case remains open.

The frozen formulas are described in
[`root_prism_free_overlay.md`](root_prism_free_overlay.md). Each retains
the complete rooted common-neighbor caps, canonical matching units,
audited lex comparisons, and 84 zero cell-side variables. Each adds
the same 34,440 necessary near-axis prism clauses. The separate
minimum-partition refinement was absent throughout this run.

## Terminal outcomes

The four cases ran sequentially with Glucose4 proof logging enabled.
The 60-second budget included CNF parsing and solver bootstrap.
Reported elapsed times include the return from the interrupt and final
solver bookkeeping.

| Case | Anchor partition | Outcome | Actual seconds | Conflicts | Decisions |
| ---: | --- | --- | ---: | ---: | ---: |
| 7 | `222` | UNKNOWN | 60.228356476 | 140,239 | 460,871 |
| 8 | `24` | UNKNOWN | 60.321845876 | 112,709 | 334,737 |
| 9 | `33` | UNKNOWN | 60.441717967 | 153,122 | 471,643 |
| 10 | `6` | UNKNOWN | 60.220186982 | 157,720 | 434,885 |

The batch started at `2026-11-19T04:47:40.467043Z` and finished at
`2026-11-19T04:51:46.062606Z`, with total elapsed time
245.593872481 seconds. The batch process exited normally.

No UNSAT proof was emitted because no case returned UNSAT. The proof
replay wrapper remains available for future certified outcomes. No
candidate reached the exact 99-vertex validation path in this pilot.

## Audit and bindings

An independent read-only review reconstructed the full 34,440-clause
set using ordered four-site permutations. It checked the local prism
reduction, the distinction between global prism-freeness and a
prism-free chosen root, the overlay assembly and invariance, and the
runner and certificate wrapper. It found no soundness issue. That
review did not rebuild or solve a large CNF.

The terminal summary matches every result to its model, exact CNF
hash, requested budget, terminal status, statistics, and log. It also
checks that the frozen source hashes still match. This is an outcome
and provenance check, not an UNSAT certificate.

Artifacts under `experiments/logs/root-prism-free/`:

- `run-01/batch.json`
- `run-01/case-07-result.json` through `case-10-result.json`, with their logs
- `batch-run-01.log`
- `run-01-summary.json`
- `independent-read-only-review.json`

## What remains

The four-case union covers the globally prism-free hypothesis. It
does not cover graphs that have prisms elsewhere but happen to have a
prism-free chosen root. No earlier same-index case is excluded by
these UNKNOWN results.

The separately checked minimum-partition component encoding is recorded
in [`root_prism_free_anchor_min.md`](root_prism_free_anchor_min.md).
It changes the coverage convention again by choosing a near anchor of
minimum component type. No formula from that refinement was used in
this pilot, and no continuation is included in these outcome records.
