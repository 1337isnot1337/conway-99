# The must-triangle total is already bounded by eighteen

The proposed inequality
\[
\sum_{e\in E_*}y_e\le32
\]
for the 84 live spectral must-triangle edges is redundant. The existing
selector Gram equations and endpoint activations already imply the
stronger inequality
\[
\boxed{\sum_{e\in E_*}y_e\le18.}
\tag{1}
\]
This is an exact continuous linear implication. It does not require the
triangle indicators, the mixed exterior equations, integrality, or a
solver result. Eighteen is a proved upper bound here; optimality is not
claimed.

The separate graph-theoretic statement that an actual exterior has
exactly 32 triangles is valid in the stated globally prism-free,
F-free split18+18 branch. It does not make the proposed total constraint
a strengthening of the current relaxation.

## The exact exterior triangle count and its premises

Fix the central triangle of an actual SRG(99,14,1,2). Its shell has
36 vertices in three twelve-vertex fibers. The branch considered here
has two anticomplete eighteen-vertex shell components, C0 and C1.
The remaining 60 vertices form the exterior D. Every exterior vertex
has three neighbors in each component and eight in D.

These are the split-shell premises proved in
[root_prism_free_f0_components.md](root_prism_free_f0_components.md).
F-freeness participates in the earlier restriction of possible component
sizes; it is not an additional step in the triangle count once the
split and its incidence counts are fixed. The two components need not
be isomorphic, and their relative fiber alignment is not fixed.

Let k_i(v) be the number of edges inside the three neighbors of v in
Ci. Since lambda=1, the graph induced on the fourteen neighbors of any
vertex of the full graph is a matching of seven edges. Therefore
k_i(v) is either zero or one. The two component triples use
k_0(v)+k_1(v) matching edges internally, and there are no matching edges
between the two components. Their unmatched vertices must be paired
with D-neighbors. The remaining D-neighbors pair among themselves, giving
\[
t_D(v)=1+k_0(v)+k_1(v).
\tag{2}
\]
This uses the equality lambda=1 in a completed graph. Upper bounds on
common neighbors and the existing degree/mixed relaxation alone do not
supply the matching.

Each component has nine internal-fiber edges and eighteen cross-fiber
edges. A component triangle would use one vertex in each fiber and,
together with the central triangle, induce a triangular prism. Hence
global prism-freeness makes both components triangle-free.
An internal-fiber edge already has its unique common neighbor in the
central triangle. A cross-fiber edge has no common neighbor there, in
either component, or across the anticomplete components. Its unique
common neighbor therefore lies in D. It follows that
\[
\sum_{v\in D} k_0(v)=18,\qquad
\sum_{v\in D} k_1(v)=18.
\]
Summing (2) gives
\[
3T_D=60+18+18=96,\qquad T_D=32.
\tag{3}
\]
Because lambda=1, no exterior edge belongs to two exterior triangles.
Exactly 96 of the 240 exterior edges lie in these triangles.

The same split-shell count without the triangle-free premise gives
T_D+T_{C0}+T_{C1}=32. Thus exact equality T_D=32 must not be asserted
from a split alone. The full existing proof is
[root_prism_free_f0_exterior_triangle_counts.md](root_prism_free_f0_exterior_triangle_counts.md).

## What the existing 5,364 indicators count

The accepted support inventory contains 84 live targets and 5,364
distinct support triangles. It also contains exactly 5,364 target-to-
triangle incidences. Every triangle has at least one recorded target
origin, so equality of these two counts means that every recorded
triangle has exactly one target origin. Direct inspection of the saved
inventory confirms that all 5,364 origin lists have length one.

Write t_tau for the Boolean AND of the three exterior edges of the
recorded triangle tau. The existing 84 target equations are
\[
\sum_{\tau\text{ assigned to }e}t_\tau=y_e.
\]
Summing them yields the exact linear identity
\[
\sum_{\tau\in\mathcal T_*}t_\tau=\sum_{e\in E_*}y_e.
\tag{4}
\]
The rows remain an identity when the variables are relaxed to real
numbers. In an actual graph, the distinct indicators count a subset
of D's triangles, so (3) would give a necessary upper bound of 32.
The stronger upper bound of 18 in (1) already follows below.

Consequently any actual completion would have at least fourteen
exterior triangles outside this recorded family. This observation adds
no row to the current model and does not assert completeness of the
recorded family among all exterior triangles.

## The original core Gram identity

