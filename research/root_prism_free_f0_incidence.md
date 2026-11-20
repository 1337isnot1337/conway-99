# A binary incidence test for one eighteen-vertex shell component

This model is conditional on a globally prism-free
\(\operatorname{SRG}(99,14,1,2)\), on \(x_{521}=0\), and on a triangle
whose shell splits into two eighteen-vertex components. The
[complete component reduction](root_prism_free_f0_components.md)
has 66 representative component cores. The first prepared query tests
representative zero only.

The query returned SAT. Its sixty-triple witness passes exact replay,
including every Gram position, profile count, and motif conflict.
No component is excluded by this query.

Every candidate triple remains a free binary selector. The model
imposes all Gram equations and explicit conflicts between two triples
that would create a prism or the seventeen-edge motif \(F\).
It imposes no symmetry on the completed graph and specifies no edges
among the sixty exterior vertices. A satisfying assignment is therefore
only a necessary incidence witness for one component.

## Constraints and complete domain

For one eighteen-vertex component let \(G\) be the required incidence
Gram matrix. The complete admissible triple domain was obtained by
enumerating every three-subset with at most two points per fiber, then
applying positive Gram support and the known mixed cap
\((I+S)h\le2\mathbf1\).

There is one variable \(z_h\) per distinct triple. The model requires

\[
\sum_hz_hh_ih_j=G_{ij}\qquad(0\le i\le j<18).
\]

The 171 positions include every diagonal and every unordered pair.
Equal constraints are encoded once with an explicit coverage map.
A zero quota with empty support is recorded as a true equality.

The diagonal sum is 180 and every triple has weight three. Thus the
equations force sixty selected triples. Their profile counts, proved
in the component note, are 24 of type \(111\) and 36 of type \(210\).
The model does not impose these as extra assumptions or choose the
one-parameter distribution of the six oriented \(210\) profiles.

## A first \(F\) conflict

Let \(u\in V_i\), and let \(v\in V_j,w\in V_k\) be its two cross-fiber
neighbors. Let \(x,y\) be a matching pair in \(V_i\), disjoint from
\(u\) and its matching partner. Suppose two exterior vertices have
component triples
\[
A=\{u,v,x\},\qquad B=\{u,w,y\}.
\]

Then their known incidences give \(F\) with centers \(t_i,u\).
The four exclusive neighbors on the first side are
\(t_j,t_k,x,y\), paired as \((t_j,t_k),(x,y)\).
The four on the second side are \(v,w,A,B\), paired as
\((v,A),(w,B)\). The cross matching is
\[
(t_j,v),\quad(t_k,w),\quad(x,A),\quad(y,B).
\]
Together with the center edge and the eight center-to-side edges,
these are exactly seventeen required edges.

Consequently the corresponding selectors satisfy \(z_A+z_B\le1\).
Both individual triples pass the original one-column tests. This
conflict uses the globally \(F\)-free hypothesis.

## Further visible motifs

The certificate includes a second \(F\) family. Let \(u\in V_i\) and
\(v\in V_j\) be adjacent shell vertices. Let \(m_u,m_v\) be their
internal matching partners, and let \(w,z\in V_k\) be their respective
neighbors in the third fiber. The following conditions each give an
explicit \(F\), provided both displayed triples are in the complete
domain:

| Known shell edge | First triple | Second triple |
|---|---|---|
| \(m_u z\) | \(\{u,w,m_v\}\) | \(\{v,z,w\}\) |
| \(w m_v\) | \(\{u,w,z\}\) | \(\{v,z,m_u\}\) |
| \(w z\) | \(\{u,w,m_v\}\) | \(\{v,z,m_u\}\) |

The centers are \(u,v\). Their exclusive-side matchings are
\((t_i,m_u),(w,A)\) and \((t_j,m_v),(z,B)\).
For each row, the remaining known incidences make the cross matching
and one eight-cycle on the eight side vertices. The certificate
records the exact ten vertices and their adjacency rows.

There is also a prism conflict. For a four-vertex induced shell path
\(a-b-c-d\), the triples
\[
A=\{a,b,d\},\qquad B=\{a,c,d\}
\]
give triangles \((A,a,b)\) and \((B,c,d)\), with cross matching
\((A,d),(a,B),(b,c)\). If the shared pair \(a,d\) already has Gram
quota one, its Gram equation excludes the pair of triples. The
certificate keeps the additional conflicts not already excluded by
such a quota.

