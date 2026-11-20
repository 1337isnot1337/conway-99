# Pair conflicts and clique capacities from the surviving boxes

The complete 191-box cover gives 2,855 pair conflicts among the 1,102
surviving selector coordinates. It gives no implication of the form
`x_i <= x_j` between distinct surviving coordinates. The conflict graph has
665 nonisolated vertices and 1,216 nontrivial maximal cliques, of sizes two
through eighteen. Every clique gives a necessary capacity with upper bound
one. The other 437 coordinates contribute only their existing unit bounds
through this calculation.

At the exact point with denominator `3461944222`, every individual pair
conflict holds. Exactly one maximal-clique capacity fails. Its support is
`{23,260,399,403,406,761,762,763,764,765,803}`, and its excess is
`37621464/3461944222`. This is exactly the previously proved
[low-face capacity](rook_case4_box_low_face_units.md). This scan therefore
supplies no additional violated inequality at that point. It preserves a
fixed family for checking a later exact point. No comparison establishes
that every retained row is new relative to the complete existing model.

## Exact argument

For a surviving coordinate `i`, let `P_i` contain the boxes in which `i` is
not forced to zero, and let `O_i` contain the boxes in which it is forced to
one. Every actual Boolean incidence lies in at least one of the accepted
boxes.

If `P_i` and `P_j` are disjoint, no such incidence can select both coordinates.
This proves `x_i+x_j<=1`. If `P_i` is contained in `O_j`, selecting `i` forces
`j`, giving `x_i<=x_j`. The scan checks all 606,651 unordered pairs and all
1,213,302 ordered distinct pairs with exact integer bit sets.

A clique in the conflict graph has pairwise disjoint possible-box sets.
Consequently each box permits at most one of its coordinates. Its capacity
is valid over the entire box, including fractional assignments within that
box. The complete branch cover makes it necessary for every Boolean
solution in case four. This does not assume that the union of boxes is a
convex set or that an arbitrary fractional point belongs to one box.

## Artifacts and checks

The pair source
[`rook_case4_surviving_box_pair_scan.py`](../../experiments/workspace/rook_case4_surviving_box_pair_scan.py)
reads the cold-bound state strings, checks their hashes, and constructs the
two masks for each coordinate. Its
[compressed certificate](../../experiments/logs/grids-and-triangles/rook-case4-surviving-box-pair-scan01.json.gz)
retains every mask, pair conflict, implication and exact point evaluation.

The clique source
[`rook_case4_surviving_box_cliques.py`](../../experiments/workspace/rook_case4_surviving_box_cliques.py)
independently reconstructs the pair graph and uses a bounded Bron-Kerbosch
enumeration on its nonisolated vertices. It finishes the enumeration in
this run. Every reported clique is then checked for maximality and against
all 191 box maxima. The
[compressed clique certificate](../../experiments/logs/grids-and-triangles/rook-case4-surviving-box-cliques01.json.gz)
contains the complete family and all those maxima.

A separate [independent replay](../../experiments/logs/grids-and-triangles/rook-case4-surviving-box-cliques-independent-replay01.json)
reconstructs the masks with Python sets and enumerates the maximal cliques
with NetworkX. It imports neither producer. It agrees on every conflict,
implication, clique, box capacity and exact point evaluation.

Neither source runs propagation, rebuilds the large retained matrix, imports
an optimizer, fixes a new selector, or proves a case exclusion.
