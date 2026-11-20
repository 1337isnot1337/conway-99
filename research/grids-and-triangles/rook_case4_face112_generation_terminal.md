# The complete 112-zero-face numerical run

The single authorized row-generation run made one HiGHS call. It stopped
with a numerical optimum after 2.784 seconds and 4,507 simplex iterations.
The proposed common lower bound was approximately
\(t=0.01093575554898849\). The scan found no violated coordinate cover, so
no cover row was added to the initial model.

The generic rational rounding stage did not produce an accepted exact
point. The frozen result therefore remains **unresolved**. Neither
feasibility nor infeasibility is inferred from the numerical optimum.

The complete cold replay reconstructed all 166,010 base rows, all 167,112
rows after the max-min extension, and the full 164,044-row retained cover
pool. It verified the numerical-prefix transcript and all input bindings.
The replay performs no optimization and confirms that no exact point,
zero face, or contradiction was accepted in this run.

## Preserved proposal

The numerical record contains all 1,103 extended coordinates and a valid
saved simplex basis. Its active rows include 816 lower-side equations
\(x_j-t=0\). Substitution leaves 287 active equations: 286 original native
rows and the first parity equality. An artifact-only reconstruction can
solve this fixed square system and then check every original constraint.
These active equations are candidate-point assumptions, not new universal
restrictions on the incidence domain.

The source, model, bounds, row pool and call limits remain unchanged from
the published preparation. There was no second optimizer call.

## Frozen terminal bindings

- `rook-case4-face112-generation-run01/result.json`: SHA256
  `37b9488d027464f437db0228569338d49c0e1fddbd173c95523938681c4f3ce0`.
- `rook-case4-face112-generation-run01/iteration-00-numeric.json.gz`:
  SHA256 `8276a6d8b8a7d6c6dbfbcf2ce914add06d34a7618281d14be4a3f4d670f0f579`.
- `rook-case4-face112-generation-run01-replay.json`: SHA256
  `e6db315ca8b8e5337623e8ef27a15f24a761f77d2981e6fe66a1c0483b506665`.

The saved log and numerical basis accompany these files. Any later exact
reconstruction is recorded separately and does not rewrite this terminal
status.
