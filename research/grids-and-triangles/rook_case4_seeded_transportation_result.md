# The 99-zero face is stable under the transportation closure

The single authorized continuation completed all 105 projections in one
sweep. It found no new zero column and no contradiction. The resulting
face still has 99 proved zeros and 1,115 remaining original columns.

The forward run took 2.555 seconds, including complete seed and domain
reload. The separate replay rechecked the six short Gram/triple identities,
all 14 empty-cover dominance proofs, and the final feasible flow for every
projection. It also checked that every active cell lies in a positive-flow
or residual-cycle possibility. There are no new cut events to replay.

This is a fixed point for the specified 105 capacitated transportation
projections. It does not prove the full selector system feasible. In
particular, different projected flows need not lift to one common vector
of attachment weights, and the original row-potential and coordinate-cover
constraints remain part of the complete selector relaxation.

The original two-stage run and this seeded continuation are separate,
immutable runs. Both runs and their verification use exact integer flow or
row arithmetic and call no numerical optimizer.

Artifacts are under `experiments/logs/grids-and-triangles/`:

- `rook-case4-transportation-seeded-run01.json`: one complete sweep, zero
  new events, all 105 terminal flows.
- `rook-case4-transportation-seeded-run01-replay.json`: complete seed and
  terminal-flow replay.
- `rook-case4-transportation-seeded-terminal-manifest.json`: frozen source,
  preparation, seed, result and replay bindings.

The next model can substitute exactly these 99 proved zeros. Any omitted
original row still needs a separate exact implication or unit-box
tautology check. No new LP is run or claimed in this result.
