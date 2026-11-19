# Independent backtracking audit of the six-base interface obstruction

This audit uses no SAT encoding, triangle-count equation, or eigenvalue
condition. It exhausts the necessary local matching-interface model for
six rook bases. There are no valid six-base assignments. The corresponding
five-base local model has exactly 564 labeled assignments after fixing
the root gauge, and the four-base model has 136.

Consequently a hypothetical `(99,14,1,2)` graph cannot contain six
disjoint rook grids whose pairwise matching interfaces are rook
isomorphisms. The previously proved interface properties of all-red
grids make this an independent verification of the upper bound five
for their number. The positive controls are partial interface graphs,
not strongly regular graphs.

## The root gauge and the eleven maps

Choose one base `R0` and label its vertices by `(x,y)∈{0,1,2}²`. Give
each other base the labels transported through its matching from
`R0`. Those matchings become identity maps. Since the interfaces are
rook isomorphisms, each base still has the usual rook adjacency in
these labels.

Let a remaining matching send `x` in `Ri` to `z` in `Rj`. If `x,z`
are rook neighbors, the pair consisting of `x` in `R0` and `z` in
`Rj` has three visible common neighbors: `z` in `R0`, `x` in `Rj`,
and `x` in `Ri`. Hence every remaining matching must be a rook
automorphism moving no point to a rook neighbor.

The C++ program tests all `9!` permutations directly for preservation
of the thirty-six unordered adjacency/nonadjacency relations. It
finds seventy-two automorphisms and precisely eleven permitted maps.
There is also an explicit independent description of these eleven:

- the identity;
- the four maps `(x,y)↦(x+a,y+b)`, with `a,b∈{1,2}` modulo three;
- the six maps `(x,y)↦(σ(y),σ⁻¹(x))`, with `σ∈S3`.

The Python replay derives this list directly and checks that it
equals the C++ list, in the saved order.

## Direct adjacency pruning

For `b` bases let `B` be their `9b`-vertex induced adjacency matrix.
It includes the internal rook edges and one perfect matching between
each pair of bases. Every off-diagonal pair must satisfy

\[
(B^2)_{uv}+B_{uv}\le2.
\]

This is necessary because any common neighbors outside these bases
can only increase the count. No common-neighbor equality is assumed
for pairs in different bases.

The program stores each adjacency row as a sixty-four-bit word. It
adds one entire matching at a time and evaluates the displayed bound
by exact population counts. Only the two incident bases have changed
adjacency rows, so only pairs with an endpoint in one of those bases
need rechecking. Pairs in the same base cannot acquire a common
neighbor from another base, since each interface is a matching.

If a partial choice violates the bound, later choices cannot repair
it: adjacency entries and common-neighbor counts only increase. Thus
the pruning cannot remove a valid completion. Every permitted map is
tried at every surviving branch. No isomorphism pruning or further
symmetry assumption is used after the root gauge.

Closed-triangle holonomies are checked as assertions after a visible
bound check passes. They are not an additional pruning rule. Every
completed positive witness is also checked against every pair of
vertices, including pairs within a base, and against its degree
`b+3`.

## Complete five-base census

The six variable interfaces are assigned in the order

\[
(1,2),(1,3),(2,3),(1,4),(2,4),(3,4).
\]

The numbers of surviving partial assignments at successive depths are

| Assigned interfaces | Surviving partial assignments |
| ---: | ---: |
| 0 | 1 |
| 1 | 11 |
| 2 | 84 |
| 3 | 136 |
| 4 | 944 |
| 5 | 1,020 |
| 6 | 564 |

All 564 complete assignments are saved in
`experiments/logs/grids-and-triangles/seven-red-interfaces-b5-backtrack.json`.
The file includes the eleven maps and the edge order needed to
reconstruct each adjacency matrix. Its complete flag is true.

The independent Python replay constructs the full forty-five-vertex
matrix of each saved assignment and checks `B²+B≤2` off the diagonal
using integer matrix multiplication. Every one passes. It also tests
all `11³=1,331` full four-base assignments independently and finds
exactly 136, agreeing with depth three of the C++ search. Those
assignments are saved in `seven-red-interfaces-b4-backtrack.json`.

These checks impose no Gram positivity condition. They supply complete
input catalogs for a separate spectral investigation.

## Exhaustion of six-base extensions

Every valid six-base assignment restricts to one of the 564 five-base
assignments. For each seed the program tests the four remaining
interfaces `(1,5),(2,5),(3,5),(4,5)`, again trying all eleven maps and
pruning only visible common-neighbor violations.

The surviving extension counts are:

| Total assigned interfaces | Surviving partial assignments |
| ---: | ---: |
| 6 | 564 |
| 7 | 2,472 |
| 8 | 1,392 |
| 9 | 264 |
| 10 | 0 |

There are 51,612 extension attempts in total. All 2,904 choices at
the final interface fail. All 564 seeds were completely processed;
the final status is `exhaustive_no_local_assignment`, with a true
complete flag and no witness. The shared sixty-second deadline was
not reached. The recorded complete run took approximately 0.13 seconds.

This is a direct finite backtracking verification, independent of
the SAT formula and its DRAT proof.

## Reproduction

From the repository root:

```bash
g++ -std=c++20 -O3 experiments/workspace/seven_red_interfaces_backtrack.cpp \
  -o /tmp/seven-red-interfaces-backtrack
/tmp/seven-red-interfaces-backtrack 60 \
  /tmp/seven-red-interfaces-b5.json /tmp/seven-red-interfaces-b6.json
.venv/bin/python experiments/workspace/seven_red_interfaces_backtrack_replay.py
```

The archived outputs are `seven-red-interfaces-b5-backtrack.json`,
`seven-red-interfaces-b6-backtrack.json`, and
`seven-red-interfaces-backtrack.log` under
`experiments/logs/grids-and-triangles/`. The independent matrix-replay
summary is `seven-red-interfaces-backtrack-replay.json`, with the
corresponding `.log` file. No SAT-model helper is imported by either
program.
