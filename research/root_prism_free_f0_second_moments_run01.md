# Second-moment linear query 01: unresolved

The one authorized query did not establish feasibility or infeasibility. HiGHS reached its time limit, and the exact phase accepted no certificate. No LP retry was made.

The frozen model has 15,589 variables, 53,287 rows and 279,627 nonzero coefficients. It retains all 4,416 Boolean-normalized selector inequalities and the complete linear second-moment constraints. The second component and its alignment remain free. PSD constraints were not enforced.

## Recorded outcome

| Item | Recorded value |
|---|---:|
| Production optimizer calls | 1 |
| Optimizer time allowance after setup | 57.709466506 s |
| Setup through optimizer return | 60.151739731 s |
| Numerical phase including record serialization | 61.124995529 s |
| Numerical cooperative overrun | 1.124995529 s |
| Simplex iterations | 10,023 |
| Exact phase | 1.728049915 s |
| Total supervised query | 63.953826184 s |

The numerical status is `HighsModelStatus.kTimeLimit`. The solution, dual, and basis validity flags are all false. The returned 15,589 column values, 53,287 row values, and both complete basis-status lists are preserved. No existing dual ray was requested because the reported model status was not infeasible.

The first rational proposal failed 3,510 variable bounds, 6,943 equalities and 13,374 inequalities. The next two common-denominator proposals exceeded the fixed bit limit. The active-face attempt then stopped at its declared 1,600-column limit. These failures describe the returned proposal; they do not prove that the model is infeasible.

The solver log records a presolved system with 47,909 rows, 15,198 columns and 259,381 nonzeros. Its dependency search stopped early. The time-limited simplex iterate was still infeasible in the solver's numerical diagnostics. None of these numerical observations is used as a certificate.

## Replay and archive

The standalone replay passed the source/model bindings and literal-domain checks, then confirmed that the recorded outcome is unresolved. No full feasible point or infeasibility certificate exists to validate. An additional fresh-directory replay of the lossless archive returned the same report.

The archive preserves all seven original run files byte for byte. The 3,786,501 raw bytes occupy 260,792 bytes in deterministic gzip. Its SHA256 is:

```text
68e5830069e76d205e4e12a72d410059978fd98a4b87527cf2ee281eea8ae4cf
```

To restore the exact original records into a fresh directory:

```bash
python experiments/workspace/root_prism_free_f0_second_moments_archive.py unpack \
  --archive experiments/logs/root-prism-free/f0-second-moments-query-run01-archive.json.gz \
  --directory /tmp/f0-second-moments-run01
```

Then use the frozen standalone replay from the query preparation, with that directory. The original raw local records and all frozen mathematical sources remain unchanged.

The next preparation will remove only exact structural redundancies, with witnesses for every omitted constraint and the original full acceptance rules retained. No further optimizer call is authorized by this result.

