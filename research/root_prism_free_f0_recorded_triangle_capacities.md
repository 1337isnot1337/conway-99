# Capacities for the recorded exterior triangles

For each recorded exterior edge e, let S_e be the distinct saved triangle
indicators containing e. Every actual completion of the fixed F0
formulation satisfies
\[
\sum_{\tau\in S_e}t_\tau\le y_e.
\tag{1}
\]
The 5,364 saved indicators give 6,300 nonempty edge-incidence sets.
Of these, 84 target sets already have equality constraints, and 3,312
non-target sets are singletons whose inequalities are existing AND upper
bounds. The remaining 2,904 sets give the proposed side-edge capacity
family. It uses existing variables only.

For each signature a, let T_a be the sum of the distinct saved indicators
containing a, and let k0(a) count edges inside its fixed-core triple.
A second necessary family is
\[
T_a\le(2+k0(a))x_a.
\tag{2}
\]
There are 420 nonempty rows of this form. After (1), the existing degree
and mixed equations imply (2) for the Boolean formulation by integer
rounding. This is not a continuous derivation of (2) from (1).

These are proposals for a later model. The current model and query are
unchanged. The sufficient implication audit below proves that some
proposals already follow from existing Boolean constraints. It does not
prove that any remaining row is independent of the complete model.

## Necessity of each side capacity

In a strongly regular graph with lambda=1, an edge has exactly one common
neighbor in the full graph. It therefore lies in at most one triangle
whose third vertex is exterior. If y_e=0, every recorded triangle
containing e is absent. If y_e=1, at most one is present. Since the saved
indicators are the exact Boolean ANDs of their three edge bits, this
proves (1).

This argument needs the full adjacent-pair condition lambda=1. It does
not assume that the common neighbor lies in the exterior. It does not
assume that the recorded family contains every exterior triangle, and
it does not depend on the unknown second component's incidence or
alignment. The fixed branch and all domain restrictions remain those
of the accepted parent formulation.

An indicator that lies on two or three candidate side edges appears
in each corresponding capacity. There is no sharing of one capacity
between different original edge IDs.

## The local matching proof

The globally prism-free, F-free split18+18 branch has two anticomplete
shell components C0,C1. Every selected exterior vertex has three
neighbors in each and eight exterior neighbors. In a completed graph,
its fourteen neighbors induce a matching of seven edges, because
lambda=1.

Let k_i(a) be the number of edges inside its three neighbors in Ci.
Both k_i are zero or one. Exactly 6-2k_0-2k_1 of the eight exterior
neighbors are matched to shell neighbors. Pairing the others gives
\[
t_D(a)=1+k_0(a)+k_1(a)\le2+k_0(a).
\]
A recorded family counts only some of these triangles. Activation makes
its count zero when x_a=0, proving (2).

The original split and incidence premises are essential to this proof.
The same proof and the exact global count of 32 exterior triangles
are recorded in
[root_prism_free_f0_exterior_triangle_counts.md](root_prism_free_f0_exterior_triangle_counts.md).
The separate total bound on the 84 target edges is already at most
eighteen from Gram and activation alone; see
[root_prism_free_f0_must_triangle_total_bound.md](root_prism_free_f0_must_triangle_total_bound.md).

## Deriving the local caps from edge capacities and old equations

There is also a derivation that does not introduce k_1 or any new
information about the second component.

Let A0 be the fixed eighteen-vertex component adjacency and h_a its
three-site signature. The existing mixed equations are
\[
\sum_{b:\ i\in h_b}y_{ab}
 =q_{ai}x_a,\qquad
q_{ai}=2-{\bf1}_{i\in h_a}-|N_{C0}(i)\cap h_a|.
\]
Their sum over i in h_a is
\[
\sum_b |h_a\cap h_b|y_{ab}
 =(3-2k_0(a))x_a.
\tag{3}
\]
Every original eligible edge has signature overlap zero or one. Hence
the left side is exactly the degree contributed by overlap-one edges.
Subtract (3) from the existing exterior degree equation
sum_b y_ab=8x_a:
\[
\sum_{b:\ h_a\cap h_b=\varnothing}y_{ab}
 =(5+2k_0(a))x_a.
\tag{4}
\]

All saved triangles have pairwise disjoint first-component signatures.
Sum (1) over the overlap-zero edges incident with a. An edge with no
recorded triangle contributes the trivial inequality zero<=y_ab.
For a target edge use its existing target equality; for a singleton
side edge use its existing AND upper bound. Every recorded triangle
through a is counted twice, so
\[
2T_a\le(5+2k_0(a))x_a.
\tag{5}
\]
When x_a=0, nonnegativity gives T_a=0. When x_a=1, T_a is integral and
k_0 is zero or one, so division by two and rounding down proves (2).

