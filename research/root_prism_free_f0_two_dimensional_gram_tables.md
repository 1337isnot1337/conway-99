# Exact Gram tables for three plus columns

The complete table calculation on selector orbits 2, 3 and 4 gives 39
distinct tuples for each pair of columns and 610 distinct tuples for the
joint six-entry Gram matrix. Enumeration took 0.083 seconds. A separate
exact replay checked all 7,942 vector combinations using norm polarization
in 0.071 seconds.

No production count assignment or optimizer was used. These are necessary
finite constraints for one literal selector assignment, or its common
relabeling orbit. They are not conditions on arbitrary convex mixtures.

## Complete finite domains

The preceding vector-domain preparation proves that each column has exactly
the same 19 attainable integer vectors:

\[
V=\{(a,b)\in\mathbb Z^2:
\max(0,a,b)-\min(0,a,b)\le2\}.
\]

It uses all 729 saved inverse masks on each selector orbit. Each of the three
vector colors has four selectors split into two proved incompatible pairs,
so each color count lies in `0..2`. The record checks all 2,187 saved masks
and their existing diagonal count forms. It preserves a literal mask witness
for every vector and the vector domain of every saved profile. See
`root_prism_free_f0_two_dimensional_vector_domains.md` for the proof and
input bindings.

For vectors in the common representation frame, use

\[
H=\begin{pmatrix}2&-1\\-1&2\end{pmatrix},\qquad
B_{ij}=w_i^THw_j.
\]

Column indices 0, 1 and 2 refer to selector orbits 2, 3 and 4. The output
orders the six observables as

\[
(B_{00},B_{01},B_{02},B_{11},B_{12},B_{22}).
\]

These observables are the six previously reviewed integer linear forms in
unchanged native count IDs below 15,038. The preparation copies those forms
without any scaling or orbit divisor.

## Enumeration and replay

| Stage | Ordered vector combinations | Distinct Gram tuples |
|---|---:|---:|
| Columns 0 and 1 | 361 | 39 |
| Columns 0 and 2 | 361 | 39 |
| Columns 1 and 2 | 361 | 39 |
| Columns 0, 1 and 2 | 6,859 | 610 |

Each pair tuple has order `(Bii, Bij, Bjj)`. Each joint tuple has the six-entry
order above. The output retains a first vector-index witness and the number
of ordered vector combinations producing each tuple. These multiplicities
count vector combinations, not literal selector assignments, embeddings,
or probability masses.

The producer contracts the displayed integer bilinear form. The cold replay
instead uses

\[
u^THv=\frac{Q(u+v)-Q(u)-Q(v)}2,
\qquad Q(a,b)=2(a^2-ab+b^2),
\]

with Python integers. It reconstructs every visited tuple, first witness and
multiplicity. It checks the full coverage flag, all three joint-to-pair
projections, and every joint three-by-three determinant. This is a separate
arithmetic replay of the saved finite products; it does not repeat the prior
inverse-mask construction.

All three pair tables are exact projections of the joint table. A model that
imposes the joint table therefore does not need the pair tables as additional
constraints.

## Exact observable domains and two strict restrictions

Every diagonal belongs to

\[
\{0,2,6,8\}.
\]

Each off-diagonal has exact projection

\[
\{-8,-6,-4,-3,-2,-1,0,1,2,3,4,6,8\}.
\]

The pair tuple `(6, 0, 6)` is absent. Its determinant is 36, while the area
identity for two integer vectors requires

\[
B_{ii}B_{jj}-B_{ij}^2=3\det[w_i,w_j]^2.
\]

Here `36/3 = 12` is not an integer square. This is the obstruction detected
in the earlier fixed norm-six profile experiment.

The pair tuple `(2, 1, 2)` is present. Nevertheless, the joint tuple
`(2, 1, 1, 2, 1, 2)` is absent: its symmetric matrix has diagonal two and
off-diagonal one, with determinant four. All three pair projections are
allowed, but the joint rank exceeds two. Thus the joint table enforces a
condition that separate membership in these three pair tables does not.
This is a statement about the declared finite tables, not a proof of
nonredundancy against every constraint in the full count model.

## Integration schema and limits

The exact joint relation is `result.stages[3].tuples`, containing 610 rows.
The observable definitions are
`preparation.six_native_entry_forms[*].native_count_terms` in
`preparation.six_entry_order`. The exact new domains are
`result.joint_entry_values`. A future model can introduce six integer
observables, link each to its frozen native linear form, and impose one
allowed six-entry table. This package allocates no variable IDs and changes
no existing model.

The cold record has `complete_full_table = true`. It binds the result,
preparation, driver and vector-domain record. A partial table must never be
used as an exhaustive allowed table; no partial stage occurred here.

The three local vector choices are independent in this enumeration.
Cross-orbit selector conflicts, complete pair histograms and the other
native count constraints remain obligations of the surrounding model. A
table row alone is not an incidence witness. Exterior edge variables and
graph completion are outside this calculation.

## Frozen files

- Driver: `experiments/workspace/root_prism_free_f0_two_dimensional_gram_tables.py`,
  SHA256 `7fd5cf303b7a20b31305329aece575f114a76dcb6482478aed63ac491b81b33c`.
- Preparation: `f0-two-dimensional-gram-tables-preparation01.json`,
  SHA256 `71a1104cfd377f575a03afbbe4921b14a3e0504e75f1e6c891efe477ae1b5d83`.
- Result: `f0-two-dimensional-gram-tables-enumeration01.json`,
  SHA256 `dd69bcdae9fd4df56a49195b8965ef89e7ae5ddf321c21e6b4547f650d7dce7a`.
- Cold replay: `f0-two-dimensional-gram-tables-enumeration01-cold.json`,
  SHA256 `125c41ec7add01ccbcbeff1aad4788a9973c4f0e409fedacaef91846c40d7f41`.
- Root source gate: `f0-two-dimensional-gram-tables-root-source-review.json`,
  SHA256 `9be3f46884f64626655c9d945617f90279722fb55ad25e14348732997f8b647a`.

All JSON files above are under `experiments/logs/root-prism-free/`. The
original preparation package remains frozen; the terminal package adds
these outcomes, logs, this note and the source gate.
