# First query with the exterior-row cuts

The single authorized query returned SAT. Its 60-triple incidence passes
the complete original component-zero specification and all 12 new
exterior-row inequalities. A separate cold replay reproduced the full
formula and checked the point. It is not an exterior graph or a solution
of the Conway99 problem.

## Formula and run

The formula has 480 free incidence selectors, 28,308 total variables,
and 56,994 clauses. It contains the original 56,550 clauses and exactly
444 primary clauses encoding the 12 necessary row inequalities. No
incidence design, graph symmetry, or second component is fixed.

| Item | Outcome |
| --- | --- |
| Solver | Fresh proof-enabled Glucose4 |
| Requested budget, including bootstrap | 60 seconds |
| Bootstrap | 0.094768 seconds |
| Solver return, including bootstrap | 0.106569 seconds |
| Conflicts | 65 |
| Decisions | 451 |
| Propagations | 93,688 |
| Status | SAT, exact necessary incidence checked |
| Separate cold replay | Passed |

The CNF SHA256 is
`419a570047e7c1fd61cc2ddbeb6eade45af0a2570518c5fe1ea78954ad9142b0`.
The result is
`experiments/logs/root-prism-free/f0-exterior-row-cut-overlay-run01/result.json`,
with SHA256
`80daa535121c7c6c05b0b3ce90f65085b1e34236d8d53b143fe1e5ec01765bf3`.
The saved result contains all 60 selected signature indices and all
new-cut evaluations.

## What the point establishes

The point has 60 distinct triples. It satisfies all 171 local Gram
positions, all 78 saved $F$-conflicts, all 12 saved prism conflicts,
the derived occupancy identities, and all 444 new clauses. Its
occupancy distribution is 24 triples of profile $111$ and six of
each of the six $210$ orientations. These counts were inspected;
they were not additional constraints in the query.

The new point shares 52 triples with the earlier incidence. It still
contains signature 479, $\{11,16,17\}$, whose row gave the first cut.
That is its only selected target among the 12 transported inequalities.
The corresponding capped inequality is tight, with both sides equal
to two.

The point selects only signature 216 among the 55 positive-weight
candidates of that row. Its original integer weight is six, equal to
the required weighted demand. Hence any actual exterior row at
signature 479 would have to use signature 216 and avoid each selected
eligible triple with negative integer weight. This is a necessary
equality consequence. Feasibility of that full exterior row was not
tested in this query.

The old incidence remains archived and still passes its original
model. Its inability to extend to an exterior graph is a separate,
checked result. The new cuts reject it without restricting the new
query to a particular replacement design.

## Verification and limits

The coordinator read the complete overlay, and a separate reviewer
independently reconstructed the 480-column domain, all 12 target
neighbor sets, core relabelings, integer products, and guarded Boolean
logic. The reviewer also compared the actual CNF body: all 56,550 old
clauses remain unchanged and exactly 444 certified clauses follow.

The terminal cold replay reran the complete shell/component coverage,
rebuilt the base formula and all transported cuts, matched the CNF
hash, and directly inspected the saved incidence. No second query or
continuation was run.

The point specifies one component's incidence only. The second shell
component, its incidence, and the 60-vertex exterior graph remain
unspecified. The result does not exclude component zero, any other
component, or the entire split case.
