# The first local set passes the old-core Gram incidence test

The eight original signatures used by the first 35-core are compatible
with the full binary incidence equations on the old complementary-rook
27-core. An exact 72-column witness was found with parameter $a=10$.
This control shows that the checked case-zero exclusion does not follow
from fixing those eight selectors in the old Gram equations alone.

The tested local set is

\[
L=(0,1,9,10,18,20,26,27).
\]

The control retains all 252 original signature variables. It imposes
every old-core Gram equality and appends exactly the eight positive units

\[
(1,2,10,11,19,21,27,28).
\]

The $R_0$ diagonal has quota eight, so these units force the other twenty
$R_0$ candidates absent. No local matching is specified. There are no
attachment variables, exterior-edge variables, learned joint-model cuts,
or restrictions on $a$.

The formula contains 19,800 Gram clauses and eight unit clauses. A
separate unconditioned positive control uses the established explicit
72-column complementary-rook incidence design. It confirms the Gram
counter encoding without asserting that this positive-control design
contains $L$.

The conditioned query used a fresh proof-enabled Glucose4 instance with
a ten-second budget including bootstrap. It returned SAT after 0.0164
seconds. The direct verifier checked all 72 selections, every one of the
729 dense Gram entries, and exact membership of the eight $R_0$
signatures. A separate cold reconstruction reproduced the full CNF hash
and checked the saved witness again.

The witness leaves every edge between the 72 exterior vertices
unspecified. It is an incidence control, not a graph completion.

- Source: [complement_rook_35core_local_incidence_control.py](../../experiments/workspace/complement_rook_35core_local_incidence_control.py).
- Bound model: [model.json](../../experiments/logs/grids-and-triangles/complement-rook-35core-first-local-Gram-control01/model.json).
- Exact witness: [result.json](../../experiments/logs/grids-and-triangles/complement-rook-35core-first-local-Gram-control01/result.json).
- Cold replay: [cold-replay.json](../../experiments/logs/grids-and-triangles/complement-rook-35core-first-local-Gram-control01/cold-replay.json).

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_local_incidence_control.py \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-first-local-Gram-control01 \
  --replay-output /tmp/complement-rook-35core-Gram-control-replay.json
```
