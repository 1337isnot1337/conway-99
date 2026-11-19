# Graph-Schur and prism restrictions in the F0 moment model

This model retains all 15,200 variables of the reduced second-moment
model, its original linear conditions, all 4,416 selector predicates,
and the 32 previously checked selector-PSD directions. It adds 162
edge-zero equations, 39 exact graph-Schur inequalities, and 715
three-exterior prism inequalities.

The scope is component zero of a split 18+18 shell in a globally
prism-free and F-free SRG(99,14,1,2). The other component, its incidence,
and its alignment remain unrestricted. The 480 first-component selector
signatures and all 68,394 eligible literal edges remain represented.
The 162 edge-orbit variables remain in the numerical matrix and receive
explicit zero equations.

## Added rows

The [visible-edge census](root_prism_free_f0_edge_motifs.md) supplies the
162 zero equations. Its 1,884 literal prism witnesses were independently
reconstructed, and the model preparation checks each witness again.
No unspecified exterior nonedge is used in this test: the fixed 21-core
and both endpoint signatures specify the entire 23-vertex graph once
the candidate edge is present.

The [18-core scan](root_prism_free_f0_graph_schur_scan01.md) supplies 17
graph-Schur directions; the
[full-21-core scan](root_prism_free_f0_full_core_schur_scan01.md) supplies
22. Preparation reconstructs the exact kernels and all 39 literal
480-coordinate quadratic forms. It then recomputes their orbit sums,
substitutes only the existing 389 certified zero pair coordinates, and
checks each normalized inequality against its frozen certificate.
The small-gap minus-family rows remain present; no independence or
strict strengthening claim is made for them.

The [three-exterior prism calculation](root_prism_free_f0_three_vertex_prism_cuts.md)
supplies 715 sparse rows. For its certified configurations,
\(y_{ab}z_c=0\), and edge activation gives the binary inequalities

\[
y_{ab}+z_az_c\le z_a,
\qquad y_{ab}+z_bz_c\le z_b.
\]

Averaging under the verified core actions gives
\(Y_{ab}+Z_{ac}\le x_a\) and \(Y_{ab}+Z_{bc}\le x_b\).
The candidate exterior chords are forbidden by visible common-neighbor
caps; their absence is not assumed. Preparation replays the complete
frozen calculation and retains every distinct quotient row.

Identical new mathematical inequalities would share one matrix row,
while every proof input keeps its own source and row-index record.
In this preparation all 39 Schur rows and all 715 prism rows are
distinct from the earlier rows and one another. The inherited equality
and inequality prefixes are unchanged.

| Matrix quantity | Count |
| --- | ---: |
| Variables | 15,200 |
| Equalities | 6,135 |
| Inequalities | 16,505 |
| Total rows | 22,640 |
| Nonzero coefficients | 889,906 |
| Added edge-zero equalities | 162 |
| Added Schur inequalities | 39 |
| Added three-exterior prism inequalities | 715 |

## Exact mathematics and numerical scaling

The mathematical matrix has integer coefficients. Its largest
coefficient uses 31 bits. Each inherited row keeps its previous
numerical scale. Each appended inequality is divided by the positive
power of two below its largest absolute coefficient; the new zero
equations have scale one. The largest scale is \(2^{30}\).
Every stored coefficient and scaled conversion is checked exactly as
a binary rational. Appending equalities shifts combined numerical row
indices; the preparation records and checks the updated indices for
every new proof input.

The proposed numerical phase uses one thread and one HiGHS IPM call,
with crossover disabled and a 180-second bound including setup. It
stores any returned finite coordinate vector, together with the backend
status. This phase requests a numerical proposal for later exact
analysis. It does not attempt primal-point or basis reconstruction.

Only when HiGHS reports that a dual ray already exists may the driver
request that ray. It never invokes another optimizer to generate a
ray. A separate, at-most-60-second arithmetic phase divides the saved
ray entries by the stored row scales as exact fractions and attempts
an integer certificate. If there is no existing ray, the mathematical
outcome remains UNKNOWN even if the numerical status is optimal.

For a unit-box system \(Ex=f\), \(Ax\le b\), take integer equality
multipliers \(\lambda\) and nonnegative inequality multipliers
\(\mu\). Put

\[
c=E^T\lambda+A^T\mu,
\qquad r=f^T\lambda+b^T\mu.
\]

Every feasible point has \(c^Tx\le r\), while the unit box gives
\(c^Tx\ge\sum_j\min(c_j,0)\). Therefore

\[
r-\sum_j\min(c_j,0)<0
\]

is an exact infeasibility certificate. The separate replay reconstructs
the full mathematical model and checks this inequality by direct integer
arithmetic. Numerical status alone never excludes the component.

## Files and preparation scope

The mathematical builder is
[root_prism_free_f0_schur_motif_model.py](../experiments/workspace/root_prism_free_f0_schur_motif_model.py).
The frozen model is
[f0-schur-motif-model01.json.gz](../experiments/logs/root-prism-free/f0-schur-motif-model01.json.gz).
The
[query driver](../experiments/workspace/root_prism_free_f0_schur_motif_query.py),
[exact helper](../experiments/workspace/root_prism_free_f0_schur_motif_exact.py),
and [cold replay](../experiments/workspace/root_prism_free_f0_schur_motif_replay.py)
are separate sources. Their preparation does not call an optimizer.

The complete positive-semidefinite cones are not enforced. The model
contains the 71 specified selector and graph-Schur directions together
with the exact linear constraints. A runtime result requires a separate
record; this preparation makes no feasibility or component-exclusion
claim.
