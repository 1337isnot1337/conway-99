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
