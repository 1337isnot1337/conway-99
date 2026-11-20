# Free reduced-star feasibility remains unresolved

The first unconditioned query of the reduced \(R_8\) star returned UNKNOWN.
It supplied no selector assumptions, additional cuts, graph symmetry
restrictions, or new common-neighbor caps. The result establishes neither
feasibility nor infeasibility of this subsystem.

The frozen formula has 252 incidence selectors, 4,456 retained edge variables,
65,774 declared variables including unused primary-number gaps, and 144,864
clauses. Its mathematical definition and equivalent removal of redundant
counters are in `complement_rook_core_star_oracle.md`.

One fresh Glucose4 solver ran with proof logging enabled. The requested
60-second allowance included parsing and bootstrap. Bootstrap took 0.229
seconds; the cooperative interrupt returned at 63.825 seconds. Total elapsed
time was 63.860 seconds. The transcript records 170,022 conflicts, 440,464
decisions, and 267,097,540 propagations. Peak process RSS was 78,068 KiB.

There is no saved SAT point, UNSAT proof, learned selector cut, or exclusion
from this run. It did not continue after the UNKNOWN result. The previously
checked conditional proofs and the model-reduction identities are unaffected.

## Frozen files

The runner is
`experiments/workspace/complement_rook_core_star_free.py`.
The pre-solve source and formula bindings are in
`experiments/logs/grids-and-triangles/complement-rook-core-star-free-model.json`.
The terminal result and log are
`complement-rook-core-star-free-pilot01.json` and
`complement-rook-core-star-free-pilot01.log` in the same log directory.

The runner contains separate validation paths for future result types. A SAT
point would require exact checks of all 729 Gram entries, endpoint activation,
all 952 distinct supported mixed rows, and core-pair packing. Visible pair
defects within the selected star would be reported without being mistaken
for violations of caps absent from this baseline. An UNSAT result would
require direct DRAT and a cold baseline/star rebuild with retained-input
inclusion and another proof check. Neither result path was reached here.

`complement-rook-core-star-free-pilot01-artifacts.json` lists the immutable
files and hashes. The terminal binding audit checks the UNKNOWN status and
the absence of any witness or certificate; it is not a feasibility proof.
