# A complete local Boolean test at F0 center 355

This model conditions on an exterior vertex with component signature
{6,11,13}. Component labels run from zero to seventeen. Its exterior
neighbors must form an eight-element subset of the 218 remaining eligible
signatures. This is a necessary local condition; the complete sixty-vertex
incidence design and the exterior adjacency matrix remain unspecified.

## Native constraints

Every candidate receives its own Boolean variable. There are 218 variables,
although their averaged edge coordinates occupy only 217 columns. The
model records that map but imposes no equality between neighbor bits.

For every component site i, the chosen signatures obey

\[
\sum_{a:\,i\in h_a}e_a
 =2-\mathbf1[i\in h_b]-\sum_{j\in h_b}D_{ij}.
\]

All eighteen equations are included, including the three zero rows.
Their right sides sum to 24. Each candidate signature has three sites,
so the equations imply sum e_a=8. The CNF also includes that redundant
cardinality equation.

The complete frozen local conflict graph supplies 5,495 binary clauses.
The builder independently checks every candidate pair against the union
of the following literal reasons:

- a shared site whose mixed demand is one;
- at least two shared component sites, which would give three common
  neighbors after the center is selected;
- a saved two-edge path prism, checked again on its literal six vertices;
- a certified selector motif conflict.

Using that priority to assign one reason per pair gives 4,422 mixed-demand,
904 shared-core, 150 path-prism and 19 motif conflicts. This priority does
not assert that the reasons are disjoint mathematically.

There is no restriction on the unknown second component, no full
sixty-selector Gram system, and no constraint requiring a matching among
the eight chosen exterior neighbors in this first pilot.

## Encoding and controls

Primitive variables occupy 1 through 218. Fresh sequential-counter
auxiliaries encode the eighteen demand equations and the redundant
population equation. The formula has 5,408 variables and 16,105 clauses.

The preparation checked 2,817 assignments over thirty small cardinality
domains, including upper bounds near both ends of the range. It also
checked all 1,024 graph/assignment combinations for four variables and a
known synthetic eight-neighbor, eighteen-demand positive instance.
None of those controls queried center 355.

The builder is
`experiments/workspace/root_prism_free_f0_local_center355.py`,
SHA256
`e3e7852c674ec132f1a08f4ca9ff4ea0d11a581be4f6f39d512b8114b48d3054`.
The prepared formula is
`experiments/logs/root-prism-free/f0-local-center355-preparation01/model.cnf`,
SHA256
`fcb2e5af81712b914acc491de241917d6093461ef990f5b78e86c79df3deedae`.

## One bounded pilot and separate replay

The separate runner binds the builder, native model, CNF and preparation.
Before a production call it rebuilds the native rows and the exact CNF.
It allows one proof-enabled Glucose4 call, with at most thirty seconds
for solver initialization and the interrupted solve. Model reconstruction
and exact result verification have separate timing.

A SAT answer must supply an explicit Boolean assignment. Acceptance checks
every CNF clause, all eighteen native equations, the population and all
5,495 conflicts. It also constructs the visible thirty-vertex partial
graph and checks all 435 common-neighbor caps directly. This remains a
local witness, with three of the center's neighbors in the other component
unrepresented.

An UNSAT answer is initially marked unverified. A separate replay must
rebuild the exact CNF and pass its saved DRAT proof to an independent
checker. Only that checked certificate can exclude signature 355.
The twelve verified fixed-core relabelings then exclude its full selector
orbit. This would be a selector restriction within the fixed F0 branch,
not a solution of the complete SRG problem.

An interrupted call remains UNKNOWN. It triggers no automatic retry,
larger model, matching condition, or query of another center.
