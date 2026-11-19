# Global constraints research session

Starting revision: `21aedce941ec7e139f43672c65069fac03091aee`.
Coordination: [issue 2](https://github.com/1337isnot1337/conway-99/issues/2).
Branch: `research/global-constraints-ab2f`.

## Active investigations

1. Prepare the complete rook case-four model on the 112-zero face with both parity equalities and the certified pair rows. All 1,102 surviving selectors and every original row/cover remain represented. Complete unbranched propagation is finished. Owned by the independent-set worker.
2. Prepare an exact equivalent F0 model eliminating the 162 proved zero edge columns. Preserve all old obligations, all 92 held PSD directions, explicit transport maps and exact duplicate/box-tautology witnesses. The joint PSD/clique query and exact audit are finished; its invalid numerical vector is not used for another cut scan. Owned by the completion worker.
3. Prepare a complete rook Boolean branch cover. The original 72 parity patterns reduce to 64 after the new zero, certified pair and direct native pair-box exclusions. Reuse the full primary propagation engine and every cover, with explicit positive branch assumptions and bounded complete-prefix records. Owned by the literature worker.
4. Root publishes the native-bound theorem, strengthened Boolean model and its bounded UNKNOWN terminal, and reviews the new branch and full-model gates. There is no unchanged Boolean retry. The remaining native-bound objectives require a separately defined continuation. The global binary incidence rank bound remains 88.

The separate worker in issue 1 owns the incomplete-grid corner graph,
arbitrary-square extensions, complete-grid corners, and twenty-point
diagonal cubic graphs. This session does not duplicate those domains.

## Starting boundary

The repository proves necessary conditions and excludes specified construction
families. It contains neither a complete adjacency matrix with the target
parameters nor a contradiction covering all candidates. The claimed proximity
to a solution is therefore not a proved result.

The target remains a graph satisfying the exact adjacency identity
`A*A + A = 12*I + 2*J`, or a contradiction applying to every such graph.
Numerical infeasibility, a timed-out search, and failure of sampled designs do
not meet that target. New reductions will be checked on known graphs when
their hypotheses permit them; computational exclusions require exact replay.

## Work log

- Checkpoint 58: the small 1,103-variable native model makes 48 objective attempts, with 47 numerical optimal returns and one time limit. Five exact bounds are accepted. A new zero at column 663 and the rounded pair inequality for (259,590) strengthen the integer face. The other three pairs are already forbidden by Gram row 580. Refining the saved multiplier vector at denominator six gives `3*x663+sum_S x=2` for 86 columns, with no unit-box correction. Independent checking reconstructs all original rows and the full 1,214-coordinate identity.
- Full exact propagation from the 112 zeros, H1=H2=1 and four pair rows finishes with no additional assignment or contradiction. All 178,533 covers remain included. The resulting complete LP has 1,102 variables, 166,010 rows and 10,767,167 nonzeros. Its numerical query is a separate continuation.
- Root's strengthened Boolean formula preserves the 439,689-clause prefix and appends 1,475 clauses, using 170 fresh auxiliaries for a proved 86-variable sum of two. All 508 small counter controls and the independent production suffix/source checks pass. One 180-second CaDiCaL child times out after loading all 441,164 clauses; the parent kills and reaps it. The 4.708-second cold formula/terminal replay preserves UNKNOWN. No partial proof is accepted.
- The remaining 41 local F0 models are all SAT in one 8.466-second batch. Independent native acceptance and an 8.419-second cold model/CNF rebuild check every witness. Including center 355, all 42 local types pass these separate projections. A 354-member lossless archive retains every formula, witness and failed preparation/control record, with fresh-directory restoration checked.
- The 21-PSD/258-clique F0 model has 15,200 variables, 28,043 rows and 1,086,559 nonzeros. Native transport, exact new-row reconstruction and source reuse gates pass. Its single 180-second IPM child reaches 21 iterations and a time limit, with both validity flags false and no exact phase. The finite saved vector fails all 6,135 equalities and 1,110 inequalities under exact dyadic evaluation; every violation exceeds 1e-8 after the recorded scaling. All bounds hold. No feasibility or infeasibility follows from the numerical status; cold terminal and point-audit replays pass.

- Checkpoint 57: the complete two-parity-cover rook query gives an exact zero-face certificate after two native calls. Its short direct proof is a signed sum of 42 original Gram rows: H2 plus twice twelve selectors equals one after the earlier 99 zeros. Nonnegative integrality forces twelve new zeros and H2=1. The 1,214-coordinate direct identity and the complete 169,052-row bound replay pass; a separate checker imports none of the proof code.
- Complete propagation of all 2,271 native rows, both parity rows and 178,533 original coordinate covers leaves exactly 111 zeros and no positive units or contradiction. H1 has 36 live terms and H2 has 42. Original signature capacity 51 then gives the additional equality H1=1, because H1 is odd and at most two. Independent checking expands all 33 H1 and 42 H2 Gram rows and the capacity. The two unit sums give a disjoint 32-plus-40 pattern cover of Boolean solutions.
- The corrected F0 joint scan performs three numerical decompositions and 89 exact candidate evaluations, retaining sixteen selector and five full-core plus inequalities. It reaches its cooperative deadline after 61.1198 seconds. Exact replay validates all saved attempts and 21 retained rows. Known-zero substitution and equality-orientation filtering precede acceptance; significance heuristics are not claims of linear independence. The earlier serialization failure and all preparation failures remain preserved.
- The center-355 Boolean pilot is SAT, with selected signatures 69, 73, 174, 201, 212, 284, 435 and 475. All 16,105 CNF clauses, eighteen demand equations, 5,495 conflicts and visible common-neighbor caps pass. A complete 210-matching diagnostic gives eight two-edge and two three-edge extensions; a separate checker validates all ten. These are local witnesses, not graph completions.
- Root's 34,974-trial weighted local-clique scan retains 128 tiny positive-gap rows. Exact zero substitution identifies all 128 as existing equality orientations. A separate full-column checker verifies 1,945,600 coefficients. No retained row is appended; no redundancy claim covers the other 59 unsaved candidates or unsearched cliques.

- Checkpoint 56: the rook equality-only problem has a signed integer solution from one 286-square exact solve. All 632 original equalities and 99 zeros pass both full and standalone checkers. The 1,214 coordinates include 92 negatives and 67 values above one, with range -10..19. This resolves the signed-integer target without satisfying the Boolean model.
- The complete parity family consists of 286 saved binary basis equations and their 40,755 unordered pair XORs. Distinct pivot subsets prove all 41,041 supports are nonzero and distinct. The 9.374-second exact scan finds two 42-column lower covers, with gaps 214021056/1661041997 and 428042112/1661041997 at the old exact point. Their 33- and 35-native-equation parity proofs remove only 14 and 15 previously proved zero coordinates. A separate 9.166-second replay verifies every distance and both full 1,214-coordinate lifts.
- The final F0 path overlay preserves all 15,200 variables and the parent row/scaling prefixes, adding 5,124 rows. It has 6,135 equalities, 21,629 inequalities and 905,276 nonzeros. Its native transport and direct new-witness replay pass. One numerical run returns optimality after 33 IPM iterations and zero crossover iterations, with 159.223 seconds under the supervisor. No dual ray exists; the exact phase is skipped. The terminal result remains UNKNOWN after a 13.72-second cold replay. All failed and interrupted preparation versions are retained separately.
- Root prepares the full three-selector triangle/perimeter scope, validates all actual-core actions, and scans 4,808,202 anchor pairs per family at the fresh numerical point. No positive numerical candidate is found. All 258 published core-pair clique inequalities pass exact dyadic evaluation; the largest gap is about -0.0074264343. The 4.674-second cold replay certifies these exact clique gaps, not every unretained numerical row.
- The local conflict inventory finishes all 42 representatives in 7.332 seconds. The first cold run stops after twenty centers; a separately bound 4.385-second suffix replays only the remaining twenty-two and checks their complete union. The path layer adds 57,996 literal conflicts beyond the mixed/core-pair layers; 9,504 semantic motif incidences remain outside the prior homogeneous layers. These are incidence counts, not independence or exclusion claims.

- Checkpoint 55: the complete rook native-equality inventory contains 632 original equations. After the 99 proved zeros, 236 are empty identities and 396 distinct nonempty equations remain, with 13,706 nonzeros in 1,115 variables. The exact modular batch takes 5.605 seconds. Every field of order 19, 601, 145463, 2, 3, 5 or 7 has rank 286 and nullity 829, with no fixed-coordinate congruence. Both row-space inclusions and all saved modular points pass a separate 3.077-second Python-integer replay. No rational-rank or integer-feasibility conclusion follows solely from these field ranks.
- The three-exterior/two-edge prism census covers 107,520 configurations, reducing to 107,418 distinct exterior paths. Known edge zeros and single mixed quotas remove proved redundancies. The remaining 61,476 paths give 5,124 quotient rows, including two rows of the form 2Y-x<=0. All 61,488 actual-core transports pass. Production takes 13.245 seconds; cold replay takes 9.727 seconds. Together with the one-edge family and the absence of a possible three-edge split, this covers the stated exactly-three-exterior prism scope.
- Root's common-core-pair edge-clique theorem gives sum_{a: i,j in h_a}Y_ab<=x_b. Its complete 73,440-bucket inventory retains 3,096 buckets after known edge zeros and simple quota consequences. A 3.206-second construction gives 258 distinct rows with 2,802 nonzeros; all 3,096 transports and a separate 3.147-second replay pass. The largest bucket contains twelve edges. These remain edge constraints; coexistence of two signatures is not excluded.
- The combined F0 model retains 15,200 variables and both old row prefixes, adding 162 zero equations, 39 Schur inequalities and 715 mixed prism inequalities. It has 6,135 equalities, 16,505 inequalities and 889,906 nonzeros. Cold reconstruction, independent source reviews, scaled-ray controls and a native matrix transport check pass. The smallest scaled coefficient is 9/2^30, above the solver's input threshold; every native coefficient and bound matches. This preparation remains unrun while a separate overlay adds the already proved 5,124 path rows. No later family delays that one planned query.

- Checkpoint 54: the saved rook basis reduces to a 287-square integer system and yields an exact full selector point with denominator 1661041997 and minimum 17835088/1661041997. All 1,115 surviving selectors lie strictly between zero and one. Full 169,050-row face acceptance plus 2,271 native rows and 178,533 original covers pass; cold replay calls no solver. The complete current real relaxation has no further coordinate-zero or coordinate-one consequence.
- The separate rook Boolean formula retains every original clause and appends exactly 85 proved negative primary units, for 439,689 clauses and 134,852 variables. Its single 180-second CaDiCaL300 child times out and is reaped; no partial proof is accepted. The 28-second cold full-formula/unit replay preserves UNKNOWN. The exact point denominator factors as 19*601*145463; the modular continuation accounts for this before any consistency search.
- The complete F0 edge-motif census covers 5,805 actual-core edge orbits and 68,394 literal edges. It finds 1,884 prism-forbidden edges in 162 orbits, with no visible F in this two-exterior-vertex family. Independent disjoint-triangle and eight-cycle checks agree and verify every transported witness. All old Boolean model rows pass at the previous exact point, but nine new Y-zero rows fail there.
- The next visible-prism family has 9,360 configurations with three exterior vertices and one exterior edge. The pointwise implication y_ab*z_c=0 gives Y_ab+Z_ac<=x_a and Y_ab+Z_bc<=x_b. After known Y/Z-zero simplifications, 8,580 literal rows reduce to 715 distinct three-term quotient inequalities. Complete literal replay and an independent mathematical/source review pass.
- Full 21-core Schur conditioning subtracts dot(d_a,d_b)/2 in the plus family and 77/410+11*dot(d_a,d_b)/24 in the minus family. Direct rational 20/21-core inverses match all 115,440 entries per family. The eighteen-core scan returns 17 valid integer cuts and the full-core scan returns 22; all exact proposal gaps replay. Tiny minus gaps are explicitly marked as possible numerical null-identity defects. The complete pair-minor census rejects twelve edge states; separate full 23-vertex integer vectors have quadratic value -165240.
- All 127,296 five-root coordinate/signed-pair vectors and 366,356 integer shifts pass at the immutable count point. The new six-root family retains all 2,374 classes for thirty triangle-containing roots; all 180 matrices pass in 27.511 seconds and replay in 22.483 seconds. It covers genuine order-ten products, but does not cover the other 32 roots. Scalar triangle-class moments are consequences of the earlier flag span.

- Checkpoint 53: ten graph-specific dual-code inequalities follow from equal generator columns, triangle replacements, triangle toggles, weighted chains and triangle-containing supports. The complete 109-row coding relaxation has exact optimum 52183040/17817. An independent checker verifies all primal rows, every dual sign and column, and the five active multipliers. The rank bound remains 88. Two earlier formal integer enumerators fail the new graph conditions; neither constructs a code.
- The complete rook 99-zero-face LP reaches numerical optimality with positive minimum selector value in one 10.441-second native call. Coordinatewise rational recovery fails. The terminal record and full cold replay preserve UNKNOWN. The independent forced-upper transportation census finds 170 support equalities, all redundant after existing Gram rows and the 99 zeros.
- The F0 model with all 32 exact augmented-selector cuts reaches numerical optimality after 29 interior-point iterations and 9823 crossover iterations. Rational reconstruction fails, and the saved active face exceeds the fixed recovery cap. The terminal status is UNKNOWN. The lossless numerical archive and both exact terminal replays are retained.
- All 40 additional four-root graph-projector blocks pass exact PSD. The complete five-root preparation covers all 21 roots and 1296 triangle classes. All 126 matrices pass in 17.198 seconds, with a separate 13.377-second cold replay. No separator is obtained. All sources, preparations, exact results and bounded query records are retained.

- Checkpoint 52: three-triangle chains give exactly 24948-9g distinct weight-five words in the binary dual code. The bound g<=120 gives 23868 such words. The exact coding optimum 140594432/35063 is below4096, so kernel dimension is at most11 and incidence rank is at least88. A complete6435-host collision census and independent recurrence/rational checks pass. The earlier star-word query gives rank85 and is preserved.
- The rook transportation calculation gives88 zeros from six short original-row certificates; adding the14 earlier cover units gives99 distinct zeros. The seeded105-projection closure finds no further zero or contradiction. All projected flows and zero certificates replay exactly. The complete1115-column LP is prepared separately.
- The joint F0 reduction proves exact selector-row rank132 and retains all original conditions in15200 variables. Its simplex query is UNKNOWN. The separately frozen IPM query reaches numerical optimality but fails exact rational recovery. One augmented-selector PSD scan supplies32 integer-certified cuts against that proposal. A cut-augmented model is a new continuation.
- All eight five-root and thirty six-root conditioned triangle blocks pass exact PSD at the immutable count point. The six-root preparation covers2374 classes and230648 tensor terms, with674 direct host controls. The two other triangle spectral projectors remain separate from this family.

- Checkpoint 51: the binary point-triangle kernel has nonzero weights only 36,40,44,48,52,56,60. One exact coding LP gives dimension at most22. Forced dual words of weights3,4,6 strengthen its existing dual certificate to dimension at most17, hence incidence rank at least82. This second step uses no optimizer. Independent recurrence and rational-column checks pass. No lower bound on kernel dimension is assumed.
- The rook 81-zero-face run uses two native calls totaling3.54seconds and adds four original covers. Its final exact certificate needs no added cover: two original Gram equations plus the triple capacity at{5,15,27} force18 columns zero, six new overall. The full1214-column short proof uses no prior zero premises. The total is87; the whole branch remains open.
- The first joint F0 second-moment run reaches its time limit with no valid basis, exact point or ray. Its lossless seven-file numerical archive and two terminal replays preserve UNKNOWN. An exact equivalent reduction is prepared separately; the unchanged model is not retried.
- Both conditioned triangle blocks, all nine complementary blocks and both reconstructed scalar blocks pass exact PSD and cold replay. The scalar blocks follow from the existing complete four-root flag span; they are not an independent family. The larger-root census finds257 classes at eight roots of order5 and2374 classes at thirty roots of order6. Its failed first bookkeeping attempt is preserved with the corrected census.

- Checkpoint 50: exact cover compression preserves the complete rook case-four real relaxation. One bounded row-generation call exposed a zero-maxmin certificate. Its four native Gram rows give 24 additional Gram-only zeros; one was already a cover unit, so 23 are new overall. The short proof is independent of numerical optimization. All 81 known zeros pass complete original-row propagation and cold replay, with no new assignments and no integrality-dependent step.
- The saved F0 point passes all 4,416 Boolean-normalized cuts exactly. The full 480-selector/68,394-edge baseline remains intact. Root's independent integer replay verifies the new coefficient-sum quotient and every full cut. No repeated LP was launched. The new joint-moment preparation has 9,742 pair orbits, 15,589 variables, 7,165 equalities and 46,122 inequalities. Its 389 zero-pair-orbit equalities have direct nonnegative lifted-row or motif certificates. PSD conditions are recorded separately.
- The four-root triangle projector has a complete 352-class disjoint preparation and a complete 574-class extension. Both nine-block families pass exact characteristic-polynomial tests. The full family also passes 189 incidence-kernel checks. Direct ordered-pair host controls and independent tensor contractions fix the normalization. Per-embedding fixed-triangle conditioning is a separate stronger query.
- The decorated root-42 distribution has two even fifth moments. Every pair in [0,8764] times [0,966] is feasible, and no other pair is: explicit atom rows prove the upper bounds, and all four corners pass the original moment equations, nonnegativity and divisibility. The full refined high-graph feature lattice is Z^200 after the correct orbit-total factor720; no extra congruence follows from that lattice alone.

- Checkpoint 49 publishes the recovered 363-member F0 transcript. Its 4,404 proved cuts, 94 checked candidates, 64 full or partial row passes, 3,701 exact row boxes and 14 exact shared-edge obstructions pass a fresh optimizer-disabled replay. The original bounded run remains UNKNOWN. The misleadingly named terminal-registry seed contains only 2,928 cuts; the final registry is in the archived run directory.
- The recovered refined high-graph measure has 200 positive rational masses of denominator 988761395399693539 and total mass 72,926,995,680. A portable audit checks all 200 original moments, 400 exact projector characteristic polynomials and 200 shifted integer-incidence inequalities on its support. It does not claim a new replay of every removed domain column.
- All 33 decorated small-root models pass exact direct replay: 1,275 states, 1,092 positive masses, 183 zero masses. The separate root-42 presence model has the exact even interval [0,9794] for its one missing fifth moment; zero yields 241 positive masses and 12 zero masses. Independent root replays import neither query nor inversion helpers.
- The earlier 33-root presence, full F0 fractional-baseline and interrupted full rook max-min results remain as recorded in checkpoint 48. No finite-measure certificate is promoted to a graph construction or unrestricted exclusion.

- Inspected the research ledger, public claims, and existing issue ownership.
- Started separate spectral, independent-set, and completion investigations.
- Replayed `make verify` successfully: the seven-axis inequalities, all twelve
  root-cover cases, three rational theta certificates, and support enumeration
  passed. The output is in `experiments/logs/session-ab2f/baseline-verify.log`.
- Added a fixed-transversal core formulation. At size twenty the exact degree
  budget leaves 134,085 labeled patterns in 56 orbits. Both small projector
  matrices are positive semidefinite in every orbit; this test adds no
  exclusion. Exterior-signature tests are in progress.
- Added core-incidence enumeration and exact integer triple packing. The rook
  and Golay controls and an exact Farkas orientation control pass. Initial
  time-limited packing searches on the eight incomplete-grid cores are
  inconclusive.
- Reconstructed the existing norm-16 exterior templates independently. The
  4,985 templates and 8/64/11 exterior partition already occur in
  `signed_eight_heavy.py`; they are not new exclusions. The current work adds
  an algebraic even-cycle proof and full incidence-orbit classification.
- Proved that a size-twenty transversal coclique has exactly one outside
  vertex of degree seven into it and no outside vertex of degree one. Four
  universal-axis patterns are excluded by saved integer Farkas identities,
  independently replayed without spectral pruning. The other 52 patterns
  survive the tested real incidence relaxation.
- Proved that there are at most nine all-red grids, without assuming equality
  in the total-grid bound. Ten would force an eleven-grid partition with
  isomorphic interfaces, contradicting the trace on an invariant subspace.
- Completed the norm-16 full-incidence census. Seventeen classes fail an
  elementary four-vertex counting inequality; fourteen more fail a partial
  adjacency model with saved DRAT proofs. The remaining 447 classes have
  directly checked partial witnesses. This excludes 265 of the original
  4,985 labeled templates, leaving 4,720. The coordinating worker rebuilt
  every proof formula and replayed all fourteen proofs with a separately
  compiled checker. A separate worker audited the encoding and found no
  unsound restriction.
- Proved that the high class in the norm-16 partition has at most one edge
  and its eleven-vertex zero class has five or six edges. The scalar-theta
  relaxation remains exactly rationally feasible at ranks 34 through 42
  even when the norm-14 and norm-16 shells both vanish.
- Proved that an incomplete eight-vertex grid forces an independent set of
  size at least sixteen. Exact integer support tests remove 172 exterior
  signatures across its eight cores; none of the cores is excluded. A
  stronger integral incidence assignment for core five was constructed,
  then ruled out by an exact exterior-edge certificate. Four subsequent
  refinement cuts are sound; the next search timed out.
- Combined grid-line multiplicities, root types, and the all-red bound in an
  aggregate model. A saved integer witness satisfies every represented
  condition at 120 grids. This does not improve the global grid bound and
  does not construct a graph.
- Strengthened the all-red bound from nine to eight. Nine disjoint all-red
  grids would leave eighteen vertices whose twelve triangles form a double
  covering of K3,3. The connected case has at most four possible covering
  involutions, each usable twice; the disconnected case forces the impossible
  eleven-grid invariant-subspace trace. Two separate workers audited the
  proof, and a standard-library enumeration independently checked the finite
  covering count. The proof does not depend on that enumeration.
- Classified the norm-16 zero-class graph into eleven forest types. Each
  type has a directly checked high/zero witness. A separate aggregate model
  supplies 61 integer Farkas branch certificates, including complete
  independent proofs for ten of the fourteen SAT-excluded templates. All
  447 partial witnesses pass exact projection into that model; there are no
  additional template exclusions from this check.
- Exhibited a minimum 21-vertex Ramsey hemisphere of independence number
  seven with an exact root-label spectral witness. Its exterior incidence
  LP is numerically feasible and the bounded Boolean run is undecided.
  This records a concrete limitation of the current local hemisphere route.
- Strengthened the all-red bound again, from eight to seven. The remaining
  27 vertices in the eight-grid case split into points lying in two or three
  internal triangles. The nontriangle edges are cycles; an invariant-space
  identity forces their lengths to be multiples of three. Two independent
  exact calculations leave twelve spectra on five cycle partitions. Local
  six-cycle vectors and a common-covering trace bound exclude all twelve.
  The full proof and the 1,296-cover certificate audit passed two separate
  worker reviews and the coordinating worker's `make verify-red-grid-bound`.
- Proved that the ternary Hamming graph H(3,3) cannot occur as an induced
  subgraph. Boundary counting would require seventy-two distinct compatible
  neighbor triples, while only thirty-six exist. A standard-library control
  checks the finite Hamming counts.
- Found a second closure of the eight-grid case. The rook eigenvalue-one
  character of each three-base holonomy gives a cubic trace identity. It
  fails on all twelve surviving cycle spectra, so the shorter proof does
  not need the three-cover census. Integer companion-matrix cubes and
  direct 27-by-27 holonomy controls verify the coefficients and all cases.
- Added 265 exact negative Gram-vector certificates against specified
  35-vertex norm-16 partial cores, a 25-row integer Farkas certificate, and
  a checked DRAT proof for a 58-bit canonical H/Z pattern with all low
  incidences free. These reject partial choices, not additional complete
  incidence classes. The full-template symmetry run remained undecided.
- Tightened the seven-grid remainder using the cubic trace identity. The
  number of vertices in exactly two internal triangles is divisible by
  nine. The zero case fails an elementary trace condition. A complete
  catalogue of 408 nine-vertex residual cores has no permitted spectrum.
  An independent replay uses a different extension generator, leaf-twin
  quotient polynomials, rational Sturm tests, and Newton sums. It checks
  all 1,695,332 multiplicity tuples, leaving the counts 18, 27, and 36.
  Seven all-red grids remain possible under these necessary tests.
- Replayed all fifteen saved DRAT proofs and all 447 partial witnesses
  after the fixed-core additions. Every replay passed. Continued the
  norm-16 search in six models fixing the three proved zero forests for
  each of two doubled-edge support templates, with the old zero-label
  ordering removed. Time-limited runs are recorded as undecided.
- Completed all six fixed-forest incidence runs. Each reached its
  sixty-second limit with status UNKNOWN. No candidate or proof was
  produced, and the 447 unresolved incidence classes remain unchanged.
- Excluded the common triangle system in the seven-grid remainder. Its
  24 triangles give a four-sheeted cover of K3,3. All 331,776 normalized
  covers were enumerated. Connected covers fail an edge-fiber bound or
  one of three verified coloring certificates; disconnected covers reduce
  to four rook grids. A separate negative rook-space polynomial then has
  trace at most -8 despite being nonnegative on the required spectrum.
  Two workers independently checked the final algebra. The cover audit
  verifies all 2,736 surviving assignments by explicit isomorphisms. This
  leaves counts 18 and 27, without excluding seven all-red grids.
- Replaced the seven-base case split with a smaller interface obstruction.
  The six-base local model is UNSAT with a checked DRAT proof and an
  independent direct backtracker. Exhaustive four-base controls agree on
  all 1,331 assignments, retaining 136. Exact negative Gram vectors remove
  124, and twelve explicit isomorphisms identify the one remaining core.
  It has only 27 possible distinct outside signatures and needs 63. This
  proves at most three all-red grids. A separate five-base census has 564
  local assignments; 552 have exact Gram exclusions and the twelve others
  reduce to an independently excluded Petersen core.
- Excluded three disjoint rook grids whose matching interfaces are all
  rook isomorphisms. The eleven maps reduce to identity, reflection, and
  translation. They fail respectively by 36 available signatures for 72
  vertices, six available neighbors where eight are required, and the
  exact incidence identity `0=54`. The translation case also forces 81
  distinct signatures for 72 outside vertices. Independent dense and
  bit-mask constructions agree on all matrices and signatures.
- Proved an elementary closure: an all-red grid and any disjoint grid
  joined to it by a rook isomorphism force a forbidden third rook grid.
  Hence there is at most one all-red grid by this independent argument.
  An integer weighted sum of global flags gives `29g-4b<=3465`, verified
  on all 2,097,152 labeled root graphs and 1,596 grid profiles. This gives
  at most 119 grids and at least 2,016 percolating nonedges.
- Read the latest parallel work in issue 1 and PR 3. Its separate
  intersecting-red-triangle exclusion already gives the stronger bounds
  `b=0` and `g<=114`; its later `2e2d7ed` gives at most thirteen grids
  through any point. Our independent weaker bounds are retained as such.
  Workers stopped the all-red followup to avoid duplicating that work.
  The new active lane is the completion of two isomorphically matched
  rook grids and more general three-grid interface obstructions.
- Completed the general two-arm census. Of 2,720 possible third interfaces,
  explicit symmetries give 59 classes; exact quota propagation excludes 58.
  The last has two checked 72-column incidence witnesses. A fixed-point
  Farkas certificate rejects the first witness, while the joint real model
  has exact rational points, even with all core-pair packing inequalities.
- Proved independent star and short-cycle obstructions. Every grid has at
  most two isomorphic partners by 324 explicit quota violations. Separate
  arguments exclude four- and five-cycles. A dense integer audit checks
  all 23,328 four-cycle assignments, all 23,328 five-cycle prefixes, and
  all 2,592 extensions of the eight surviving prefixes.
- Excluded the last two-arm class by a full unaveraged binary model with
  168 signature and 9,846 edge variables. No lazy cut or orbit equality was
  used. The coordinating worker regenerated the 1,151,148-clause formula,
  checked retained-clause membership, and verified the DRAT proof. An
  independent implementation checked the complete domain and logical
  constraint families, 62,692 packing clauses, and 37,888 Boolean controls,
  reproducing the same CNF hash. Together with the disjoint-partners lemma,
  this proves at most one rook-isomorphic partner per grid. A separate
  CP-SAT implementation matched the domain and passed a nine-rook control;
  its bounded target run remained UNKNOWN during presolve.
- Replayed the ordinary suite of the parallel root-grid branch at
  `2e2d7ed`. Its larger full-axis replay completed support sizes zero
  through eighteen before being interrupted to relieve resource contention
  during the new independent proof audits. No completed full-axis replay
  is claimed from that interrupted run.
- Constructed an exact integer zero-grid witness for the existing
  order-nine count system and all 584 selected cached moment blocks.
  It satisfies all 23,189 original extension equations, all 6,535
  nonnegative induced counts, and zero broken-rook count. Saved integer
  triangular congruences turn every moment matrix into a strictly
  diagonally dominant positive matrix. An independent audit checks count
  normalization, all 429,428 congruence entries, and fixed-width overflow
  bounds. The verifier now computes coefficient-sum bounds with Python
  integers and rejects noninteger congruence entries. This establishes
  minimum grid count zero in the stated finite relaxation, without
  constructing a graph or deciding stronger flag constraints.
- Continued the single-pair case with all 81 exterior vertices present.
  The baseline 60-second run found two partial graphs and 1,939 necessary
  cap clauses. An independently justified ordering of the 36 duplicate
  pairs compares only their adjacency vectors to the nine fixed tips;
  its 180-second run returned UNKNOWN without another point. Exhaustive
  Hall certificates leave 103 of 256 tip neighborhoods and supply 1,377
  propagation clauses. The strengthened 180-second run found 31 partial
  graphs and 30,446 additional cap clauses, then also returned UNKNOWN.
  Direct integer replays check all 33 saved graphs and all 32,385 distinct
  cap witnesses. No full graph or two-grid exclusion was obtained.
- Derived the necessary tip condition `3I-R+J-2Z` positive semidefinite
  in two ways: a rational Schur congruence and an exterior spectral
  projector. Exact certificates check both original partial tip graphs.
  The first has a kernel-integrality obstruction, but its tip four-clique
  already violates common-neighbor bounds. No new whole case is excluded.
- Read the parallel branch's `006cce9` checkpoint and updated the current
  total grid bound to its stronger value 113. Its full-triangle component
  work remains separate. The active completion follow-up replaces lazy
  cap separation with every exterior common-neighbor bound in one model.
- Audited the 31 Hall-run tip graphs exactly: 26 have positive definite
  tip matrices and five have negative integer vectors. All five already
  violate tip-only common-neighbor bounds. The 21 cap-compatible saved
  tip graphs have no edge in common with the original rook graph; a
  signed-incidence factorization makes the tip matrix automatically PSD
  throughout that subcase. This observation motivated a separate small
  test of whether the tip cap and Hall conditions force disjoint edge sets.
- Refuted that local implication with the three-edge tip path `{01,04,13}`.
  It passes all 1,377 Hall clauses, every tip-only common-neighbor cap,
  and an exact positive definite Gram certificate. The 36-variable SAT
  model has 3,394 clauses and returns this point; direct arithmetic replay
  independently checks it. Its feasibility concerns only the tip projection.
- Replaced all lazy exterior caps by a complete forward-path/cardinality
  encoding: 3,240 pair caps, 226,044 path variables, 778,752 total variables,
  and 1,556,032 clauses. All 3,069 Boolean controls and 100,440 independent
  pair comparisons on the saved points pass. Two readers checked the
  existential encoding and the degree-sum argument making a SAT point a
  full graph. The proof-enabled 180-second run ended UNKNOWN after 317,782
  conflicts. It supplied no graph or impossibility certificate.
- Exhausted the eighteen-edge tip boundary. Cauchy-Schwarz and the tip
  caps force an abstract rook graph. Two independent generators agree on
  all 5,040 labelled graphs. Hall masks leave 89 in six root-automorphism
  orbits; exact Gram kernels and binary margin propagation leave 19 in
  two orbits. The exported domains keep every candidate signature and
  all certified forced values. Joint incidence/edge tests are a separate
  next step, without choosing a fixed 72-column witness.
- Extended the exact zero-grid certificate to all 832 cached spectral and
  Schur projector blocks. The preliminary numerical screen found no
  violation. The exact certificate then checked eight explicit kernels
  per block and integer positive-definiteness congruences on the remaining
  principal matrix. Generation reread and verified the saved compressed
  artifact. Together with the original 584 blocks, 1,416 blocks pass at
  the same integer count point. This is still a finite relaxation witness.
- Derived the duplicate-pair compression `6I-D` positive semidefinite of
  rank at most 28, together with exact exterior spectra and an aligned-tip
  triangle restriction. In the complementary-rook tip case, a complete
  `a=0` incidence census has sixteen designs in orbits of sizes 12, 2, 2.
  Exact integer Farkas certificates exclude fourteen fixed designs. The
  remaining orbit has a rational mixed-edge and packing witness, with
  21 of its 33 edge-orbit weights fractional. No whole-core exclusion or
  positive lower bound on `a` follows from this linear test.
- Excluded the eighteen-member rook-tip boundary orbit by a joint binary
  model retaining all 188 possible signatures and 12,010 eligible edges.
  No incidence witness or orbit equality was fixed. The coordinator rebuilt
  its 1,424,532-clause CNF, matched the hash, checked all 3,667 retained
  input clauses, and verified the trimmed DRAT proof. The complementary
  252-signature case returned UNKNOWN after 205.562 seconds on a requested
  200-second budget. The independent real-LP attempt on the first case
  also returned UNKNOWN and is not an additional proof.
- Rebuilt all 5,311 cap-compatible nine-vertex types. There is one
  seventeen-edge type, the broken rook, and one eighteen-edge type, the
  rook. The norm-fourteen argument excludes the former. Combining the
  new boundary proof with this catalogue gives `e(Z)<=16` or `Z=J-I-R`.
  The Hall inequality then gives the weighted bound `4e(Z)+t<=72`.
- Excluded the last complementary-rook `a=0` incidence orbit with a
  complete binary-edge model: all 1,764 possible edges and all 2,556
  exterior caps. Its 593,820-clause formula returned UNSAT. The coordinator
  replayed the complete sixteen-design census and the earlier fourteen
  Farkas exclusions, rebuilt the full formula, checked retained inclusion,
  and verified the DRAT proof. Thus `a>=1` in this boundary case. The
  complementary-rook case with positive `a` remains unresolved.
- Read the parallel branch's `9c58d1d` result, which improves its global
  total to 112 grids and bounds full triangles by 24. Our next computation
  returns to an unrestricted mandatory-root model. Its anchor-matching
  normalization and positive control are being audited before any batch.
- Built and independently audited the unrestricted mandatory-root model.
  Its 84 exterior signatures are forced, and all 3,486 possible edges
  remain free. Every mixed equation and exterior cap is present, with
  285,852 path variables. The 84 broken-rook implications use the
  unconditional norm-fourteen proof. Each normalized formula has
  960,414 variables and 1,908,864 clauses. Direct nine-rook and free
  normalized controls pass, as do 3,069 exhaustive Boolean controls.
- Three coverage calculations agree on all 10,395 anchor matchings and
  eleven orbits. The independent certificate saves an explicit signed-axis
  transport for every matching and separately traverses generator orbits.
  Root reviewed the complete domain, runner, status handling, source
  binding, and proof wrapper before starting eleven sequential 180-second
  runs. Model construction and coverage do not exclude any case.
- Excluded complementary-rook `a=1` using all 252 incidence selectors
  and a checked DRAT proof. Together with the complete `a=0` exclusion,
  this gives `a>=2`. A complete selector-only census finds 576 `a=2`
  designs in four orbits of size 144. Root regenerated every blocking
  clause and orbit, rebuilt the final formula, and replayed its proof.
  Complete exterior edge tests for these four representatives are separate.
- Read the external `51329e0` checkpoint, which reduces full triangles
  to at most 22 while retaining the total grid bound 112. Its forbidden
  nine-triangle cover does not immediately exclude the complementary-rook
  core: an exhaustive partition check on that core's 27 triangles finds
  no partition into nine triangles with only zero or three cross-edges.
- Tested a possible parity shortcut on the complementary-rook incidence
  system. The 180 equality rows have rank 154 over the binary field;
  the coefficient vector defining `a` is outside their row span. Thus
  these equalities alone do not give a forced parity for `a`.
- Excluded all four complementary-rook `a=2` incidence orbits with
  complete binary edge models. Each has 1,764 independent edges and
  all 2,556 exterior caps. The solver returned UNSAT in every case;
  retained cores have 289, 499, 655, and 1,833 input clauses. Root
  independently rebuilt all four complete formulas, checked their hashes
  and retained-clause inclusion, and verified the four DRAT proofs.
  This excludes all 576 designs and strengthens the necessary bound
  to `a>=3`. It does not exclude the whole complementary-rook core.
- The first two unrestricted root cases, with matching partitions
  `(1,1,1,1,1,1)` and `(1,1,1,1,2)`, returned UNKNOWN after their
  180-second budgets. They produced no graph or impossibility proof.
- Built the full complementary-rook real incidence/edge projection before
  averaging over its 144 core relabelings. It keeps all 252 candidate
  signatures and 20,934 eligible edges. The averaged system has 182
  variables, 54 equalities, and 517 inequalities. Exact rational primal
  and dual witnesses agree at `a=36`; all point denominators divide four.
  Thus this particular linear relaxation gives no smaller upper bound.
  Binary single-row neighborhood tests are the separate next step.
- All three binary single-source projections admit exact partial witnesses.
  Each retains the full 252-selector incidence and a complete local
  neighborhood matching. A separate matrix replay checks all incidence
  entries, known pair caps, and the local matching without importing the
  SAT builder. No signature orbit is excluded.
- Derived the unrestricted 39-point triangle-core identities. The cubic
  shell has no repeated open-neighbor row exactly when its visible core
  caps hold. Its Gram rank is `35-c`; fiber and component balances exhaust
  the kernel. Both principal eigenspace projector tests are automatic.
  The exact counts are `sum e(D[h])=36-3f` and `t(C60)=32-f`, where
  `f=fix(Q)`. Root replayed the integer and rational controls. No general
  triangle core was excluded. Saturated-triangle spread work remains
  with the external branch.
- Extended the exact subgraph reduction to order ten: 48,965 types and
  549 ordinary core coordinates. Two 30-second numerical probes tested
  the fixed order-nine zero-grid point and a free-prefix zero-grid model.
  Both reached their limits without a primal point or certificate. Their
  source/status audit preserves this UNKNOWN scope. A separate feasibility
  formulation with rigorous count bounds is being prepared.
- The forced duplicate RS pair has 21 possible unordered tip pairs.
  Its verified four-element core stabilizer gives eight orbits. Both
  complete source neighborhoods, their matching edges, their required
  disjointness, and the full incidence design are jointly feasible in
  every orbit. Root replayed all eight partial witnesses directly. No
  tip-pair choice is excluded. The next split uses the complete joint
  incidence/edge/packing model rather than only two source rows.
- Prepared a separate lexicographic overlay for the unrestricted root
  formulas. All eleven stabilizers were independently enumerated among
  the 46,080 signed-axis maps and reproduced by generator closure.
  The finite-orbit minimum argument preserves coverage. All 55,824
  solver-based Boolean controls, the nine-rook controls, and 784 direct
  independent existential controls pass. No large overlay solve was
  started during the original batch.
- The original unrestricted rooted batch finished all eleven cases.
  Every case returned UNKNOWN at its 180-second budget; no graph or
  UNSAT proof was found. Total batch time was 1,993.537 seconds.
  The separately audited lex pilot then started cases zero and ten
  at sixty seconds each. Its result is recorded separately.
- Both lex pilots also finished UNKNOWN, in 60.248 and 60.425 seconds.
  The separate maximum-anchor convention preserves the union of its
  eleven new cases, but it may change an original partition case.
  Its controls pass; no maximum-anchor solve is included in this checkpoint.
- All eight complementary-rook full joint two-tip splits returned UNKNOWN.
  The independent audit checks complete tip-pair coverage and exact
  assembly of the unchanged base plus two positive selector units.
  No incidence witness or symmetry of the completed graph was imposed.
  Full exterior pair caps remain absent from this necessary model.
- Scaled order-ten feasibility separates the published order-nine point.
  An exact nonnegative integer combination of 52 induced inequalities,
  fifteen proved upper bounds, and 31 nonnegativity bounds gives
  `-67377959`. Root independently reconstructs all rows and bounds,
  including separate automorphism-order checks. This excludes only
  that frozen prefix. A free-prefix numerical proposal fails exact
  count verification and remains a proposal.
- Simplified the 52-row count certificate by recognizing denominator-36
  weights. Every positive new-coordinate coefficient disappears.
  The resulting universal inequality is an integer sum of 52 induced
  counts and 21 ordinary counts; no upper bounds remain. Its value at
  the frozen point is `-2564720`. Root independently checks all embedded
  source forms against the exact cache and reconstructs this identity.
- Exact principal-projector tests on all 48,965 induced types through
  order ten exclude only the rook graph plus an isolated vertex.
  The explicit integer quadratic witness has value -8. The only
  singular passing types are the rook graph and the rook graph with
  one pendant vertex. This test adds no zero-grid restriction.
- Read the current four-page arXiv2610.16266v2 PDF. Its revised title
  is *A Spanning Subgraph of Conway's 99-graph* and it does not claim
  nonexistence. Its mandatory rooted reduction agrees with the model
  already in use. The older indexed sum-of-squares title is superseded.
- Read the parallel `b611eb7` and `a39ef45` checkpoints. Their new
  eight-triangle exclusion leaves only pencil full-triangle components,
  bounds full triangles by 21, and gives at least 1,215 two-edge
  disjoint triangle pairs. Their total grid bound remains 112.
- All four maximum-anchor zero-count cases finished UNKNOWN. This
  separate normalization preserves an eleven-case union, not each
  original same-index case. The run took 246.918 seconds in total.
  Case nine's delayed interruption is retained in its actual time.
- Scanned the first free order-ten proposal against all 1,416 cached
  moment blocks. Four exact integer vectors reject it. A separate
  bounded loop added those inequalities and the universal count cut,
  found a new proposal, and rejected it with nine more exact vectors.
  The next LP round hit its thirty-second limit. No feasibility or
  infeasibility conclusion follows from these numerical searches.
- Audited all 180,445 original order-ten extension equations after
  exact reduction. Every equation vanishes coefficientwise, every
  induced form has integer coefficients, and ordinary forms have the
  required automorphism divisibility. No extra equality or congruence
  is missing from the reduced model.
- The complementary-rook Schur census excludes 1,296 eligible exterior
  triangles in nine size-144 orbits. All single signatures and pairs
  pass both projector tests. Root replayed the exact census and also
  independently checked the nine full thirty-vertex integer witnesses
  and all exported clauses without using an inverse. All forbidden
  triangles use three mixed-type signatures; every source and eligible
  disjoint edge retains triangle support.
- The separate prism-zero order-ten IPM run returned a numerical proposal
  in 16.925 seconds. It keeps all fourteen certified inequalities. Exact
  rounding gives two induced counts equal to minus one, with no
  divisibility failures. No integer-vector separator was found among
  the 1,416 cached PSD blocks, which does not certify their PSD status.
  The initial metadata failure made zero solver calls and is preserved.
- Read the parallel `f494f2f` six-grid exclusion and integer checker.
  That branch now reports at most 105 grids and twenty full triangles,
  at least 2,268 percolating nonedges, and at least 21 triangles on at
  most two grids. Its full 919,143-core replay remains separate from
  this branch's checks. Its generic crossing and transitive 60-point
  exterior investigations remain reserved to the external worker.
- Repaired the prism-zero point by changing only coordinate 549 from
  five to six. Root independently reconstructed all 48,965 counts,
  checked all 180,445 original equations, and directly identified
  all 1,443 prism-containing types as zero. The unchanged older prefix
  now has exact certificates for all 1,416 cached PSD blocks, with
  separate owner and coordinator replays. This is a finite relaxation
  witness, not a graph. New order-ten moment blocks remain untested
  by that certificate.
- Improved all 549 ordinary-core upper bounds by subtracting used
  vertices in the embedding recurrence. All 76 small rook controls
  pass, including every vertex order. The repaired point satisfies
  all improved bounds; its largest count-to-bound ratio is below 0.44.
- The baseline incidence-master pilot completed eight designs with
  `a>2`; all eight conditional calls were UNSAT. Fresh explicit-unit
  proofs and all eight separate full-formula rebuild/DRAT replays pass.
  The pilot stopped at its design limit, not exhaustion. Removing only
  unused units and closing the patterns under the 144 core relabelings
  gives 1,152 distinct non-subsumed clauses. Root replayed this closure.
- Read Theorem 1 and Lemma 2.4 of Makhnev and Nirova's 2006 slender
  partial-quadrangle classification. It explicitly retains the
  `(99,14,1,2)` parameter set; the classification is not an exclusion.
  Source: https://m.mathnet.ru/php/getFT.phtml?jrnid=al&option_lang=eng&paperid=161&what=fullt.
- Eleven new order-ten induced moment blocks reject the repaired
  prism-zero point. Their roots have eight vertices and their flags
  add one vertex. A separate direct-graph implementation reconstructs
  every product and reduced cut. Owner and coordinator replays pass.
  The coordinator's first replay was killed with exit 137; a serialized
  retry passed in 8.984 seconds. That failure is preserved separately.
  The full reusable cache has all 916 roots with no point-dependent
  pruning. The previous 1,416-block PSD certificate remains valid.
- Exact incidence implications shorten all eight checked signed patterns
  to sizes 22, 16, 18, 29, 28, 18, 18, and 18. The package has 34 small
  DRAT proofs, 64 exact Gram counterexamples, and replayed quota traces.
  A separate case-one deletion pilot removes its last negative assumption
  and four positive assumptions. Its final eleven-positive pattern has
  a fresh proof and independent full-baseline replay. The eleven other
  deletion queries were UNKNOWN, so no minimality is claimed. Static
  relabeling gives 144 positive patterns and a refined 1,152-clause export.
- Global prism-freeness yields 34,440 necessary four-edge clauses from
  seven near-axis matching comparisons. Exact controls, an independent
  clause census, and overlay/wrapper reviews pass. All four complete-cap
  pilots returned UNKNOWN at sixty seconds each, taking 245.594 seconds
  in total. The separately checked minimum-anchor component encoding
  was not used in these runs. No root case is excluded.
- Read the parallel branch's `935a9f1` and `182df61` triangle-exterior
  argument. It gives the exact exterior spectrum, excludes vertex-transitive
  exteriors by a finite group calculation, and characterizes walk-regular
  exteriors by full triangles. The group census was not replayed here.
  That worker now owns the eight incomplete-grid cores; this branch
  retains the count, complementary-rook, and prism-free matching lanes.
- Exact prism-containment closure fixes 58 ordinary coordinates and
  makes all 1,443 prism-containing induced forms vanish coefficientwise.
  The simple one-row sign rule alone fixes only 28 coordinates. The
  stronger closure uses direct motif containment, not an LP inference.
- A one-round count loop with those zeros and all 25 certified cuts
  returns an exact integer count witness with x521=116. Its numerical
  precursor survives the two complete separator scans, with one
  unconfirmed small negative in the older family. Root independently
  checks all 48,965 saved integer counts and 180,445 original equations.
  The rounded point has no exact PSD certificate.
- The ten-vertex, seventeen-edge motif F has ordinary and induced count
  x521. Its exact edge-shell interpretation gives 3*x1+2*x521<=4158
  unconditionally, and x521=e24+3*e222 in a prism-free graph. The zero
  face for globally minimal shell types 33 or 6 also has an exact count
  witness after one IPM call. Independent full-model and original-equation
  replays pass. All 2,332 moment blocks are scanned at this integer point
  without finding an exact or unconfirmed numerical negative. No graph
  or exact PSD certificate follows.
- Exact binary flag triangle inequalities give no additional cut at
  either the earlier repaired witness or the new positive-x521 rounded
  witness. Each complete scan checks 170,183,860 inequalities. These
  finite inequalities do not describe all Boolean moment constraints.
- Attributing every retained input of the eight joint proofs to its
  original equation shows that cases four and five fit inside a single
  core-point star. Their two reduced formulas have 144,864 clauses.
  Exact identities remove population and degree counters; all 18 R/S
  transports and both renamed conditional DRAT proofs replay. The free
  R8 pilot returns UNKNOWN after 63.825 seconds to cooperative return.
- A complete local R0 census gives 864 signature sets in 118 orbits and
  2,521 eligible matching choices on the representatives. All 35-vertex
  cores pass visible caps and 5,042 exact projector checks. No local case
  is excluded. These cases now seed full 35-core incidence work.
- The new count replay target rebuilt the catalogue and passed both
  original-equation audits. The edge-component checker completed its
  mathematical checks, then its report rejected a relative certificate
  path. The Makefile now supplies the absolute path; the target passes.
- Six-root flags with up to two free vertices produce eighteen exact
  order-ten moment cuts against the positive-x521 count witness. Sixteen
  also reject the x521-zero witness. A separate graph constructor
  reproduces all 374,505 product entries used by the eighteen forms.
  These are exclusions of saved points, not either entire count face.
- The reusable six-root family now includes all 62 roots and 14,348
  flags, with 3,913,479 lower-triangle entries. The seven larger blocks
  complete the earlier 55-block scan. Independent domain and product
  controls include flags whose value can be two; no binary diagonal
  shortcut is used. All 7,812,610 exact flag-range inequalities pass
  at each of the two saved points, yielding no further separator.
- Read the latest issue-one coordination: the external worker now owns
  the 48-point incomplete-grid corner graph, its fiber-transitive
  classification, arbitrary-square extensions, and 20-point diagonal
  cubic graphs. Our count, complementary-rook, and prism-free shell
  work remains separate. The external new classifications have not
  been independently replayed on this branch.
- The first 35-core binary incidence query is UNSAT with a fresh proof,
  independent attachment/row audit, full cold formula rebuild, and DRAT
  replay. The same local eight-signature set still has a 27-core Gram
  witness with parameter a=10, so the stronger attachment constraints
  supply information absent from those Gram rows.
- The full first-local-set pilot covers 28 matching descriptions. Cases
  0, 1, 3, 8, and 21 have checked exclusion proofs; the other 23 are
  UNKNOWN. Cases 0, 1, 8, and 21 cover every matching containing one
  specified edge. Exact matching coverage and endpoint activation give
  a seven-literal conditional edge clause. All 144 core relabelings
  produce distinct clauses with explicit transports. The local set
  itself remains open.
- On the globally prism-free x521-zero face, the triangle shell is
  connected or splits into two eighteen-vertex components. A complete
  census covers 8,992 retained descriptions by 66 representatives.
  Every exterior vertex has three neighbors in each component. The
  first component's binary incidence model is SAT with sixty distinct
  triples, all 171 Gram positions, and 90 visible-motif conflicts checked.
  Its cold formula/witness replay passes. A connected shell with all
  three central edge types 33 prevents an invalid split inference.
- The full six-root count loop adds three exact cuts. Independent direct
  products reconstruct all 15,979 supported entries and their reductions.
  Changing x525 from 119 to 118 repairs the next rounded count point;
  every original equation and all 47 retained inequalities then pass.
  The complete integer-point scan of 2,394 blocks finds no separator.
- The complete four-root/three-free and two-root/four-free families add
  eleven blocks. The C4 block rejects the repaired point. Independent
  direct products reconstruct its 39-term inequality. A separate exact
  symmetry decomposition gives an eighteen-term variance inequality.
- The 48-cut model, with x521 also fixed to zero, returns a new exact
  integer count point without repair. A separate checker verifies all
  original equations, all saved induced and ordinary reduction rows,
  every bound and required zero, and all 48 inequalities. All 2,405
  blocks are scanned at the unrounded proposal without a separator.
  At the integer point, the C4 block separately has an exact rank-13
  PSD certificate. The full selected family is not certified PSD there.
- An exact case-two Gram downdate census gives 886 new pair conflicts.
  A non-author audit reconstructs every column and checks each full
  integer negative vector. The overlay query is UNSAT. Its retained
  proof uses zero downdate clauses, and a separate cold original-only
  formula/proof replay passes. Six first-local matchings are now excluded;
  the other 22 remain unresolved. The old UNKNOWN record is preserved.
- The split-shell cross Gram matrix is `2J-diag(J6,J6,J6)`. An exact
  fractional control fixes one saved component incidence and averages
  the other over six actual core automorphisms. A separate binary model
  fixing both incidences has 792 assignments and is UNSAT with direct
  and cold DRAT checks. This excludes one fixed design pair and alignment;
  it does not exclude either component or the complete split-shell case.
- All 22 then-unresolved local cores have complete exact downdate
  preparations, accounting for 17,612,727 column pairs. The six-case
  matching cover gives 576 conditional clauses under explicit relabeling.
  Two subsequent pilots exclude cases nine and ten with direct and cold
  checks. Their retained proofs need only five additional Gram clauses;
  small integer vectors certify those clauses. Eight of 28 matchings are
  excluded, and a bounded continuation of the other twenty is prepared.
- The full component-zero pair keeps all 39,168 columns and fixes neither
  incidence design. Exact rank-thirty-three Gram and inverse identities
  pass an independent review. Its complete streamed CNF has 3,173,640
  clauses. One 180-second proof-enabled query ends UNKNOWN, returning at
  181.332 seconds. It yields neither an incidence point nor an exclusion.
- The new C4 integer scan checks all 265,720 small-coefficient shifted
  quadratic inequalities and finds no cut. A stronger exact certificate
  represents all fifteen flags' first and second moments by 75 integer
  atoms with positive rational weights. A separate literal constructor
  checks every matrix entry. This closes the pointwise integer quadratic
  route in those flags at this point, without realizing graph neighborhoods.
- The complete eight-root projector build covers all 916 roots and 3,664
  blocks at the latest integer count point. Exact contractions and nine
  kernel checks per block pass. Numerical separation finds no direction;
  no exact PSD certificate follows. All 29 reusable cache chunks are kept.
- The same cache gives exact class-size second moments. All 68,176
  optimal shifted-integer quadratic inequalities pass. This tests every
  integer shift for each class, without an eigensystem or optimizer.
- Seven-root absence-conditioned moments reduce to parent-minus-child
  congruences. A residual quota-one pair makes 4,478 cases positive sums
  of child matrices. The complete remaining domain has 737 cases over
  82 roots, with 48,785 coefficientwise selected-row checks and a literal
  control that includes a size-two child class. A bounded scan is prepared.
- The fixed twenty-case rook continuation finishes with three new
  exclusions, cases six, seven and fourteen. Their retained proofs use
  only original incidence inputs, with separate cold replays. Seventeen
  other queries return UNKNOWN. Eleven of the first local set's
  twenty-eight matchings are now excluded; no whole local set is closed.
- A complete two-column screen for the component-zero pair has no new
  conflict. All negative pairs already violate triple packing, and every
  pair with intersection at most two has a strictly positive determinant.
  Independent native and vectorized integer censuses agree on all counts.
- The complete fixed-first exterior model is UNSAT after forty-four
  conflicts. Its direct and cold proof checks retain only 120 inputs.
  Independent attribution places them in one exterior row. An integer
  potential gives a nonnegative-real counting contradiction for that row,
  then a necessary 55-term incidence inequality with twelve transports.
  An explicit eight-neighbor full-domain control prevents incorrectly
  excluding the target signature. The unused first-fixed coupling query
  is superseded; no second component was needed for this proof.
- All 737 single-flag complements and all 916 scalar child blocks are
  scanned at the integer point without a separator. Stronger clique
  localizers use a complete 477-clique universal census. Root restrictions
  and quota-one reductions leave 3,939 cases. Verified root automorphisms
  cover them by 711 representatives. All selected rows vanish exactly;
  the preparation supplies no exact PSD certificate.
- The complete 711-representative clique scan finishes without an exact
  or unconfirmed numerical negative. It covers all 3,939 remaining cases
  by the saved congruences. This closes that proposed separation family
  at the current point, without certifying exact PSD.
- The twelve exact exterior-row cuts reject the old component incidence.
  A fresh free-selector query gives a different sixty-triple incidence,
  sharing fifty-two triples with the old one. Every new inequality and
  original constraint passes an exact check and a cold replay. Exterior
  row-capacity separation is the next test; this is not a graph.
- The replacement incidence also fails extension: a complete sixty-row
  capacity pass finds three exact integer deficits and fifty-seven exact
  rational box witnesses. Independent domain, capacity and relabeling
  checks pass. One deficit has a direct counting form: eight neighbor
  triples must supply seventeen incidences into a specified set, but
  every available triple supplies at most two.
- Two new exact case-four row inequalities seed a sixty-second LP loop.
  It checks 848 row proposals and adds fifty-eight further integer cuts.
  Complete positive-support checks finish in the first two rounds;
  nineteen rows remain unvisited in the third. The last twenty cuts were
  not followed by another global query. All sixty cuts replay exactly,
  but no matching case is excluded and no proposal is certified feasible.
- The complete visible-pair count scan tests 811 representatives and
  finds no separator. A separate prism-free preparation adds 1,155
  genuine incompatibilities, all classified by induced paths on four
  root vertices. Two complete clique constructions and exact zero-support
  checks prepare 1,225 representatives without using the count point.
- A separate six-root double-absence identity gives 1,112 candidate pairs
  in eighty-four root orbits. All 88,326 selected-row coefficient checks
  pass. A JSON-key comparison limitation in the frozen constructor's
  embedded replay is documented; a separate wrapper cold-replays the
  unchanged domain successfully. The complete point scan finds no exact
  or unconfirmed negative and does not certify PSD.
- The free 480-selector loop finds a third component-zero incidence.
  All sixty rows have exact rational box witnesses. An independent
  arithmetic audit checks them; they certify individual rows only.
- The third incidence fails the shared symmetric edge equations. An
  exact Farkas ray has fifty-eight nonzero multipliers, maximum absolute
  multiplier five, and right-hand side minus two. Every standard-form
  column is nonnegative, including all upper-bound slacks. The cold replay
  passes. Nine supported row potentials lift this contradiction to a
  universal selector cut and twelve core transports over all 68,394 edges.
  The normalized cut has five positive and 163 negative coefficients.
  Its value at the saved incidence is two; the incidence is not assumed
  in the cut's proof. Component zero remains open.
- The full symmetric real-edge case-four model has 276,792 variables and
  590,165 rows. Its single sixty-second LP query returns UNKNOWN. All
  integer matrix arrays cold-replay, but no feasible point or Farkas ray
  is available. The next test encodes the sixty proved cuts in the
  original Boolean incidence formula.
- The prism-free clique scan finishes all 1,225 representatives without
  an exact or unconfirmed negative. Six-root products of two clique
  absences have a complete 3,283-case preparation with 347 root orbits.
  Exact primitive identities certify all 41,413 union rows. Their point
  scan is separate from this preparation.

- The combined free-selector loop rejects five more incidences. Eleven
  individual-row obstructions yield 132 transported cuts. A fifth
  incidence passes all sixty individual rows but fails the shared LP
  with an exact Farkas right-hand side of minus one. Eight of twelve
  new signed cuts fit before the fixed variable ceiling stops encoding.
  All twelve are saved, and the complete five-candidate transcript passes
  a cold replay. This is an encoding limit, not an UNSAT conclusion.
- A separate carry-save/ripple encoder preserves all 192 proved cuts,
  including the four unencoded transports. Its complete formula has
  100,296 variables and 620,370 clauses. Full Boolean controls, an
  independent gate audit, and cold formula reconstruction pass. The
  original thresholds and parent transcript remain unchanged.
- The sixty-cut case-four Boolean query returns UNKNOWN. A complete
  intrinsic-row census then gives fourteen direct support-dominance
  exclusions, twelve new beyond its earlier explicit units. Every
  augmented target passes exact mod-two and mod-three span membership.
  The next preparation collects all coordinate-difference cover clauses.
- The corrected clique-pair scan completes 347 representatives without
  a separator. The exact four-class atom screen passes all 10,864,739
  expressions. The five-class integer-sum screen passes all 72,699,792
  signed functionals at their minimizing integer shifts. A fresh scan
  also closes the older triangle-family coverage gap at the latest point:
  all 170,183,860 inequalities pass. None constructs a graph.
- The five-root triple-clique family has 236 candidates in twenty-three
  root orbits. Its conditional preparation checks all 171 selected union
  rows on complete coefficient supports and retains four impossible
  triples as zero contributions. The point scan is a separate step.


- The compact F0 loop records nine further SAT incidences. Fifteen exact
  individual obstructions reject eight; the ninth passes all sixty row
  boxes. Its numerical shared LP ray initially failed exact recovery,
  so the parent run remains frozen UNKNOWN. A separate arithmetic repair
  rounds only equality multipliers and recomputes exact upper deficits.
  The repaired right-hand side is minus 26. Its universal cut has gap 26
  and twelve verified transports. Independent arithmetic replay passes.
- The next preparation retains 348 individual and 36 signed inequalities.
  Its 208,836-variable, 1,476,450-clause formula cold-replays. The new helper
  records and replays every exact-deficit reconstruction recipe.
- A separate clause pilot derives twelve 446-literal consequences using
  Boolean bounds and twelve 60-literal consequences using the exact
  population. It adds no auxiliaries and changes no existing formula.
  Complete small Boolean controls, cold replay, and independent literal
  arithmetic checks pass. The shorter clauses retain all sixty selected
  variables, so their scope is explicit.
- The case-four coordinate census covers 476,766 positive differences.
  Exact deduplication and same-target implications leave 178,533 clauses,
  including all fourteen units. The full streamed formula preserves its
  complete previous clause body and passes cold reconstruction.
- The triple-clique point scan completes 23 representatives covering 236
  cases, with no exact or unconfirmed numerical negative. The next count
  family asks whether all known degree-at-most-four moments on five
  binary flags extend to a nonnegative 32-atom distribution. Its missing
  fifth moment is one scalar, giving an exact interval feasibility test.

- The deficit continuation then rejects fourteen more incidences with
  26 exact individual obstructions and three shared rays. It reaches
  1,999,803 clauses. Thirteen proved transports do not fit. The complete
  registry has 660 individual and 72 signed inequalities. Its 39 raw
  transcript records are preserved in a checked lossless archive, and
  the exact final formula cold-replays. A later lazy continuation will
  retain all 732 cuts and justify every added clause arithmetically.
- The one coordinate-cover query returns UNKNOWN after sixty seconds,
  including its streamed bootstrap. Full cold reconstruction passes.
  The independent-set worker now checks forced-absence closure using
  the original coordinate demands and the degree capacities.

- The five-variable extension scan completes all 4,543,737 subsets.
  All exact extension intervals are nonempty. Of these, 4,459,591 are
  tight and 84,146 have positive width. This gives separate local
  distributions only. The bounded population scan also passes all
  3,583 polynomials across 153 high-mask families.
- The capacity closure finds no new absence after the fourteen known
  case-four units. CaDiCaL300 then queries the unchanged full formula.
  Its parent saves UNKNOWN and terminates the child at 180 seconds.
  The cold formula replay passes. There is no new matching exclusion.
- The lazy F0 preparation retains all 732 certified inequalities in an
  exact registry. Its initial formula has 58,206 clauses and no new
  auxiliary variable. Independent registry and clause audits pass.
- The lazy run records 25 SAT candidates before its twenty-row-pass
  limit. Four candidates fail existing cuts before any LP. Twenty row
  passes yield 29 individual obstructions, 1,171 exact rational boxes,
  and three shared rays. The registry now has 1,116 inequalities.
  The final formula has 58,974 clauses. Its complete cold replay passes.
  The last candidate satisfies the registry but remains untested by rows.
- An exact Gram-equality shift reduces a large repaired cut from 43,735
  encoding clauses to 26,583. Its independent explanation has 244
  literals, down from 446. All twelve transports preserve the gap 26.
  Both cold replay and an independent arithmetic audit pass.
- The next preparations retain the full lazy registry and assess complete
  local packing distributions. No graph or unrestricted contradiction
  follows from the present results.

- The longer lazy run records seventeen candidates and fourteen row passes.
  Fifteen individual obstructions and five shared rays enlarge the registry
  to 1,356 inequalities. The final formula has 59,442 clauses and cold-replays.
  The last candidate passes sixty individual row boxes. Its shared LP
  returns no numerical dual ray. No saved multiplier supports arithmetic
  recovery, so a distinct bounded-potential separator is being prepared.
- The complete high-mask census gives 132,062 universal pair-capacity atoms.
  All 62 root domains contain 350,963 atoms before the outside-pair filter
  and 266,159 afterward. Independent enumeration and domain review pass.
- The empty-root feature preparation retains the complete degree-four matrix.
  Its active part has 17,903 rows and 90,776 columns. All zero moments
  correspond to unsupported structural rows, with no additional atom removal.
  Exact root-label averaging is being prepared before any optimizer query.
- The completed root-label quotient has 73 active equations and 249 orbit
  masses. Explicit generator maps cover all 90,776 structural atoms.
  All 124,500 literal incidence identities pass. Source reviews and a
  separate complete S6 census verify the averaging and group coverage.
  A small primal query with exact rational reconstruction is now being prepared.
- The finite-domain polynomial helper checks exact constant corrections and
  zero-moment penalty recovery. Four known separators, 160 true distributions,
  and an independent arithmetic review pass. A metadata-only correction
  preserves the original source and fixes the largest coefficient bit count.
- The native case-four model retains 1,214 Boolean variables and 180,804
  constraints. Exported-byte checks and full reconstruction pass. Its one
  bounded query returns UNKNOWN after 63.32 solver seconds. No witness or
  further matching exclusion follows. The next preparation considers lazy
  cover enforcement while retaining complete external checks.


- The presence-only packing query gives 73 positive rational masses with
  denominator 1,443,221. Separate replay checks all 73 equations and all
  124,314 individual moments. This finite relaxation permits the saved point.
- The complete induced high-graph domain has 157,711 decorations above 249
  presence representatives. Independent C++ and Python searches agree on
  every edge histogram. All graph codes are saved and checked for uniqueness.
- The induced-pattern matrix has 200 rows and 18,427 distinct columns.
  Every original column reproduces the earlier presence coefficients.
  Independent colored-graph controls check 26,049 subsets. All 200 direct
  catalogue moment products and 73 presence aggregates pass exact checks.
- The bounded F0 separator rejects the preceding unresolved incidence with
  gap 33. The next continuation records 81 candidates and reaches 2,916
  universal cuts. Its 253-record transcript and final formula cold-replay.
  A separate bounded-only query rejects its terminal incidence with gap 64.
  Neither result excludes the full component.
- The lazy native rook query returns UNKNOWN after its first ten-second
  call. The log confirms main search starts at 0.32 seconds. Complete
  exact forward propagation then adds no new assignment after the fourteen
  original units. Explicit assumption checks are the next preparation.


- The complete induced high-graph moment query has an exact witness on
  200 positive rational graph masses. All 200 equations and the full
  root-label lift pass. A separate saved-support audit reproduces them.
- Principal-projector certificates remove 22,146 of the 157,711 graphs.
  A separate suffix continuation completes the first bounded scan without
  repeating its prefix. Every removed graph has a full integer negative
  vector, checked again by the cold removal replay.
- All 200 positive-mass graphs survive. Their existing weights satisfy
  the restricted 200-by-17,922 system without a new optimizer. Exact
  characteristic polynomials check all 400 full principal matrices.
- The centered exterior-Gram identity proves that another Gram PSD scan
  would add no restriction. The next model enumerates complete binary
  outside-incidence signatures for the saved sixteen-vertex support graph.
- Seventeen exact rook assumption probes prove column 359 absent. Its
  reason reduces to three original Gram rows. Their nonnegative sum
  forces 46 columns absent, including 44 new ones. This proof needs no
  earlier absence or integrality premise. Complete small-combination
  facial closure is the next preparation.
- The F0 allocation pilot checks 44,064 historical candidate/family pairs.
  Its best Boolean allocation is stronger than a fixed allocation.
  Three additional shared-family violations already fail individual cuts,
  so this pilot gives no new exclusion beyond the complete prior registry.

## Checkpoint 43: workspace outage and recovered results

The execution environment became unavailable before the next full publication cycle.
Checkpoint 42 remains the last complete local package.
This checkpoint recovers two results through independent JavaScript checks and the public repository inputs.

- The specified ten-high core has the necessary inequality `5e(H)-sum binom(deg_H(v),2)>=6`.
  It excludes its empty high graph and all thirty eligible single edges.
- The F0 base Gram and motif system has an exact interior point from 1,836 checked binary incidences.
  Every selector occurs between 24 and 851 times. No base-only selector zero forcing is possible.
- Before the outage, the complete integer filter removed exactly those 31 graph columns.
  The refined 200-moment query then reported another exact rational measure.
  Its result hash and independent cold replay were not captured.
- Rook propagation stabilized at 58 zeros. A complete selector LP was prepared but never optimized.
- The allocated F0 run ended UNKNOWN with 4,404 cuts and 65,622 clauses.
  Its chronological cold replay passed. The terminal package remains in the unavailable workspace.

See the [recovery record](checkpoint43_recovery.md) for captured hashes and exact publication limits.
The next owned lanes are the complete rook selector LP, the other sixty-one root moment models, and the complete fractional F0 edge model.

## Checkpoint 44: exact finite measures and a complete fractional baseline

- Case four has a nonnegative rational Gram point on 287 columns, with common denominator 648602182798933000000000000. The full 1,214-coordinate witness passes all 630 Gram equations, all individual bounds, all 46 Gram zeros and population 64. A fresh artifact-only replay and a coordinator replay pass. This also proves every shifted integer quadratic Gram inequality for this core.
- Root 49 has a complete high-mask domain of 80 atoms in 19 actual-root orbits. Exact inversion at the saved count point gives 74 positive and six zero integer masses, totalling 11,975,040. Every individual and quotient equation passes. Literal graph checks establish the population-four bound, all product factors and complete local coverage. No separator is obtained.
- The complete F0 structural/motif baseline has 5,847 quotient variables, 686 equalities, 11,373 inequalities and 57,801 nonzeros. Explicit row maps cover all 145,690 full rows. Both the literal model and quotient regenerate exactly. This package contains no optimizer query.
- The shared-edge projection theorem identifies the full family of raw integer-potential inequalities with the fixed-selector box-image condition. It does not identify Boolean-normalized cuts with the fractional model.
- Exact finite-box max-min algebra is prepared for future forced-selector discovery. Its complete small controls pass, but no case-four max-min driver or query is included here.

All new files were frozen as Git blobs and independently reviewed before this commit. The unavailable local checkpoint-43 outputs remain unavailable; this publication does not silently reconstruct or replace their reported results. Native bounded queries will be separate continuations with their own gates and outcomes.

## Checkpoint 45: bounded native recovery replay preparation

The next commit adds a branch-limited CI workflow for the eight already-reviewed finite checkers. It resolves the remaining untested Node filesystem wrappers during the local workspace outage. The workflow has read-only repository permission, pinned actions, sparse checkout and explicit job/child deadlines. It runs no optimizer. Its first execution result will be recorded separately. The exact public-input extraction source for root 49 is also preserved.

## Checkpoint 46: native replay passed; complete rook LP recovery queued

The recovery workflow at commit 27938c7 passed all eight Node filesystem checks. Its job log reproduces the frozen F0 interior, structural, baseline and root-49 result objects exactly. The native summary is preserved as a repository artifact.

An exact evaluation of the reconstructed case-four Gram point finds one failed triple capacity and 21 failed exterior-row inequalities. All 186 signature capacities, thirty Gram no-goods and fourteen older zero units pass. This rejects that rational point from the stronger relaxation and does not exclude case four.

The complete selector-LP recovery source has been read and hash-checked by the coordinator. It imports three public inputs, proves all 58 fixed zeros, accounts for all 2,271 native rows and 178,533 covers, and requires the pre-outage exact row stream. A separate native preparation/cold-replay job is queued by this commit. No optimizer is authorized at this preparation stage.

## Checkpoint 47: complete rook model recovered; joint F0 query gate

The complete rook selector LP has been recovered and independently rebuilt. Its 174,208-row integer stream and 5,312,569-byte compressed matrix match both captured pre-outage hashes exactly. The new model JSON, preparation and cold records are preserved; the old lost source is not represented as recovered.

The F0 native exporter, exact helper and one-call supervisor have all been read and hash-checked. The coordinator rebuilt the 2,087,803-byte model payload from the frozen specifications and matched its exact canonical hash. The workflow requires native arithmetic controls and exact export before one sixty-second joint LP, then permits one sixty-second exact reconstruction. Full original-row or strict integer Farkas replay is required for any mathematical conclusion. The query outcome is pending. The unavailable terminal selector-cut registry remains outside this baseline.

## Checkpoint 48: complete small-root presence certificates and feasible joint F0 model

The remaining 32 small-root presence models pass complete exact inversion: 1,035 integer atom masses, 954 positive and 81 zero, with all 492 quotient equations checked. Together with root 49, this covers 33 roots, 1,115 atoms and 511 quotient equations. The independent checker sums the saved masses directly and replays the literal moment forms; the coordinator reproduced both algorithms. This closes the presence-only test at this count point, while decorated edge states remain a stronger test.

The one native F0 baseline query returned a numerical proposal that was reconstructed exactly with a 532-column rational solve. Its 191-bit denominator is retained. Independent Node replay and a separate coordinator replay check all 145,690 original rows and 68,874 variable bounds. This is an exact feasible relaxation, not a graph. The 4,404 terminal Boolean cuts were not included. Their complete transcript has now been recovered from the preserved old checkout and is being prepared as a separate strengthening.

The local runtime returned with the old checkout still at checkpoint 42. It was preserved, including 210 untracked entries. A separate checkout at checkpoint 47 is used for new integration. The complete rook max-min driver passed native preparation with mathematical model hash `550972cca292015d484287228700402642d1e3eb52ea3d1b89ed0b74f83dff0c`. Exactly one bounded production query is authorized; only an exact replay can establish its outcome.

The authorized complete rook query stopped after 60.091 solver seconds and 1,264 simplex iterations. No valid numerical solution or basis, exact point, zero-face certificate, or contradiction was obtained. The numerical state and log are retained. Case four remains open; no automatic retry was made.
