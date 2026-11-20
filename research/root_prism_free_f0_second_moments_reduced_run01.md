# Equivalent reduced second-moment query: run 01

The single authorized query ended **UNKNOWN**. It produced neither an exact
feasible point nor an exact infeasibility certificate. The complete original
linear model remains unresolved. No component is excluded and no graph is
constructed.

## Model and scope

The model concerns component zero in the split 18+18 shell under global prism
and F exclusion. The second component and its fiber alignment remain free.
All 480 possible first-component triples remain available. The model retains
the original fractional incidence and exterior-edge equations, all 4,416
proved selector inequalities, and the complete linear second-moment lift.
It imposes no positive-semidefinite constraint.

The exact reduction is described in
`research/root_prism_free_f0_second_moments_reduction.md`. It removes only
certified zero coordinates and rows with explicit exact implication witnesses.
Its real feasible set is equivalent to the original linear model after the
389 zero coordinates are restored.

| Quantity | Reduced representation |
|---|---:|
| Variables | 15,200 |
| Equalities | 5,973 |
| Inequalities | 15,719 |
| Matrix nonzeros | 183,702 |
| Original literal rows required for exact point acceptance | 650,350 |
| Original variable bounds required for exact point acceptance | 183,834 |

The matrix SHA-256 is
`5e417221ed814a5a0dcb03e31820871113bcc0eb8af2856dd2ac493958d16f39`.
The query preparation and all source bindings are recorded in
`f0-second-moments-reduced-query-publication-manifest.json`.

## Actual outcome

There was one HiGHS call, using the frozen simplex configuration and one
thread. The 60-second numerical budget included setup. The supervisor allowed
five additional seconds for a cooperative return and output preservation.

| Observation | Value |
|---|---|
| Backend status | `HighsModelStatus.kTimeLimit` |
| Simplex iterations | 10,479 |
| Numerical phase, including its output write | 60.162106 seconds |
| Cooperative numerical overrun | 0.162106 seconds |
| Reported primal, dual and basis validity | All false |
| Exact arithmetic phase | 3.038278 seconds |
| Total supervisor time | 65.279481 seconds |
| Accepted exact certificate | None |

The numerical arrays and basis statuses were saved despite their invalidity
flags. They are proposals only. The first direct rational proposal failed
3,864 variable bounds, 5,971 equalities and 3,859 inequalities of the reduced
model. The next two rational proposals exceeded the predeclared denominator
bound. Active-face reconstruction then stopped at its unchanged column
resource bound. These failures are not an infeasibility argument.

No dual ray was requested, because the backend did not report infeasibility.
There was no second optimization, feasibility repair, or automatic retry.
The first, unreduced run also timed out after more than 10,000 simplex
iterations. These two observations motivate a separate numerical-method
experiment; they do not establish any comparative speed claim.

## Cold replay and lossless archive

The independent replay rebuilds the exact reduction and literal domains. It
checks all source, preparation, matrix and run-file bindings. It returned
`PASS: terminal scope replay; no exact conclusion`. This is a successful
audit of an unresolved result, not a mathematical exclusion.

The deterministic archive
`f0-second-moments-reduced-query-run01-archive.json.gz` preserves all seven
original run files byte for byte, including the numerical arrays and empty
logs. It stores 1,937,323 bytes of original files in 149,612 compressed bytes.
Its SHA-256 is
`95737767282db79e36f7052be502a1c2d93ccf62b5ca3ae145a1a4036a396ad3`.
The archive was restored into a fresh directory and replayed. That replay is
byte-identical to the original terminal replay. The local raw run is unchanged.

Replay without an optimizer:

```bash
python experiments/workspace/root_prism_free_f0_second_moments_reduced_archive.py unpack \
  --archive experiments/logs/root-prism-free/f0-second-moments-reduced-query-run01-archive.json.gz \
  --directory /tmp/f0-second-moments-reduced-run01-restored
python experiments/workspace/root_prism_free_f0_second_moments_reduced_replay.py replay \
  --preparation experiments/logs/root-prism-free/f0-second-moments-reduced-query-preparation.json \
  --model experiments/logs/root-prism-free/f0-second-moments-reduced-model.json.gz \
  --directory /tmp/f0-second-moments-reduced-run01-restored \
  --output /tmp/f0-second-moments-reduced-run01-replay.json
```

Both output paths must be fresh. The terminal publication manifest records
the complete whitelist, hashes and dependency manifests.
