# Case4: first exact failed-literal prefix

The bounded prefix checked 17 of its 32 planned positive assumptions. It proved
one new zero, column 359. The other 16 assumptions reached noncontradictory
fixed points. These fixed points are partial assignments, not incidence
witnesses. Case4 remains open.

The run used the frozen 2,271 primary integer constraints, all 178,533 coordinate
covers, and the 14 previously proved zero columns. For each tested column `a`,
it added the explicit assumption `x_a = 1`. Only a checked contradiction could
produce the unconditional unit `x_a = 0`. Conditional assignments from a
noncontradictory branch were discarded before the next probe.

The tested prefix was:

```text
556, 554, 1078, 972, 443, 431, 633, 896, 575,
627, 1113, 359, 945, 566, 555, 909, 624
```

The complete initial candidate list has 1,200 columns. Thus neither the planned
32-column prefix nor the full candidate list was exhausted. The cooperative
60-second batch ceiling ended the run after 60.200 seconds. Peak resident memory
was 78,180 KiB. No solver, optimizer, retry, or additional production probe ran.

## Checked new unit

Probe 11 assumed column 359 selected. It reached a contradiction after 214 exact
reason records, with three conditionally selected columns and 210 conditionally
absent columns. No earlier learned zero was needed for this probe. The final
contradiction was a capacity-one triple containing two forced selected columns.

Every reason cites its original integer row or registered cover, its forbidden
value, and only earlier assignments. The complete transcript retains all 17
traces with compressed and decompressed hashes. A separate cold replay checked
the traces in order, including the induction that later probes may use the
already proved zero at column 359. It accepted exactly that one new unit.

The transcript does not promote the other conditional values to global units.
It also does not claim that the noncontradictory assumptions are extendible.

## Replay

From the repository root:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_failed_literal_batch.py replay \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-failed-literal-batch-preparation.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-failed-literal-run01/result.json \
  --output /tmp/conway99-case4-failed-literal-replay.json
```

The result SHA256 is
`98aa0aca94a60de4b37ab2224451b19396fa71a5672badbc1294dd9df28896d4`.
The saved cold replay SHA256 is
`a6813dbbb22475c4bf146d92351c340e118fdc424941b71b073dc106e6479a70`.

The separate Gram zero-face certificate derives a shorter consequence from
the contradiction support. It is not inserted into this frozen run.
