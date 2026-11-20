# Coupling the two eighteen-vertex components

This continues the conditional
[split-component reduction](root_prism_free_f0_components.md).
It assumes a globally prism-free graph, \(x_{521}=0\), and a triangle
shell split into two eighteen-vertex components. It does not cover the
connected thirty-six-vertex shell.

The cross-component Gram equations are exact. A rational control
satisfies them with the first component incidence fixed and the second
incidence allowed to vary. A separate, smaller binary model fixes both
incidences to the same saved sixty-triple design. That fixed pair is
excluded by a checked UNSAT proof. These are different models; the
component and the split-shell case remain unresolved.

## The cross Gram matrix

Let the two components be \(V,W\), with six vertices of each in every
global fiber. They are anticomplete. A vertex of \(V_i\) and one of
\(W_j\) have one known common neighbor in the central triangle if
\(i=j\), and none otherwise. Their required exterior common-neighbor
counts are therefore

\[
C_{uv}=2-\mathbf1_{i=j},\qquad
C=2J-\operatorname{diag}(J_6,J_6,J_6).
\]

Equivalently, in the full thirty-nine-vertex core matrix, this is the
cross block of \(12I+2J-B^2-B\). There are 324 cross entries.

Every exterior vertex has exactly two neighbors in each twelve-vertex
global fiber and three neighbors in each component. If its component
triples have occupancy vectors \(a,b\), then
\[
a+b=(2,2,2).
\]
Thus \(111\) pairs with \(111\), and each oriented \(210\) pairs with
the opposite \(012\).

Conversely, combining two individually admissible component triples
with complementary occupancies passes the one-column support and
mixed-cap tests for the full core. Cross Gram entries are positive,
and a shell vertex has no neighbors in the other component. The
central mixed equations are exactly the two-per-fiber condition.
This is a complete candidate-column statement, not a claim that
sixty such columns satisfy all pair quotas.

## Domain sizes and relative alignments

With component zero on both sides and the identity fiber alignment:

| Restrictions on incidence | Candidate columns or assignments |
|---|---:|
| Both sides use their complete 480-triple domains | 39,168 |
| First side fixed to the saved 60-triple design; second domain free | 5,472 |
| Both sides fixed to that same 60-triple design | 792 |

For the last row, the count is
\(24^2+6\cdot6^2=792\). The saved design has 24 triples of profile
\(111\) and six of every oriented \(210\) profile.

The certificate also records domain sizes for component zero paired
with each of the 66 possible second components, under all six
relative fiber permutations. Direct paired-column counts range from
34,272 to 50,112. Fixing the first saved incidence gives between
4,752 and 6,912 assignment variables.

These 396 records are domain counts only. The single fixed-design
restriction below was tested separately; the family was not searched.
The relative fiber permutations are retained because canonicalizing a
component may permute its three central vertices. Two separately
canonicalized components cannot silently be assumed to have the same
alignment.

## An exact fractional self-coupling

Component zero has six explicitly checked automorphisms fixing its
three fibers. This group is transitive on the six vertices in each
fiber. Apply these six maps to the saved sixty-triple design and
average the resulting binary designs on the second component.
No symmetry of an unknown full graph is assumed.

For a fixed first-side triple with profile \(a\), distribute its unit
mass among the averaged second-side triples having profile \(2-a\).
The profile multiplicities are 24 for \(111\) and six for every
oriented \(210\), so opposite profiles have the same multiplicity.
Every first row has total one, and the resulting second-side
selection is precisely the average of the six binary designs.
It has the correct second-component Gram matrix and no triple
multiplicity exceeding one.

Transitivity makes the conditional expected incidence at any fixed
vertex of second fiber \(j\) equal to \((2-a_j)/6\). If \(x\) is a
first-component vertex, the expected cross entry is

\[
\frac16\sum_{h\ni x}(2-a_j(h))
=\frac{20-\sum_{z\in V_j}G_{xz}}6.
\]

The fiber sum in the numerator is fourteen when \(x\in V_j\), and
eight otherwise. The cross entry is therefore one or two as required.

The saved control has 2,916 positive weights with common denominator
144 and uses 234 different second-side triples. Integer replay checks
all 1,521 entries of the full thirty-nine-vertex Gram matrix, all
sixty first-row sums, second-triple multiplicity at most one, all
supported core-triple packing inequalities, and the second-side
linear prism/\(F\) conflicts.

This fractional point belongs to the 5,472-variable model with the
second domain free. It is not a point of the 792-variable restriction.
Uniform profile matching using only the original sixty second
triples fails 167 cross entries. That failed particular matching
does not prove the smaller model infeasible.

