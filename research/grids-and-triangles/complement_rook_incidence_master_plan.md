# Incidence master and conditional joint-model pilot

The proposed pilot separates incidence selection from conditional edge
feasibility. Its proof semantics have been checked on a small complete
control. No large joint formula has been loaded or solved for this
pilot, and no Conway-core exclusion is claimed here.

## The two formulas

The master retains all 252 signature selectors and the 180 exact Gram
margin equations for the complementary-rook core. It fixes no incidence
design and imposes no graph symmetry. Every master solution selects
exactly 72 signatures. Each selected set must be checked against all
729 entries of `XX^T=12I+2J-B^2-B` before querying the edge model.

The conditional model is the existing frozen formula with 1,156,482
variables and 2,575,728 clauses. It retains all 252 selectors and all
20,934 eligible edges. The formula imposes Gram incidence, activation,
mixed and degree equations, and core-pair neighbor packing. It does not
impose all exterior common-neighbor caps.

For a master design `D`, pass exactly one signed assumption for each
selector:

\[
A_D=\{z_s:s\in D\}\cup\{\neg z_s:s\notin D\}.
\]

No counter or edge variable is fixed by the master. No additional
`a` bound, symmetry clause, or triangle cut is part of this baseline
proposal.

If the conditional formula returns SAT, its entire selected edge model
must be checked directly. All 252 selector values must agree with `D`.
The Gram, degree, mixed, and packing equations must hold, and the
99-vertex graph must be checked for all pair defects. A SAT point with
defects is a partial point of the necessary model. It is not a completion.

If the formula returns UNKNOWN, there is no model or exclusion to add.
The solver's last core must not be read as evidence for that call.

## What an assumption core proves

For a genuine UNSAT result, `get_core()` returns a signed subset
`C` of the supplied assumptions. Its signs must be preserved. The
claim to certify is

\[
F\land\bigwedge_{\ell\in C}\ell\quad\text{is UNSAT}.
\]

Only after that claim has an independently checked proof may the master
receive the clause

\[
\bigvee_{\ell\in C}\neg\ell.
\]

This clause excludes every incidence design containing the specified
signed pattern. A core need not be minimal. A fixed-design failure
therefore excludes the certified pattern; it excludes the whole core
only if the master is exhausted using valid necessary constraints and
certified cuts alone. An empty assumption core would require a checked
proof of `F` itself.

The proposed implementation uses a fresh proof-enabled solver for
`F` plus the exact core units, with no assumptions in that certification
solve. It writes the exact unit-augmented CNF and proof. A checker then
verifies the proof before the cut enters the master. If that proof
stage times out or fails, the cut is not added.

The artifact binding must include the original formula and domain
hashes, the ordered signed units, the new CNF hash, the proof hash, and
the learned selector clause. A retained proof requires the same checks
used elsewhere in the repository: retained input clauses belong to the
bound full formula, and DRAT verification succeeds. Rebuilding the full
formula from its frozen mathematical source remains part of publication
replay. The large base need not be mathematically regenerated for every
exploratory oracle call.

## A cumulative-proof failure control

The installed PySAT version is `1.9.dev23`. Its `Glucose4.get_proof()`
reads the complete proof file from solver creation. It does not return
only the latest solve call. An assumption-UNSAT call appends an empty
clause to that transcript.

The control uses two separately guarded, unsatisfiable pigeonhole
formulas. The first solve has assumption core `[1]`; the next has core
`[2]`. The cumulative proof includes the first empty clause. Checking
that cumulative text against the base plus only unit `2` fails. A fresh
proof solve on that exact unit-augmented formula verifies.

This is an expected negative control, saved as
`cumulative-expected-rejection.log`. It establishes why a later core
cannot inherit an earlier assumption proof merely by calling
`get_proof()` again. The fresh-unit certification path avoids that
dependency. No proof text is silently accepted or treated as a global
exclusion.

## Complete small positive control

The toy master has four selectors and chooses exactly two, so there
are six complete designs. Two separately guarded pigeonhole blocks
forbid designs `{1,2}` and `{3,4}`. The other four designs have explicit
SAT witnesses. Each unguarded pigeonhole block is independently checked
under all 64 assignments to its six variables.

The master/oracle loop visits all six designs. It verifies four SAT
witnesses directly and extracts two mixed-sign UNSAT cores. Each core
is proved by a fresh explicit-unit CNF and independently checked DRUP
proof. Its negated clause is added only after verification. Each cut
is also checked against the complete six-design truth table, ensuring
that it preserves all four valid designs.

The four SAT designs receive separate visitation blocks to finish this
small census. Those blocks are explicitly marked as exploratory. They
are not theorems and cannot be included in an exhaustion argument for
nonexistence. A real pilot must maintain the same distinction between
certified cuts and blocks used to avoid revisiting partial SAT points.

## Files and replay

Files:

- `experiments/workspace/complement_rook_incidence_master_controls.py`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-controls.json`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-controls.log`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-controls/`

The directory contains the small CNFs, DRUP proofs, positive checks, and
expected proof-rejection control. The JSON binds their hashes and the
local solver source.

```sh
python experiments/workspace/complement_rook_incidence_master_controls.py \
  --directory experiments/logs/grids-and-triangles/complement-rook-incidence-master-controls \
  --drat-trim /tmp/conway99-drat-trim/drat-trim \
  --output experiments/logs/grids-and-triangles/complement-rook-incidence-master-controls.json
```

These checks validate the proposed API use and proof handling. They do
not measure the conditional joint model's performance. If complete
incidence designs usually return partial SAT points, this pilot will
not learn exclusions from those designs; stronger exterior constraints
would then be needed.
