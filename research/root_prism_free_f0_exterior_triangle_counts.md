# Required triangles in the split-shell exterior

This note gives necessary checks for an actual graph in the existing
prism-free, F-free split18+18 branch. The first component incidence H
is fixed; the second incidence and its relative fiber alignment remain
free. No exterior graph has been found or tested here.

Let D be the adjacency on the sixty exterior vertices. It is
eight-regular. Every exterior vertex v has three neighbors in each
eighteen-vertex component and no neighbor in the central triangle.
Let k0(v) and k2(v) be the numbers of edges induced by its two
component-neighbor triples. Let t_D(v) be the number of triangles of
D containing v.

Then
\[
 k0(v),k2(v)\in\{0,1\},\qquad
 t_D(v)=1+k0(v)+k2(v).
 \tag{1}
\]
In particular, using only the known first incidence,
\[
 1+k0(v)\le t_D(v)\le2+k0(v).
 \tag{2}
\]
Every exterior vertex therefore belongs to at least one exterior
triangle, and to at most three. This is compatible with global
prism-freeness: exterior triangles themselves are allowed.

## Local proof

Since the full graph has lambda=1, the graph induced by the fourteen
neighbors of any vertex is exactly a matching of seven edges. Its
vertices split into the two component triples and eight D-neighbors.

Each component triple induces at most one matching edge, proving
k_i in {0,1}. The components are anticomplete. After its k_i internal
matching edges are used, exactly 3-2k_i vertices of that triple must
be matched to D-neighbors.

Thus exactly 6-2k0-2k2 of the eight D-neighbors are matched to core
neighbors. The remaining 2+2k0+2k2 D-neighbors pair among themselves.
Each such matching edge forms one D-triangle through v. Dividing
by two proves (1).

This proof needs the full lambda=1 equality, not just an upper cap
on common neighbors. A partial exterior relaxation satisfying only
degree and mixed equations need not satisfy (1).

## The total is exactly thirty-two

A shell component has nine internal-fiber matching edges and eighteen
cross-fiber edges. A shell triangle would have one vertex in each
fiber: two vertices in one fiber cannot have a common neighbor in
another fiber because each cross interface is a matching. Such a
three-fiber triangle, together with the central triangle and their
three matching edges, would be an induced triangular prism.
Consequently both shell components are triangle-free in this branch.

An internal-fiber edge already has its unique common neighbor in
the central triangle and has no exterior common neighbor. A
cross-fiber edge has no central common neighbor, no common neighbor
in its own triangle-free component, and none in the anticomplete
other component. Its unique common neighbor must lie in D.

Counting component edges inside the sixty neighbor triples gives
\[
 \sum_v k0(v)=18,\qquad \sum_v k2(v)=18.
 \tag{3}
\]
Summing (1) and dividing by three gives
\[
 \#\{\text{triangles in }D\}
 =\frac{60+18+18}{3}=32,\qquad
 \operatorname{tr}(D^3)=192.
 \tag{4}
\]
No D-edge belongs to two D-triangles, again by lambda=1. Therefore
exactly96 of D's240 edges lie in its32 triangles; the other144
D-edges lie in none.

As a scope check, if the same split-shell structure were considered
without prism-freeness, a component triangle would consume the
unique common neighbor of three cross-fiber edges. The same counting
would give T_D+T_C0+T_C2=32, not necessarily T_D=32. The triangle-free
hypothesis is used exactly at this point.

## Exact future candidate checks

For a complete simple exterior D,
\[
 t_D(v)=\frac12(D^3)_{vv}.
\]
The known quantity k0(v) is the number of edges of the fixed
eighteen-vertex core inside the selected triple h_v. It can be
computed directly from the three sites without choosing H2.

A future candidate may therefore be rejected by one explicit vertex
violating (2), or by the global triangle total (4). These conclusions
exclude that candidate, not every first incidence or the whole branch.

On the padded480-signature Boolean model, let x_a be selection and
y_ab actual exterior adjacency. The necessary cubic inequalities are
\[
 (1+k0(a))x_a
 \le \sum_{b<c,\ b,c\ne a} y_{ab}y_{ac}y_{bc}
 \le (2+k0(a))x_a.
\]
The global sum over a<b<c equals32. Missing original edge variables
are zero. Edge activation makes all terms vanish when x_a=0.
This is a valid polynomial statement; no triangle-variable
linearization or model change is made here.

If a counts vertices whose two component triples both contain an
edge, then
\[
 n_{00}=24+a,\quad n_{10}=n_{01}=18-a,\quad n_{11}=a,
 \qquad 0\le a\le18.
\]
The numbers of vertices lying in one, two, and three D-triangles are
respectively 24+a,36-2a,a. These are consistency consequences of
(1)-(4), not additional independent equations.

## Relation to existing work and bindings

The split-shell structure, three neighbors per component, and
one-neighbor-per-fiber component structure are proved in
research/root_prism_free_f0_components.md, Git blob
e9ba184ee254130652c252b981487266ad078c15.

The degree-eight and first-incidence mixed equations are recorded in
research/root_prism_free_f0_first_design_exterior.md, Git blob
6757de8df7ffbeccada3b7f0590487d7036c1b1a. Those equations alone do
not supply the full neighborhood matching used above.

The characteristic third-moment calculation independently agrees
with (4); see research/root_prism_free_f0_spectral_gap_pair_minor.md,
SHA256 169a4b0c8ba1381302d0eeacb449599a5e4913cd6a55a24bb711e5d4126829ce,
Git blob168ca05d66609a2ac7027d3958a4f22c63385e1c.

No equitable partition, automorphism, equality of the two components,
or fixed relative fiber alignment is asserted. No numerical census,
candidate inspection, optimizer call, or graph-existence conclusion
is part of this note.
