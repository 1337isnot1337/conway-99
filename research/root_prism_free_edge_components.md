# Edge partitions and an exact order-ten count

There is an exact connection between the rooted matching partition and
ordinary core coordinate 521 in the order-ten count system. It gives the
unconditional inequality

\[
3x_1+2x_{521}\le 4158, \tag{1}
\]

where `x1` is the number of induced triangular prisms. In a globally
prism-free graph, the exact identity is

\[
x_{521}=e_{24}+3e_{222}. \tag{2}
\]

Here `e_lambda` counts undirected edges with matching partition `lambda`.
Equation (2) can connect a new global choice of root edge to a count face.
It does not exclude any graph by itself. The existing repaired prism-zero
count point has `x521=133`, so it satisfies (1).

## 1. The matching partition belongs to an undirected edge

Let `r,a` be adjacent vertices in a hypothetical SRG(99,14,1,2), and let
`p` be their unique common neighbor. Put

\[
X=N(r)\setminus\{a,p\},\qquad
Y=N(a)\setminus\{r,p\}.
\]

Both sets have twelve vertices. The graph induced by a vertex's
neighborhood is seven disjoint edges, so `X` and `Y` each induce a perfect
matching. They are disjoint because `p` is the only common neighbor of
`r,a`.

For `x` in `X`, the pair `a,x` is nonadjacent. Its two common neighbors
are `r` and exactly one vertex of `Y`. The second neighbor cannot be `p`:
inside `N(r)`, the point `p` is matched to `a`. Applying the same argument
from `Y` shows that the `X`–`Y` interface is a perfect matching.

Identify the two twelve-point sets using this cross matching. Their
internal matchings become two perfect matchings `M,P` on the same twelve
labels. The union of two matchings decomposes into alternating components;
a common edge is counted as an alternating two-cycle. Write their lengths
as `2 lambda_1,...,2 lambda_k`. Then `lambda` is a partition of six.

In the actual induced graph on `X` and `Y`, each component has length
`4 lambda_i`: internal and cross edges alternate, and the internal edges
alternate between the two sides. Exchanging `r,a` exchanges `M,P` and
preserves this partition. Thus it is meaningful to write `lambda(e)` for
an **undirected** edge `e`; no orientation or graph automorphism is needed.

The matching audit exhausts all 10,395 perfect matchings on twelve labels
against a fixed reference matching. It verifies the component lengths and
endpoint reversal for every matching. It recovers the eleven partitions
used by the complete rooted search.

## 2. The ten-vertex motif

A part `lambda_i=2` gives an eight-cycle in `X` and `Y`. Adjoin `r,a` to
that component. The resulting induced graph `F` has ten vertices and
seventeen edges:

- the edge `ra`;
- four edges from `r` to the `X` vertices and four from `a` to the `Y` vertices;
- the eight edges of the shell cycle.

The shell colors around the cycle are `XXYYXXYY`. The two centers have
degree five in `F`, and all eight shell vertices have degree three.
Consequently the two centers, and their joining edge, are intrinsic to
each copy of `F`.

Conversely, consider any induced copy of `F` in the SRG. Its two centers
determine an adjacent pair `r,a`; its shell vertices belong to the sets
`X,Y` defined above. Each shell vertex already has its unique internal
mate and its unique cross neighbor inside the copy. The eight-cycle
therefore is a whole component of the induced graph on `X` and `Y`.
It cannot be part of a longer component.

This proves a bijection between induced copies of `F` and pairs consisting
of an undirected edge and a part of size two in its matching partition.
If `m_j(lambda)` denotes the number of parts of size `j`, then

\[
N_{\mathrm{ind}}(F)=\sum_{e\in E(G)}m_2(\lambda(e)). \tag{3}
\]

### Ordinary embeddings have no extra edges

Every possible extra edge of `F` violates the SRG upper cap
`(A^2+A)[u,v] <= 2`. The 28 missing edges have three forms.

An edge from a center to the opposite fiber gives an existing
center–shell edge a second common neighbor. An additional edge inside
one fiber does the same. An extra cross edge `x_i y_j`, with `j != i`,
gives the nonadjacent pair `a,x_i` the three common neighbors
`r,y_i,y_j`. Thus an ordinary embedding of `F` in the SRG is necessarily
induced. The executable certificate records an explicit violated pair
for each of the 28 possible extra edges; adding further edges cannot
repair an upper-cap violation.

The two centers are the only degree-five vertices, and the shell is a
cycle of length eight. Every automorphism is therefore among the two
center permutations and sixteen dihedral shell maps. Exactly eight of
these 32 candidates preserve the full graph. Hence

\[
|\operatorname{Aut}(F)|=8,
\qquad
\#\operatorname{Inj}(F,G)=8N_{\mathrm{ind}}(F). \tag{4}
\]

The factor eight converts labeled ordinary embeddings into unlabeled
copies. There is no factor two for orienting the central edge in (3).

## 3. Exact count-coordinate identification

