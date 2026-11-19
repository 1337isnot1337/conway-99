# Global prism-freeness in the rooted matching model

This note derives a local consequence of global prism-freeness that is
absent from the completed maximum-anchor zero searches. It produces
34,440 four-edge clauses on the existing 3,486 primary variables.
It also gives matching-complete partial controls for all four surviving
anchor types. The controls show that this local matching condition and
the visible upper caps do not eliminate any of those types.

No complete graph is constructed or excluded here. No solver is run.
The new clauses require a globally prism-free graph. A root that belongs
to no prism is a weaker hypothesis.

## 1. Three matchings around one triangle

Use the mandatory triangle neighborhood from
[`triangle_root_constraints.md`](grids-and-triangles/triangle_root_constraints.md).
The shell has three twelve-point fibers and adjacency

\[
D=\begin{pmatrix}M&I&I\\I&P&Q\\I&Q^T&R\end{pmatrix}.
\]

Here `M,P,R` are perfect matching matrices and `Q[i,q(i)]=1` is a
permutation matrix. The core also contains the central triangle, whose
three vertices are adjacent to their respective fibers.

**Local characterization.** This complete 39-point core contains no
induced triangular prism if and only if

\[
\operatorname{Fix}(q)=\varnothing,
\qquad E(M)\cap E(P)=E(M)\cap E(R)=\varnothing,
\qquad E(P)\cap E(QRQ^T)=\varnothing. \tag{1}
\]

To prove necessity, a fixed point of `q` gives a shell triangle with a
perfect-matching interface to the central triangle. A common edge of
two transported internal matchings gives two triangles centered at
the corresponding adjacent central vertices. Their four shell
vertices and the central edge induce a prism.

For sufficiency, the absence of fixed points removes every shell
triangle. The remaining triangles are the central triangle and the
six internal-edge triangles centered at each of its three vertices.
Two triangles with the same center intersect. For different centers,
a prism occurs exactly when their internal matching edges correspond
under the cross-fiber matching. These are precisely the three
matching intersections in (1).

Condition (1) also implies every visible core upper cap. The only way
to violate such a cap is a pair of equal open-neighbor rows in the cubic
shell. For two vertices in different fibers, equal rows force a common
edge in the internal matchings transported across that interface.
Condition (1) excludes this. The converse is not asserted: core caps
alone do not forbid prisms.

The executable check enumerates all 216 configurations with four points
per fiber, a fixed reference matching, two free internal matchings, and
an arbitrary cross permutation. Direct prism enumeration agrees with
(1) in every case; 22 configurations are prism-free. Every one of those
22 passes the visible upper caps.

## 2. What changes under a globally prism-free hypothesis

Fix a root `r`, with near labels `0,...,13` and mates `a^1`.
Write `x_ab` for the unique exterior vertex with near signature `{a,b}`.
For each near anchor `a`, the twelve vertices `x_ab` form a perfect
matching, represented by a matching `M_a` on the other twelve labels.

For the root triangle `{r,a,a^1}`, the reference matching `M` is the
near-label mate matching, while `P=M_a` and `R=M_(a^1)`. The cross
permutation `q_a` is determined by

\[
x_{ab}\sim x_{a^1,q_a(b)}.
\]

If the root belongs to no prism, each `M_a` avoids reference mates,
and each `q_a` has no fixed point. These facts are already encoded by
the 84 zero cell-side variables in the maximum-anchor zero cases.
They give the first three conditions in (1).

Global prism-freeness additionally requires

\[
E(M_a)\cap E(Q_aM_{a^1}Q_a^T)=\varnothing
\quad\text{for all seven root axes}. \tag{2}
\]

The excluded prisms have one triangle centered at `a` and the other
centered at `a^1`. They do not contain the chosen root. Thus (2) must
not be inserted into a search claiming to cover every graph with only
a prism-free chosen root.

## 3. The four-edge clauses