Let h_a be signature a in the fixed 480-signature domain, and define
\[
k_0(a)=\sum_{\{i,j\}\in E(C0)}
 {\bf1}_{i,j\in h_a}.
\]
Let B be the fixed adjacency of the central triangle and C0, with the
18 component sites occupying B indices 3 through 20. The original
selector equation for i<=j is
\[
\sum_{a:\ i,j\in h_a}x_a
=12{\bf1}_{i=j}+2-|N_B(i+3)\cap N_B(j+3)|
 -B_{i+3,j+3}.
\tag{5}
\]
These are the original equations checked and installed by
root_prism_free_f0_direct_literal_model.py, not new incidence assumptions.

For the 27 edges of C0, the nine internal-fiber equations have quota
zero and empty support. The other eighteen have quota one. Their sum is
\[
\sum_{a=0}^{479} k_0(a)x_a=18.
\tag{6}
\]
The saved domain has 204 signatures with k0=1 and 276 with k0=0.
Every one of the 84 signatures incident with E_* has k0=1. Therefore,
for nonnegative selectors,
\[
\sum_{a\in V_*}x_a\le18.
\tag{7}
\]

The eighteen nonempty equations used in (6) are listed below. Original
IDs use the original lexicographic i<=j order; native row IDs are
zero-based in the preserved direct-literal prefix. The final column is
the number of selector terms. Every displayed right side is one.

| Core sites | Original equation | Native row | Terms |
| --- | ---: | ---: | ---: |
| 0, 6 | 6 | 4445 | 11 |
| 0, 12 | 12 | 4450 | 11 |
| 1, 7 | 24 | 4460 | 11 |
| 1, 13 | 30 | 4465 | 11 |
| 2, 8 | 41 | 4475 | 11 |
| 2, 14 | 47 | 4480 | 11 |
| 3, 9 | 57 | 4488 | 11 |
| 3, 15 | 63 | 4493 | 11 |
| 4, 10 | 72 | 4501 | 11 |
| 4, 16 | 78 | 4506 | 11 |
| 5, 11 | 86 | 4512 | 11 |
| 5, 17 | 92 | 4517 | 11 |
| 6, 13 | 100 | 4524 | 12 |
| 7, 12 | 110 | 4533 | 12 |
| 8, 15 | 123 | 4546 | 12 |
| 9, 14 | 131 | 4553 | 12 |
| 10, 17 | 142 | 4564 | 12 |
| 11, 16 | 148 | 4570 | 12 |

The zero-quota core edges are
(0,1), (2,3), (4,5), (6,8), (7,10), (9,11), (12,14), (13,16),
and (15,17). They occur in no retained signature.

## An endpoint certificate with each selector used once

The target graph E_* has 84 vertices and 84 edges, in two connected
components of 42 vertices and 42 edges. Each component has one cycle,
of length eighteen. Its degree histogram is twelve degree-one,
sixty degree-two, and twelve degree-three vertices.

Orient each cycle cyclically and every edge of an attached tree toward
the cycle. Every vertex is then the tail of exactly one edge. For every
oriented target edge a->b, the original endpoint row gives
y_ab<=x_a. Sum these 84 rows:
\[
\sum_{e\in E_*}y_e\le\sum_{a\in V_*}x_a\le18.
\]
The explicit orientation below makes the argument checkable without
relying on the component summary. Each edge ID occurs once, each tail
occurs once, and the tail set is exactly V_*.

An exact nonnegative slack certificate is
\[
18-\sum_{e\in E_*}y_e
 =
\sum_{a\to b\in E_*}(x_a-y_{ab})
 +\sum_{a\notin V_*}k_0(a)x_a.
\tag{8}
\]
Equation (6) supplies the equality. Each term on the right is already
nonnegative in the old continuous relaxation. The last sum has 120
nonzero selector coefficients.

The two directed cycles are
\[
(8,73,35,104,33,109,19,96,285,306,278,327,202,155,236,176,217,177)
\]
and
\[
(12,77,42,136,65,126,23,100,270,333,295,323,206,159,245,198,249,165).
\]
The last entry in each cycle points back to the first.

An edge's native variable is 540+edge_id. Its endpoint rows are
17162+2*edge_id and the next row, for the smaller and larger endpoint
respectively. The final column below identifies the unique C0 edge
inside the tail signature; it can be checked directly against the
bound domain. Native row messages are preserved by the later model
extensions.

