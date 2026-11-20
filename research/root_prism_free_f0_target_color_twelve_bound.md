# A twelve-edge bound from the fixed target graph

Let E_* be the 84 live spectral must-triangle target edges in the accepted
indicator inventory. Their Boolean edge variables satisfy
\[
\boxed{\sum_{e\in E_*}y_e\le12.}
\tag{1}
\]
The argument uses twelve original quota-one selector Gram equations,
the existing endpoint activations, and the fixed combinatorial structure
of this 84-edge target graph. It does not use a solver, the unknown second
component, or any new triangle-domain enumeration.

The value twelve is attained in the relaxation on the 84 target vertices
containing only at-most-one inequalities for the eighteen colors and
endpoint activations. That attaining
assignment is not a feasible point of the full current model. The bound
is an integer consequence of original constraints; no independence from
the complete model is claimed.

The finite structural facts below are the obligations of the frozen
checker. This note supplies their general implication. Until that checker
has passed and its output is independently accepted, the literal
certificate and proposed native row remain preparation.

## Colors inherited from original Gram equations

Every target-incident signature h_a contains exactly one edge of the
fixed component C0. Call that core edge its color. The original Gram
equation for each of these eighteen colors is
\[
\sum_{a:\ i,j\in h_a}x_a=1.
\tag{2}
\]
It follows that at most one target vertex of each color can be selected.
Signatures outside the target graph are still present in (2); discarding
their nonnegative contributions only weakens the restriction.

The original site labels put the first six-vertex fiber at sites
0 through 5. Divide target vertices into:

- private vertices P, whose color has one endpoint in that first fiber
  and the other in either of the other fibers;
- shared vertices S, whose color joins the other two fibers.

The fixed target graph has 72 private vertices, divided into twelve
colors of six vertices each, and twelve shared vertices, divided into
six colors of two vertices each. Therefore
\[
|P\cap X|\le12
\tag{3}
\]
for every Boolean selected set X. This upper bound uses only the twelve
private-color equations, not the six shared-color equations.

The names private and shared describe this graph decomposition only.
They impose no automorphism on an exterior graph or equality of the two
unknown component incidences.

## Structural conditions that imply the bound

Take the private subgraph induced on P. Designate its twelve vertices
of private degree three as centers C. Call a private vertex exposed if
it has a neighbor in S.

The certificate checks every one of the following conditions on the
complete fixed target graph:

1. There is no edge between two shared vertices.
2. No two centers are adjacent.
3. Every noncenter private vertex has private neighbors of at most one
   private color.
4. Each private vertex has at most one shared neighbor.
5. Centers have no shared neighbor.
6. Each center has at most one exposed private neighbor.
7. No private edge has two exposed endpoints.

The certificate retains every vertex's complete private and shared
neighbor lists, its color, and its center/exposed flags. It also checks
the two 42-vertex, 42-edge components, all eighteen color supports and
the corresponding original Gram quotas. These component counts are
additional exact metadata; the argument below needs the seven local
conditions.

Condition 3 and the color quotas imply that any selected noncenter has
degree at most one in the selected private graph. Conditions 2 and 3
then imply that each connected component of the selected private graph
is a star with one center, an edge between two noncenters, or a singleton.
In particular, it is a tree.

A selected star has at most one exposed vertex: its center is unexposed
by condition 5, and it has at most one exposed leaf by condition 6.
An edge between two noncenters has at most one exposed endpoint by
condition 7. A singleton has at most one exposed vertex. Condition 4
then makes the number of available shared attachment edges at most
one for every selected private component.

If K is such a component, it has |K|-1 internal edges and at most one
edge to a selected shared vertex. Charge those edges to K:
\[
e(K)+e(K,S\cap X)\le |K|.
\]
A shared vertex may join different private components; every such edge
is charged to its private endpoint's component, so this does not change
the sum. Condition 1 rules out uncharged shared-shared edges. Thus
\[
e(E_*[X])\le |P\cap X|\le12.
\tag{4}
\]
Endpoint activations ensure that every target edge with y_e=1 lies in
E_*[X]. Removing any such edge can only decrease the left side, so
(4) proves (1).

The attachment-edge condition is essential. One exposed private vertex
could otherwise have two selected shared neighbors. The checker
therefore verifies both the per-component exposed-vertex conditions
and the at-most-one-shared-neighbor condition explicitly.

## Exactness for the at-most-one-color relaxation

