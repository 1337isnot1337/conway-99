# Recovered allocated-lazy F0 continuation

The final pre-outage continuation is recovered. A fresh mathematical replay reproduces the captured replay report byte for byte. The run remains UNKNOWN; it does not exclude component zero or construct a graph.

The conditional setting is a globally prism-free, F-free split 18+18 triangle shell with component zero as its first 18-vertex component. All 480 first-incidence selectors remained free. The second component and its alignment were unrestricted.

## Frozen search outcome

The single run had a 180-second overall budget, at most 1,000 SAT refinements and 100 row passes, with the previously checked per-call limits. It stopped during a row pass after 185.240050815 seconds. The 5.240050815-second cooperative overrun is recorded. Thirty rows of the last pass were processed and thirty were left unprocessed.

| Result | Count |
|---|---:|
| SAT candidates checked against their current prefixes | 94 |
| Registry-only refinements | 30 |
| Complete row passes | 63 |
| Partial row passes | 1 |
| New exact individual-row obstructions | 109 |
| Exact rational individual-row boxes | 3,701 |
| Original shared-edge feasibility phases | 14 |
| Exact shared-edge obstructions | 14 |
| Bounded fallback calls | 0 |
| Exact shared-edge feasible points | 0 |
| Exact quadratic-allocation checks | 64 |
| Refinements found only by the quadratic portfolio | 0 |

The retained registry grew to 3,948 individual inequalities and 456 signed shared inequalities. Its 4,404 rows are distinct from the file named f0-allocated-lazy-terminal-registry.json.gz, which is the older 2,928-cut seed. The actual final records are the individual-registry.json.gz and symmetric-registry.json.gz members under f0-allocated-lazy-continuation-run01.

The final formula has 28,308 variables, 65,622 clauses and 8,628 explained primary clauses. Its SHA256 is b37bc914aa5ec290329410cddf249586abbe166b8e61d475af93f9a6bb958a4f. No incremental UNSAT answer or fresh proof query occurred. Each added clause follows from an exactly checked necessary inequality; there are no unproved visitation blocks.

The final portfolio contains 38 integer-potential families and 456 transported quadratic predicates. The 64 portfolio checks took about 4.258 seconds in total. They supplied no extra refinement in this run. This timing is an arithmetic observation, not a matched-input comparison of search methods.

## Recovery and exact replay

The archive contains all 363 frozen JSON or gzipped-JSON records, totaling 37,909,307 uncompressed bytes. The 6,766,832-byte archive has SHA256 7345f9cef9f0785310a7568067ba2a2e5dc90c72c8fe843051d3d3993a245ce0. Its manifest has SHA256 75e803942a2cda8332f20a90f5b668d13cff4978652b85238708130ce7c776cb.

A new read-only identification audit checks every archived member against its saved hash and the preserved local raw file. It also authenticates the source, preparation, cold-replay and restoration records. The recovered restoration report says that all 363 existing equal files were preserved, no missing files were written, and no unequal file was overwritten.

A separate isolated copy was then used for a fresh mathematical replay of the unchanged frozen reconstruct function. HiGHS run and dual-ray extraction, SciPy LP/MILP entry points, and PySAT Solver construction were disabled. No disabled entry point was attempted.

The replay took 49.206466550 seconds and used 334,556 KiB peak RSS. It rebuilt the exact initial and final formulas, checked every candidate and clause prefix, verified the individual and shared certificates, replayed the quadratic portfolio, and reconstructed all explained clauses. The resulting mathematical report has the same SHA256 as the pre-outage report: 4c437fb8ad028bc9aa55753cc0da33d557d884c75962531e991fc2743b2dde9a.

The new wrapper report records the separate recovery replay and its resource use. The older UNKNOWN transcript and all mathematical sources remain unchanged.

## Replaying the package

Use a disposable checkout or copy. The original bundle checker restores only its fixed transcript prefix and refuses unequal-file overwrites. Its complete replay entry point is:

```sh
python experiments/workspace/root_prism_free_f0_allocated_lazy_transcript_bundle.py cold-replay \
  --output /tmp/f0-allocated-recovered-cold-replay.json
```

The source and preparation manifests bind the required earlier packages. No optimizer is called by this replay. The separately saved recovered-cold wrapper additionally disables optimizer entry points and checks equality with the captured report.

## What follows from the recovery

The recovery makes the final 4,404 exact selector inequalities available for a separate Boolean-normalized fractional preparation. It does not authorize another copy of the old search. The newer joint fractional baseline has its own exact rational feasibility certificate; raw potential inequalities follow from that baseline. Capping and integer threshold rounding require a separate derivation before they can strengthen a real relaxation.

The original terminal status remains UNKNOWN: row-pass or overall time budget; unresolved. The recovered cuts retain their stated component-zero scope.
