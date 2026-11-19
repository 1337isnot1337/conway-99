# Exact edge-orbit packing bounds in the fixed F0 component

The complete census gives an exact compatibility bound for each of the
5,643 retained exterior-edge orbits. Sixty-two bounds improve the bounds
transferred from the corresponding selector-pair orbits. No orbit is
forced to zero, and no complete incidence or graph is constructed.

This calculation uses the fixed F0 component and its existing literal
core. It does not assume that a completed graph admits a core symmetry.

## Why the bounds hold

For an edge orbit R, construct a finite graph whose vertices are the
literal eligible exterior edges in R. Two vertices are adjacent when
the two edges pass the retained necessary pairwise conditions. If a
graph completion selects several edges from R, those edge objects form
a clique in this finite graph. Thus its clique number bounds the edge
count for R.

Every omitted compatibility edge has a literal witness. The complete
inventory has 76,641 exclusions from a previously proved selector-pair
zero, 576 from a mixed quota-one common-neighbor condition, and eighteen
from a previously proved two-edge prism obstruction. These counts use
the first applicable witness in a fixed priority order. They do not
count all possible witnesses for the same exclusion.

The checker distinguishes the two sources of earlier selector-pair
zeros: 4,320 literal pairs have direct quota-one Gram witnesses; ninety
use the earlier checked binary motif argument. It does not assign a
Gram witness to all 4,410 pairs.

The twelve actual core relabelings preserve every finite compatibility
graph and act transitively on its vertices. Therefore, for any fixed
vertex v,

`omega(G) = 1 + omega(G[N(v)])`.

This reduces each census to at most eleven vertices. The saved exact
certificate uses the deletion recurrence

`omega(S) = max(omega(S without v), 1 + omega((S without v) intersect N(v)))`.

Each certificate records all required subset values and an attaining
clique. The attaining clique concerns the finite compatibility graph;
it need not extend to an incidence or to the target graph.

## Complete results

| Bound | Edge orbits |
| ---: | ---: |
| 1 | 30 |
| 2 | 197 |
| 3 | 1,533 |
| 4 | 233 |
| 5 | 73 |
| 6 | 3,156 |
| 12 | 421 |

The 5,643 bounds include 5,153 improvements over raw orbit sizes.
The comparison with the already certified selector-pair bound is more
informative:

| Previous pair bound | New edge bound | Edge orbits |
| ---: | ---: | ---: |
| 12 | 6 | 50 |
| 6 | 3 | 8 |
| 12 | 4 | 2 |
| 6 | 2 | 1 |
| 4 | 2 | 1 |

These are improvements over that specific comparison. They are not a
claim that all sixty-two bounds are independent of every other row in
the complete count model.

## Verification and limits

The graph preparation completed in 11.50 seconds. A separate 5.59-second
preparation checked every stored nonedge premise, all actual actions,
the literal correspondence with each selector-pair orbit, and graph
inclusion in the previous pair-compatibility graph. It performed no
clique search.

The single census completed in 12.73 seconds and saved 100,315 recurrence
states. Its uncompressed ledger has 1,763,970 bytes. The separate
2.21-second replay checked every saved recurrence without repeating a
clique search. The census and replay had separate sixty-second owners;
their observed owner times were 29.87 and 5.28 seconds. No optimizer ran.

The sources are
[graph preparation](../experiments/workspace/root_prism_free_f0_edge_orbit_packing_preparation.py)
and [census and replay](../experiments/workspace/root_prism_free_f0_edge_orbit_packing.py).
The frozen [census](../experiments/logs/root-prism-free/f0-edge-orbit-packing-scan01.json.gz),
[certificate ledger](../experiments/logs/root-prism-free/f0-edge-orbit-packing-scan01-ledger.jsonl.gz),
and [cold replay](../experiments/logs/root-prism-free/f0-edge-orbit-packing-scan01-cold.json)
bind the premises and complete result.

The next use is a separate domain intersection on the signed integer
count model. Such a model still needs exact acceptance of any returned
count vector, a literal selector lift, and an exterior-edge completion.
The other F0 components and the unrestricted graph problem remain open.