Choose one root axis `{a,a^1}`. Let `{b,c}` and `{d,e}` be disjoint
non-mate pairs among the other twelve near labels. The four edges

\[
x_{ab}x_{ac},\quad x_{a^1d}x_{a^1e},\quad
x_{ab}x_{a^1d},\quad x_{ac}x_{a^1e} \tag{3}
\]

cannot all be present in a globally prism-free graph. Together with
the mandatory edge `aa^1` and the four mandatory near-to-exterior
edges, they form a prism. Swapping `d,e` gives the other cross matching.
The clause is the disjunction of the four negated edge variables.

There are 60 choices for `{b,c}`. After removing these two labels,
41 non-mate pairs remain: among the ten remaining labels there are
45 pairs, of which four are reference mate pairs. Hence each axis gives

\[
60\cdot41\cdot2=4,920
\]

clauses, for a total of 34,440 distinct clauses.

No omitted case is needed. An internal reference-mate pair is already
excluded by a zero cell-side variable. If the two internal pairs share
a near label, either a cross edge is a zero cell side, or opposite
vertices of the four-cycle have that near point plus the two cycle
neighbors as three common neighbors. The visible cap already excludes
the latter possibility. Therefore these clauses exhaust the remaining
prism exclusions inside the seven mandatory triangle cores, given the
root-zero conditions and the visible caps.

The clause file uses exactly the primary order of `root_full_caps.py`:
lexicographically ordered non-mate near pairs, followed by all unordered
pairs of their 84 exterior indices. It introduces no variable and no
symmetry assumption. Its deterministic gzip file is
`experiments/logs/root-prism-free/near-axis-clauses.cnf.gz`.

| Binding | SHA-256 |
| --- | --- |
| Raw 34,440-clause CNF | `05a7d5d559c00cb557001c6b80a64145dd6119ae2018f2ae1273d9c3b4d4bcf2` |
| Deterministic gzip | `2e7a23d57754fc90c5794ce40d71efb7997ac1829c281ac52684892324e1a3bb` |

## 4. Simultaneous seven-axis controls

The controls label the near vertices by `(a,s)` with `a` in the cyclic
group of order seven and `s` in `{0,1}`. For each axis, split the six
nonzero offsets `1,...,6` into consecutive blocks of one of the four
partitions

\[
222,\quad24,\quad33,\quad6.
\]

On a block, the positive anchor matches the sign-one point at each
offset to the sign-zero point at the next offset cyclically. The
negative anchor uses the same matching on blocks of length at least
three. On a two-offset block, it instead matches points of equal sign.
All seven cross-fiber permutations reverse signs, `q_a(b)=b^1`.
The source gives every matching explicitly in the certificate.

This determines all near-fiber internal matchings and all seven
cross-fiber matchings simultaneously. Their cross-fiber edges are the
42 exterior antipodal pairs. The fourteen internal matchings contribute
84 further exterior edges.

| Common anchor type | Components of each cubic triangle shell | Visible cap failures | Known prisms |
| --- | --- | ---: | ---: |
| `222` | `12+12+12` | 0 | 0 |
| `24` | `12+24` | 0 | 0 |
| `33` | `18+18` | 0 | 0 |
| `6` | `36` | 0 | 0 |

Every control includes the complete mandatory root incidence. It has
315 known edges, 91 known triangles, and passes all 4,851 visible pair
upper caps. The root and its fourteen neighbors have degree 14; the
84 exterior points have known degree five. Their missing exterior
edges are not supplied. These are partial configurations, not graphs
with the required parameters or completed incidence designs.

A separate countercontrol uses type `6` but replaces the negative
matching with the sign-reversal conjugate of the positive matching.
It still supplies all fourteen matchings and all seven cross matchings,
passes all visible caps, and contains no prism through the chosen root.
It has six prisms at each near mate edge, for 42 prisms in total, and
violates exactly 42 of the new clauses. This explicitly separates the
two hypotheses at the matching-complete local level.

