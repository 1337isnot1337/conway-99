# Two-edge path prism cuts: completed census

The complete two-edge census gives 5,124 distinct quotient inequalities
on the existing 15,200-variable F0 second-moment model. Every inequality
has the form

\[
Y_{ab}+Y_{bc}\le x_b.
\]

When the two edge coordinates coincide under the actual-core quotient,
the coefficient is added. Two of the rows are 2Y-x_b<=0; the other
5,122 have three distinct columns. No graph automorphism is assumed.

The [scope and proof note](root_prism_free_f0_path_prism_cuts.md)
derives the canonical prism pattern and the two permitted pruning rules.
The production construction completed in 13.244671
seconds under its 30-second limit. Cold replay took
9.726567 seconds and reproduced the complete
mathematical record exactly.

## Complete dispositions

| Disposition | Literal core witnesses | Distinct exterior paths |
|---|---:|---:|
| Known Y zero, leaving edge activation | 8,724 | 8,664 |
| One mixed quota-one equation, with edge nonnegativity | 37,284 | 37,278 |
| Retained inequality | 61,512 | 61,476 |
| Total | 107,520 | 107,418 |

The quota-one witness count splits into 34,296 cases at the pattern's
shared core site and 2,988 cases at the extra shared signature site.
Different core witnesses can give the same exterior path, which accounts
for the difference between the two columns.

The retained paths collapse to 5,124 linear rows. All twelve actual-core
actions are checked on the fixed core and every signature. Their 144
compositions, 42 selector orbits and 5,805 edge orbits are verified.
For every retained row, all twelve transported literal witnesses are
saved and checked, giving 61,488 row transports.

The record stores every literal witness, its two edge IDs, its pruning
reason and exact supporting site or zero edge, its exterior-path ID,
and its quotient row ID when retained. It also stores all exterior-path
multiplicities. The compact array schemas are explicit in
literal_witness_fields and path_fields.

## Complete exactly-three-exterior scope

The separate scope checker directly verifies that the fixed 18-vertex
component is cubic and triangle-free. All ten triangles in the full
21-core meet the central three vertices. Every exterior signature avoids
those central vertices.

In a triangular prism, three chosen vertices induce one, two or three
edges. The complete twenty-subset control has six one-edge cases,
twelve path cases and two triangle cases. The complementary three
vertices induce the same number of edges.

A three-edge exterior case would therefore require a core triangle,
with one exterior matching neighbor at each of its three core vertices.
Every core triangle has a central vertex, which has no exterior
neighbor. This case is impossible.

Consequently the [715 one-edge rows](root_prism_free_f0_three_vertex_prism_cuts.md)
and the 5,124 path rows cover every visible prism using exactly three
exterior signature vertices and three vertices of the fixed 21-core.
The two row sets are disjoint: the one-edge rows involve a Z coordinate,
while the path rows use only x and Y. Their union has 5,839 rows.

This scope statement includes the previously certified pruning premises.
It does not cover motifs involving vertices from the other unknown
component or more than three exterior vertices. It does not characterize
fractional motif absence without the required graph-moment semantics.

## Files and bindings

The production source is
`experiments/workspace/root_prism_free_f0_path_prism_cuts.py`,
SHA256 `b332326f90a428565d12d58fefa230bcfb3c5ac4b1e86983115cbc73979c339b`.

The full compressed record is
`experiments/logs/root-prism-free/f0-path-prism-cuts01.json.gz`,
SHA256 `d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886`.
Its canonical uncompressed content has SHA256
`970bff3808d58dfab072974c42a65e04679f301daef258ae4e43c8fccfe1c6f6`.

The preparation and replay records are
`f0-path-prism-cuts01-preparation.json` and
`f0-path-prism-cuts01-replay.json` in the same directory.
The scope checker is
`experiments/workspace/root_prism_free_f0_three_exterior_prism_scope.py`,
SHA256 `8f1e41ec2349d8f73f2e3ab41952be3d853c3c6050c7780333f2aaca99f8de0e`.
It checks the literal fixed core and the twenty prism splits; it reads
the two frozen census records without repeating their enumerations.

The rows are necessary for the globally prism-free component-zero
branch. The other component and its alignment remain free. No point
was loaded, no optimizer was called, and no graph-existence conclusion
is claimed by this package.