| Edge ID | Tail | Head | Endpoint row | Tail's core edge |
| ---: | ---: | ---: | ---: | --- |
| 193 | 0 | 390 | 17548 | 0, 6 |
| 471 | 1 | 445 | 18104 | 2, 8 |
| 1385 | 4 | 337 | 19932 | 0, 12 |
| 1675 | 5 | 405 | 20512 | 2, 14 |
| 2409 | 8 | 73 | 21980 | 0, 6 |
| 2817 | 9 | 177 | 22796 | 3, 9 |
| 3650 | 12 | 77 | 24462 | 0, 12 |
| 4042 | 13 | 165 | 25246 | 3, 15 |
| 4917 | 16 | 109 | 26996 | 0, 6 |
| 5858 | 19 | 96 | 28878 | 4, 10 |
| 6155 | 20 | 126 | 29472 | 0, 12 |
| 7084 | 23 | 100 | 31330 | 4, 16 |
| 9990 | 33 | 109 | 37142 | 0, 6 |
| 10554 | 35 | 104 | 38270 | 0, 6 |
| 11025 | 37 | 88 | 39212 | 0, 6 |
| 12449 | 42 | 136 | 42060 | 0, 12 |
| 15559 | 54 | 92 | 48280 | 0, 12 |
| 18563 | 65 | 126 | 54288 | 0, 12 |
| 10523 | 72 | 35 | 38209 | 1, 7 |
| 10524 | 73 | 35 | 38211 | 2, 8 |
| 12391 | 76 | 42 | 41945 | 1, 13 |
| 12392 | 77 | 42 | 41947 | 2, 14 |
| 24553 | 88 | 360 | 66268 | 1, 7 |
| 25351 | 91 | 479 | 67864 | 4, 10 |
| 25474 | 92 | 336 | 68110 | 1, 13 |
| 26276 | 95 | 455 | 69714 | 4, 16 |
| 26389 | 96 | 285 | 69940 | 1, 7 |
| 27146 | 99 | 285 | 71454 | 5, 11 |
| 27345 | 100 | 270 | 71852 | 1, 13 |
| 28097 | 103 | 270 | 73356 | 5, 17 |
| 9985 | 104 | 33 | 37133 | 1, 7 |
| 30 | 107 | 0 | 17223 | 1, 7 |
| 5871 | 109 | 19 | 28905 | 1, 7 |
| 1241 | 114 | 4 | 19645 | 1, 13 |
| 7107 | 126 | 23 | 31377 | 1, 13 |
| 18571 | 136 | 65 | 54305 | 1, 13 |
| 38681 | 154 | 236 | 94524 | 2, 8 |
| 38887 | 155 | 236 | 94936 | 5, 11 |
| 39516 | 158 | 245 | 96194 | 2, 14 |
| 39720 | 159 | 245 | 96602 | 5, 17 |
| 3731 | 165 | 12 | 24625 | 2, 14 |
| 42814 | 176 | 217 | 102790 | 2, 8 |
| 2499 | 177 | 8 | 22161 | 2, 8 |
| 43509 | 180 | 210 | 104180 | 2, 8 |
| 45135 | 189 | 214 | 107432 | 2, 14 |
| 46815 | 198 | 249 | 110792 | 2, 14 |
| 38864 | 202 | 155 | 94891 | 3, 9 |
| 47704 | 203 | 327 | 112570 | 4, 10 |
| 39694 | 206 | 159 | 96551 | 3, 15 |
| 48358 | 207 | 323 | 113878 | 4, 16 |
| 48938 | 210 | 427 | 115038 | 3, 9 |
| 49076 | 211 | 467 | 115314 | 5, 11 |
| 49535 | 214 | 404 | 116232 | 3, 15 |
| 49682 | 215 | 454 | 116526 | 5, 17 |
| 43001 | 217 | 177 | 103165 | 3, 9 |
| 1564 | 222 | 5 | 20291 | 3, 15 |
| 363 | 233 | 1 | 17889 | 3, 9 |
| 42831 | 236 | 176 | 102825 | 3, 9 |
| 46811 | 245 | 198 | 110785 | 3, 15 |
| 40802 | 249 | 165 | 98767 | 3, 15 |
| 56904 | 270 | 333 | 130970 | 4, 16 |
| 57869 | 278 | 327 | 132900 | 4, 10 |
| 49611 | 283 | 215 | 116385 | 4, 16 |
| 58653 | 285 | 306 | 134468 | 4, 10 |
| 48996 | 287 | 211 | 115155 | 4, 10 |
| 59873 | 295 | 323 | 136908 | 4, 16 |
| 57851 | 306 | 278 | 132865 | 5, 11 |
| 26195 | 311 | 95 | 69553 | 5, 17 |
| 48205 | 323 | 206 | 113573 | 5, 17 |
| 25269 | 325 | 91 | 67701 | 5, 11 |
| 47548 | 327 | 202 | 112259 | 5, 11 |
| 59882 | 333 | 295 | 136927 | 5, 17 |
| 21635 | 336 | 76 | 60433 | 7, 12 |
| 6306 | 337 | 20 | 29775 | 6, 13 |
| 20650 | 360 | 72 | 58463 | 6, 13 |
| 5101 | 390 | 16 | 27365 | 7, 12 |
| 4181 | 404 | 13 | 25525 | 9, 14 |
| 39624 | 405 | 158 | 96411 | 8, 15 |
| 2962 | 427 | 9 | 23087 | 8, 15 |
| 38813 | 445 | 154 | 94789 | 9, 14 |
| 28202 | 454 | 103 | 73567 | 11, 16 |
| 48450 | 455 | 207 | 114063 | 10, 17 |
| 27249 | 467 | 99 | 71661 | 10, 17 |
| 47805 | 479 | 203 | 112773 | 11, 16 |

