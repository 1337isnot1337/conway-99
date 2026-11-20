# A joint real relaxation for the overlap-four rook-tip core

## Outcome and scope

One bounded, single-thread linear-programming attempt on the complete
joint incidence/edge relaxation returned **UNKNOWN**. It produced
neither an exact Farkas obstruction nor a certified feasible point.
No mathematical exclusion follows from this run. No second solve or
SAT/proof rebuild was launched in this lane.

The same core has a separate [checked integer exclusion](two_rook_tip_boundary_joint_integer.md).
This real-LP attempt does not supply an alternative proof of that result.

The core is representative `3679836361` from the complete boundary
census in [two_rook_tip_rook_boundary.md](two_rook_tip_rook_boundary.md).
Its tip rook graph shares four edges with the original rook labeling.
All 188 possible exterior signatures are retained. The model does
not fix a 72-column incidence design.

The complementary-rook core is not tested here. Its separate exact
rational control is recorded in
[two_rook_pair_structural.md](two_rook_pair_structural.md).

## Independent model reconstruction

The source reconstructs the 27-core adjacency matrix from the graph
code and checks it against the exported core. It recomputes

\[
G=12I+2J-B^2-B
\]

using integers. It enumerates all `9^3` triples, retaining exactly the
188 signatures whose core-pair quotas are positive and whose mixed
quotas are nonnegative. This agrees exactly with the frozen exported
domain. Elementary margin propagation independently rederives the
16 forced selected signatures and 32 forced rejected signatures.

The 12,010 possible exterior edges are reconstructed directly.
An edge between candidates `v,w` requires at most one common core
neighbor and positive mixed quotas at both endpoints for every
core neighbor of the other. No integer-model builder or CNF is
imported.

Let `s_v` denote a candidate selector and `e_vw` a possible edge.
The real relaxation contains the following necessary constraints:

- Full Gram equations, the selected population 72, and the propagated
  units.
- `0 <= s_v <= 1`, `e_vw >= 0`, `e_vw <= s_v`, and `e_vw <= s_w`.
- For every candidate and core vertex, the conditional mixed equation
  \[
  \sum_{w:\ i\in h_w}e_{vw}
  =\bigl(2-((B+I)h_v)_i\bigr)s_v.
  \]
- Conditional exterior degree `sum_w e_vw = 11s_v`.
- For every candidate `v` and core pair `i,j`, activated packing
  \[
  \sum_{w:\ i,j\in h_w}e_{vw}\le s_v.
  \]

The final inequality is necessary for every binary completion. Two
vertices in the indexed family already share the two core vertices,
so they cannot have `v` as another common neighbor. If `v` is absent,
activation makes all its incident edges zero. The inequality is the
whole-family packing constraint, rather than just a list of pairwise
inequalities between its edges.

## Averaging without a symmetry assumption on the graph

The source enumerates the simultaneous rook relabelings preserving
the tip graph, optionally exchanging the first two grids. There are
eight such core/domain automorphisms. It verifies their action on
the core, the entire candidate domain, the propagated units, and the
possible-edge set. It also checks closure of the action group.

Averaging any real solution over these eight actions preserves all
the displayed linear constraints. Thus an infeasible averaged
relaxation would exclude every incidence choice. This does not
require any completed graph to have those automorphisms. The
nonlinear common-neighbor equations between exterior vertices are
not imposed by this relaxation.

The averaged model has the following exact size:

| Item | Count |
| --- | ---: |
| Candidate selectors before averaging | 188 |
| Candidate edges before averaging | 12,010 |
| Selector orbits | 24 |
| Edge orbits | 1,532 |
| Equalities | 650 |
| Inequalities | 5,880 |
| Gram equalities after normalization and deduplication | 26 |
| Population equality | 1 |
| Distinct forced-unit equalities | 6 |
| Mixed equalities | 593 |
| Degree equalities | 24 |
| Selector upper bounds | 24 |
| Activation inequalities | 2,976 |
| Core-pair packing inequalities | 2,880 |

Nonnegative slack variables convert the inequalities to equations
for the solver and for any later integer Farkas replay.

## Recorded attempt

HiGHS 1.16.0 ran with one thread, a 30-second limit, and presolve
disabled to request a dual ray directly if infeasibility was found.
It returned `HighsModelStatus.kUnknown` after approximately 7.526
seconds. This was not a wall-budget timeout, an infeasibility result,
or a feasibility result. The cause of the unknown status was not
determined.

The saved result contains no dual and no primal point. Replay
rebuilds the exact model and checks its hash and the source-domain
hash; it cannot turn the solver status into a mathematical claim.
The source also includes exact integer-dual and rational-point
checkers for a possible future certificate, but neither checker
accepted a certificate in this run.

## Files and replay

- Source: `experiments/workspace/two_rook_tip_overlap_joint_lp.py`.
- Result: `experiments/logs/grids-and-triangles/two-rook-tip-overlap-joint-lp-result.json`.
- Generation and replay logs use the same stem.
- Input: `experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-domains.json`.

The following command rebuilds the model and replays the saved
status using only the Python standard library. It does not solve
the LP again:

```sh
python experiments/workspace/two_rook_tip_overlap_joint_lp.py \
  --domains experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-domains.json \
  --certificate experiments/logs/grids-and-triangles/two-rook-tip-overlap-joint-lp-result.json
```

The averaged-model SHA-256 is
`e794d8a6696cb70311c17f6a004d5676f2f77479199bb3bf40a24217a864a087`.
The exported-domain SHA-256 is
`ceada008c0d03c91a6805074f6022ae48777b805b5a0e8752be442e02929a072`.
