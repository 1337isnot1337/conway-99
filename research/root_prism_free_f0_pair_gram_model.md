# Full incidence preparation for the component-zero pair

The complete two-component incidence formulation has 39,168 independent
column selectors. Neither component's sixty-triple design is fixed.
Its projected sequential-counter encoding has 1,478,076 variables and
3,173,640 clauses. This package prepares exact supports and encoding
sizes; it assembles no full CNF and calls no solver.

The scope is two copies of component zero with the identity relative
fiber alignment, under the globally prism-free \(x_{521}=0\) split-shell
reduction. Other component pairs, other relative alignments, and the
connected thirty-six-vertex shell are separate cases.

## Binary columns and derived component selections

Let \(\mathcal D\) be the complete 480-triple component domain. For
every \((a,b)\in\mathcal D^2\) with complementary occupancy profiles,
introduce \(x_{ab}\in\{0,1\}\). There are 39,168 such pairs, in the
same order as the frozen full-domain Gram certificate.

For each component triple introduce derived selectors \(u_a,v_b\).
The linking equations are

\[
\sum_b x_{ab}=u_a,\qquad
\sum_a x_{ab}=v_b.
\]

Both right sides are binary. This is necessary: two exterior vertices
cannot share an entire three-point component neighborhood. Otherwise
they would have at least three common neighbors in the core.

Each link is encoded as exactly one true literal in

\[
\{x_{ab}:b\text{ compatible with }a\}\cup\{\neg u_a\},
\]

and analogously for \(v_b\). For binary variables, this is exactly the
displayed equality. It is not a choice of a component design. Every
one of the 480 selectors on each side remains free.

The primary column variables have IDs 1 through 39,168. The 960 derived
component selectors have IDs 39,169 through 40,128. All counter
auxiliaries begin after these IDs.

## Complete Gram coverage

Write \(A\) for the component Gram matrix. The local equations are

\[
\sum_a u_a aa^T=A,\qquad
\sum_b v_b bb^T=A.
\]

The cross equations are

\[
\sum_{a,b} x_{ab}ab^T=C,
\qquad
C_{ij}=2-\mathbf1_{\lfloor i/6\rfloor=\lfloor j/6\rfloor}.
\]

There are 171 upper-triangular positions on each local block and 324
cross positions. Identical local supports with the same quota are
encoded once; all positions retain a coverage entry. This leaves 150
nonempty local counter rows per component. The 114 upper-triangular
positions touching the saturated central triangle are identically
zero because every exterior column vanishes there.

The links make the local equations exactly the local blocks of the
full column Gram matrix. Thus these constraints cover all 780
upper-triangular positions, or all 1,521 ordered positions, of the
thirty-nine-vertex Gram matrix.

No explicit population counter is needed. Each component column has
three marks, and the eighteen local diagonal quotas are ten, giving

\[
3\sum_a u_a=18\cdot10,
\qquad \sum_{a,b}x_{ab}=60.
\]

Adding both redundant 480-variable population equalities would cost
100,800 further auxiliaries and 201,600 clauses with the same encoder.
They are absent from this prepared specification.

## Component motifs and all triple packing

The 78 certified \(F\) conflicts and twelve certified prism conflicts
on each component become direct clauses on \(u\), or on \(v\).
There are 180 binary motif clauses in total. Their original finite
supports and proofs that the unknown new-vertex edge is absent are
reconstructed from the frozen motif certificate. The other component's
unmodeled incidences do not invalidate those visible local obstructions.

If two selected six-neighbor columns share three core points, the two
exterior vertices would have at least three common neighbors. Thus
every core triple has capacity one. A compact complete encoding uses
one at-most-one row for each relevant core-triple support, instead of
enumerating all pairs of columns.

Every one of the \(\binom{36}{3}=7,140\) shell triples is accounted for:

| Coverage reason | Core triples |
|---|---:|
| At most one candidate column contains the triple | 1,860 |
| Triple is inside one component; its component link already gives capacity one | 960 |
| Triple contains a core pair with Gram quota one | 3,744 |
| Explicit additional mixed-triple capacity | 576 |

