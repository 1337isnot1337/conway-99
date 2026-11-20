# The eighteen-edge tip boundary reduces to two core types

## Result and scope

For two disjoint rook grids with an isomorphic matching, consider the
nine matching-edge tips. If their induced graph has 18 edges, it is a
rook graph. The complete labelled-rook census gives this reduction:

\[
5040\text{ labelled tip graphs}
\longrightarrow89\text{ Hall survivors}
\longrightarrow6\text{ root-automorphism orbits}
\longrightarrow19\text{ labelled cases in two orbits}.
\]

The last reduction uses exact core-Gram kernels and binary incidence
margin propagation. It does **not** exclude the eighteen-edge boundary.
The complement-rook case survives, as does one orbit with 18 labelled
members. Survival of propagation alone does not assert incidence
feasibility or a full graph completion.

The later [joint integer proof](two_rook_tip_boundary_joint_integer.md)
excludes the eighteen-member surviving orbit. Only the complementary
rook graph remains at this boundary. The census below retains its
original propagation result and supplies the proof's complete domain.

## Why eighteen edges force a rook graph

Let `Z` be any graph on nine vertices satisfying
`(Z^2)_ij+Z_ij <= 2` for distinct vertices. If its degrees are `d_i`,
then

\[
\frac12\sum_i d_i^2
=\sum_{i<j}\big((Z^2)_{ij}+Z_{ij}\big)\le72.
\]

At 18 edges, `sum(d_i)=36`. Cauchy-Schwarz forces
`sum(d_i^2)>=144`, so equality holds throughout. Every degree is four,
and every pair cap is saturated. Thus the graph is an SRG(9,4,1,2).

For completeness, its rook structure follows locally. Choose a vertex
0. Its four neighbors induce two disjoint edges. Each of the four
nonneighbors meets one endpoint of each edge: two neighbors on the
same edge would give that edge a second common neighbor. Each choice
of one endpoint from each edge occurs exactly once, because the two
chosen endpoints already have 0 as one common neighbor and require
exactly one more. These four vertices form a two-by-two array. Pairs
sharing one chosen endpoint must be adjacent, to supply the unique
common neighbor of the corresponding core edge. Their degrees leave
no further edges. This is the nine-point rook graph.

The same inequality also gives the general upper bound of 18 tip edges.

## Complete labelled coverage and Hall filtering

The main catalogue construction takes the 280 partitions of nine points
into three unordered triples. Each has 36 orthogonal partitions. The
10,080 resulting row/column descriptions give exactly 5,040 distinct
rook graphs, each twice, because the two parallel classes can be
interchanged.

Replay checks this catalogue against an independent construction at
vertex 0: choose its four neighbors in 70 ways, split them into two
unordered pairs in three ways, and assign the other four vertices to
the two-by-two array in 24 ways. This gives exactly
`70*3*24=5040` distinct graphs and the identical catalogue.

Every graph is checked against the exact 103-mask Hall table at every
tip. The 89 survivors form six orbits under the 72 automorphisms of the
fixed root rook graph `R`. The certificate includes every labelled code
and an explicit coordinate permutation from each orbit representative
to every member.

All rook tip graphs automatically satisfy the necessary PSD condition.
Indeed, if `E_R,-2` and `E_Z,-2` denote the negative rook eigenspace
projectors, then

\[
3I-R+J-2Z=3E_{R,-2}+6E_{Z,-2}\succeq0.
\]

The exact control checks, for every labelled rook graph, that
`K_Z=3I-3Z+J` satisfies `K_Z^2=9K_Z`. Symmetry implies its eigenvalues
are 0 or 9. No numerical eigenvalue filter is used.

## Exact incidence domains

For each tip graph, the 27-point core adjacency is

\[
B=\begin{pmatrix}R&I&I\\I&R&I\\I&I&Z\end{pmatrix},
\qquad G=12I+2J-B^2-B.
\]

Only the first two rook graphs are required to have isomorphic matching
coordinates. The identity matching into `Z` is **not** assumed to be
a rook isomorphism. No one-partner theorem is used in this census.

Every vertex outside an induced rook graph has exactly one neighbor in
it. There cannot be two: adjacent rook points already have their unique
common neighbor inside the rook graph, and nonadjacent rook points
already have both common neighbors there. Counting the 90 edges from
the rook graph to its 90 exterior vertices then gives exactly one each.

Consequently, the remaining 72 vertices have signatures `(p,q,t)`, one
point in each grid. A signature cannot repeat, since repeated vertices
would have three common core neighbors. Its selector is therefore
binary.

The initial domain contains every triple whose selected core pairs have
positive `G` entry. All mixed nonnegativity conditions are checked too.
Equivalently, `p,q` are distinct rook-nonadjacent points, `t` differs from
both, and the two margins `2-R_pt-Z_pt` and `2-R_qt-Z_qt` are positive.

The binary equations are the full positive cross-grid pair margins.
The first/second-grid margins are two. The other two sets of margins
are `2-R-Z` off the diagonal. The diagonal core degrees follow by
summing these pair margins. Every selected signature participates in
three margin equations, and exactly 72 signatures must be selected.

If `v` lies in both rook eigenvalue-one spaces, the lifted vector
`(v,v,v)` is in `ker(G)`. Every incidence column must be orthogonal to
it. The verifier computes the entire exact kernel and checks that
these vectors, together with the two constant grid-difference vectors,
span it. Thus it deletes precisely those initially allowed triples
failing core-Gram range membership.

For each margin, subtract already selected variables. A zero residual
forces all remaining variables to zero; a residual equal to the number
of remaining variables forces them all to one. A negative residual or
one exceeding the available variables is a contradiction. Every forced
step and final contradiction is saved. A separate replay checks each
step directly without using the propagation queue.

## Results by orbit

Graph codes use the 36 unordered pairs from
`combinations(range(9),2)` as bits, starting at bit zero.

| Representative | Orbit size | Edges shared with R | Pair-allowed triples | Gram-allowed triples | Result |
| ---: | ---: | ---: | ---: | ---: | --- |
| 3671418578 | 36 | 7 | 144 | 124 | Margin contradiction |
| 3677706962 | 18 | 4 | 192 | 192 | Margin contradiction |
| 3679836361 | 18 | 4 | 188 | 188 | Survives propagation |
| 3943553752 | 1 | 0 | 252 | 252 | Survives propagation |
| 6200933548 | 4 | 9 | 108 | 108 | Margin contradiction |
| 10625800604 | 12 | 6 | 162 | 162 | Margin contradiction |

The complement-rook representative is `3943553752`. Its 252 signature
variables remain unassigned by this propagation. The other survivor
has 16 forced selected signatures, 32 forced rejected signatures, and
140 unresolved signatures. Its tip edges are

```text
01 04 07 08 15 16 18 23 24 26 28 35 37 38 46 47 56 57
```

The certificate lists all 19 surviving labelled codes and their
transport permutations. It also retains the exact domains and forced
assignments, so a subsequent model can use all possible incidence
choices without fixing an arbitrary 72-column witness.

## Replay

Source: `experiments/workspace/two_rook_tip_rook_boundary.py`.
Certificate and logs:
`experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-*`.

```sh
python experiments/workspace/two_rook_tip_rook_boundary.py \
  --hall experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json \
  --certificate experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-certificate.json
```

Add `--write` to regenerate. Replay uses the standard library, reconstructs
both complete catalogues, checks all coordinate transports and Gram
kernels, and replays every propagation deduction. No completion solver
or large search is used.
