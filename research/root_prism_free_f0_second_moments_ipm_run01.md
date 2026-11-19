# IPM second-moment query: run 01

The single authorized IPM/crossover call returned a numerical optimum with a
valid basis. Exact reconstruction did not produce a feasible point or an
infeasibility certificate. The mathematical result remains **UNKNOWN**.

## Unchanged model

This is the exactly equivalent reduced linear second-moment model with
15,200 variables, 21,692 rows and 183,702 nonzeros. The complete component-zero
domain is retained under the split 18+18, globally prism-free and F-free
assumptions. The second component and its alignment remain free. All 4,416
proved selector inequalities remain present. No PSD condition was imposed.

The matrix SHA-256 is
`5e417221ed814a5a0dcb03e31820871113bcc0eb8af2856dd2ac493958d16f39`.
The exact acceptance rule still requires all 650,350 original literal rows
and 183,834 original bounds. The prepared method and source bindings are in
`root_prism_free_f0_second_moments_ipm_query.md` and its publication manifest.

## Actual execution

| Observation | Value |
|---|---|
| Number of optimization calls | 1 |
| Backend status | `HighsModelStatus.kOptimal` |
| IPM iterations | 29 |
| Crossover iterations | 9,853 |
| Primal, dual and basis validity flags | All true |
| Numerical phase including setup and output | 161.196662 seconds |
| Numerical hard limit | 180 seconds |
| Exact arithmetic phase | 2.078181 seconds |
| Total supervisor time | 165.089986 seconds |
| Accepted exact certificate | None |

The interior phase reached its marked stopping line at approximately 70.8
seconds in the solver log. Requested crossover then completed. The numerical
record preserves all 15,200 column values, 21,692 row values and basis
statuses. Of the column statuses, 8,806 are basic and 6,394 are at their lower
bounds. These are numerical records, not an exact basis certificate.

The first bounded rational proposal passed all reduced variable bounds and
inequalities, but failed 5,960 exact equalities. The next two direct proposals
exceeded the denominator resource limit. The active-face reconstruction then
stopped at its unchanged 1,600-column limit before a large exact solve. No
claim is made that the numerical point has no exact nearby counterpart.

The backend did not report infeasibility, so the driver did not request a dual
ray. There was no retry or additional optimization. The valid numerical basis
and point are preserved for separate, reviewed exact reconstruction or PSD-cut
proposals.

## Cold replay and archive

The optimizer-free independent replay cold-rebuilt the equivalent reduction,
checked the complete literal domain and verified every source, preparation,
matrix and result binding. It returned
`PASS: terminal scope replay; no exact conclusion`.

All seven original run files are preserved byte-exactly in
`f0-second-moments-ipm-query-run01-archive.json.gz`. The archive compresses
1,987,077 bytes to 177,482 bytes. Its SHA-256 is
`274b51e321840d416bbeb520e6d1a3cf9a89877fbb0eeaa4806a586d6c189d7a`.
It was restored into a fresh directory and replayed; the replay is
byte-identical to the first terminal replay. Raw local files are unchanged.

The numerical JSON SHA-256 is
`20674e3a41842e42232df60e24abf3f34a5a5c8ec9a16a258d4906bb58562fd9`.
The terminal result SHA-256 is
`571ff5c23da8febc4bb0f76a54f1d9196e268d6a7bd1d02b3dc087ab516b3421`.

Replay without an optimizer:

```bash
python experiments/workspace/root_prism_free_f0_second_moments_ipm_archive.py unpack \
  --archive experiments/logs/root-prism-free/f0-second-moments-ipm-query-run01-archive.json.gz \
  --directory /tmp/f0-second-moments-ipm-run01-restored
python experiments/workspace/root_prism_free_f0_second_moments_ipm_replay.py replay \
  --preparation experiments/logs/root-prism-free/f0-second-moments-ipm-query-preparation.json \
  --model experiments/logs/root-prism-free/f0-second-moments-reduced-model.json.gz \
  --directory /tmp/f0-second-moments-ipm-run01-restored \
  --output /tmp/f0-second-moments-ipm-run01-replay.json
```

Both output paths must be fresh. No component exclusion, PSD certificate, or
graph construction follows from this run.