Equation (5) is continuous. The rounding step to (2) uses integrality.
Thus the local rows are valid explicit rounded bounds even when an
implementation retains real-valued relaxations internally. No claim is
made that they strengthen the full continuous relaxation; that would
require an actual implication certificate or a feasible separating
point for the complete parent.

## Complete proposed row families

The indicator offset in the frozen combined configuration is 71,382:
indicator j is native variable 71382+j. An original edge with ID e
has native variable 540+e. Selector a is native variable a.

The output preserves all candidate side rows in ascending original edge
ID, followed by all nonempty local rows in ascending selector ID.
Each row key is [lower,upper,terms], with sorted distinct
[variable,integer coefficient] terms.

The side row for e has key
\[
[-1,0,\ [(540+e,-1)]\cup[(71382+j,1):j\in S_e]].
\]
The local row for a has lower bound -(2+k0(a)), upper bound zero,
selector term (a,-(2+k0(a))), and one coefficient-one term for each
distinct recorded triangle containing a. These lower bounds are the
automatic minimum activities from nonnegative indicators and Boolean
selectors; the substantive restrictions are the upper bounds.

| Family or disposition | Rows | Indicator terms | All terms |
| --- | ---: | ---: | ---: |
| Existing target equalities | 84 | 5,364 | 5,448 |
| Existing singleton side AND bounds | 3,312 | 3,312 | 6,624 |
| Proposed non-target side capacities | 2,904 | 7,416 | 10,320 |
| Proposed nonempty local capacities | 420 | 16,092 | 16,512 |
| Proposed appended total | 3,324 | 23,508 | 26,832 |

The 2,904 side rows have multiplicities two through six, with counts
1,860, 636, 264, 132, and 12 respectively. All 84 target equalities
and all 3,312 singleton AND rows are identified separately in the
complete 6,300-edge incidence list; they are not proposed again.

Among local rows, 216 have k0=0 and right-side coefficient two; 204 have
k0=1 and coefficient three. Sixty other selectors occur in no recorded
triangle and give tautologies. The largest local row contains 232
indicator terms plus its selector, with absolute coefficient sum 235.

The exact row-array digest convention is SHA-256 of
JSON.stringify(the ordered row-key array), without a trailing newline.
The source report itself uses its exact UTF-8 bytes with a trailing
newline and has its own independent artifact hash. No model is
constructed by the extractor.

## Sufficient existing Boolean implications

A candidate capacity may already be an integer consequence of old
constraints. The audit tests every pair of distinct triangles sharing
the candidate edge. Their third selectors are distinct c and d.

It records the first available exact witness in this order:

1. A quota-one original Gram row containing both c and d. It implies
   x_c+x_d<=1.
2. A saved original selector-motif conflict on c,d.
3. A quota-one mixed row at one endpoint of the shared edge, containing
   both corresponding third-vertex edges.
4. A retained core-pair edge clique at one endpoint containing those
   same two edges.

Any witness forbids the two indicators from both being one. If every
pair has a witness, the Boolean indicators form a conflict clique and
their sum is at most one. If y_e=0, the AND upper bounds force all of
them to zero. These two cases prove (1) for Boolean originals.
The result does not give the conditional linear inequality
sum t<=y_e for fractional originals.

There are 6,852 tested pairs across the 2,904 candidate capacities.
The first-witness priority supplies 2,394 quota-one Gram witnesses
and 1,428 quota-one mixed witnesses. The other two witness kinds are
implemented but are not needed for the actual priority-selected
certificates. All pairs are covered for 1,548 candidate rows.

A further 48 candidate edges are the accepted cap-one spectral pairs
with installed forest extensions. For these, each saved third vertex
has the corresponding forest wedge variable z_c. Boolean original
edges force z_c to be their AND. Hence t_abc<=z_c. The installed
aggregate equality and bounds give sum z_c<=x_a,x_b. Together with
the y_ab=0/1 cases this proves their capacities for Boolean originals.
All saved third-vertex wedges and the two aggregate bound rows are
checked against the accepted forest inventory and combined offsets.
These 48 rows are disjoint from the 1,548 just certified.