The small order-ten preparation table identifies `F` as catalogue type
48,936 and ordinary core coordinate 521. Its stored adjacency bit rows
are

```text
560, 336, 416, 704, 515, 261, 266, 524, 614, 409
```

The certificate checks an explicit isomorphism from the direct cycle
construction to those rows, including every adjacency and nonadjacency.
The independent one-row extraction from the existing reduction checks

\[
\begin{aligned}
\texttt{cores[520]}&=48936,\\
\texttt{inj[48936]}&=8e_{521},\\
\texttt{induced[48936]}&=3{,}628{,}800e_{521}.
\end{aligned}
\]

The last line uses the reduction's exact scale `3,628,800`. Therefore
both the ordinary unlabeled count and the induced unlabeled count of
`F` are exactly `x521` in the 550-coordinate system. The labeled ordinary
embedding count is `8*x521`.

The extraction is saved in
`experiments/logs/moments-and-counts/root-prism-free-edge-component-row.json`.
It binds the reduction cache hash and its extracting source. The small
replay checks this binding and every exported coefficient; it does not
reload the large reduction. The graph-theoretic equality of ordinary and
induced counts also follows directly from the 28 chord witnesses above.

## 4. The count identities and bounds

A part of size one gives a triangular prism. Each prism is counted at
exactly its three edges joining its two triangles. Thus, with `P=x1`,

\[
\sum_e m_1(\lambda(e))=3P. \tag{5}
\]

For every partition of six,

\[
m_1(\lambda)+2m_2(\lambda)\le 6.
\]

There are `99*14/2=693` undirected edges. Summing and applying (3) and
(5) proves (1). In particular, the unconditional upper bound is
`x521 <= 2079`. The previous generic embedding bound for this coordinate
was 19,404. The exact nonnegative row in ordinary-core coordinates is

```text
4158*x0 - 3*x1 - 2*x521 >= 0,   x0 = 1.
```

Global prism-freeness removes every part of size one. The four remaining
partitions and their contributions to (3) are:

| Edge partition | Number of reference-labeled matchings | Shell cycle lengths | Contribution to `x521` |
| --- | ---: | --- | ---: |
| `222` | 120 | `8+8+8` | 3 |
| `24` | 1,440 | `8+16` | 1 |
| `33` | 640 | `12+12` | 0 |
| `6` | 3,840 | `24` | 0 |

This proves (2), with `e222+e24+e33+e6=693`.

## 5. A new global minimum-edge convention

For a globally prism-free graph, choose an edge whose partition is
earliest in the order `222 < 24 < 33 < 6`, and use its endpoints as the
root and near anchor. This is a choice of labels, not an assumption that
the graph has an automorphism. Every globally prism-free graph has a
representative under this new four-case convention.

| Globally minimum edge type | Consequence | Exact count restriction |
| --- | --- | --- |
| `222` | At least one edge has type `222`. | `3 <= x521 <= 2079` |
| `24` | No edge has type `222`; at least one has type `24`. | `1 <= x521 <= 693` |
| `33` | No edge has type `222` or `24`. | `x521 = 0` |
| `6` | Every edge has type `6`. | `x521 = 0` |

The earlier minimum-anchor convention in
[`root_prism_free_anchor_min.md`](root_prism_free_anchor_min.md) minimizes
only over the fourteen edges incident with a fixed root. It does not
justify the zero face in the last two rows. The completed root SAT
formulas and their outcome tables are unchanged by this note.

The repaired prism-zero order-ten point has `x521=133`. It passes (1)
and the unconditional upper bound, but does not lie on `x521=0`.
This is only a fact about that one count-relaxation point. No feasibility
or infeasibility result for the new zero face is claimed here.

## 6. Exact controls and replay

The audit checks the endpoint reversal and shell partition for all
10,395 matchings. For each of the eleven canonical partitions, it also
enumerates all 495 four-subsets of `X`, takes their cross-matched `Y`
vertices, and tests the resulting ten-vertex graph for isomorphism to
`F`. These directly enumerated copies equal the eight-cycle components.

The same independent four-subset enumeration runs on every root edge
of the four matching-complete partial controls in
[`root_prism_free_structure.md`](root_prism_free_structure.md). It finds
42, 14, 0, and 0 distinct copies whose central edge is incident with the
root for types `222,24,33,6`, respectively. Every root/near endpoint has
its full degree fourteen in these controls, and every visible upper cap
passes. The exterior vertices have only five known neighbors, so these
controls are not complete SRGs.

Replay uses the standard library and takes about three seconds:

```bash
.venv/bin/python experiments/workspace/root_prism_free_edge_components.py
```

Files:

- `experiments/workspace/root_prism_free_edge_components.py`
- `experiments/logs/root-prism-free/edge-components-certificate.json`
- `experiments/logs/root-prism-free/edge-components-generation.log`
- `experiments/logs/root-prism-free/edge-components-replay.log`
- the separate one-row extraction identified in Section 3.

No solver is called. No dense cache is loaded by this replay. No existing
search formula or count-loop model receives a new constraint from this
package.
