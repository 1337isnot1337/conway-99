# Native case 4 query: unresolved

The single reviewed native CP-SAT query returned `UNKNOWN`. It produced
no incidence assignment and no infeasibility certificate. Case 4 remains
open. No retry was made.

The child reconstructed the complete 1,214-variable, 180,804-constraint
model and reproduced its frozen binary hash before solving. Reconstruction
took 27.47 seconds. The requested one-worker, 60-second solve returned
after 63.32 seconds; the backend reported 63.30 seconds of wall time.
The owned child exited normally and was reaped after 92.08 seconds,
within the 180-second hard parent wall.

The response reports:

| Counter | Value |
|---|---:|
| Boolean variables in the response | 1,193 |
| Integer variables in the response | 1,193 |
| Branches | 4,074 |
| Conflicts | 0 |
| Binary propagations | 164,584 |
| Integer propagations | 168,658 |
| LP iterations | 633 |
| Deterministic time | 18.600650708694953 |
| Child peak RSS | 1,504,460 KiB |

The solver-phase peak RSS exceeded the preparation's 1 GiB observed
stage limit. The query package explicitly records RSS without imposing
an operating system memory ceiling. Its hard limit was the parent wall.

Search-progress logging was not enabled. These aggregate counters do
not identify the time spent in presolve, probing, root processing, and
main search. In particular, zero recorded conflicts does not prove that
the solver spent the entire limit in presolve. The response confirms
propagation and LP work, but no phase timing can be recovered from the
saved log.

The result hash is
`70e24b6043bef675760ad1b186363dae7b40f6b7294e2e7d63e3712773436341`.
The outcome-only audit hash is
`c746790667520403414557baf1a8b005e542b8d49806a89df3559573724d0e39`.
That audit checks all current source/runtime bindings, the previously
completed cold proto replay, the process log, the terminal response and
its counters. It imports no CP-SAT model or solver and repeats no model
reconstruction. No feasible candidate required an incidence inspection.

```bash
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_native_cpsat_outcome_audit.py \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-run01/result.json \
  --output /tmp/conway99-case4-native-outcome-independent-audit.json
```

The full native formula remains frozen. A later change to candidate
generation or solver settings needs a separate model description and
review; this result does not authorize or imply a second identical run.