Thus 1,596 of the 2,904 proposals have a sufficient Boolean implication
certificate. The remaining 1,308 are unresolved by these criteria.
The audit does not claim independence from the complete selector cuts,
path/prism families, signed spectral rows, or other combinations of
parent rows. It preserves every proposal, including the 1,596 integer
consequences, because this audit does not establish continuous
redundancy and makes no model-family selection.

Thirty of the local rows have no more recorded indicators than their
coefficient 2+k0. They follow continuously from the individual
t_tau<=x_a activations. This includes eighteen k0=0 rows and twelve
k0=1 rows. All 420 are preserved in the metadata. Once every side
capacity is supplied, the integral derivation (3)-(5) covers every
local row.

## A small partial diamond shows the missing edge condition

The first two saved triangles are
(0,91,325) and (0,91,479). Their shared side edge is original ID 16,
and their target edges are IDs 25269 and 25351 respectively.
Their signatures are
\[
h_0=\{0,2,6\},\quad h_{91}=\{1,4,10\},\quad
h_{325}=\{5,11,13\},\quad h_{479}=\{11,16,17\}.
\]

Set the five edges of these two triangles to one and all other
original edges to zero; select these four vertices and no others.
The full saved indicator family then has exactly indicators zero and
one equal to one. All AND definitions and all 84 target equations
hold, as do endpoint activations and all individual non-overdraw
checks for the four vertices' mixed quotas and selector Gram quotas.
The selector-motif conflicts are also respected.

The proposed side row is
\[
t_0+t_1\le y_{0,91},
\]
with native key [-1,0,[[556,-1],[71382,1],[71383,1]]].
It rejects this partial diamond because its two sides are two and one.

This is only a partial assignment with nonnegative mixed residuals.
It does not satisfy the full degree, population, or Gram equalities,
and is not a feasible point of the full current model. It therefore
shows precisely why AND and target equations alone do not encode
the side-edge condition; it is not a proof that the row is new to
the complete formulation.

The diamond also violates the required full graph common-neighbor
conditions: adjacent vertices 0 and 91 have two exterior common
neighbors, and vertices 325 and 479 have the three distinct common
neighbors 0, 91, and core site 11.

## Frozen source and authorities

The read-only extractor is
experiments/workspace/root_prism_free_f0_recorded_triangle_capacity_inventory_v8.js,
Git blob a68bba4532f1e4efa41d47cc38865ce8d3d780d5,
SHA-256 3357917e76a94f2c79fdc5a65e00a3413ad1e019c63e4d5ae3400f7978f12699.
Its configuration is
experiments/logs/root-prism-free/f0-recorded-triangle-capacity-configuration01.json,
Git blob ab1f2f6e7daa6aea302a4d6b716f2cf68fb16ec6,
SHA-256 bb11f3e22de3c601bd28c7add7317eea3b7552630c82bf0a13f567fcb5ede1f9.

The configuration binds the exact domain, indicator inventory, literal
zero/clique overlay, forest inventory, both separate literal root
acceptances, and the combined native configuration. In particular:

- Indicator inventory SHA-256
  8606d51ced038b40135fa22bc16d056873b80c16c26d2c34db7e24ac8effd2c7.
- Domain archive SHA-256
  665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4.
- Overlay archive SHA-256
  4f75f8480ac0e73572a19affc9f17df9f54a9b3aefbeef62832c13bffb8fc183.
- Forest inventory SHA-256
  83d0822e59f3ad2f27d6611800b90e2333702118c617bd764156b3683c376515.
- Combined configuration SHA-256
  3fcf3a742a53cf200810aea92cfa594c2ef4623e54aa5679e8afbeda00409059.

The Gram, mixed, and native endpoint meanings are read from the preserved
sources cited in the total-bound note. The retained clique semantics are
confirmed by root_prism_free_f0_boolean_shared_model_v2.py, Git blob
086e30caac2cadd4dd18d332857b6e84f89699b5, SHA-256
062737362b889823c8fd2c068bcdd08feac2737214cc7bbd1f3802ec31ea6c71,
and [root_prism_free_f0_core_pair_edge_cliques.md](root_prism_free_f0_core_pair_edge_cliques.md),
Git blob 74779ad8fb4e2fcafe501fc21d4dce4ffe783752.

The displayed counts come from exact inspection of the existing saved
incidence metadata. The frozen extractor's terminal report, when
produced and reviewed, binds its full tables and row keys. This note
does not claim that the extractor or a later native append has already
been independently accepted. No new eligible-edge or triangle census,
native model construction, optimizer, graph construction, or component
exclusion is part of this work.
