# Case 4 row-loop terminal record

The single authorized continuation reached its requested 60-second
budget after 60.363 seconds. It added 58 checked integer exterior-row
inequalities, bringing the pool to 60. Cold optimizer-free replay passed
for every inequality and every model-prefix binding. Case 4 remains
unresolved.

| Round | Cuts in the global LP | Positive proposal columns | Rows tested | New exact inequalities | Complete row pass |
|---|---:|---:|---:|---:|---|
| 0 | 2 | 287 | 287 | 21 | Yes |
| 1 | 23 | 290 | 290 | 17 | Yes |
| 2 | 40 | 290 | 271 | 20 | No |

All three global LPs returned numerical optimal statuses. The 848 visited
row LPs finished before the loop stopped. No exact feasible point or
Farkas infeasibility certificate was obtained. There was no SAT query.

The final 20 inequalities were discovered after the last reoptimization.
Thus the experiment makes no LP feasibility claim about the complete
60-cut pool. Nineteen positive columns of the final proposal were not
tested:

```text
1134, 1138, 1142, 1144, 1149, 1154, 1164, 1165, 1174, 1175,
1178, 1184, 1185, 1193, 1196, 1199, 1200, 1205, 1209
```

The greatest absolute integer potential coordinate among the 60 cuts is
660. Each cut's complete coefficients and demand are stored with its
integer potential. Their mathematical validity follows from the exact
row identity and endpoint activation. Numerical proposal gaps remain
numerical diagnostics.

## Frozen result and replay

Result:
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-run01.json`

Its SHA256 is
`9b0713b668e2c0ae47139007cdf6ad8961be2fb0e9caf2b42e0193a5528ecaa6`.

Optimizer-free replay:
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-replay01.json`

Its SHA256 is
`0de66ba641844b5ff0b942cc0d1f5c79c5236d41a6eee48b26d3a6694c22ba93`.

The source, preparation, coordinator review, exact input dependencies,
result, and replay are listed in the terminal artifact manifest. The
separate equivalent eleven-coordinate presentation of the original
column 628 cut does not change any frozen certificate.

These results concern only indexed 35-core case 4. They leave all earlier
SAT outcomes and the remaining matching cases unchanged.
