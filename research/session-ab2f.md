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
