# Global constraints research session

Starting revision: `21aedce941ec7e139f43672c65069fac03091aee`.
Coordination: [issue 2](https://github.com/1337isnot1337/conway-99/issues/2).
Branch: `research/global-constraints-ab2f`.

## Active investigations

1. Coupled short-vector constraints in the negative eigenlattice, beyond the
   existing scalar theta tests. Owned by the eigenlattice worker.
2. Exact spectral constraints on a coclique containing seven neighbors of a
   root. Owned by the independent-set worker.
3. Unrestricted completion of a square with its four triangle tips. Owned by
   the completion worker.
4. Global counts and compatibility of triangles, grids, and small cores.
   Owned by the coordinating worker.

The joint-cell Gram analysis for roots in fifteen grids is reserved to the
separate worker in issue 1. This session does not claim that case.

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
