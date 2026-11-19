# Hall-strengthened two-grid completion run

A separate bounded run added all 1,377 certified local Hall clauses
to the frozen duplicate-label model and its 1,939 seed cap clauses.
It returned `UNKNOWN` after 180.48 seconds. The run found 31 partial
binary points and added 30,446 necessary cap clauses. None of the
points is a strongly regular graph.

The existence of two disjoint rook-isomorphic grids remains
unresolved. No UNSAT certificate or graph-existence claim is made
for this run.

## The added clauses

The [Hall audit](two_rook_tip_hall.md) checks every possible local
tip-neighborhood mask. Of the 256 masks, 103 have explicit integral
flow witnesses and 153 have explicit integer Hall obstructions.
Each obstruction is a consequence of the existing mixed core
equations and duplicate-pair packing.

For a forbidden mask at one tip, add the eight-literal clause
disagreeing with at least one specified adjacency bit. Translate
the nine-point rook coordinates to apply each mask at each tip.
This gives `9*153=1377` clauses.

The strengthened builder first replays the complete Hall
certificate. It constructs every translated clause, then decodes
the clause back to its unique falsifying local mask and verifies
that mask is the certified one. A separate reviewer checked the
translation and literal orientation.

The model also contains the 252 duplicate-label clauses described
in the [lex continuation note](two_rook_iso_pair_integer_lex.md).
They compare adjacency vectors only against the nine fixed tips.
No full-neighborhood ordering or graph automorphism is assumed.
No tip-PSD cut was included in this version.

## Formula and outcome

The initial model has 147,060 variables including auxiliaries and
301,252 clauses. These comprise the original 297,684 clauses, 252
duplicate-label clauses, 1,939 verified seed caps, and 1,377 Hall
clauses. The initial CNF hash is

```text
e4df127a4e86f4f48745a0291ef19bd725077dfbca6d2603c29a9d69ad394e7c
```

The run requested 180 seconds and at most 100 refinement rounds.
It found 31 partial points before interruption at 180.48 seconds.
Every point has all 99 degrees equal to fourteen and satisfies
every common-neighbor equation involving the 18-point core. It
also satisfies the duplicate-label and Hall clauses.

The outside/outside equations still fail. The number of defective
pairs ranges from 2,060 to 2,200; the last point has 2,108. These
counts come from reconstructing and checking each entire 99-point
matrix, not from a solver's feasibility status.

The same universally necessary cap-clause construction used in the
[first run](two_rook_iso_pair_integer.md) added 30,446 new clauses.
There are 32,385 distinct cap clauses including the seed. The final
formula has 331,698 clauses, with hash

```text
cab9952c3dd434581d67604cf650281f569d96eb361b4f2a8fc87e24cc0199ac
```

The first run, the lex-only run, and this strengthened run remain
separate and reproducible. All saved graph points are marked as
partial points; there is no completed graph witness.

## Exact replay

The frozen builder is
`experiments/workspace/two_rook_iso_pair_integer_hall.py`. The full
transcript is
`experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-hall.json.gz`.
It contains every point, every new cap witness, the seed transcript
hash, the Hall certificate hash, and both CNF hashes.
The adjacent artifact manifest binds both the compressed bytes and
the decompressed JSON by SHA-256. Compression is deterministic, with
gzip timestamp zero and no header filename.

```bash
python experiments/workspace/two_rook_iso_pair_integer_hall_replay.py \
  experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-hall.json.gz
```

This replay uses only the standard library. It checks the source
and certificate hashes, every Hall obstruction and flow witness,
every translated clause, all 33 partial points including the two
seed points, all defect histograms, and all 32,385 cap clauses.
It also verifies duplicate-label ordering for the 31 new points.

When the saved execution CNFs under `/tmp` are present, the replay
checks their full hashes, the actual 1,377 appended Hall clauses,
and the exact clause-by-clause extension from the initial formula
to the final formula. The mathematical point/cut replay remains
available from the repository artifacts when those execution files
are absent.
