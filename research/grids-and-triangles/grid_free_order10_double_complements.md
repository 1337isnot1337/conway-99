# Six-root double-complement localizers

This preparation gives 84 matrix tests for two absent outside classes.
They cover 1,112 class pairs under verified relabelings of sixteen roots.
The identities hold for every SRG(99,14,1,2). They do not assume prism
freeness, a graph automorphism, or values from a proposed count point.

No point scan is included in the preparation. A scan can reject a count
assignment only after an exact negative integer form is checked. A scan
that finds no negative form does not establish positive semidefiniteness.

## The matrix identity

Fix a labelled six-vertex induced root H. For an allowed mask a with at
least three root neighbors, let X_a count outside vertices with that
mask. The common-neighbor bound gives X_a in {0,1}: two different
vertices cannot share three root neighbors.

Let X contain the constant one and every allowed high-mask class. For
two different masks a,b, the pointwise matrix

\[
(1-X_a)(1-X_b)XX^T
\]

is positive semidefinite. Sum over all labelled embeddings of H. Write
M for the unweighted induced six-root matrix, C_a for the sum weighted by X_a,
and C_ab for the sum weighted by X_a X_b. The necessary matrix is

\[
L_{a,b}=M-C_a-C_b+C_{ab}\succeq0.
\]

Each C_a is a sparse congruence of a seven-root matrix. Selecting its
unique a vertex gives a labelled child embedding. An old class i then
equals its selected-vertex contribution plus the two child classes
distinguished by adjacency to that vertex.

For C_ab, select the unique a and b vertices in that order. There are
at most two child roots, for their mutual edge or nonedge. For each
allowed child, an old class i is its selected-vertex contribution plus
at most four child classes. These distinguish adjacency to a and b.
All these child masks retain at least three neighbors in H, so they
belong to the complete eight-root scalar cache.

The selected classes a and b become constants in the corresponding
double child. A third vertex with either old mask would share at least
three root neighbors with the selected vertex and is forbidden. The
sum therefore has no missing multiplicity or automorphism divisor.
It is a bijection between labelled parent embeddings with selected
vertices and labelled child embeddings.

Every product uses at most ten vertices. The a and b rows of L vanish
as unrestricted coefficient identities. The preparation checks every
entry of those rows before a scan can remove them.

## Complete domain and proved reductions

The catalogue has 62 six-vertex roots, 829 high masks, and 9,118 unordered
pairs of different high masks. No root or flag is removed because its
count happens to vanish at a proposed point.

For root vertices i,j, put

\[
q_{ij}=2-A_{ij}-|N_H(i)\cap N_H(j)|.
\]

If a contains a pair with q_ij=1, then exactly one outside vertex has
both i and j as neighbors. Consequently

\[
1-X_a=\sum_{m\supseteq\{i,j\},\ m\ne a}N_m.
\]

This sum includes the size-two mask. Multiply by (1-X_b)XX^T and select
the vertex of class m. If m=b, the contribution is zero. Otherwise,
X_b becomes the sum of its two high child classes. They are incompatible,
so the contribution is a sparse congruence of a seven-root clique
complement. A contained clique follows from a maximal-clique complement
by adding the omitted positive conditional matrices. This proves the
redundancy of all 7,527 pairs having a quota-one witness in either mask.

Among the remaining 1,591 pairs, 479 are incompatible already. For those
pairs, X_a X_b=0 and L=M-C_a-C_b is a clique complement. Sum its
seven-root extension forms over every outside class, including masks
of size zero, one, and two. There are 99-6=93 outside vertices, so this
sum equals 93L. Selected extensions of class a or b contribute zero;
the others give contained-clique complements under the same sparse
congruences. These 479 tests therefore follow from the seven-root
clique family and the exact extension identities.

The remaining 1,112 pairs have compatible masks, and every root pair
inside either mask has residual two. They occur on sixteen roots.
Complete root-automorphism enumeration gives 942 automorphisms and
84 pair orbits. These are relabelings of fixed roots; they impose no
automorphism on a hypothetical graph.

## Exact preparation and scan size

The preparation checks 88,326 selected-row coefficient identities and
five direct adjacency controls. The controls include both selected
classes, either class alone, neither class, and an allowed mutual edge.

The 84 representative quotients have 48,703 lower entries and order at
most 41. They need 94 single lifts and 107 double lifts. Their sparse
contractions use at most 114,839 lower-entry terms. The largest planned
per-root cache has 119,523 Python-object matrix cells; this is a sizing
count, not a process-memory guarantee.

The domain source is
`experiments/workspace/grid_free_order10_double_complement_domains.py`.
Its SHA256 is
`1283b15c44f408e0baf2cb1f9abd1c59b4ebee8717ca099c39e52b55c56ea935`.
The complete compressed ledger has SHA256
`166c66d9b990f5806ee5fcd729eb90a6e073a98a890a348f12450908f5235eac`.

The separate scanner contracts all counts with Python integers. It
checks the two zero rows again at the selected integer count point.
Floating eigensystems propose directions only. An accepted cut must
have a strictly negative exact integer quadratic value and the same
value after full expansion into induced-count coordinates. A separate
supported-product reconstruction is still required before an accepted
discovery cut enters a count solver.

## First point scan

The separate first scan tested all 84 representatives at the existing
48-cut integer count witness, SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
It covered all 1,112 pairs by the saved root relabelings. All 168
designated selected rows were exactly zero before deletion.

The scan found no exact negative direction and no unconfirmed numerical
negative. It completed in 0.844 seconds of scan time and 3.046 seconds
including setup, with peak recorded memory of 209,304 KiB. It had no
timeout or error. This is a completed separation attempt at one count
point, not an exact PSD certificate or a graph realization.

The result is
`experiments/logs/moments-and-counts/order10-double-complement-scan01.json`.
Its preparation binds the source, domain, exact count witness, and every
source cache. The domain has a separate cold regeneration and an
independent read-only mathematical review.

## Reproduction

Use fresh output paths:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_double_complement_replay.py \
  --certificate experiments/logs/moments-and-counts/order10-double-complement-domains.json.gz \
  --output /tmp/order10-double-complement-domains-replay-new.json

.venv/bin/python experiments/workspace/grid_free_order10_double_complement_scan.py \
  --preparation experiments/logs/moments-and-counts/order10-double-complement-scan01-preparation.json \
  --output /tmp/order10-double-complement-scan-new.json --seconds 30
```

Neither command changes the existing count witness or any source cache.

The separate replay wrapper normalizes integer dictionary keys through
JSON before comparison. The frozen constructor's embedded replay did
not normalize those keys and failed at that comparison. Its preparation
and all arithmetic checks had completed. The wrapper leaves both the
original constructor and the domain certificate unchanged.
