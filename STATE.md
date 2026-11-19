# Conway 99 research ledger

The endpoint is an explicit graph satisfying srg(99,14,1,2), or a verified contradiction that applies to every such graph. Neither has been obtained. All computations here are local and unrefereed.

The current interface result on this branch proves that every induced rook
grid has [at most one rook-isomorphic partner](research/grids-and-triangles/rook_partner_bound.md),
without any red assumption. A complete 59-class census excludes 58 classes
by exact incidence propagation; a checked integer completion proof excludes
the last. Independent domain and encoding audits reproduce its full CNF.
The earlier [three-base boundary proof](research/grids-and-triangles/three_red_boundary.md)
also independently gives at most one all-red grid. A separate
[integer flag certificate](research/grids-and-triangles/grid_count_119.md)
proves `29g-4b<=3465`, hence at most 119 grids from that bound.
The parallel [root-grid branch, PR 3](https://github.com/1337isnot1337/conway-99/pull/3)
has stronger global restrictions: its intersecting-red-triangle exclusion
gives no all-red grid and at most 114 grids in total. Checkpoint `006cce9`
further improves the total bound to 113 using a five-grid branching exclusion.
Its full-component census at `9c58d1d` improves this to 112 and bounds
the number of full triangles by 24. Its later nine-triangle-cover
exclusion and component update at `51329e0` reduce the full-triangle
bound to 22; the total grid bound remains 112.
The later eight-triangle exclusion at `b611eb7` leaves only pencil
components and gives at most 21 full triangles. Checkpoint `a39ef45`
also raises the lower bound on disjoint triangle pairs with two
cross-edges to 1,215. These are results on the parallel branch.
Its later six-grid exclusion at `f494f2f` gives at most 105 grids,
at most twenty full triangles, and at least 2,268 percolating nonedges.
The coordinator has read its argument and checker source; its complete
919,143-core run has not been independently replayed on this branch.
Its earlier checkpoint
`2e2d7ed` also bounds the number through a point by thirteen. The historical
bounds and count witnesses below are retained with their original scope.

An [exact zero-grid count witness](research/grids-and-triangles/grid_free_order_nine.md)
satisfies all 23,189 original extension equations through order nine, all
6,535 nonnegative integral induced counts, and all 584 selected cached
ordinary/induced moment blocks. Integer congruences certify every block as
positive definite. Thus this finite count/moment relaxation has minimum
grid count zero. It neither constructs a graph nor proves feasibility of
every possible order-nine inequality. The absence of a forced grid is a
specific gap left by the interface program.
The same point now also has [exact PSD certificates for 832 cached
projector blocks](research/grids-and-triangles/grid_free_projector_order_nine.md),
giving 1,416 checked blocks in total. Each added block has eight exact
kernels and a positive definite principal quotient.
The next [order-ten count probes](research/grids-and-triangles/grid_free_order10_probe.md)
use 48,965 graph types and 549 core coordinates. Both initial 30-second
linear searches ended UNKNOWN. No order-ten witness or exclusion follows.
The subsequent [scaled calculation](research/grids-and-triangles/grid_free_order10_scaled.md)
gives an exact contradiction for extending this particular order-nine
point. A positive integer combination of 52 induced order-ten counts
and 21 ordinary core counts gives a universal inequality on the old
coordinates, with value `-2564720` at the point. No upper bound is needed
for this simplified identity. An independent integer replay checks all
52 source forms against the exact reduction and reconstructs the cut.
This excludes the fixed prefix, not all zero-grid count assignments.
The free-prefix numerical proposal still fails exact count verification.
The [complete reduction audit](research/grids-and-triangles/order10_reduction_audit.md)
checks all 180,445 original identities coefficientwise and finds no
additional reduced equality or congruence. Exact moment separation gives
four cuts against the first free proposal and nine against a subsequent
proposal. The [bounded count/moment loop](research/grids-and-triangles/grid_free_order10_moments_loop.md)
then reached its time limit with fourteen added inequalities. It gives
neither an exact feasible point nor an infeasibility certificate.
The separate [prism-zero probe](research/grids-and-triangles/grid_free_order10_prism_zero.md)
retains all fourteen inequalities and returns a numerical proposal.
Only two induced counts become negative after rounding, each minus one.
The moment scan finds no exact separator, but it does not certify PSD.
This run gives neither an exact count witness nor a prism-free exclusion.
A subsequent [one-coordinate repair](research/grids-and-triangles/grid_free_order10_prism_zero_repair.md)
does give an exact prism-zero count witness through order ten. Increasing
coordinate 549 from five to six makes all 48,965 induced counts nonnegative
integers. An [independent replay](research/grids-and-triangles/prism_zero_count_independent_audit.md)
checks every original equation, level total, reduced count, and all 1,443
prism-containing types. The new prefix also has [exact PSD certificates
for all 1,416 selected cached blocks](research/grids-and-triangles/grid_free_order10_prism_zero_psd.md).
Both owner and coordinator replays pass. These blocks use counts through
order nine; new order-ten moment blocks are a separate search.
[Stronger injective embedding bounds](research/grids-and-triangles/order10_embedding_bounds.md)
improve every individual core bound but also permit this point. The
finite relaxation therefore still cannot force a prism or rook grid.
The next [eight-root, one-vertex flag scan](research/grids-and-triangles/grid_free_order10_r8s1.md)
does reject that repaired point. Eleven integer quadratic witnesses give
eleven distinct inequalities involving genuine order-ten counts. A separate
replay constructs the extension graphs directly and checks every cut.
The complete reusable cache retains all 916 roots without point-dependent
zero-flag removal. These cuts exclude this point; they do not exclude the
prism-free case. The earlier 1,416-block PSD certificate remains valid
within its stated finite family.
The [exact prism-containment closure](research/grids-and-triangles/grid_free_order10_prism_zero_closure.md)
fixes 58 ordinary cores and all 1,443 prism-containing induced types.
After these zeros and all 25 retained cuts, a
[new count loop](research/grids-and-triangles/grid_free_order10_prism_zero_moments_loop.md)
gives another exact integer count witness. Its unrounded proposal has no
exact separator in the two complete scans, with one unconfirmed numerical
negative in the older family. A separate
[edge-component identity](research/root_prism_free_edge_components.md)
identifies the ten-vertex motif coordinate `x521` with `e24+3*e222` in a
prism-free graph. Thus global minimum edge-shell types 33 or 6 require
`x521=0`. This [additional count face](research/root_prism_free_x521_face.md)
also has an exact integer witness satisfying all 25 cuts. Both witnesses
pass [independent original-equation audits](research/grids-and-triangles/prism_zero_followup_audits.md).
The face witness's [complete 2,332-block scan](research/root_prism_free_x521_moments.md)
finds no exact or unconfirmed numerical negative; it is not an exact PSD
certificate. Separate [binary flag triangle inequalities](research/grids-and-triangles/binary_flag_triangle_inequalities.md)
give no cut against either the earlier repaired point or the new
positive-x521 rounded point, after 170,183,860 exact inequalities per point.
These finite witnesses leave graph existence unresolved.
The next [six-root, two-vertex flag family](research/grids-and-triangles/grid_free_order10_r6s2_results.md)
rejects both saved count witnesses. Eighteen exact quadratic inequalities
reject the positive-x521 point; sixteen of them reject the x521-zero point.
A separate graph constructor reproduces all 374,505 product entries used
by these eighteen certificates. This excludes the two points, not their
entire count faces. Their earlier finite-scope certificates remain valid.
The [complete reusable family](research/grids-and-triangles/grid_free_order10_r6s2_full_cache.md)
now contains all 62 roots, 14,348 flags, and 3,913,479 lower-triangle
matrix entries. Some flags take values zero, one, or two, so the product
construction retains overlapping and disjoint copies. An
[exact range scan](research/grids-and-triangles/grid_free_order10_r6s2_ranges.md)
checks 7,812,610 inequalities at each saved point and finds no further cut.
All diagonal range inequalities follow from existing count equations;
general cross-range redundancy has not been proved.
The [next count loop and higher-flag test](research/grids-and-triangles/grid_free_order10_higher_flags_loop.md)
add three more six-root inequalities, each independently reconstructed.
A one-coordinate repair gives an exact integer witness for all 47 held
inequalities. The complete 2,394-block scan at that integer point finds
no separator. A new four-cycle block with three free vertices then
rejects it by an independently reconstructed 39-term inequality.
The [complete additional families](research/grids-and-triangles/grid_free_order10_higher_flags_results.md)
contain eleven blocks, including nontrivial free-vertex stabilizers.
After retaining the four-cycle cut, the 48-cut model with `x521=0`
has another exact integer count witness. A separate audit checks every
original equation, all 48,965 saved reduction rows, all bounds and zeros,
and all 48 held inequalities. Its unrounded proposal has no separator
in the complete 2,405-block scan. At the integer point, the
[four-cycle block alone](research/grids-and-triangles/grid_free_order10_higher_flags_c4_structure.md)
has an exact rank-thirteen PSD certificate. The other blocks have no
exact PSD certificate at this point. Eight-root spectral/projector
blocks form a separate family; the selected scans do not cover them.
The [C4 integer-moment continuation](research/grids-and-triangles/grid_free_order10_c4_integer_distribution.md)
checks 265,720 shifted-integer inequalities without finding a cut. It
then gives a stronger exact certificate: 75 integer-valued atoms with
positive rational weights reproduce every entry of the fifteen-flag
moment matrix. Independent literal products verify all 120 distinct
entries. Thus no pointwise quadratic inequality based only on these
flag-value restrictions can reject this point. The atoms are not
claimed to be realizable graph neighborhoods or integer root populations.
The [complete eight-root projector family](research/grids-and-triangles/grid_free_order10_projector_full_scan.md)
now has all 3,664 blocks and 13,735,344 lower entries. The complete scan
at that integer point finds no separator. Every contraction and all nine
kernel identities per block are exact, but numerical separation supplies
no PSD certificate. The reusable cache retains all 916 roots and every
allowed neighborhood mask. A separate
[integer class-size calculation](research/grids-and-triangles/grid_free_order10_projector_integer_classes.md)
checks the optimal shifted quadratic for all 68,176 classes exactly.
All pass, so this family gives no further cut.
The [seven-root complement preparation](research/grids-and-triangles/grid_free_order10_complement_domains.md)
expresses absence-conditioned moment matrices as differences of existing
parent and child blocks. Residual-pair identities make 4,478 of 5,215
cases positive sums of child blocks. The remaining 737 cases over 82
roots have complete sparse lifts and coefficientwise zero-row checks.
This preparation makes no point-feasibility or exclusion claim.
Its [bounded point scan](research/grids-and-triangles/grid_free_order10_complement_scan.md)
now covers all 737 complements and separately checks all 916 scalar child
blocks at the same integer point. It finds no separator and gives no
exact PSD certificate. The stronger
[clique-complement preparation](research/grids-and-triangles/grid_free_order10_complement_cliques.md)
uses mutually incompatible flags. Two independent constructions give
477 universal maximal cliques. Their complete restrictions to the roots
leave 3,939 nonredundant cases under the stated quota-one reduction.
Exact root relabelings reduce these to 711 representatives. Every selected
zero row and every orbit transport is checked before the
[complete scan](research/grids-and-triangles/grid_free_order10_complement_clique_scan.md).
That scan finds no separator in any representative, covering all 3,939
cases by congruence. It is not an exact PSD certificate.
A [complete visible-pair graph](research/grids-and-triangles/grid_free_order10_complement_visible_domains.md)
adds incompatibilities from root pairs with only one residual common
neighbor. Literal checks of both mutual-edge choices and two independent
clique censuses give 3,821 remaining cases in 811 root orbits. This
stronger family is prepared separately; its domain record is not a scan.
The [principal-projector scan](research/grids-and-triangles/order10_projector_zeros.md)
excludes only the rook graph plus an isolated vertex among all types
through order ten. It adds no new zero-grid restriction.

The [single isomorphic pair](research/grids-and-triangles/two_rook_iso_pair_integer.md)
remains unresolved. Its forced 81-vertex exterior has nine singleton tips
and 36 duplicate-signature pairs. Four bounded completion runs ended
UNKNOWN. The [Hall-strengthened run](research/grids-and-triangles/two_rook_iso_pair_integer_hall.md)
found 31 partial graphs and added 30,446 necessary cap clauses; every
partial graph still violates exterior common-neighbor equations. Exact
replays check every saved point and cut. The
[local Hall projection](research/grids-and-triangles/two_rook_tip_hall.md)
admits 103 of 256 neighborhoods at each tip, and the
[tip Gram condition](research/grids-and-triangles/two_rook_tip_psd.md)
is `3I-R+J-2Z` positive semidefinite. These are necessary conditions,
not an exclusion of the pair or a construction of a full graph.
The [complete exterior-cap model](research/grids-and-triangles/two_rook_iso_pair_full_caps.md)
has 778,752 variables and 1,556,032 clauses. Its 180-second proof-enabled
run also ended UNKNOWN. The model includes every exterior pair cap, so a
satisfying primary assignment would be a complete graph under the pair
hypothesis; no such assignment or UNSAT proof was obtained.

These local tip tests permit a rook-adjacent tip edge. The exact
[three-edge path](research/grids-and-triangles/two_rook_tip_near_edge.md)
with edges `{0,1}`, `{0,4}`, and `{1,3}` satisfies all Hall masks, all
tip-only common-neighbor caps, and a positive definite tip Gram matrix.
Thus none of those tests, even together, forces the tip graph to use
only rook-nonadjacent labels.
At the [eighteen-edge tip boundary](research/grids-and-triangles/two_rook_tip_rook_boundary.md),
the tips must form a rook graph. Complete coverage of all 5,040 labelled
rook graphs, Hall filtering, Gram kernels, and exact binary propagation
leave 19 labelled cases in two core orbits. A [joint integer proof](research/grids-and-triangles/two_rook_tip_boundary_joint_integer.md)
excludes the eighteen-member orbit without fixing any incidence witness.
The coordinator rebuilt the complete formula, checked retained-clause
membership, and replayed its DRAT proof. Only the complementary-rook
tip graph remains at eighteen edges. Together with the independent
seventeen-edge exclusion, this proves
[`e(Z)<=16` or `Z=J-I-R`, and `4e(Z)+t<=72`](research/grids-and-triangles/two_rook_tip_edge_bound.md),
where `t` counts edges shared by the tip and original rook graphs.
The complementary-rook joint run remains UNKNOWN. Within that case,
the [complete `a=0` incidence class is now excluded](research/grids-and-triangles/two_rook_a0_fixed_completion.md):
fourteen designs have integer Farkas proofs and the two equivalent
remaining designs have a checked binary-completion proof. A separate
[complete incidence proof excludes `a=1`](research/grids-and-triangles/complement_rook_a_incidence.md),
so `a>=2`. The [complete `a=2` incidence census](research/grids-and-triangles/complement_rook_a2_incidence_census.md)
has 576 designs in four orbits of size 144. Exact orbit regeneration and
a checked final blocked-formula proof establish completeness. All four
[complete binary edge models are now excluded](research/grids-and-triangles/complement_rook_a2_fixed_completion.md).
The coordinator rebuilt each full formula, checked every retained clause,
and independently verified all four DRAT proofs. Therefore `a>=3`.
None of these statements excludes a single isomorphic pair.
The [single-source](research/grids-and-triangles/complement_rook_row_projection.md)
and [forced duplicate-pair](research/grids-and-triangles/complement_rook_duplicate_row_projection.md)
binary projections also retain the complete incidence design. All three
signature orbits and all eight duplicate-tip orbits have exact partial
neighborhood witnesses. The latter orbits cover all 21 tip pairs, so this
particular projection excludes no choice. A separate full-domain real
projection has an exact feasible point at `a=36` and no smaller upper bound.
All eight [full joint two-tip splits](research/grids-and-triangles/complement_rook_joint_split.md)
also returned UNKNOWN at their thirty-second budgets. The split coverage
is complete, but no split has an exclusion certificate. This necessary
model has all mixed and packing constraints and omits general exterior
pair caps.
An [exact projector-Schur census](research/grids-and-triangles/complement_rook_projector_schur.md)
forbids 1,296 eligible exterior triangles in nine relabeling orbits.
Direct integer quadratic witnesses certify all nine representatives,
and an independent clause audit checks the complete orbit expansion.
All rejected triangles use three mixed-type signatures. No signature
or eligible edge loses all triangle support, so this is not a core
exclusion.

The [baseline incidence-master pilot](research/grids-and-triangles/complement_rook_incidence_master_pilot_01_results.md)
now gives eight checked signed selector-pattern exclusions. Their source
designs have `a=11,14,12,17,17,17,19,18`. Each proof has a separate
complete-base rebuild, retained-clause inclusion check, and DRAT replay.
The pilot reached its eight-design limit without exhausting the class.
[Static relabeling closure](research/grids-and-triangles/complement_rook_incidence_master_cut_orbits.md)
gives 1,152 distinct necessary clauses. This does not improve the current
global `a>=3` bound or exclude the complementary-rook core.
The [exact incidence implications](research/grids-and-triangles/complement_rook_incidence_core_simplification.md)
shorten those eight patterns to sizes `22,16,18,29,28,18,18,18`.
Quota traces, 34 small DRAT proofs, and 64 exact incidence counterexamples
check the reductions. A separate deletion pilot gives an
[eleven-positive-signature exclusion](research/grids-and-triangles/complement_rook_positive_pattern.md),
with no negative assumptions. Its fresh proof and independent full-base
replay pass. The 144 relabelings replace the older case-one patterns in
a refined 1,152-clause export. No whole-core exclusion or minimality follows.
The [retained-row audit](research/grids-and-triangles/complement_rook_retained_row_support.md)
shows that two of the original proofs fit inside one-core-point subsystems.
The [reduced star models](research/grids-and-triangles/complement_rook_core_star_oracle.md)
keep all incidence selectors and 4,456 eligible incident edges, with 65,774
declared variables and 144,864 clauses. Exact identities remove redundant
population and degree counters, and both transported conditional proofs
pass DRAT. The first [free star pilot](research/grids-and-triangles/complement_rook_core_star_free.md)
returns UNKNOWN and gives no new exclusion.
A [complete local-star census](research/grids-and-triangles/complement_rook_local_star_census.md)
has 864 local signature sets in 118 stabilizer orbits and 2,521 eligible
matching choices on those representatives. All resulting 35-vertex cores
pass visible pair caps and both exact principal-projector tests. This
census supplies complete local cases for stronger incidence models; it
does not establish extension of any case to 99 vertices.
The [35-core attachment model](research/grids-and-triangles/complement_rook_35core_incidence.md)
adds complete Gram quotas, signature uniqueness, and core-triple packing.
A [bounded sweep of the first local set](research/grids-and-triangles/complement_rook_35core_first_local_sweep.md)
checks all 28 matching descriptions: five have full-domain DRAT exclusions
and 23 remain UNKNOWN. Four exclusions cover every matching containing
one specified edge. This gives a conditional forbidden edge and 144
explicitly transported seven-literal clauses. The original local set
still has a [27-core Gram witness](research/grids-and-triangles/complement_rook_35core_local_incidence_control.md);
neither the local set nor the complementary-rook case is excluded.
A separate [case-two continuation](research/grids-and-triangles/complement_rook_35core_case0002_exclusion.md)
now excludes a sixth matching. Exact Gram downdates give 886 additional
pair conflicts, each checked by a full integer negative vector. The
resulting run has a checked UNSAT proof. Its retained inputs use none
of those extra conflicts, so a separate cold replay verifies the proof
directly against the original case-two formula. The excluded matching
indices are now `0,1,2,3,8,21`; the other 22 remain unresolved. The
historical sweep records remain unchanged.
The [six-case matching cover](research/grids-and-triangles/complement_rook_35core_six_case_matching_cover.md)
gives three single-edge restrictions and one two-edge restriction.
Its 144 explicit transports yield 576 distinct clauses, including all
144 previous clauses. The [complete 22-case downdate preparation](research/grids-and-triangles/complement_rook_35core_downdate_preparation.md)
checks 17,612,727 column pairs and gives 1,863 new binary conflicts.
Two subsequent [case-nine and case-ten proofs](research/grids-and-triangles/complement_rook_35core_cases09_10_exclusion.md)
pass direct and cold checks. Their retained proofs need only five of
the extra Gram clauses, each with a small integer negative vector.
At that stage eight matchings are excluded: `0,1,2,3,8,9,10,21`.
A [fixed continuation](research/grids-and-triangles/complement_rook_35core_continuation_terminal.md)
of the other twenty gives three more checked
exclusions, cases `6,7,14`. Every retained input of those three proofs
belongs to its original incidence formula; none needs the downdate
overlay. The other seventeen runs return UNKNOWN. The current excluded
set is `0,1,2,3,6,7,8,9,10,14,21`; the first local set remains open.

On the globally prism-free `x521=0` face, a triangle's cubic shell is
connected on 36 vertices or splits into two eighteen-vertex components.
The [complete split-component census](research/root_prism_free_f0_components.md)
has 66 representatives, with explicit coverage of all 8,992 retained
normalized descriptions. Every exterior vertex must have three neighbors
in each component. A [binary incidence model](research/root_prism_free_f0_incidence.md)
for representative zero has an exact sixty-triple witness satisfying
all 171 Gram positions and 90 additional visible-motif conflicts.
The other 65 representatives were not queried. This witness does not
provide the other component or the exterior graph. A
[connected shell control](research/root_prism_free_f0_connected_control.md)
also has all three central edge types equal to 33, so those types alone
do not force the split.
The [two-component coupling](research/root_prism_free_f0_coupling.md)
has cross Gram block `2J-diag(J6,J6,J6)`. An exact fractional control
uses the first saved incidence and the second component's full domain.
A smaller binary model fixes both sides to the saved sixty-triple
design and has 792 possible assignments. That fixed pair, under the
identity fiber alignment, is UNSAT with a direct proof check, a cold
complete formula rebuild, and retained-proof replay. It excludes only
that fixed pair of designs. The component and the split case remain open.
The [complete component-zero pair](research/root_prism_free_f0_pair_gram.md)
retains all 39,168 compatible columns. Every column passes an exact
rank-thirty-three Gram-downdate screen. A factorization expresses all
inverse products through a 480-by-480 component table. The
[unfixed incidence model](research/root_prism_free_f0_pair_gram_model.md)
uses 1,478,076 variables and 3,173,640 clauses, with complete Gram and
triple-packing coverage. Its single [180-second query](research/root_prism_free_f0_pair_gram_run01.md)
returns UNKNOWN after 181.332 seconds to cooperative return. It gives
no incidence point, proof, or component-pair exclusion.
The [complete two-column downdate classification](research/root_prism_free_f0_pair_downdate.md)
covers 767,046,528 unordered distinct column pairs. Every negative pair
already violates triple packing. All 721,041,624 pairs with intersection
at most two have strictly positive determinants. A separate integer
implementation reproduces the census, so this family gives no new cut.
The [saved first incidence is now excluded](research/root_prism_free_f0_first_design_exterior.md)
by its exterior equations, with every second component and alignment
left unspecified. A complete exterior formula has a checked proof with
120 retained inputs. A separate integer potential contradicts one mixed
row even over nonnegative real neighbor weights. It also gives a
55-term necessary incidence inequality and twelve verified transports.
The full-domain control for that row is feasible, so the target signature
itself is not excluded. A separately prepared model with only the first
incidence fixed was not queried because this exterior proof supersedes it.
Adding the twelve transported row inequalities to the original free
480-selector component model gives another exact incidence witness.
All Gram, profile, motif and new-cut checks pass, as does a separate cold
replay. Its exterior rows and the second component are still unspecified.

## Scope of the unrestricted computations

The [complete rooted binary model](research/root_full_caps.md) starts from
the mandatory root and its fourteen neighbors. All 84 exterior signatures
are forced, and all 3,486 possible exterior edges remain independent.
It imposes every mixed equation and exterior pair cap. The chosen
near-vertex matching has eleven normalization cases. Two independent
audits cover all 10,395 matchings, including explicit signed-axis
transports and a separate orbit-size calculation. The
[builder audit](research/root_full_caps_builder_independent_audit.md)
checks the full domain and encoding, including the 84 necessary
broken-rook implications. A direct nine-rook assignment and 3,069
Boolean controls pass. Each case has 960,414 variables and 1,908,864
clauses. The sequential batch uses 180 seconds per case and records
each outcome separately. All eleven cases returned UNKNOWN, with a total
batch elapsed time of 1,993.537 seconds. No graph or UNSAT proof was found. The
model and coverage proofs are not
nonexistence proofs; every UNKNOWN case remains open.
The [separate lexicographic overlay](research/root_full_caps_lex.md) is
audited and has complete stabilizer coverage and small Boolean controls.
It preserves a labeling of every possible graph by finite-orbit minima.
Its sixty-second pilots on cases zero and ten both returned UNKNOWN.
The [completed run tables](research/root_full_caps_runs_01.md) record
all thirteen outcomes and their exact bindings. A separate
[maximum-anchor convention](research/root_full_caps_anchor_max.md)
also preserves coverage of an eleven-case union; it can move a graph
between the original partition cases. Its [four zero-count cases](research/root_full_caps_anchor_max_runs_01.md)
also returned UNKNOWN in a separate sixty-second-per-case batch.
The [prism interpretation](research/root_full_caps_prisms.md) identifies
the anchor statistic with prism copies through the chosen root. Its
zero cases make that root prism-free. A global choice of root would
be a further normalization and was not imposed in those four runs.
Under the globally prism-free hypothesis, a separate
[matching reduction](research/root_prism_free_structure.md) gives 34,440
necessary four-edge clauses and exact mixed spectral traces. Four partial
controls satisfy every clause and visible pair cap; they are not complete
graphs. The [complete-cap overlay](research/root_prism_free_overlay.md)
retains the older full edge model and all four matching cases.
Its [first four runs](research/root_prism_free_runs_01.md) all returned
UNKNOWN at sixty seconds each. A separately checked
[minimum-anchor normalization](research/root_prism_free_anchor_min.md)
gives shorter component clauses. It was not imposed in those runs.

The [general 39-point triangle identities](research/grids-and-triangles/triangle_root_constraints.md)
show that both principal projector tests are automatic. The visible caps
exclude equal shell-neighbor rows, and the incidence Gram kernel gives
exact fiber and component balances. These identities leave binary
exterior incidence and individual-signature tests unresolved.

- [`subgraph_counts.py`](experiments/workspace/subgraph_counts.py) enumerates all induced graph types through a specified order that avoid a diamond and a (non-induced) K₂,₃. Integer extension equations count outside vertices, neighbors of a marked vertex, and common neighbors of a marked pair. It found no contradiction modulo 2 through order ten (180,445 equations, rank 46,268). [`inspect_counts.py`](experiments/workspace/inspect_counts.py) checks the original equations on all subsets of the 3-by-3 rook graph. Its floating LP reported infeasibility on both 99 and the known 243 parameters. That solver status was spurious on 99.
- [`core_counts.py`](experiments/workspace/core_counts.py) removes a vertex of degree at most two in ordinary injective embedding counts. In the degree-two case the common-neighbor number for the two image vertices is two minus their adjacency indicator. Subtracting previously used image vertices gives a recurrence requiring no unproved subgraph statistics. Minimum-degree-three subgraphs supply the remaining variables. Inverting deletion of edges gives induced counts. The integer solutions in [`core8.log`](experiments/logs/moments-and-counts/core8.log) and [`core9.log`](experiments/logs/moments-and-counts/core9.log) were replayed against every original equation and every nonnegativity and integrality condition. These are count assignments, not graphs.
- [`flag_moments.py`](experiments/workspace/flag_moments.py) sums outer products of rooted flag counts over all embeddings of a root. The two flags may overlap away from the root. The induced version checks compatible identifications and sums over all unknown cross edges. [`flag_separate.py`](experiments/workspace/flag_separate.py) selects integer quadratic-form tests using approximate eigenvectors and writes the resulting exact linear inequalities. A numerical feasible point does not certify a graph or prove feasibility of higher orders.
- [`root_search.py`](experiments/workspace/root_search.py) uses the full rooted pair-label model. Each outer row must have exactly two neighbors incident to an anchor label, reduced by one if that label or its mate occurs in the source. Summing these constraints gives outer degree 12. The remaining inequalities cap shared outer neighbors plus the edge indicator at two minus the number of common anchor labels. The total common-neighbor count in a regular graph forces equality when all upper bounds hold. Matching normalization at anchor 0 covers all eleven partitions of six. [`anchor_seed.py`](experiments/workspace/anchor_seed.py) obtains a starting assignment for the linear constraints only. The 7-cycle used to find that starting point is released during the full search. The generic search recovered the 9-vertex positive control. The bounded 99 runs did not decide existence.

## Conditional construction searches

**A root with 21 grids.** Pair the root's 14 neighbors into seven axes. The 84 outer vertices form 21 cells of four, each labeled by its axes and two signs. Assume every cell completes a 3-by-3 grid through the root. Each cell then induces a square. Distinct vertices of the same square have exhausted all their common neighbors inside the grid. The anchor equations forbid edges between cells that share an axis, and every vertex consequently has one neighbor in each of the ten disjoint cells. The unknown interface on each edge of KG(7,2) is a permutation of four points.

Every such permutation is affine on two binary coordinates. On the three nontrivial sign characters its matrix is a signed permutation with sign product positive. In the orthonormal character basis the near-outer coupling is √2 at the shared coordinate character, and the within-cell nontrivial block has diagonal (0,0,−2). The outer relation obtained from A²+A=12I+2J gives, modulo 2, that the sum of the three character permutations on length-two paths between disjoint cells equals the direct permutation. Between intersecting cells the sum of the six permutations is zero. The six three-letter permutation matrices over GF(2) have precisely one nonzero linear relation (their sum). Thus the three paths between disjoint cells either all have the direct permutation or consist of the direct permutation and two equal permutations. The latter pair could a priori have an even nonidentity holonomy. In the four-point permutation representation the required sum of three holonomy permutations is I+D₁+D₂, where D₁,D₂ are the two double transpositions induced by square opposition at the endpoints. Decompositions of this matrix use only translations or a pair of permutations whose induced nonidentity linear parts are transpositions. This last four-point assertion is checked by direct enumeration in [`check_cover_local.py`](experiments/workspace/check_cover_local.py).

The faces with odd holonomy are therefore both the binary coboundary of edge parities and a binary 2-cycle in the matching complex on seven axes. [`matching_cover.py`](experiments/workspace/matching_cover.py) computes its eight-dimensional bicycle space, all 256 masks, and their four orbits under axis relabeling. After an edge-sign gauge fixes the order-three character labels up to translations, flat-face transport and the equality on pairs of twisted faces are homogeneous linear equations over GF(3). The tree-gauged spaces all have dimension one. [`cover_frames.py`](experiments/workspace/cover_frames.py) enumerates axis assignments using even path multiplicities. Only the nontrivial flat cyclic triple cover survives, up to negation of ternary coordinates. [`cover_signs.py`](experiments/workspace/cover_signs.py) translates parity of the signed path sums into 1,260 binary equations. The compatible frame count is zero even before enforcing all axis inequalities. This excludes this construction family if the reduction is correct. There is no assumption-free implication that any vertex has 21 grids.

**One fixed point of an involution.** Every swapped adjacent pair has a unique fixed common neighbor. For a unique fixed point it must lie in that point's neighborhood. If e is the number of such pairs, the trace of the adjacency on the 49-dimensional odd space gives e divisible by 7, and the involution's action on the seven matched edges at the root gives e odd. Hence e=7. The action swaps all seven signed axes and pairs all 84 outer points into opposite-root pairs. Each far pair has exactly one full interface to another far pair, since its two common neighbors form a swapped pair. In the even quotient the far matrix B has 42 vertices, one double edge and ten single edges per row. If U is the signless axis incidence (each pair of axes occurs twice), then UB=4J−2U and B²+B=12I+4J−UᵀU. The signed lift also has to be satisfied.

We tested an order-seven rotation on the **quotient** taking the seven axes cyclically. There are six far orbits of size seven. The real symmetric row-sum matrix R satisfies R1=12·1 and R²+R=12I+24J. On a nontrivial rotation character the 7-dimensional near/far sector has only eigenvalues 3,−4. Its trace is 1−c, where each nonzero offset has the same total c of within-orbit edges, since a rational linear combination of seventh roots of unity has constant coefficients on the six nonzero offsets. No doubled edge can lie in its own orbit because its mates are a perfect matching and seven is odd. Thus 0≤c≤6, and 1−c divisible by seven gives c=1. Then tr(R)=6 with nonnegative even diagonal and diagonal less than 6 from the row-square equations. Both possible diagonal profiles were exhausted by [`quotient_rows.py`](experiments/workspace/quotient_rows.py) with no matrix. This does not exclude a general involution.

## Sources and replay

- https://aeb.win.tue.nl/graphs/srg/srgtab51-100.html, the (99,14,1,2) entry.
- https://alco.centre-mersenne.org/articles/10.5802/alco.418/, published automorphism restrictions and earlier computer-assisted exclusions.
- https://arxiv.org/abs/2608.11211v3, unrestricted vertex-root reduction.
- https://arxiv.org/abs/2604.23037, prior SAT approaches.
- https://joe975.github.io/math-lab/conway-99.html, prior searches with the partner-regular root assumption.
- https://github.com/YesterdaysLemon/conway-99-research, earlier six- and eight-vertex counts, covariance methods, and many conditional calculations.

The original local Python environment was `/tmp/conway99-tools/venv`. It used NumPy, SciPy, pynauty, z3-solver, python-sat, and threadpoolctl. The [replay guide](experiments/README.md) gives the setup for the main checks. Rebuildable moment caches are generated by [`flag_moments.py`](experiments/workspace/flag_moments.py). The next targets are the unrestricted induced and spectral moment constraints, and construction searches allowing general local neighborhoods.

## Unrestricted outer-edge moments and status audit

Signed permutations of the fourteen neighbors of a chosen root act by relabeling every candidate. Averaging over relabelings gives 275 degree-at-most-two moment classes for the 3,486 binary outer-edge variables, with six fixed-vector moment blocks up to order 134. These blocks suffice to test positivity on the whole space: averaging a coordinate vector over its stabilizer and projecting to any negative eigenspace produces a nonzero invariant vector for at least one coordinate. The first 120 cut rounds found no infeasibility certificate. The nine-vertex rook control passes. The local row degree vector (four ones and ten twos) has 56,011,010 labeled realizations. The independent path/cycle and perfect-matching enumeration in [`row_profiles.py`](experiments/workspace/row_profiles.py) recovers the same number, and yields exactly 486 second-moment count profiles in 42 columns, allowing exact convex hull constraints on these moments.

A J-STAGE workshop paper, Theorem 28, claims nonexistence: https://www.jstage.jst.go.jp/article/jsaisigtwo/2022/AGI-021/2022_01/_pdf/-char/ja . Its equation (88) counts two common neighbors in the outer graph for every non-neighbor there. In fact the outer graph is connected: two labels from distinct components could share at most one original root neighbor, violating mu=2. For a given label {a,b}, the other outer labels sharing a or b number 22; exactly one per endpoint is adjacent to {a,b}. Each of the other 20 has precisely one common neighbor in the outer graph, as the endpoint already supplies the other common neighbor. The remaining 51 non-neighbors have both common neighbors in the outer graph. The right side of (88) thus overcounts by 20, and its stated contradiction fails.

The November 9 revision of Thakkar and Severini (arXiv:2608.11211v3) still states that the existence question is unresolved.
The current PDF of [Natal and Al-saadi, arXiv:2610.16266v2](https://arxiv.org/abs/2610.16266v2),
dated October 24, is titled *A Spanning Subgraph of Conway's 99-graph*.
It gives the mandatory rooted spanning graph and the 84-vertex exterior
spectrum. It does not claim nonexistence. An older indexed title claiming
a sum-of-squares proof should not be confused with this revised paper.

## Four-cycle neighborhoods and lattice restrictions

The determinant proof and the modulo-7 rank bound are in [`square_certificate.md`](research/eigenlattices/square_certificate.md). The four-cycle neighborhood has 48 vertices, four corners and 44 neighbors. The corner codegree equations are identities in [`square_ball.py`](experiments/workspace/square_ball.py). The mathematical filters and the candidate-generation implementation impose no automorphism on the completed graph. The 243-vertex ternary Golay graph verifies the neighborhood extraction and Gram tests on its 80-vertex four-cycle ball. The separate triangle-ball program recovered all 180 correct exterior signatures of the Golay example. Random square-shell switches in the case of absent opposite tip edges returned 352 distinct determinants passing numerical interlacing and exact common-neighbor inequalities; all 352 were nonsquares. This is a sample. The controlled construction [`square_c5.py`](experiments/workspace/square_c5.py) obtained twelve full-rank shells *with* square determinant and fivefold symmetry on the shell. [`square_exterior.py`](experiments/workspace/square_exterior.py) enumerated all feasible exterior signatures by a modular filter and exact rational norms for each. All twelve admitted just the four-tip signature and cannot supply the required 51 vertices. The symmetry was local and the exterior test unrestricted. No global search was exhausted.

An additional integral obstruction excludes an induced 3-by-3 rook graph with a single edge deleted. Write H for these nine vertices and z = (3I-A+J/9) 1_H. It is an integral -4 eigenvector, and its squared norm is 7(27-2·17+9)=14. Every integral -4 eigenvector of squared norm 14 has seven +1 and seven -1 entries: a coordinate of absolute value at least two would require opposite-sign mass at least eight and hence total absolute mass at least sixteen. For each of the seven negative sites there are at least four positive neighbors. The count of pairs of positive sites with a designated negative common neighbor is therefore at least 7·6=42, whereas every pair has at most two common neighbors, giving the matching upper bound 2·21=42. Thus every common neighbor of two positive sites is negative. But the two endpoints of the deleted edge both have z-coordinate +1 and their third vertex on the original rook line has coordinate zero. This is a contradiction. The nine-vertex diamond/K2,3-free catalogue has exactly one 17-edge type, and the preexisting integer witness already sets its count to zero.

The third-order unrestricted outer-edge model is in [`triple_moments.py`](experiments/workspace/triple_moments.py), [`stabilizer_pairs.cpp`](experiments/workspace/stabilizer_pairs.cpp) and [`orbit_arithmetic.py`](experiments/workspace/orbit_arithmetic.py). After Boolean identifications it has 47,226 orbit coordinates, 65,145 linear equalities and 320,061 inequalities apart from coordinate bounds. Root-symmetry averaging permits integral orbit populations after multiplication by each orbit size, with no automorphism required of the graph. The row-primitive integer equations are consistent modulo two, of rank 33,258 on the nonconstant variables. A 180-second ordinary LP time limit did not decide real feasibility. The full model at rook parameters has a feasible exact 0/1 solution.

Prior-art correction: Dilan Djematene's October 2026 archive https://doi.org/10.5281/zenodo.23305123 contains a discriminant proof ruling out order three (including the six-triangle count), a computer-assisted order-two exclusion, and a genus proof of the even rank upper bound 42 on 27I-9A+J modulo 7. Those conclusions predate this project. The archive labels itself awaiting independent review and does not resolve unrestricted existence. Brouwer lists it in the parameter-table references. Keep work on the unrestricted graph.

The eight-core reduction for a missing grid center, which applies without any graph-automorphism assumption, is in [`incomplete_grid.md`](research/grids-and-triangles/incomplete_grid.md). The 27-vertex cores all survive the first exterior-incidence LP. The 243-vertex graph and nine-vertex rook graph serve as controls for the distinct triangle, square, and exact signature procedures. For the third-order unrestricted model, 1,771 moment coordinates vanish by positivity and equality propagation. Joint graph-projector and bit-conditional PSD cuts reduce numerical violations, but no exact infeasibility or exact joint PSD witness has been obtained. Finite partial checks do not decide existence.

Unrestricted global re-rooting. [`hom_moments.py`](experiments/workspace/hom_moments.py) expands 10,395 cubic coordinates involving at most four signed axes into ordinary graph homomorphism counts by inclusion-exclusion over signed axis partitions. All 12 expansions on the 9-vertex rook control agree with direct enumeration. For the target, 65,578 comparisons of permitted reductions on 29,925 initial patterns with at most one axis coincidence give zero additional identities. After the positivity zeros, the rooted integral system admits verified points modulo 3 and 8. The global modulo-8 system links the rooted counts, domain-group Burnside congruences, small graph counts and catalogue congruences. Its 74,221 rows and 51,958 columns admit an explicit point checked by matrix multiplication. Sources: [`global_lift.py`](experiments/workspace/global_lift.py), [`power_two.py`](experiments/workspace/power_two.py), [`global-lift.log`](experiments/logs/moments-and-counts/global-lift.log). Cubic row enumeration gives 8,105 rooted row types, with 6,396 distinct profiles on 299 star coordinates. These are necessary conditions.

Constructions using two nonadjacent centers. [`pair_anneal.py`](experiments/workspace/pair_anneal.py) and [`pair_switch.cpp`](experiments/workspace/pair_switch.cpp) produced a complete incidence assignment of 71 exterior vertices to a 28-vertex core, seed 1. The integer identity B²+B+NNᵀ=12I+2J holds on the entire core. The symmetric exterior incidence LP is infeasible for this particular assignment (HiGHS). The two-center signature and edge-incidence tests retain all 199 exterior vertices and 1,809 exterior edges of the 243-vertex control. This assignment is a partial matrix.

Hoffman coclique construction. A coclique of size 22 would give an incidence matrix C of a 2-(22,4,2) design, with no two blocks sharing three points. Given C, complete block neighborhoods can be enumerated with integer multiplicities: for block b, its ten outside neighbors cover each of b's four points once, the remaining points twice, and no two of these neighbors share two points. Between two allowed block-neighborhood masks X_b and X_c, enforce adjacency symmetry and |X_b intersect X_c|=2-|b intersect c|-1[c in X_b]. These conditions suffice for the full graph. [`coclique_finish.py`](experiments/workspace/coclique_finish.py) reconstructed the nine-vertex control by the same method. A sampled 11-cyclic incidence design was excluded with unrestricted choices of the 77 block neighborhoods. A size-22 coclique is not known to be forced.

[`hemisphere.md`](research/independent-sets/hemisphere.md) gives a uniform fourteen-vertex coclique normalization, via an independent transversal of the seven root-neighborhood edges and a seven-set in the opposite 21-vertex shell. Its expectation argument uses the published Radziszowski–Kreher lower bound for triangle-free graphs. The earlier 13-coclique edge construction is credited to Misha Lavrov in the YesterdaysLemon project. The global rooted/unrooted count system in [`seven_field.py`](experiments/workspace/seven_field.py) also admits a directly verified solution modulo seven (rank 42,449).

The maximal-transversal construction tightens to coclique sizes 14..20, proved in [`hemisphere.md`](research/independent-sets/hemisphere.md). The rank-7 coordinate and homomorphism system passed a direct verification modulo seven. The all-point-marked coclique incidence equations in [`coclique_flags.py`](experiments/workspace/coclique_flags.py) pass 207 exact identities on the nine-vertex rook graph and 7,299 on a maximal 27-coclique in the 243-vertex graph. At h=20 there are eleven initial integer block-size profiles under the root-neighbor positive excess bound. Several survive the order-three real relaxation. A complete star search for two sampled cuts fixing three or five of the seven outer rows reached 25 specified neighborhoods. It did not find a 99-graph.

For size-22 cocliques, the difference-family census in [`coclique_families.cpp`](experiments/workspace/coclique_families.cpp) and the independent-design check in [`coclique_batch.cpp`](experiments/workspace/coclique_batch.cpp) excluded 5,550 mixed and 42,372 pure normalized labeled records under a free 11-action on the incidence design. Every record was checked directly for all point-pair quotas and the triple-packing condition. The completion test propagates unrestricted row domains. The counts can include isomorphic records. For order eleven, one eleven-cycle and eleven fixed points on the 22 points is impossible: every pair of fixed points lies in exactly two size-four blocks, both fixed, giving a 2-(11,4,2) subdesign with nonintegral replication. The conditional computation has no bearing on designs without that symmetry and gives no unconditional graph exclusion. Temporary lists are rebuilt by the two C++ sources.

[`grid_intersections.md`](research/grids-and-triangles/grid_intersections.md) proves g ≤ 120 for the number of induced nine-vertex rook grids. The resulting lower bound on the number of percolating nonedges is 1,998. The seven-vertex extremal inequalities and equality form were exhaustively checked in [`grid_intersections.py`](experiments/workspace/grid_intersections.py). The qualitative two-vertex percolation consequence was already in the public research ledger. An independent affine grid restriction is in [`affine_grids.md`](research/grids-and-triangles/affine_grids.md). [`grid_field.py`](experiments/workspace/grid_field.py) excluded the fixed nine-cell finite-field matching assignment even with arbitrary internal rook labelings. The square populations in [`outer_squares.py`](experiments/workspace/outer_squares.py) pass the complete rook control and the 35,860 corner incidences on the 243-vertex control. In normalized seven-anchor case zero, the reduced 100,136-column system admits a verified solution modulo eight and its real feasibility run timed out.

[`grid_intersections.md`](research/grids-and-triangles/grid_intersections.md) also proves at least 1,188 pairs of disjoint triangles with two cross-edges and at most 15 grids through each vertex. [`root_cover_audit.py`](experiments/workspace/root_cover_audit.py) independently recomputes the exclusion of the 21-grid root. The 17-grid root is impossible by a signed four-cycle argument.

The integral inequality for bᵀ(3I−A)b and the equivalence between a norm-14 integral −4 eigenvector and two maximum cocliques meeting in 15 are in [`shortest_vectors.md`](research/eigenlattices/shortest_vectors.md). In an independent triangle-based route, a single complete triangle star would give 60 exterior vertices, each corresponding to one nonmate pair in each of three twelve-point fibers. The third fiber's attachment problem becomes a simultaneous selection of twelve ten-element sets with specified intersections. [`triangle_free_mates.cpp`](experiments/workspace/triangle_free_mates.cpp) allows the third fiber's entire internal matching and all twelve attachment sets to vary. All 456 cyclic first-two-fiber designs at the two surviving twelve-cycle twists fail this test. The cyclic assumption covers only that local construction.

[`triangle_star.md`](research/grids-and-triangles/triangle_star.md) describes the 48-vertex shell forced by an independent exterior signature. [`level_seven.md`](research/eigenlattices/level_seven.md) derives a scalar theta-series obstruction at modular ranks 28, 30, and 32. Exact rational certificates and a separate eta-product verifier leave the five ranks 34, 36, 38, 40, and 42.

[`nine_cosets.md`](research/eigenlattices/nine_cosets.md) records the reduction to a determinant-49 maximal lattice, translated-shell identities, and a degree-ten single-coordinate test with an integral feasible count assignment. The maximal extension is a relaxation of every possible graph rank.

[`positive_lattice.md`](research/eigenlattices/positive_lattice.md) describes the separate determinant-eleven gluing in the positive eigenspace and an injection of all six-site lifts of a fixed mass. In the negative eigenspace, [`six_coset_floors.py`](experiments/workspace/six_coset_floors.py) proves an analogous lower bound in every translate by isolating the only possible six-site collisions.

Prior-art correction: ProofAtlas's August 2026 Conway research record already reports elimination of 28, 30, and 32 by different opposite-star methods. Our rank frontier is an independent confirmation. See [`level_seven.md`](research/eigenlattices/level_seven.md) for the source and distinction.

The cube-class argument in [`cube_shells.md`](research/eigenlattices/cube_shells.md) gives joint bounds on the two shortest integral shells. The rank-34 through rank-40 averaged maximal-extension scalar tests in [`averaged_extensions.py`](experiments/workspace/averaged_extensions.py) remain rationally feasible. [`shell_profiles.py`](experiments/workspace/shell_profiles.py) and [`profile_refinement.py`](experiments/workspace/profile_refinement.py) test exact coordinate profiles against the common-neighbor equations; actual rook and ternary Golay eigenvectors pass the neighborhood identities.

## Global constraints and exact partial-completion certificates

The coordinated work in [issue 2](https://github.com/1337isnot1337/conway-99/issues/2)
is recorded in [the session log](research/session-ab2f.md). It adds necessary
conditions and exact exclusions, but does not decide existence.

The earlier [all-red bound of three](research/grids-and-triangles/red_grid_three_bound.md)
has now been strengthened by the three-base result linked above.
The complete four-base matching census has 136 assignments. Exact integer
negative Gram vectors exclude 124; explicit isomorphisms identify the
other twelve with one core. That core permits only 27 distinct outside
neighborhoods, while 63 outside vertices are required. The finite replay
uses no SAT assumption. Independent five- and six-base checks give weaker
confirmations: a Petersen boundary obstruction and both a direct
backtracker and a checked DRAT proof. The earlier covering arguments below
remain independent intermediate results.

[The all-red grid argument](research/grids-and-triangles/eight_red_exclusion.md)
proves that at most seven grids can have all six triangles contained in six
grids each. Eight would leave a 27-vertex graph. Its nontriangle edges form
cycles on the vertices belonging to exactly two internal triangles. A
rational invariant-subspace calculation leaves twelve spectra on five
cycle partitions. Local alternating vectors eliminate two partitions;
the other three give a common three-cover of K3,3 and violate a compression
trace bound. Two independent spectral enumerations agree, and all 1,296
normalized three-covers are checked exactly. The
[preliminary nine-grid argument](research/grids-and-triangles/red_grid_limit.md)
uses a double covering and an elementary complementary-neighborhood proof.
A separate
[aggregate grid-line model](research/grids-and-triangles/grid_flag_relaxation.md)
has an exactly checked integral count assignment at 120 grids using the old
bound of seven all-red grids. It fails the stronger all-red restriction and
is retained only as a witness for that earlier relaxation.

[Transversal coclique constraints](research/independent-sets/transversal_constraints.md)
show that a size-twenty coclique containing seven neighbors of a root has
exactly one outside vertex of degree seven into the coclique and no outside
vertex of degree one. These elementary proofs recover two previously
numerical profile exclusions. Four of the 56 degree-feasible axis patterns
are excluded by saved integer Farkas identities. The other 52 pass the
examined real incidence relaxations, including the additional integer
vertex-degree cuts. Neither PSD feasibility nor real incidence feasibility
constructs a graph.

[Coupled norm-16 shells](research/eigenlattices/coupled_shells.md) force even
components in the two deficit multigraphs and the partition
`8+8+8+64+11`. The 8-point high class has at most one edge, and the 11-point
zero class has five or six edges. The previously archived 4,985 labeled
incidence templates reduce to 478 classes under side-preserving isomorphisms.
Seventeen classes fail a direct counting inequality and fourteen further
classes have checked DRAT exclusions. The other 447 classes have explicit,
directly checked partial adjacency witnesses. They represent 4,720 of the
original templates. This reduction is conditional on a norm-16 vector;
exact rational witnesses show that forbidding both norm-14 and norm-16
vectors still leaves the current scalar-theta relaxation feasible at ranks
34, 36, 38, 40, and 42.

[The zero-class structure](research/eigenlattices/coupled_zero_structure.md)
narrows its induced graph to eleven forest types, all witnessed at the
represented high/zero overlap level. An
[independent aggregate linear model](research/eigenlattices/coupled_shells_linear.md)
gives integer Farkas proofs for ten of the fourteen SAT-excluded templates.
These strengthen verification, not the total of 31 excluded classes.

[A minimum Ramsey hemisphere](research/independent-sets/transversal_hemisphere_minimum.md)
with 21 vertices, 35 edges, and independence number seven admits a root-label
assignment passing both exact core spectral tests. Its exterior incidence
relaxation is numerically feasible. This demonstrates that the tested local
criteria do not force an independent eight-set in every hemisphere.

[Incomplete-grid completion constraints](research/unrestricted-completion.md)
prove that an induced rook grid with its center absent forces an independent
set of at least sixteen vertices. Across the eight resulting 27-vertex
cores, exact support certificates remove 172 exterior incidence signatures.
All eight cores remain unresolved. One integral assignment of 72 exterior
signatures satisfies the core Gram equations and additional pair constraints,
but an exact certificate excludes its exterior-edge completion. That result
excludes the particular assignment, not its starting core.

`make verify-global-constraints` replays the integer and rational certificates
and witnesses. `make verify-coupled-shells DRAT_TRIM=/absolute/path/to/drat-trim`
regenerates the norm-16 census and replays all 478 results using the separately
built, pinned proof checker. [The replay guide](experiments/README.md) specifies
the dependencies and distinguishes partial witnesses from completed graphs.

The later [cubic trace argument](research/grids-and-triangles/red_grid_cubic_trace.md)
gives a shorter closure of the all-red bound of seven. Three-base matching
holonomies have a rook character determined by their fixed-point counts.
Counting their triangles yields an additional cubic trace identity, which
fails on all twelve spectra of the exact cycle census. This proof does not
use the three-cover enumeration; the covering proof remains available as an
independent route.

[Stronger norm-16 completion tests](research/eigenlattices/coupled_zero_completion.md)
reject 265 specified H/Z cores by integer negative quadratic vectors. A
separate row Farkas certificate and a checked DRAT proof for a 58-bit pattern
in the canonically labeled full-incidence model reject further specified
partial choices. These checks leave the 447 whole incidence classes
unresolved. All whole-template and time-limited solver outcomes remain
separate from these fixed-point certificates.

[The seven-grid remainder](research/grids-and-triangles/seven_red_residual_reduction.md)
has 36 vertices. Its number of vertices in exactly two internal triangles
is divisible by nine. The zero case fails an elementary spectral trace
condition, and the nine case fails a complete census of 408 residual cores.
An independent implementation reconstructs the catalogue and characteristic
polynomials, then checks all 1,695,332 factor-multiplicity tuples. None passes
the cubic identity. The remaining counts are 18, 27, and 36; seven all-red
grids have not been excluded. `make verify-seven-red-residual` replays this
exclusion and is included in the global-certificate target.

The subsequent [four-cover reduction](research/grids-and-triangles/seven_red_four_cover_reduction.md)
excludes the count 36. A complete census of 331,776 normalized covers of
K3,3 removes the connected case through edge-fiber counts and three small
coloring certificates. The disconnected cases reduce to four rook grids.
A [negative rook-space compression](research/grids-and-triangles/seven_red_four_rook_exclusion.md)
then contradicts a nonnegative polynomial trace. Independent explicit
isomorphisms and coloring checks cover every surviving connected assignment.
Only the counts 18 and 27 remain in this seven-grid reduction.
