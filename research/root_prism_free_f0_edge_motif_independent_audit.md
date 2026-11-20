# Independent audit of the visible edge motifs

The independent census reproduces every representative prism count in
the complete edge-domain record. Among the 5,805 edge orbits, 5,643 have
no visible prism, 160 have one, and two have two. The 162 prohibited
orbits contain 1,884 literal edges. All 1,884 saved induced-prism
witnesses and their core transports pass direct checks.

The production prism calculation in this audit enumerates unordered
pairs of disjoint triangles. It accepts a pair exactly when each vertex
has one neighbor in the other triangle. This specifies the complete
induced six-vertex prism. A prism has exactly these two triangle faces,
so this method counts each induced copy once. The audit imports no
function from the coordinator's census or a model builder.

The audit also reconstructs the 68,394 eligible edges from the signature
overlaps and exact mixed targets, verifies the full orbit partition,
and derives all twelve actual 21-core relabelings from their actions on
the signatures. These checks justify transport from representatives to
the complete literal edge domain.

## Review of the shell completeness argument

For an edge \(uv\), let \(L=N(u)\setminus(N(v)\cup\{v\})\) and
\(R=N(v)\setminus(N(u)\cup\{u\})\). A vertex in \(L\) has at most
one neighbor in \(L\), because it is adjacent to \(u\). It has at most
one neighbor in \(R\), because its nonedge to \(v\) already has the
common neighbor \(u\). The same statements hold on the other side.
Thus the shell has degree at most two, with at most one edge of each
kind at each vertex.

Every cycle in the shell alternates same-side and opposite-side edges.
A four-cycle produces a prism when its two centers are included. An
eight-cycle produces the ten-vertex motif \(F\). Conversely, a visible
prism or \(F\) supplies such a cycle at a corresponding center edge.
Its shell vertices already have degree two, so other visible vertices
cannot enlarge that component. A prism is counted at its three matching
edges; \(F\) has one intrinsic center edge joining its two degree-five
vertices. This proves completeness of the coordinator's shell method
on the cap-valid specified graphs.

As an additional implementation check, the independent audit walks
eight-cycles in every representative's exclusive-neighbor shells. It
finds no \(F\). This uses a separate walk implementation and no saved
shell components. Thirty-two explicit controls include a prism, the
nine-vertex rook graph, \(F\), isolated-vertex extensions, and every
single-edge deletion from the two motifs.

The source is
[root_prism_free_f0_edge_motif_independent_audit.py](../experiments/workspace/root_prism_free_f0_edge_motif_independent_audit.py).
The bound result is
[f0-edge-motif-independent-audit.json](../experiments/logs/root-prism-free/f0-edge-motif-independent-audit.json).
It records all input hashes and the complete count digest. The audit
took 6.009 seconds and used no optimizer or numerical point. Its
conclusion supplies necessary edge-zero rows under global prism-freeness;
it does not establish a completion for any surviving edge state.
