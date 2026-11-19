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
