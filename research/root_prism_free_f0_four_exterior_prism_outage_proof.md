# A local four-exterior prism inequality

Work in the project's fixed F0 branch, with its hypothesis that the
completed graph contains no induced triangular prism. The other
eighteen-vertex component and its alignment remain free. All exterior
labels below are literal signature positions; no symmetry of a completed
graph is assumed.

The local proof uses two properties of a hypothetical SRG(99,14,1,2):
every adjacent pair has exactly one common neighbor, and the indicated
mixed core/exterior quotas hold. In fact, the adjacent-pair part of the
proof uses only the upper bound of one common neighbor.

## Statement and notation

Let \(i\) and \(j\) be distinct nonadjacent vertices of the fixed component.
For an exterior signature \(a\), let \(h_a\) be its set of neighbors in
that component. Let \(x_a\) be its Boolean selection indicator and let
\(y_{ab}=y_{ba}\) be the Boolean exterior-edge indicator. Endpoint
activation gives

\[
0\le y_{ab}\le x_a,\qquad y_{ab}\le x_b.
\]

An absent or ineligible exterior edge contributes zero.

Choose distinct exterior signatures \(b,c\) with

\[
i\in h_b,\quad j\notin h_b,\qquad
j\in h_c,\quad i\notin h_c,
\qquad q_{b i}=q_{c j}=1.
\]

The last two conditions are the quota-one mixed equalities

\[
\sum_{a:\ i\in h_a}y_{ab}=x_b,\qquad
\sum_{d:\ j\in h_d}y_{cd}=x_c.
\]

Define

\[
T=\{a:\ i,j\in h_a\},\qquad
L=\sum_{a\in T}y_{ab},\qquad
R=\sum_{d\in T}y_{cd}.
\]

Then every graph embedding in this branch satisfies

\[
\boxed{\ y_{bc}+L+R\le x_b+x_c.\ }
\]

The use of the selector sum on the right retains the cases in which one
or both endpoint signatures are absent.

## Reduction to two chosen side edges

The two mixed equalities and nonnegativity imply

\[
L\le x_b,\qquad R\le x_c.
\]

Since the variables are Boolean, each of \(L\) and \(R\) is either zero
or one. If \(y_{bc}=0\), these bounds already prove the desired inequality.

Suppose instead that \(y_{bc}=1\). Activation forces \(x_b=x_c=1\).
A violation would therefore require \(L=R=1\). There would be a selected
signature \(a\in T\) with \(y_{ab}=1\), and a selected signature \(d\in T\)
with \(y_{cd}=1\).

Membership in \(T\) ensures that neither \(a\) nor \(d\) is \(b\) or \(c\).
Both are adjacent to \(i\) and \(j\). There are two cases.

## Coincident side endpoints

If \(a=d\), the edge \(ab\) has two distinct common neighbors:

- \(i\), because \(i\in h_a\cap h_b\);
- \(c\), because \(ac=dc\) and \(bc\) are both edges.

The core vertex \(i\) and exterior vertex \(c\) are distinct. This
contradicts the adjacent-pair common-neighbor bound. Hence the coincident
case cannot realize \(L=R=y_{bc}=1\).

## Distinct side endpoints

If \(a\ne d\), all six vertices \(i,j,a,b,c,d\) are distinct. They contain
the two triangles

\[
\{i,a,b\}\quad\hbox{and}\quad\{j,c,d\},
\]

and the three matching edges

\[
id,\qquad aj,\qquad bc.
\]

To identify an induced triangular prism, it remains to rule out the
other six cross edges between these triangles.

| Possible cross edge | Reason it is absent |
| --- | --- |
| \(ij\) | The two core sites were chosen nonadjacent. |
| \(ic\) | The premise says \(i\notin h_c\). |
| \(bj\) | The premise says \(j\notin h_b\). |
| \(ad\) | If present, this adjacent pair would have the two common core neighbors \(i\) and \(j\). |
| \(ac\) | If present, the edge \(ab\) would have the two common neighbors \(i\) and \(c\). |
| \(bd\) | If present, the edge \(cd\) would have the two common neighbors \(j\) and \(b\). |

The last three exclusions each use the adjacent-pair parameter one.
Thus the induced graph on the six vertices has exactly the two triangles
and the stated matching between them. It is a triangular prism,
contradicting the branch's global prism-free hypothesis.

Both cases rule out a violation when \(y_{bc}=1\). Together with the
\(y_{bc}=0\) case, this proves the inequality.

## Linear row and scope

Moving the selectors to the left gives the necessary row

\[
y_{bc}+\sum_{a\in T}y_{ab}+\sum_{d\in T}y_{cd}-x_b-x_c\le0.
\]

Its left side is at least \(-2\), since every edge term is nonnegative
and \(x_b+x_c\le2\). Consequently \([-2,0]\) is a valid linear domain.
Terms whose edge variables have separately proved value zero may be
omitted.

The proof is about actual Boolean graph embeddings. A linear inequality
valid for every such embedding is also valid for their convex
combinations. This statement does not assert that the existing linear
relaxation already implies the row.

The existing finite census specification additionally restricts the core
pair to have no common neighbor in the complete fixed 21-vertex core,
including the central triangle. In its notation this is the filter
\(G_{ij}=2\) for a nonadjacent pair. That filter is not needed by the
local proof: the proof above uses nonadjacency of \(i,j\), but never
uses the number of their other common core neighbors.

This is a standalone proof written during the execution outage. It
records the local implication only. It makes no assertion that a finite
census is complete, that an independent native-model replay has run, or
that the F0 branch has been excluded.

## Source context

The statement and premises were checked against the previously reviewed
producer
[root_prism_free_f0_four_exterior_prism_inventory.py](../experiments/workspace/root_prism_free_f0_four_exterior_prism_inventory.py)
and its
[independent source review](../experiments/logs/root-prism-free/f0-four-exterior-prism-inventory-independent-source-review01.json).
Their recorded SHA-256 values are:

- Producer: 774f0f82e6e0773ed49661df7b1ae517fd9680afdc46d883cc684b669c0c663a.
- Review: beaaccbdffce36e4a828d37bce60db988be3a08bf053cda15d3676cf91313e95.

The proof is given in full above and uses no solver output.
