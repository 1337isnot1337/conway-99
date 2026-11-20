# At most five all-red grids from their matching interfaces

The later [three-base boundary proof](three_red_boundary.md) gives a
stronger obstruction and at most one all-red grid. This note retains the
independent six-base SAT and direct-backtracking certificates.

A hypothetical `srg(99,14,1,2)` contains at most five all-red grids.
The finite obstruction uses only the matching interfaces of six grids
and common-neighbor upper bounds on their 54 vertices. It does not use a
remainder triangle count, a spectral restriction on that remainder, or
the earlier seven-base case split.

The stronger local statement is that six disjoint induced rook grids
cannot have pairwise perfect matchings that are rook isomorphisms while
satisfying the SRG common-neighbor upper bounds. All-red grids would
have exactly those properties by
[`red_grid_limit.md`](red_grid_limit.md).

The UNSAT certificate is checked with `drat-trim`. A separate direct
encoding reproduces the six-base exclusion without the main builder's
adjacency, conjunction, or cardinality auxiliary variables.

## Gauge and complete label set

Choose one of the six bases as a root and label its vertices by a
three-by-three array. Label each other base using its matching to the
root. Those matchings are rook isomorphisms, so this makes every root
matching the identity and every internal grid the same rook graph.
It does not identify graph vertices or assume any automorphism of the
full 99-vertex graph.

Each remaining matching is an automorphism of the nine-vertex rook
graph. There are exactly 72: independently permute rows and columns,
with the additional option of exchanging the two directions. Completeness
follows because an automorphism permutes the six maximal triangles and
preserves their two parallel classes, possibly exchanging them.

For any three bases, compose the matching maps around the triangle to
obtain a rook automorphism `P`. This map cannot send a point to a rook
neighbor. Normalize the direct matching between the first and third
bases to identity. A cross-base pair at adjacent rook positions already
has two common neighbors, one in each of those bases. A matching path
through the second base would be a third common neighbor.

In particular, every nonroot matching belongs to the eleven rook
automorphisms with no move to a rook neighbor. This condition is applied
to every three-base product as well.

Here is a second description of the eleven maps. In ternary coordinates
`(x,y)`, change to `u=x+y, v=x-y`. The original rook adjacency becomes
inequality in both new coordinates. The allowed maps are exactly

\[
(S_3\times\{1\})\ \cup\ (\{1\}\times S_3),
\]

with the identity counted only once. To see completeness, a product
permutation that changes both coordinates has some point moved in both,
which is forbidden. A map exchanging the coordinate directions also has
such a point: at most six of the nine points can keep either coordinate.
Thus only permutations of one coordinate remain. No linearity assumption
is imposed on the matching maps.

The implementation checks the 72 rook automorphisms directly and obtains
the same eleven-element list. Of the `11^3=1331` assignments to the
three edges of a triangle of nonroot bases, 581 have an allowed product.

## The necessary finite model

After fixing the root gauge, six bases have ten free matching labels.
Each label has eleven choices. For every triangle of nonroot bases, the
product is constrained to the same eleven-element set.

Given the labels, let `A_R` be the complete adjacency matrix on the
union of the bases. Its diagonal blocks are rook adjacency matrices,
and its off-diagonal blocks are the selected permutation matrices.
For every pair of distinct vertices impose

\[
(A_R^2)_{xy}+(A_R)_{xy}\le2.
\]

For an adjacent pair this permits at most one common neighbor inside
the base union. For a nonadjacent pair it permits at most two. Common
neighbors outside the union are not chosen. These are necessary upper
bounds, not assertions that every required common neighbor is already
inside the union.

Pairs within one base satisfy their bounds automatically: their internal
rook graph supplies the exact quota, and a matching to another base
cannot give them a common neighbor. The CNF therefore needs to encode
only pairs in distinct bases.

The main builder uses one Boolean variable per label choice and exact
one-choice clauses. Matching adjacency bits are equivalent to the
appropriate disjunctions of label choices. Conjunction variables encode
potential common neighbors, and exact cardinality encodings impose the
upper bounds. Triangle-product tables retain all 581 allowed assignments.

The certified instance sets `y=None` and `require_both=False`. Thus it
contains no prescribed red-triangle count and no requirement that both
coordinate factors occur. Optional exploration constraints in the shared
builder are disabled. Some unused indicator definitions remain in the
full CNF; they impose no further restriction on matching labels.

## Checked exclusion and positive controls

The six-base CNF has 25,505 variables and 80,120 clauses. Glucose returned
UNSAT, and `drat-trim` verified the proof. The trimmed certificate retains
14,796 input clauses and 5,647 proof lemmas. The checker reports zero RAT
lemmas: its retained proof uses RUP steps.

The seven-base model with the same weak assumptions was checked
separately and is also UNSAT. It is redundant for the bound of five.

Positive controls exercise the same necessary model:

- All eleven three-base label choices are SAT and pass direct adjacency
  checks.
- Four- and five-base models are SAT. Their explicit matching labels
  reconstruct partial graphs satisfying every represented pair bound.
- An independent exhaustive comparison checks all 1,331 four-base label
  assignments and finds exact agreement between direct adjacency and
  the main CNF; 136 assignments are valid.

These are positive controls for the partial-interface model. They are not
constructions of the full strongly regular graph. In particular, the
saved five-base witness fails an additional global Gram positivity test.

The independent encoding works directly with matching labels and
necessary clauses from violated common-neighbor counts. It uses no
adjacency, conjunction, or cardinality auxiliary variables. It also
returns SAT for five bases and UNSAT for six and seven. See
`seven_red_interfaces_independent_audit.py` and its separate audit note
for that verification.

## Certificate replay

The frozen builder is
`experiments/workspace/seven_red_interfaces.py`. Its SHA-256 is

```text
a809f3ddcbcc8e936485d005219b62ed3eac65f754c6fafb9a8156a3d30ee16e
```

The manifest
`experiments/workspace/seven-red-interfaces-b6-certificate.json`
records the model parameters and digests. Its neighboring files contain
the retained CNF and trimmed proof.

`seven_red_interfaces_certificate.py` regenerates the full CNF and
checks its digest. It checks the retained input clauses against the
regenerated formula, verifies the saved file digests, and invokes
`drat-trim` on the retained formula and proof:

```bash
python experiments/workspace/seven_red_interfaces_certificate.py \
  experiments/workspace/seven-red-interfaces-b6-certificate.json \
  --drat-trim /absolute/path/to/drat-trim
```

The finite certificate establishes the inconsistency of the encoded
necessary conditions. The graph-to-CNF argument is the gauge, complete
eleven-map classification, and common-neighbor bounds given above. This
is a computational proof of the stated grid restriction, not a proof in
a proof assistant or a resolution of the 99-graph existence problem.