The proposed attaining selected set consists of twelve private vertices
\[
\{35,72,73,202,203,327\}
\quad\text{and}\quad
\{42,76,77,206,207,323\},
\]
and four shared vertices
\[
\{360,479,336,455\}.
\]

The intended twelve edges are the four paths
\[
360-72-35-73,\qquad
479-203-327-202,
\]
\[
336-76-42-77,\qquad
455-207-323-206.
\]
Every private color occurs once, and the four shared colors are distinct.
The checker verifies all sixteen labels, every actual edge ID, all
eighteen at-most-one color inequalities, and the complete induced target-edge count of
twelve. Set those twelve target edges to one and the other target edges
to zero. This attains (1) in the restricted at-most-one-color/activation
relaxation. Shared colors (8,15) and (9,14) are unused. This sixteen-vertex
witness does not itself saturate all eighteen original Gram equalities.

This is not an exterior graph candidate. The full population, the other
Gram equations, degrees, mixed equations, previously accumulated cuts,
and completion in the other shell component are not asserted.

No 6^6 search is needed. The structural certificate proves the upper
bound and the explicit assignment supplies the matching lower bound
for this precisely stated relaxation.

## The bound is not a continuous consequence of color quotas alone

For a separate fractional control, give every private target selector
value 1/6 and every shared target selector value 1/2. Set every target
edge to 1/6. Each private color contains six target vertices and each
shared color contains two, so every one of the eighteen color sums is
one. Endpoint activation holds, but
\[
\sum_{e\in E_*}y_e=84/6=14>12.
\]

The checker uses numerator arithmetic with denominator six. It checks
the eighteen color equations and all target endpoint inequalities
exactly. It does not test the other original constraints, and this is
not a separating point for the full parent model.

This control locates the integrality used in the proof: a noncenter
cannot have two selected neighbors of one color in a Boolean solution,
although fractional neighbor mass can be distributed among them.
The independent continuous bound of eighteen in
[root_prism_free_f0_must_triangle_total_bound.md](root_prism_free_f0_must_triangle_total_bound.md)
remains valid. The present Boolean aggregation is tighter.

## Proposed native row and fixed scope

The literal edge with original ID e remains native variable 540+e.
The proposed row is
\[
0\le\sum_{e\in E_*}\mathrm{var}_{540+e}\le12.
\]
It has 84 coefficient-one terms, no new variable, and no dependence on
an auxiliary-variable choice. Its exact row key is
[0,12,[[540+e,1] for e in ascending target-edge order]].
The checker emits this key and its SHA-256 over compact JSON without
a trailing newline.

The current native model and active query remain unchanged. Root
acceptance and an independently checked native append are separate
requirements before using the row in a later query.

## Frozen checker and bounds

Source:
experiments/workspace/root_prism_free_f0_target_color_twelve_certificate_v8.js,
Git blob 54fa064c0211d3cfa07214bf2304d7b0122b9cc9,
SHA-256 dfb0764a29e53db9ba59b5fd291a45a612af0f690699b1892c195487014a152e.

Configuration:
experiments/logs/root-prism-free/f0-target-color-twelve-configuration01.json,
Git blob 9676d56ffaf8ae7be0094db062357e1be69ca0d5,
SHA-256 d3067a6166a3c4b4a0f684df224afe5691182a780a267e6de828ca20d1b16ca2.

The single planned call has a thirty-second total checked bound,
including input binding, report serialization and hashing, and a one-MiB
report bound. It performs no assignment enumeration. It reads only
the already accepted domain, target/indicator list, literal support
acceptance, previous complete independent target-graph review, and
combined native configuration.

The input identities include:

- Domain archive SHA-256
  665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4.
- Indicator inventory SHA-256
  8606d51ced038b40135fa22bc16d056873b80c16c26d2c34db7e24ac8effd2c7.
- Separate literal support root acceptance SHA-256
  9d4e3a9b44a2140d95091425a346396ed84dd8d9d88f3a4e7fa3e67d47cd51d4.
- Complete independent eighteen-bound review SHA-256
  84572d32b842a905db9b08efe91be0fbf3fb8c1185ead6b782d9f6555f4eed3d.
- Combined native configuration SHA-256
  3fcf3a742a53cf200810aea92cfa594c2ef4623e54aa5679e8afbeda00409059.

The original Gram formula and native row mapping are read from
root_prism_free_f0_direct_literal_model.py, Git blob
3c5e9c810af89818a6da0417e1bdb9a878f896c3, SHA-256
b500336db29820777afb59076384a48382fa54453fce5b232a072719893cea40.
All previous branch premises and graph-existence limitations remain.
