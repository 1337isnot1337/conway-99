# Three finite A2 vector domains

The three prepared plus-representation columns on selector orbits 2, 3 and 4
each attain exactly 19 integer vectors on their frozen local inverse masks.
Their norms belong to `{0, 2, 6, 8}`. This reduces the proposed pair-table
enumeration to 1,083 ordered vector pairs across three pairs of columns, and
the proposed joint six-entry table to 6,859 ordered vector triples.

The preparation has not built those Gram tables. It read 2,187 previously
saved masks, checked their column vectors and diagonal forms, and completed
in 0.996 seconds. It did not enumerate new selector subsets, evaluate a
production count assignment, or run an optimizer.

## Literal colors and proved conflicts

The metric is

\[
H=\begin{pmatrix}2&-1\\-1&2\end{pmatrix}.
\]

All three columns use the plus representation and anchor vector `(1, 0)`
from the frozen group preparation. In each 12-selector orbit, the literal
column vectors have three values:

\[
e_1=(1,0),\qquad e_2=(0,1),\qquad -e_1-e_2=(-1,-1).
\]

Each value occurs at four selectors. Within every four-selector color,
exactly two disjoint pairs belong to a previously proved-zero selector-pair
orbit. These two pairs cover the color. The preparation retains all literal
endpoint witnesses and checks the pair IDs against the original pair map.

| Selector orbit | Proved-zero original pair orbit | Saved profiles | Saved masks |
|---|---:|---:|---:|
| 2 | 945 | 237 | 729 |
| 3 | 1397 | 237 | 729 |
| 4 | 1837 | 237 | 729 |

The six pairs, taken across the three colors, are a matching covering the
12 selectors. They are also exactly the prior proved-zero pairs within the
selector orbit. Every frozen inverse mask avoids them. There are 729
distinct saved masks, equal to `3^6`, the number of independent sets of six
disjoint edges. Inclusion and this cardinality equality prove that the saved
mask set is exactly that matching-independent domain. No new 4,096-subset
census is needed.

Let `n0, n1, n2` count the selected members of the three colors. The two
forbidden pairs in each color give

\[
0\le n_i\le2,\qquad
w=(n_0-n_2,n_1-n_2).
\]

Thus the vector domain is

\[
V=\{(a,b)\in\mathbb Z^2:
\max(0,a,b)-\min(0,a,b)\le2\}.
\]

This is equivalent to `|a| <= 2`, `|b| <= 2` and `|a-b| <= 2`, and contains
19 points. Conversely, for a point of this hexagon set
`n2 = max(0, -a, -b)`, `n0 = a+n2` and `n1 = b+n2`. All three counts lie in
`0..2`. Each color consists of two independent forbidden pairs, so these
counts are individually attainable and can be combined across colors.

The source checks the same equality in three ways: the 27 color-count
triples, the 25 integer points in the enclosing coordinate square, and the
vectors directly obtained from every saved inverse mask. It saves a literal
mask witness and the number of preimages for each of the 19 vectors. It also
saves every profile's attainable vector indices and checks that all its
preimages have the diagonal prescribed by the existing native count form.

## Proposed Gram-table scope

For three selected vectors `w0, w1, w2`, use the shared representation frame
and form

\[
B_{ij}=w_i^T H w_j.
\]

The six-entry order is

\[
(B_{00},B_{01},B_{02},B_{11},B_{12},B_{22}),
\]

where column indices 0, 1 and 2 denote selector orbits 2, 3 and 4. The
preparation copies the six exact linear count forms from the reviewed group
preparation. All their variable IDs are unchanged native count IDs below
15,038. No orbit, stabilizer or dimension divisor occurs. No auxiliary
variable IDs have been allocated.

Each of the three pair products has 361 vector combinations. The joint
product has `19^3 = 6,859` combinations. The proposed enumeration will retain
distinct pair triples `(Bii, Bij, Bjj)` and joint six-entry tuples, with exact
vector witnesses. The shared triple table must use one frame for all three
vectors. Independent rotations chosen separately for the three pairs would
lose the joint rank condition.

Every diagonal lies in `{0, 2, 6, 8}`. Positive definiteness of `H` and the
largest norm eight give the valid initial off-diagonal interval `[-8, 8]`.
The enumeration and its separate replay are proposed at 30 seconds each,
with a four-MiB raw-record limit. At 256 bytes per visited combination, the
complete pair and triple workload gives a conservative 2,033,152-byte
tuple-payload estimate. Those stages require their own frozen driver and
source gate; neither has run in this preparation.

## Meaning and limits

An actual literal selector assignment has one of these vectors on each of
the three orbits. Therefore its six linear count forms must occur in the
joint Gram table. The same Gram tuple is unchanged under a common relabeling
by the actual core group. These statements do not require a graph
automorphism.

The product of the three vector domains does not test cross-orbit selector
compatibility, the original count equations, exterior adjacency, or graph
completion. A table row can therefore be present without admitting a full
count assignment or literal incidence. The table is a necessary finite
constraint, not a sufficient realization test. Arbitrary mixtures of
unrelated assignments need not lie in the table.

## Frozen preparation

- Source: `experiments/workspace/root_prism_free_f0_two_dimensional_vector_domains.py`,
  SHA256 `0b2d15c2d331466acbc29b3585bec4c53de5a912424c9d50b179e5ed37d15660`.
- Record: `experiments/logs/root-prism-free/f0-two-dimensional-vector-domains-preparation01.json`,
  SHA256 `571b52265dc70a9e5992750d05ab0928364a68fa650716734bd3727728e135c1`.
- Reviewed group/form source: `root_prism_free_f0_two_dimensional_moments.py`,
  SHA256 `31793743ba11fb56f42bcc9f383fe8b3268dae1cd8ebf6ec0271160a1d58d2fd`.
- Frozen inverse record: `f0-character-literal-lift-preparation01.json.gz`,
  SHA256 `241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e`.

The record binds the prior source review, inverse cold replay, and original
pair-map archive. Those prior checks are dependencies; this preparation does
not claim to repeat their full construction.
