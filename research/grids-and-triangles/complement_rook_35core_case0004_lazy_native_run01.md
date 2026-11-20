# Case4 lazy native run01

The authorized lazy loop returned UNKNOWN on its first ten-second native
call and stopped. It found no candidate and added no cover clauses.
Case4 remains open. The unchanged initial prefix has 1,214 Boolean
selectors, 2,271 original constraints and 14 proved units.

The owned child exited normally and was reaped. It took 20.76 seconds
from process entry through terminal recording; its peak RSS was 185,164
KiB. The parent did not reach its 180-second hard deadline. No second
native call or retry ran.

## Explicit phase evidence

| Saved event or statistic | Value |
| --- | ---: |
| Solver search start after presolve | 0.21 seconds |
| Main subsolver search start | 0.32 seconds |
| Main task wall time, rounded in log | 9.79 seconds |
| Solver response wall time | 10.003299411 seconds |
| Branches | 67,183 |
| Conflicts | 147 |
| LP iterations | 75,457 |
| Complete incidence candidates | 0 |

These explicit markers establish that this call reached main search
quickly. Initial presolve did not consume the ten-second search budget.
The LP iteration count is not a separate CPU profile. The older full
native query had no phase logging and is not reclassified by this result.

The internal log includes a generic `hint search` phase label. The saved
model and driver contain no supplied solution hint.

## Exact replay

Cold replay reconstructed the original mathematical row inventory, all
178,533 external covers, and the native prefix bytes. It checked the
single saved response and the unchanged chronological clause IDs. The
final prefix is identical to the initial 108,494-byte prefix. No solver
or optimizer was called by replay.

The separate phase auditor binds the terminal result, child log, response
and cold replay. It parses the phase markers and checks the numerical
statistics against the saved response. It builds no model.

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_lazy_native_loop.py replay \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-loop-preparation.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-run01/result.json \
  --output /tmp/case4-lazy-native-terminal-replay.json

.venv/bin/python experiments/workspace/complement_rook_35core_case0004_lazy_native_phase_audit.py \
  --output /tmp/case4-lazy-native-phase-audit.json
```

## What the presolve log does not prove

The log reports 22 removed input variables, including the 14 initial
units, and eight additional Boolean fixes during probing. It records no
primary variable IDs or proof reasons for those eight fixes. It also
reports zero affine relations. These messages alone do not justify
additional selector units or equivalences in a mathematical certificate.
An exact propagation derivation from the original constraints is a
separate task. This terminal package contains no such new inference.