These are explicit families of necessary conflicts. No completeness
claim about every possible multi-column obstruction is needed.

## Unknown exterior adjacency is not set to zero

For every retained conflict, the checker constructs the twenty-one
core vertices plus the two proposed vertices and their three known
component incidences each. It verifies all visible caps and the
claimed prism or \(F\) on the recorded support.

The edge between the two proposed exterior vertices is initially
unspecified in the mathematical model. The checker also adds that
edge and verifies a visible common-neighbor cap violation. Therefore
that edge is forced absent in any completion. All other edges of
the recorded motif are fixed by the core and selected columns.
Edges to vertices outside the support cannot remove these edges or
repair the cap violation.

The \(F\) check verifies two adjacent degree-five centers, eight
degree-three side vertices, exactly one center neighbor at each side
vertex, an eight-cycle on the side vertices, and one same-side
matching edge at every side vertex. This characterizes the motif
from the existing \(x_{521}\) certificate.

## Frozen preparation and controls

The sources are
[the motif checker](../experiments/workspace/root_prism_free_f0_pair_clauses.py)
and
[the incidence builder and replay](../experiments/workspace/root_prism_free_f0_incidence.py).
The [motif certificate](../experiments/logs/root-prism-free/f0-pair-clauses.json.gz)
contains separate \(F\) and prism witnesses for all 66 representatives.
Generation and standard-library replay passed.

For representative zero:

| Item | Count |
|---|---:|
| Binary triple selectors | 480 |
| Total CNF variables | 28,308 |
| Total CNF clauses | 56,550 |
| Gram positions covered | 171 |
| Distinct Gram equalities, including empty zero | 151 |
| \(F\) conflicts centered on a central-shell edge | 60 |
| \(F\) conflicts centered on a cross shell edge | 18 |
| Additional prism conflicts | 12 |

The [model manifest](../experiments/logs/root-prism-free/f0-incidence-case00-model.json)
binds the full domain, motif certificate, source files, and serialized
CNF. It records all 171 positions and separate conflict-family counts.

Before preparing the main model, 773 elementary Boolean assignments
checked the cardinality and conflict-clause semantics. A known
nine-vertex rook graph supplied a direct incidence positive control.
Deleting one of its actual columns gave the expected negative control.
This tests the generic Gram encoder; the rook graph is not asserted
to satisfy the prism-free shell hypothesis.
The main preparation also replayed the full component coverage and
all finite motif witnesses.

## Query and certificate scope

The first query used one fresh proof-enabled run, bounded by sixty
seconds including solver bootstrap. It returned SAT after 0.064 seconds
including bootstrap. The result and exact incidence checks completed
in 1.31 seconds. There was no 66-case sweep.

The [saved result](../experiments/logs/root-prism-free/f0-incidence-case00-run01/result.json)
contains all sixty selected triples. It has 24 profile-\(111\) triples
and six of each oriented \(210\) profile. Direct checks passed for all
171 Gram positions, all 78 \(F\) conflicts, and all twelve prism
conflicts. A [cold replay](../experiments/logs/root-prism-free/f0-incidence-case00-run01-replay.json)
reconstructed the complete domain and CNF, matched the serialized
CNF hash, and checked the same incidence witness.

An [independent audit](../experiments/logs/root-prism-free/f0-incidence-independent-audit.json)
rebuilt the twenty-one-vertex core and all 816 possible three-subsets
without importing the subject builders. It recovered the 480-column
domain and all Gram rows, and verified every explicit motif support
and cap witness.

For SAT, the verifier directly checks sixty distinct triples, all 171
Gram positions, all fiber-profile counts, and every retained \(F\)
and prism conflict. It does not claim a completion of the other
component or of the sixty-vertex exterior.

For UNSAT, the direct DRAT proof must pass. A separate replay then
reconstructs the complete domain, all motif witnesses, and the full
CNF, checks its hash, verifies that retained input clauses belong to
that CNF, and checks the retained proof. Only that component
representative and its explicitly covered relabelings would be
excluded. UNKNOWN gives no exclusion.

The SAT result leaves both the second component and the exterior
adjacency unresolved. In particular, it is not a ninety-nine-vertex
graph or an incidence solution for the full thirty-nine-vertex core.
