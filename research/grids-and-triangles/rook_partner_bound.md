# A rook grid has at most one isomorphic partner

In a hypothetical strongly regular graph with parameters `(99,14,1,2)`,
an induced three-by-three rook grid has at most one disjoint induced rook
grid whose matching to it is a rook-graph isomorphism. No red-triangle
assumption is used.

Equivalently, form a graph on the induced rook grids, joining two disjoint
grids when their matching preserves rook adjacency. That graph is a
matching together with isolated vertices.

## Why the three-grid calculation covers every pair of partners

Every vertex outside a rook grid has exactly one neighbor in it. Thus two
disjoint grids have a perfect matching between them. Call the second grid
a partner when this matching is a rook isomorphism.

Distinct partners of a fixed grid are disjoint. If partners `S,T` shared a
point `v`, let `p` be its unique neighbor in the fixed grid `R`. For each
rook neighbor `q` of `p`, the images of `q` in `S` and `T` are both common
neighbors of `q,v`, as is `p`. Since `q,v` are nonadjacent, their two-neighbor
quota forces the images to coincide. Two of these four common images are
nonadjacent. The grid-intersection lemma then forces `S=T`. The
[full proof](rook_interface_star.md#distinct-partners-are-disjoint) gives
the details.

Two distinct partners would consequently produce three disjoint grids
with two rook-isomorphic interfaces incident to the first. Gauge those two
matchings to identities. The third matching is an arbitrary permutation
of nine points subject to a visible common-neighbor restriction.

## Complete interface classification and the last integer exclusion

The [exact three-grid census](two_rook_interfaces.md) checks all `9!`
permutations. Exactly 2,720 avoid the immediate quota obstruction. Explicit
rook conjugation and inversion divide them into 59 classes. Exact binary
incidence propagation excludes 58 classes, containing 2,702 permutations.

The last class consists of eighteen conjugates of

\[
p=(0,5,7,8,6,1,4,2,3).
\]

Its 27-point core admits 168 possible outside signatures. A signature
cannot repeat, because two outside vertices with the same signature would
share three common neighbors. The remaining necessary problem therefore
has 168 binary selection variables and 9,846 possible outside edges.

The [integer completion proof](two_rook_iso_joint_integer.md) excludes
this whole class. It imposes all core Gram equations, endpoint activation,
conditional mixed codegree equations, and necessary neighbor-packing
inequalities. There is no fixed incidence assignment, orbit equality,
graph automorphism assumption, or lazy cut.

The exact CNF is unsatisfiable. Its retained proof has 14,860 input clauses
and 1,088 lemmas, checked by `drat-trim`. The replay regenerates the full
1,151,148-clause CNF, checks its hash and frozen source hashes, checks that
every retained clause belongs to that formula, and verifies the proof.

A separate implementation rebuilds the core, all signatures and edges,
and every logical constraint family. It checks all 62,692 packing clauses
and 37,888 complete Boolean assignments for the conditional-count helper.
It reproduces the same full CNF hash. This checks the translation from the
mathematical problem to the formula separately from the DRAT proof.

All 59 interface classes are therefore excluded. Two distinct partners of
one grid cannot exist, proving the stated bound.

## What the result leaves open

The [real joint relaxation](two_rook_iso_joint_incidence.md), including the
packing inequalities, has exact rational feasible points. Integrality is
essential to the integer exclusion. The saved 72-column incidence controls
satisfy only the core equations and do not construct completed graphs.

The canonical pair of isomorphically matched grids still has a forced
81-column outside-incidence matrix. This theorem excludes a second partner;
it does not by itself exclude that pair or force any grid to exist.
The unrestricted Conway existence problem remains unresolved.

## Replay

```sh
make verify-rook-partner-bound DRAT_TRIM=/absolute/path/to/drat-trim
```

The earlier star, four-cycle, and five-cycle obstructions remain independent
weaker checks. Their exact integer replays and the fractional controls are
collected in `make verify-general-rook-interfaces`.
