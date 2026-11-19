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
- Replaying the repository's existing exact certificate checks before adding
  constraints to the baseline.
