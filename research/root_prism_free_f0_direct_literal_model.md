# Direct F0 literal-selector model

## Scope and current status

This is a separate necessary-condition model for the fixed first F0 component.
It keeps all 480 literal selector variables free. It does not introduce
population averages, Fourier coordinates, edge variables, product constraints,
tables, symmetry assumptions, hints, or a fixed incidence.

The source is
[the direct literal builder](../experiments/workspace/root_prism_free_f0_direct_literal_model.py).
At this source checkpoint, the mathematical plan and native model have not
been built. The proposed next phases are one owned 60-second preparation and
one separate owned 60-second cold replay. Both require the source gate.
The source contains no solver construction or solve call.

The earlier free-selector lane did not explicitly encode every final
inequality. Its final registry contained 4,404 inequalities, while its SAT
formula contained 8,628 necessary explanation clauses. That bounded run ended
UNKNOWN without an incremental UNSAT result or fresh proof. The recovered
note is
[the allocated-lazy terminal record](root_prism_free_f0_allocated_lazy_run01_recovered.md),
SHA-256 1184d6c67ce56a3202eb8a9f2f8b79de3848b2a0285c35bc36d991fc4f614be2.
The present target includes those 4,404 inequalities and the earlier 12 direct
cuts, as the frozen authoritative archive of 4,416 literal inequalities.

The recent full Fourier query also ended without a candidate. Its target
contains many additional count and exterior-moment obligations. The direct
model is a smaller necessary projection intended to obtain a literal
selection for subsequent checks; it is not claimed equivalent to that full
target.

## Exact variables and rows

The frozen literal layer has native variables 31,756 through 32,295.
Subtracting 31,756 gives the new variables 0 through 539.

| Group | Variables or rows |
| --- | ---: |
| Literal Boolean variables | 480 |
| Existing radix auxiliaries | 60 |
| Direct cut inequalities | 4,404 |
| Limb equalities for the 12 large cuts | 36 |
| Nonempty original Gram/population equations | 151 |
| Explicit motif conflicts | 90 |
| Total variables | 540 |
| Total native linear rows | 4,681 |

The first 480 rows of the old literal layer link literal bits to Fourier
inverse coordinates. Those rows are omitted. Every later layer row uses only
the 540 retained variables. The builder checks this, remaps each coefficient
index, then reverses the remap and compares every retained variable and row
with the original layer. All 4,416 original cut records retain their
authoritative row hashes and their native-row intervals.

The 12 large cuts have original IDs 4,164 through 4,175. They are not the last
12 archive rows. Each has three radix limbs and five auxiliary variables.
All other cuts remain direct signed integer inequalities. No coefficient is
rounded, divided, capped, scaled, or discarded in this new transport.

The layer archive is
`f0-literal-cut-native-layer01/layer.json.gz`,
SHA-256 dcb44159712f9c9a4f61cc61950c23d62b804a0d57709ca43afb33e3711d2b33.
Its independent cold record is
`f0-literal-cut-native-layer01-cold.json`,
SHA-256 7bed3fffebe2bf026eac13961bbee1c2ba25ac04913a11b4b3f9f7dc8d6fa44b.
The builder binds that proof chain and rechecks the complete row remap.

## The original incidence equations

For the 18 component sites, let \(h_a\) be signature \(a\), and let \(C\)
be the frozen 21-vertex core adjacency matrix. For each
\(0\leq i\leq j<18\), the direct equation is

\[
\sum_{\{a:i,j\in h_a\}} z_a
 =12[\,i=j\,]+2-(C^2)_{i+3,j+3}-C_{i+3,j+3}.
\]

These are 171 equations. The additional population equation is

\[
\sum_{a=0}^{479}z_a=60.
\]

The builder derives their literal supports and right sides from the frozen
core and signature domain. It compares all 172 equations with the saved
original rows in the full specification. Exactly 21 have empty support and
right side zero. Their IDs and proof records remain in the plan; they need
no native row. The other 151 equations are appended without a rank
reduction or a quotient.

