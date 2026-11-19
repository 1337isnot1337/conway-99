# Local exterior-neighbor conflicts in the fixed F0 branch

This preparation inventories stated necessary conflicts. It does not test
local feasibility, enumerate maximal cliques or odd cycles, or evaluate a
fractional point. It leaves the other shell component and its alignment free.

The source is
`experiments/workspace/root_prism_free_f0_local_conflict_inventory.py`.
All five input records have fixed SHA256 bindings in that source. The new
work uses the completed prism and core-pair ledgers; it does not repeat
either census.

## Local variables and degree

Fix a selected exterior vertex with signature b on the eighteen-vertex
component. For every eligible signature a whose edge to b is not a
certified zero, use a separate Boolean variable e_a. It means that the
exterior edge ab is present. Distinct signatures remain distinct variables,
even when their averaged edge coordinates coincide.

Let D be the component adjacency matrix, and let h_b be the incidence
vector of the three sites in signature b. The exact mixed demands are

\[
t_b=2\mathbf1-h_b-Dh_b,\qquad
\sum_a h_a e_a=t_b.
\]

The component is cubic, so the eighteen demands sum to
36-3-9=24. Each neighboring signature has weight three. Consequently

\[
\sum_a e_a=8.
\]

This is the exterior degree after accounting for the three neighbors in
each of the two shell components. All eighteen demands remain in the
record. A local solution would still be only a necessary partial witness.

## Conflict layers

A conflict between a and c means that they cannot both be neighbors of b.
The preparation retains the following layers separately.

1. A mixed demand t_b(i)=1 gives a clique on all eligible neighboring
   signatures containing i. A selector Gram quota one gives a clique on
   its support, using the existing lifted Gram equation at b and Y<=Z.
2. The published common-core-pair rows give the remaining stated cliques:
   two neighbors containing sites i,j would share b,i,j as three common
   neighbors. The preparation recovers their literal supports from the
   saved 258 quotient rows and all 3,096 actual-core transports.
3. The published path-prism rows give 61,476 distinct retained literal
   conflicts. Their 5,124 quotient rows and saved transports cover every
   path in this layer. The new preparation does not enumerate new prisms.
4. Certified selector-pair zeros give semantic neighbor conflicts through
   edge activation. All 4,320 quota-one zeros are already in the first
   layer. The other 90 motif zeros are retained with their own provenance.

A zero selector moment Z_ac and edge activation alone do not provide the
homogeneous fractional row Y_ab+Y_bc<=x_b. For example, set x_a=x_b=x_c=1/2,
Z_ab=Z_bc=Y_ab=Y_bc=1/2 and Z_ac=0. These values satisfy the individual
pair-moment bounds and the selector conflict x_a+x_c<=1, but violate the
homogeneous row. The three-selector moment triangle inequality supplies
the missing implication; that separate family is owned by the coordinator.

The inventory therefore records both semantic conflicts and coverage by
specific homogeneous inequalities. “Covered” means a recorded mixed,
lifted Gram, core-pair or path row proves that pair conflict. It does not
mean all consequences of the current linear model were enumerated. Nor
does it assert that every published row has already been installed in a
particular numerical model.

## Center orbits

The twelve verified relabelings of the fixed core have 42 orbits on its
480 exterior signatures. Only the choice of center is reduced by these
orbits. The preparation checks actual core adjacency, signature transports,
mixed demands, live neighbor domains and every conflict layer under these
relabelings. It saves a transport from a representative to each of the
480 centers.

This is a relabeling of a necessary local problem. It assumes no
automorphism of the unknown graph and imposes no equality on the distinct
Boolean neighbor variables.

## Bounded inventory

The proposed single run has a ten-second budget, including input loading.
For each of the 42 centers it records the full live neighbor list, all
eighteen mixed demands, saved clique and path references, and complete
adjacency for the union of the stated conflict layers.

It also counts edges, degrees and triangles by bitset intersections, and
computes a deterministic degeneracy deletion order. Differences of
triangle counts between nested layers count triangles containing a new
edge. They do not prove that the corresponding clique inequality is
independent of other linear combinations. No triangle witnesses, maximal
cliques, induced odd cycles, or eight-neighbor selections are searched.

Every completed center is retained if the deadline or an assertion stops
the run. A complete result must cover all 42 representatives and all
480 centers by verified transports. A separate replay must reproduce the
canonical record.

The small controls compare bitset edge counts, triangle counts and
degeneracy with direct calculations on all 1,024 simple graphs on five
vertices. Boolean activation controls and the fractional counterexample
above test the provenance distinction. These controls do not query the
F0 local problems.

No conclusion about graph existence follows from this preparation.
