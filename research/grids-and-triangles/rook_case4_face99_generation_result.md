# Face99 row-generation outcome

The single prepared run stopped after one numerical optimization call.
The solver reported an optimal max-min value of approximately
0.0107372890223. Scanning all 169,050 rows found no violation above the
prepared 1e-7 tolerance. The maximum floating residual was about 1.42e-14;
all 165,969 coordinate covers had nonnegative floating slack. No cover
was appended, and there was no second optimizer call.

This is not an exact feasibility certificate. All eight coordinate-wise
rationalization attempts failed the first exact Gram row. No exact
infeasibility certificate, new zero face, or rational point was accepted.
The terminal status is unresolved.

The solver call took 10.441 seconds. The numerical phase took 11.393
seconds, and the exact proposal checks took 5.361 seconds. Total run time,
including input verification, was 23.918 seconds. Peak RSS was 429,780
KiB. The separate cold replay rebuilt the complete published-input face
model and replayed the sole prefix scan in 69.663 seconds. Its recorded
conclusion is the same unresolved status; it called no optimizer.

The complete numerical point, basis, row multipliers and original row IDs
are retained in iteration-00-numeric.json.gz. All 1,116 variable columns
are basic. The 1,116 nonbasic rows consist of 829 lower extension rows
x_j=t and 287 native rows, with 148 upper and 139 lower statuses. Therefore
the saved basis suggests a 287-variable exact reconstruction after those
829 substitutions. This is a proposal for a separate arithmetic task,
not a set of proved equalities for all feasible points. Every acceptance
would still have to check the complete original row pool exactly.

The full trace replay command is:

```sh
python experiments/workspace/rook_case4_face99_cover_generation.py replay --preparation experiments/logs/grids-and-triangles/rook-case4-face99-cover-generation-preparation.json --model experiments/logs/grids-and-triangles/rook-case4-face99-model01/model.json --arrays experiments/logs/grids-and-triangles/rook-case4-face99-model01/arrays.npz --root . --result experiments/logs/grids-and-triangles/rook-case4-face99-cover-generation-run01/result.json --output /tmp/rook-case4-face99-terminal-replay.json
```

The face99 model, its sources and this outcome remain frozen. No binary
incidence, exterior completion, or Conway graph has been constructed or
excluded by this run.