## Every known zero pair is covered

The frozen second-moment preparation contains 4,410 proved zero literal
pairs. Its 4,320 quota-one pairs already follow from the direct Boolean
equations. If

\[
\sum_{a\in S}z_a=1,\qquad z_a\in\{0,1\},
\]

then \(z_a+z_b\leq1\) for every distinct \(a,b\in S\).
The builder records the original equation ID for each such pair.

The remaining 90 pairs are the explicit motif conflicts: 78 F witnesses
and 12 prism witnesses. Each supplies \(z_a+z_b\leq1\).
The builder checks the indicated motif on the 21-core plus the two selected
outside signatures. It also checks that making the two outside vertices
adjacent violates a common-neighbor cap. Thus the pair is excluded whether
that outside adjacency is absent or present, in the same frozen
prism-free F0 scope as the parent model.

The complete newly derived pair list is compared with all 4,410 saved
certificates and with every member of the 389 saved zero-pair orbits.
This is a coverage check, not a new pair census. Consequently no separate
4,320-row AMO expansion is needed. The 90 motif rows are present explicitly.

## Exact radix equivalence

For one large cut, write \(c\cdot z\leq0\). Let \(B=2^{30}\), use three
limbs, and introduce nonnegative slack digits \(u_0,u_1,u_2<B\).
The limb equation is

\[
\sum_a \operatorname{sgn}(c_a)
       \operatorname{digit}_k(|c_a|)z_a
 +u_k+t_k-Bt_{k+1}=0,
\]

with \(t_0=t_3=0\). The two internal carries have the existing certified
bounds \(|t_k|\leq m+2\), where \(m\) is the number of nonzero cut terms.

Multiplying the three equations by \(1,B,B^2\) and adding cancels both
carries. The result is \(c\cdot z+u_0+Bu_1+B^2u_2=0\), which implies the
cut. Conversely, any Boolean point satisfying the cut has the nonnegative
slack \(-c\cdot z\). The frozen magnitude check places it below \(B^3\).
Its ordinary base-\(B\) digits and the successive integer carries satisfy
the limb system and the certified carry bounds.

The builder compares every literal limb coefficient and auxiliary domain
with this formula, and checks the exact weighted contraction. Necessity of
the underlying 4,416 inequalities is inherited from the frozen archive and
its existing proof chain; it is not inferred from a native solver status.

## Native preparation and cold replay

Preparation will create the exact protobuf and construct the same model
through the public OR-Tools 9.15.6755 API. It must pass the native validator
and an exact exported-protobuf byte comparison. Each coefficient, domain
endpoint, and absolute row activity is checked with Python integers before
native conversion. The installed `cp_model.py` file is hash-bound.

Cold replay will reread the frozen input archives, redo the direct
coefficient and implication checks, and reconstruct the complete mathematical
plan and protobuf. It compares both complete byte streams with the saved
archives. It does not repeat native construction or invoke a solver.

The 60-second owners include imports, input loading, construction, and raw
writes. The reviewed supervisor kills and reaps a child at its deadline.
A late or failed child cannot produce an accepted preparation.

## Candidate and proof boundaries

A future returned 540-integer vector must satisfy every native row and every
variable domain. The separate integer inspection also evaluates all 172
original equations, all 90 motif conflicts, and all 4,416 authoritative cuts
directly on its first 480 bits, with Python integer arithmetic. It checks
all known zero-pair consequences and the derived incidence profiles.

A passing vector is a literal first-incidence witness only. Exterior-edge
realization and a full graph remain unresolved. The root's exact
core-matching oracle can inspect the selected eight-element sets at the
18 core sites. Any later added matching clause must retain its own exact
necessity witness. No such clause has been added here.

A future native INFEASIBLE status alone is not an exclusion certificate.
A separate proof-capable encoding and independent checker would be required
before a mathematical impossibility claim.
