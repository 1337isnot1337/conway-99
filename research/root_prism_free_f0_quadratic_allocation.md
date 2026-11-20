# Exact allocation of shared row potentials

This package retains a quadratic consequence of every saved shared-row
potential. It tests all 288 transported consequences against 153 saved
incidences with integer arithmetic. No optimizer or graph search runs.

The test finds three violations that the 288 earlier fixed shared
allocations miss. Those three incidences already violate retained
individual-row inequalities. The historical scan therefore adds no
exclusion beyond the full existing registry. It establishes a stronger
shared-potential check that can be reused at later Boolean candidates.

## Scope and equations

The conditional setting is unchanged: a globally prism-free,
\(F\)-free split \(18+18\) shell has component zero as its first
18-vertex component. Its first-component triple domain has 480 distinct
signatures. The other component, its incidence, and its fiber alignment
are unrestricted.

For each possible signature \(a\), let \(h_a\) be its 18-entry
indicator column and let

\[
q_a=2\mathbf 1-h_a-A_1h_a.
\]

All columns have weight three and all \(q_a\) have sum 24. There are
68,394 universally eligible unordered signature pairs. A completion
has Boolean selectors \(z_a\) and symmetric exterior-edge variables
\(y_{ab}\), with

\[
\sum_{b:ab\text{ eligible}}h_b y_{ab}=q_a z_a,
\qquad 0\le y_{ab}\le z_a z_b.
\]

The mixed equations imply exterior degree eight by summing their 18
coordinates. The argument below uses their complete vector form.

Choose any integer row potentials \(v_a\in\mathbb Z^{18}\). Define

\[
d_a=v_a^Tq_a,
\qquad w_{ab}=v_a^Th_b+v_b^Th_a,
\qquad w_{ab}^{+}=\max(w_{ab},0).
\]

Summing the weighted mixed equations over the selected signatures gives

\[
\sum_a d_a z_a=\sum_{ab}w_{ab}y_{ab}
\le\sum_{ab}w_{ab}^{+}z_a z_b.
\]

Thus every completion satisfies the universal quadratic inequality

\[
Q_v(z)=\sum_{ab}w_{ab}^{+}z_a z_b-\sum_a d_a z_a\ge0.
\tag{1}
\]

Potential validity does not depend on how an LP originally found the
potential. The source reconstructs every coefficient in (1) from the
saved integer vectors and the complete eligible-edge domain.

## A necessary linear cut at any Boolean candidate

For each positive-weight edge, choose one of its endpoints \(e(ab)\).
Since \(z_a z_b\le z_{e(ab)}\), equation (1) implies

\[
L_e(z)=\sum_a d_a z_a-\sum_{ab}w_{ab}^{+}z_{e(ab)}\le0.
\tag{2}
\]

This is a necessary signed linear selector inequality for every
completion. Its endpoint choices may be made after inspecting a
candidate. Once chosen, equation (2) has no fixed-candidate premise.

At a Boolean candidate \(T\), allocate each positive edge to an absent
endpoint whenever one exists. If both endpoints are present, choose
either one. The payment of that edge is then exactly
\(w_{ab}^{+}\mathbf 1_{\{a,b\}\subseteq T}\). Therefore

\[
\max_e L_e(T)=-Q_v(T).
\tag{3}
\]

Each edge minimizes its payment independently, which proves (3)
without searching endpoint assignments. If \(Q_v(T)<0\), the chosen
allocation gives a violated necessary linear cut. Its signed
coefficients can use the existing exact clause-explanation code.

Equation (3) requires Boolean selectors. For fractional selectors the
minimum endpoint payment is \(w_{ab}^{+}\min(z_a,z_b)\), which need
not equal \(w_{ab}^{+}z_a z_b\). The pilot makes no fractional-selector
claim. Fractional *edge* values remain valid when the selectors are
Boolean and the mixed equations hold.

No one allocated linear cut is claimed to dominate every other
allocation at every point. The quadratic test represents their
pointwise strongest value.

## Complete recovery and transport

The source recovers 24 base potential families from the frozen
certificates and transcripts. It extends each potential by zero on
unsupported signatures, recomputes \(d_a\) and every positive
\(w_{ab}\), and reproduces the previous endpoint allocations.

The 12 core relabelings are regenerated from the saved generators.
Every map preserves the complete core, triple domain, targets, and
eligible edges. The source verifies the transported coefficients of
all 276 parent signed inequalities and all 12 gap-64 inequalities.
These are 288 distinct quadratic predicates. Their base representations
contain 66,925 positive edge terms in total.

A transported quadratic is evaluated by applying the inverse signature
map to the candidate. This is exactly the same expression as moving
every potential, demand, and edge coefficient. No automorphism of a
hypothetical completed graph is assumed.

All 2,916 parent inequalities, the 12 gap-64 inequalities, and the
5,340 existing explanation clauses remain unchanged. This package
creates no CNF and edits no registry.

## Exact controls and historical scan

The small controls check 216 endpoint maxima by enumerating all endpoint
choices and 1,000 individual allocation comparisons. Another 72
artificial activated edge boxes satisfy the exact mixed equations and
degree-eight identities. Of these, 24 use fractional exterior edges.
All have Boolean selectors and weight-three columns. These controls
test the algebra; they are not claimed to be SRG completions.

The saved-candidate scan checks all \(153\cdot288=44,064\)
candidate/family pairs. Every old fixed-allocation value is at most the
new pointwise value. There are 43,986 strict improvements in value, 25
violations of old fixed shared allocations, and 28 violations of the
quadratic tests.

The three additional shared-family detections are:

| Saved incidence | Family and core map | New normalized gap | Nonzero linear coefficients | Retained individual inequalities already violated |
|---|---|---:|---:|---:|
| First lazy run, iteration 2 | Family 21, map 10 | 1 | 99 | 2 |
| First lazy run, iteration 3 | Family 21, map 10 | 1 | 100 | 2 |
| First lazy run, iteration 18 | Family 21, map 3 | 1 | 99 | 3 |

Family 21 comes from the later bounded-lazy run, iteration 42. It has
two supported vertex potentials. The three new allocations have raw
gap three and coefficient gcd three. The scan exports their exact
integer coefficients and endpoint-choice hashes. These are historical
controls, not new component exclusions or matched-input performance
measurements.

## Replay and intended use

The implementation is
`experiments/workspace/root_prism_free_f0_quadratic_allocation.py`.
Its preparation and scan are stored as deterministic gzip JSON under
`experiments/logs/root-prism-free/f0-quadratic-allocation-*`.

The complete optimizer-free replay is:

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_quadratic_allocation.py replay-scan \
  --preparation experiments/logs/root-prism-free/f0-quadratic-allocation-preparation.json.gz \
  --result experiments/logs/root-prism-free/f0-quadratic-allocation-scan.json.gz \
  --output /tmp/f0-quadratic-allocation-replay.json
```

The separate registry-context checker recomputes the old individual
inequalities violated by the three additional detections. It prevents
confusing a stronger shared-family test with a new exclusion beyond the
full retained model.

A future continuation can evaluate every retained potential family at
each Boolean candidate before calling a new row or shared LP. A
negative value gives an exactly certified linear inequality through
(2). A nonnegative value only means this saved family does not separate
the candidate. All existing cuts must remain, and any new potential
requires the same direct integer reconstruction. No production
continuation is part of this pilot.