The source and exact certificate are
[root_prism_free_f0_coupling.py](../experiments/workspace/root_prism_free_f0_coupling.py)
and
[f0-coupling-certificate.json.gz](../experiments/logs/root-prism-free/f0-coupling-certificate.json.gz).
Generation and standard-library replay passed without an optimizer.

## The fixed-pair binary model

For each allowed pair \((s,t)\) of indices in the two saved
sixty-triple designs, let \(y_{st}\) be a binary variable. The model
requires one choice in every first row and every second column.
It also imposes all 324 cross Gram equations.

If two candidate assignments use different first and second indices
but their full six-neighbor signatures share at least three core
vertices, their conjunction is forbidden. Otherwise the two exterior
vertices would have at least three common neighbors. Pairs using
the same first row or second column are already excluded by the
matching quotas.

The frozen model has 792 primary variables, 23,100 total variables,
and 56,096 clauses. It contains sixty row quotas, sixty column
quotas, 324 cross equations, and 8,180 explicit packing conflicts.
There are no variables for exterior edges, no automorphism
constraints, and no chosen permutation of the sixty vertices.

The [builder and replay](../experiments/workspace/root_prism_free_f0_fixed_pair.py)
bind the
[model manifest](../experiments/logs/root-prism-free/f0-fixed-pair-model.json)
to the exact saved designs and identity fiber alignment.
A nine-vertex rook control checks all 120 permutations of a smaller
matching problem against direct incidence products and packing.
The empty matching is also rejected.

The pilot used one fresh proof-enabled query with a sixty-second
limit. Its SAT verification branch reconstructs the full core
incidence and checks all 1,521 Gram entries, all 1,770 exterior
signature overlaps, all 4,851 known partial-graph caps, and
core-triple packing. It separately scans the known partial graph
for visible prisms and \(F\) motifs. These further motif restrictions
are not all encoded in the matching formula, so any detected motif
is reported as a defect of the SAT candidate.

Even a candidate passing all these checks still needs the exterior
edges. Its 39 core vertices have degree fourteen, but its sixty
exterior vertices have only their six specified core neighbors.
It is not a complete graph.

## Checked outcome

The single query returned UNSAT in 0.300 seconds including its
0.089-second bootstrap. The direct DRAT check passed. A separate cold
process rebuilt the complete paired domain and all 56,096 clauses,
matched the recorded CNF hash, checked that all 7,447 retained input
clauses belonged to that rebuilt formula, and independently replayed
the retained DRAT proof. That replay also passed.

Before the run, a separate
[independent audit](../experiments/workspace/root_prism_free_f0_fixed_pair_independent_audit.py)
reconstructed the thirty-nine-vertex core, all 1,521 Gram entries,
all 792 candidate columns, the 444 quota supports, and every one of
the 8,180 packing conflicts. It did not import the subject builder
or invoke a solver. The actual packing-clause suffix was checked.

The result excludes exactly the two saved sixty-triple designs,
placed on two copies of component zero with the identity fiber
alignment. It does not exclude component zero, another incidence
design, a different relative alignment, or the split case.

| Model | Verified result |
|---|---|
| First saved incidence fixed; second complete domain free | Exact fractional point with denominator 144 |
| Both saved incidences fixed; identity fiber alignment | UNSAT with direct DRAT and cold replay |

The durable result is
[result.json](../experiments/logs/root-prism-free/f0-fixed-pair-run01/result.json).
The small proof consists of
[retained.cnf](../experiments/logs/root-prism-free/f0-fixed-pair-run01/retained.cnf)
and
[retained.drat](../experiments/logs/root-prism-free/f0-fixed-pair-run01/retained.drat).
The
[cold replay report](../experiments/logs/root-prism-free/f0-fixed-pair-run01-replay.json)
records the exact scope and checker hash.

The complete CNF hash is
`af2adcaffbcca28aa0013405b9627a0e5bedf1cac3a6f4c0a83c18f17e899615`.
It can be regenerated and the saved proof replayed with:

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_fixed_pair.py replay \
  --model experiments/logs/root-prism-free/f0-fixed-pair-model.json \
  --result experiments/logs/root-prism-free/f0-fixed-pair-run01/result.json \
  --output /tmp/f0-fixed-pair-fresh-replay.json \
  --drat-trim /tmp/conway99-drat-trim/drat-trim
```

The output path must not already exist. No second query or wider
sweep was run.
