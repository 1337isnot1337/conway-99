# Three grids with two rook-isomorphic interfaces

The later [integer completion proof](two_rook_iso_joint_integer.md) excludes
the final class retained by this boundary-incidence census. Together they
give [at most one rook-isomorphic partner per grid](rook_partner_bound.md).
The positive incidence controls below remain valid for their stated core
equations; they do not extend to graphs.

Suppose three disjoint induced rook grids occur in a hypothetical
`srg(99,14,1,2)`, and the matching from the first grid to each of the
other two is a rook isomorphism. After transporting labels through
those two matchings, the remaining interface must be conjugate to

\[
p=(0,5,7,8,6,1,4,2,3).
\]

This permutation fixes point zero and interchanges four pairs. It is
not a rook automorphism. Its orbit under common rook relabeling has
eighteen members. The complete calculation excludes every other
interface by exact outside-neighborhood counts and forced binary
variables. It uses no SAT or floating-point certificate.

The remaining core has an exact 27-by-72 outside-incidence matrix
satisfying all core common-neighbor equations. This is a positive
control for the reduction, not a complete graph: no edges among the
72 outside vertices have been chosen.

## Complete permutation reduction

Label the three grids `0,1,2`, with point labels `3x+y` for
`x,y in {0,1,2}`. The two root matchings are identities, and the
matching from grid one to grid two is an arbitrary permutation `p`.
It need not preserve rook adjacency.

If `p(x)` were a rook neighbor of `x`, root point `x` and point
`p(x)` in grid two would have three common neighbors: root point
`p(x)`, point `x` in grid two, and point `x` in grid one. Consequently

\[
p(x)=x\quad\text{or}\quad p(x)\not\sim x
\]

for every point `x`.

The standard-library checker visits all `9!=362880` permutations.
Exactly 2,720 satisfy this restriction. It partitions them into
59 classes using only the following explicit relabelings:

- Common conjugation by one of the 72 rook automorphisms.
- Inversion of the permutation, corresponding to exchanging grids
  one and two.

These operations preserve both identity root matchings. Every orbit
is computed explicitly, and disjointness and the total of 2,720 are
checked. No graph-isomorphism package or heuristic orbit pruning is
used.

## Necessary binary incidence equations

Every vertex outside an induced rook grid has exactly one neighbor
in it. Thus, for the 27-vertex core with adjacency matrix `B`, each
outside vertex has a signature with one vertex in each base.

Every core vertex has six core neighbors and needs eight outside
neighbors. If `X` is the matrix from the core to its 72 exterior
vertices, then

\[
XX^{\mathsf T}=G=12I+2J-B^2-B.
\]

For every one of the `9^3=729` candidate signatures `s`, with
indicator `h_s`, the checker requires

\[
G_{ij}>0\quad(i,j\in s,\ i\ne j),
\qquad (B+I)h_s\le2\mathbf1.
\]

Both conditions are necessary. The first is the remaining
common-neighbor quota of a core pair; the second counts the core
contribution to the common neighbors of a core vertex and the
outside vertex.

Let `z_s` be the number of outside vertices having signature `s`.
It is zero or one, because two vertices with the same three-point
signature would share three common neighbors. Every positive entry
of `G`, including its diagonal, therefore gives the equation

\[
\sum_{s\ni i,j}z_s=G_{ij},\qquad z_s\in\{0,1\}.
\]

For a diagonal entry, the sum runs over signatures containing its
one vertex. These equations require exactly eight exterior
neighbors at every core vertex.

## Straight-line exclusion certificates

The checker repeatedly scans the equations. If the remaining quota
is zero, every unassigned variable in that equation is zero. If the
remaining quota equals the number of unassigned variables, all are
one. A quota outside the interval from zero to that number is a
contradiction.

Every assignment records its equation, value, and affected variables.
Every final contradiction records the equation's required value and
the attainable interval. A separate replay routine reconstructs all
available variables and checks each implication independently of the
scan order. It does not branch on an unforced variable.

The complete counts are:

| First available obstruction | Classes |
| --- | ---: |
| A quota exceeds its entire signature supply | 29 |
| Initially forced signatures exceed another quota | 25 |
| Repeated zero/one forcing gives a contradiction | 4 |
| No propagation contradiction | 1 |
| Total | 59 |

Thus 58 classes, containing 2,702 permutations, are excluded. Only the
eighteen permutations in the displayed involution's class remain.

## Exact positive incidence control

The surviving representative is class 48 in the zero-based
lexicographic class order. It has 192 signatures satisfying the pair
quotas and 168 satisfying the mixed caps as well. There are 187
positive upper-triangular Gram equations. Eight variables are forced
to one by the initial equations.

A bounded integer-programming call proposed a selection of 72
different signatures. The saved witness records the full ordered
168-signature list and its 72 selected indices. The standard-library
replay then checks, with exact integer arithmetic,

\[
\sum_{s\text{ selected}}h_s h_s^{\mathsf T}=G
\]

on all 729 entries, including the zero entries and diagonal. It also
checks every forced value against the selected signatures. The
validity of this positive control does not depend on the optimizer's
status or numerical tolerances.

The calculation establishes existence of one incidence matrix, not
uniqueness. It has not completed the outside adjacency equations or
constructed a strongly regular graph.

## Reproduction

```sh
python experiments/workspace/two_rook_interfaces.py \
  --verify experiments/logs/grids-and-triangles/two-rook-interfaces.json
```

The default positive-control artifact is
`experiments/logs/grids-and-triangles/two-rook-interfaces-incidence.json`.
Both enumeration and certificate replay use only the Python standard
library and complete in approximately two seconds in the project
environment.

The prior [three-isomorphic-interface obstruction](three_red_boundary.md)
is recovered as a special case. The identity, six reflection maps,
and four translations all occur among the 58 excluded classes.
No red-triangle assumption is used in this stronger interface
classification.