## 5. An exact mixed spectral trace

Let `C` be the complete adjacency matrix on the 84-point root exterior,
and let `H` be its 2-regular subgraph consisting of the 84 edges with
a common near label. Let `m_r` count prisms containing the chosen root.
Exactly `m_r` of the edges of `H` are cell sides.

The root mixed equations force the spectrum

\[
12^1,\quad3^{40},\quad0^7,\quad(-2)^6,\quad(-4)^{30}.
\]

Indeed, if `S` is the 14-by-84 near-incidence matrix and `M` is the
near mate matching, then `SC=2J-(I+M)S`. The image of `S^T` has dimension
14: its constant, centered axis-support, and signed-axis spaces have
dimensions 1, 6, and 7 and eigenvalues 12, minus two, and zero.
On the 70-dimensional kernel of `S`, the exterior block identity gives
`C^2+C=12I`. The zero trace of `C` then gives the multiplicities 40
and 30 for eigenvalues three and minus four.

Its zero eigenspace has an explicit orthogonal basis: for each near
axis `A`, the signed indicator `f_A` is plus or minus one when an
exterior signature contains the corresponding sign of `A`, and zero
otherwise. Each has squared norm 24. Thus

\[
E_0=\frac1{24}\sum_A f_Af_A^T.
\]

For an `H` edge, the signed endpoint dot product is one unless it is a
cell side, in which case it is zero. Hence

\[
\operatorname{tr}(HE_0)=7-\frac{m_r}{12}. \tag{4}
\]

Likewise, the six-dimensional minus-two space comes from the centered
axis-support indicators `h_A=1_A-2/7`. Their frame operator is twenty
times the projector, so

\[
E_{-2}=\frac1{20}\sum_A h_Ah_A^T,
\qquad
\operatorname{tr}(HE_{-2})=\frac{18}{5}+\frac{m_r}{10}. \tag{5}
\]

Together with `tr H=0`, `tr(CH)=168`, and `tr(HE_12)=2`, these give

\[
\operatorname{tr}(HE_3)=\frac{72}{5}+\frac{2m_r}{105},
\qquad
\operatorname{tr}(HE_{-4})=-27-\frac{m_r}{28}. \tag{6}
\]

Consequently

\[
\operatorname{tr}(C^3H)=5544+2m_r,
\qquad
\operatorname{tr}(C^4H)=35784-6m_r. \tag{7}
\]

In the globally prism-free case, `m_r=0` at every root. These are exact
necessary equalities, not a spectral contradiction. The source checks
the fixed-space traces on all partial controls and checks the rational
algebra in (4)--(7) for all formal integer values `0<=m_r<=84`.

The external exploratory
[Wave 65 audit](https://github.com/YesterdaysLemon/conway-99-research/blob/main/verification/wave65-rooted-hypergraph-algebra/audit.md)
already records the rooted 2-factor/triangle decomposition and studies
the scalar `tr(HE_3)` in an interval. Equations (4)--(6) determine that
scalar from the actual fixed signed-axis eigenspace. The separate
[Wave 59 audit](https://github.com/YesterdaysLemon/conway-99-research/blob/main/verification/2026-07-27-wave59-integration-audit.md)
records related point-triangle incidence restrictions. Neither external
audit claims to resolve the prism-free case. The present derivations
do not depend on executing their code or accepting their claimed checks.

## Reproduction and scope

```sh
python experiments/workspace/root_prism_free_structure.py \
  --certificate experiments/logs/root-prism-free/structure-certificate.json \
  --clauses experiments/logs/root-prism-free/near-axis-clauses.cnf.gz --replay
```

The certificate contains all partial controls and binds the source,
primary order, raw clause CNF, and compressed clause file. The source
uses the standard library only. It proves a local reduction and records
why the resulting matching conditions do not by themselves remove any
of the four prism-free anchor types.
