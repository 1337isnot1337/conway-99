# Case4 forward propagation reaches no new assignment

The one authorized exact forward closure finished. Its only assignments
are the 14 previously proved absent columns. It derives no selected
column, additional absent column or contradiction. Case4 remains open.

The closure uses all 2,271 original integer rows, with 28,784 term
occurrences, and all 178,533 coordinate covers. It starts from the 14
proved cover units. It checks signed Boolean interval implications and
guarded unit propagation. There is no solver call or failed-literal probe.

The closure completed in one sweep, taking 0.259 seconds. A separate
integer reason and fixed-point check took 1.752 seconds. Including input
reconstruction, the first process took 2.694 seconds and used a peak RSS
of 77,280 KiB. The 60-second closure allowance was not exhausted.

Cold replay reconstructed the immutable row and cover inventory, checked
the 14 unit reasons, and verified that no remaining one-variable interval
or cover implication was available. It did not repeat discovery or run
an optimizer. The result proves completeness only for these forward
propagation rules. It does not determine what a failed-literal assumption
would imply.

The eight extra fixes in the native presolve log therefore have not been
recovered by this procedure. Their IDs and reasons remain unspecified in
that log and are not accepted as mathematical premises.

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_primary_propagation_closure.py replay \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-primary-propagation-closure-preparation.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-primary-propagation-closure-run01.json \
  --output /tmp/case4-primary-closure-replay.json
```