In the third row, the exact Gram equation for the contained pair
already limits the larger triple support to one selected column.
For a local pair, the component links transfer this bound from \(u\)
or \(v\) to \(x\). For a cross pair, it is a direct cross Gram row.

The remaining 576 mixed triples have every pair quota equal to two.
Each has one point in each global fiber. Their support sizes are
224, 240, or 256. Encoding these supports with at-most-one counters
covers every remaining pair of columns with overlap at least three.
This coverage argument does not require a 767-million-pair enumeration.

## Exact encoding sizes

Every counter uses PySAT's sequential-counter encoding, with disjoint
auxiliary variables. The preparation verifies the closed counter-size
formula against actual individual encodings. It never builds the full
formula.

| Constraint family | Counter rows | Auxiliaries | Clauses |
|---|---:|---:|---:|
| Component links | 960 | 78,336 | 235,008 |
| Deduplicated component Gram equations | 300 | 55,656 | 112,920 |
| Cross Gram equations | 324 | 1,166,292 | 2,413,116 |
| Additional mixed-triple capacities | 576 | 137,664 | 412,416 |
| Direct component motif clauses | — | 0 | 180 |

Adding the 39,168 independent and 960 derived selectors gives
1,478,076 total variables. There are 7,370,472 literal occurrences.
A DIMACS serialization with one space per token is bounded above by
72,681,628 bytes. This bound follows from the maximum variable width,
literal signs, and the exact clause and literal counts.

The text bound does not bound solver memory. A Python list containing
every clause and every separately allocated integer literal would
use much more memory than the DIMACS file. A later builder should
generate counters and write their clauses sequentially, without
keeping a second full formula in memory.

The generation controls compare 306 small counter-size cases, 510
Boolean link assignments, and all 595 pairs of four-subsets of seven
sites for the overlap-versus-shared-triple equivalence. These controls
call no SAT solver.

## Factoring the two-column Gram calculation

Let \(R_{ac}=d\,a^TA^{-1}c\), where \(d=2,288,520\). The exact
480-by-480 table has entries between \(-342,896\) and 858,218, so an
int32 representation needs only 921,600 bytes. Its full ordered-byte
hash is recorded and can be reconstructed.

For \(h=(a,b)\), \(k=(c,d')\), the inverse products use this table and
the profile correction from the
[Gram note](root_prism_free_f0_pair_gram.md). No dense full-column
inverse-product matrix is required.

For a further arithmetic compression, classify a component ordered
pair \((a,c)\) by:

- The two occupancy profiles.
- The two diagonal inverse products and their mutual inverse product.
- The intersection's occupancy profile.
- Whether the intersection contains a quota-one local pair.
- Whether the two component triples form a certified motif conflict.

There are 36,134 such types among the 230,400 ordered component pairs.
Their multiplicities and exact keys are saved. Combining complementary
profile types requires 33,578,176 ordered type combinations, compared
with 1,534,132,224 ordered full-column pairs including the diagonal.

These keys determine the two-column Gram determinant, the total column
overlap, every shared quota-one pair, and the component motif flags.
For cross quota-one pairs, use the dot product of the two intersection
profiles. Counting a combined type can therefore use the product of
its component multiplicities; no completed-graph symmetry is assumed.

This package computes the component types and the number of compatible
type combinations only. It does not classify those 33,578,176
combinations or export any two-column Gram exclusions.

## Artifacts and scope of a later result

Source:
[root_prism_free_f0_pair_gram_model.py](../experiments/workspace/root_prism_free_f0_pair_gram_model.py).
Preparation:
[f0-pair-gram-model-preparation.json.gz](../experiments/logs/root-prism-free/f0-pair-gram-model-preparation.json.gz).
The certificate binds the complete column order, every counter support,
all coverage records, the direct motif clauses, and the projected sizes.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_pair_gram_model.py \
  --certificate experiments/logs/root-prism-free/f0-pair-gram-model-preparation.json.gz \
  --replay
```

No full CNF, optimizer, or SAT query is part of this preparation. A later
SAT point would supply a sixty-column incidence candidate; the exterior
adjacency and further forbidden motifs would still require checking.
A checked UNSAT result would exclude this complete component pair and
alignment, rather than only a saved pair of designs. It would still
leave the other component pairs and the connected shell case open.