The canonical JSON list of [edge_id,tail,head,core_i,core_j], in
ascending tail order as above, has SHA-256
42efb9f4a1fbca4160c8c8fd8052d726356ef134386bcdd4f17c20095aef57df.
The endpoint-row column is derived by the stated formula and is not
part of that digest.

## Immutable inputs and scope of the check

The exact input records are:

- Domain: experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz,
  Git blob 99d66387b71a752c39828c9a5f10b5103354db42,
  compressed SHA-256
  665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4,
  raw SHA-256
  fa3bd2e5bb541d58cb647aa1d3df95a9d3c17e394836a657ad4f4bf6eb5f6bfe.
- Target/support ledger: experiments/logs/root-prism-free/f0-spectral-triangle-support-ledger01.json,
  Git blob 7a516562bbdbe26c8bc25c0d7eb1654a6efd79d2,
  SHA-256 0103baa3822afaae8992e2be6517e6a173615a937a721e3e5a83c724cdc89e86.
- Indicator inventory: experiments/logs/root-prism-free/f0-spectral-triangle-support-indicator-inventory01.json,
  Git blob 8188edc640d4dd896df0e64c4e08db4c78627e96,
  SHA-256 8606d51ced038b40135fa22bc16d056873b80c16c26d2c34db7e24ac8effd2c7.
- Complete separate literal-support replay:
  experiments/logs/root-prism-free/f0-spectral-triangle-support-independent-literal-replay01.json,
  Git blob 06bfec7ae8e9817e58fc885f7611364daaebecb4,
  SHA-256 52c75dea2f4ef93fb7881eb76e1e02f7b652058ecc2a6a02248bcdbdae05faeb;
  root acceptance SHA-256
  9d4e3a9b44a2140d95091425a346396ed84dd8d9d88f3a4e7fa3e67d47cd51d4.
- Original selector source: experiments/workspace/root_prism_free_f0_direct_literal_model.py,
  Git blob 3c5e9c810af89818a6da0417e1bdb9a878f896c3,
  SHA-256 b500336db29820777afb59076384a48382fa54453fce5b232a072719893cea40.
  Its checked_original_equations and derive functions supply (5) and
  the native Gram row map.
- Endpoint source: experiments/workspace/root_prism_free_f0_boolean_shared_model.py,
  Git blob 3a43d37f39ffe81bec2ab01db21f00a63eb96b70,
  SHA-256 5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2.
  Its expected_base function installs both endpoint inequalities for
  every original eligible edge.
- Existing triangle-count proof:
  research/root_prism_free_f0_exterior_triangle_counts.md,
  Git blob 83580252626b2951069ac5f618c0462ac8a42e9e,
  SHA-256 b03e2c0f3cc97b499bafebc25b6f11f733e71d91025adf15fa200ba45dd3329b.
- Existing split-shell proof:
  research/root_prism_free_f0_components.md,
  Git blob e9ba184ee254130652c252b981487266ad078c15,
  SHA-256 a2172ef9b0d6c3d8a86eaac3d7db2014708fbe6ba0f91b572e5e07d53c110667.

Only saved graph/incidence metadata and small exact integer sums were
inspected. The 84-edge orientation, all 84 tail signatures, the 27
core-edge quotas, the 18 native Gram indices, and the coefficient
identity in (8) were checked directly. No support census, native model
construction, optimizer, or new graph search ran. No constraint was
added, deleted, or replaced. This result is a redundancy certificate
within the fixed component-zero formulation, not an exclusion of the
component or a resolution of the SRG existence problem.
