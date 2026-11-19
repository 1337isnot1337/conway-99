# Completion constraints for rook-isomorphic interfaces

The canonical pair of disjoint rook grids with an isomorphic matching
has a forced outside-incidence matrix. Its edge completion remains
unresolved. A related 27-vertex core has a saved 72-column incidence
assignment whose edge completion is excluded by an exact integer
Farkas certificate. These are separate statements.

## The forced incidence of two grids

Label the two grids by the same nine rook points and make their
matching the identity. Their adjacency matrix is

\[
B=\begin{pmatrix}R&I\\I&R\end{pmatrix},
\]

where `R` is the nine-point rook adjacency matrix. The core degree is
five. Every outside vertex has one neighbor in each grid. For a pair
of labels `(p,q)`, its multiplicity is therefore the corresponding
cross-block entry of

\[
XX^{\mathsf T}=12I+2J-B^2-B.
\]

This gives nine diagonal signatures `(p,p)`, each once, and 36 ordered
nonadjacent, unequal rook pairs `(p,q)`, each twice. The other
signatures have multiplicity zero. The resulting 81 columns satisfy
the entire Gram equation by direct integer multiplication.

Write `Z` for the nine diagonal vertices and `Y` for the other 72.
Each outside vertex requires twelve neighbors outside the two grids.
The mixed block equation is

\[
XC=2J-(B+I)X,
\]

where `C` is the unknown 81-point adjacency matrix. The visible bounds
leave 3,060 possible outside edges. A 20-second floating-point LP
attempt on these mixed equations reached its time limit. That run
provides no exclusion or feasibility certificate.

## A necessary inequality for the nine diagonal vertices

No assumption that `Z` is a rook grid is made. For `z_t` in `Z`, let
`d_N(t)` count its neighbors `z_p` whose labels are rook-adjacent to
`t`, and let `d_F(t)` count those whose labels are nonadjacent to `t`.
Then

\[
d_N(t)\le d_F(t).
\]

To see this, record the neighbors of `z_t` in `Y` as a matrix indexed
by the two core labels `(p,q)`. Each allowed cell contains at most one
neighbor: its two possible vertices already share two core neighbors
and cannot also share `z_t`. The matrix has zero diagonal and is
supported on ordered nonadjacent rook pairs. Its row and column sums,
for `p != t`, are both

\[
r_p=2-R_{pt}-C_{z_pz_t};
\]

the row and column indexed by `t` have sum zero.

The four labels nonadjacent to `t` form a two-by-two rook rectangle.
There are only four allowed ordered cells within this set. The total
row demand on these four labels is `8-d_F(t)`. At most four can be
supplied internally. The remaining cells use columns at the four
rook neighbors of `t`, whose total demand is `4-d_N(t)`. Therefore

\[
8-d_F(t)\le4+(4-d_N(t)),
\]

which proves the inequality.

## One 27-core incidence assignment is excluded

The separate two-arm interface census has a surviving 27-point core
with root interfaces equal to the identity and third matching

\[
p=(0,5,7,8,6,1,4,2,3).
\]

Its 168 admissible signatures permit a saved integer incidence
assignment selecting 72 distinct columns. That assignment satisfies
`XX^T=12I+2J-B^2-B` exactly. The certificate here excludes this
assignment only; it does not exclude all assignments of the core.

For its fixed incidence matrix, write

\[
D=2J-(B+I)X.
\]

An outside edge `a--b` is possible only if its endpoint signatures
share at most one core point and each endpoint's signature fits in
the other endpoint's column of `D`. This leaves 1,872 candidate
edges. Introduce one nonnegative variable for each, require the
mixed equations `XC=D` and degree eleven, and impose an upper bound
of one on each edge variable.

There are 2,016 mixed and degree equations. Each edge upper bound is
written as `edge + nonnegative slack = 1`. For the resulting matrix
`M` and right side `b`, the saved integer vector `q` satisfies

\[
q^{\mathsf T}M\ge0,
\qquad q^{\mathsf T}b=-2.
\]

Thus no nonnegative real solution exists. The vector has 71 nonzero
entries; four belong to edge upper-bound equations. A numerical
solver proposed it, but the replay evaluates every coefficient and
the contradiction with Python integers.

## Exact replay

The fixed certificate embeds the interface map, signature domain,
selected columns, candidate edge list, and integer vector. The
standalone checker rebuilds the core and permitted edge list without
importing the LP implementation. It verifies the full incidence Gram
identity before checking the ray.

```bash
python experiments/workspace/two_rook_iso_completion.py \
  --two-grid-audit \
  --fixed-certificate experiments/logs/grids-and-triangles/two-rook-iso-completion-case48-ray.json
```

The checker uses only Python's standard library. Its saved replay is
`experiments/logs/grids-and-triangles/two-rook-iso-completion-replay.json`.
No conclusion about the full 168-signature incidence problem follows
from this fixed-assignment certificate.
