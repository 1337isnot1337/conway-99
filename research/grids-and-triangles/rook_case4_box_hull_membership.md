# Membership in the hull of the 191 surviving boxes

This test uses the six-cut exact point with denominator 2,594,289,631. It
uses all 191 final axis-aligned boxes from the completed whole-case branch
cover. The original 2,835 weighted patterns are accounted for by 2,391
native-capacity rejections, 184 checked native contradictions, 69 checked
full-row contradictions, and the 191 surviving boxes. No partial branch is
used as a covering proof.

The input bindings reuse the completed cold records. They do not repeat the
branch traces or load the large selector matrix. The boxes use the same
1,102 surviving coordinates and 112 proved zeros as the accepted point.

## Exact formulation

Write box B as the product of intervals [l_Bj,u_Bj], whose endpoints are zero
or one. There is one nonnegative weight lambda_B for every box. The weights
sum to one. For each surviving coordinate j, impose

\[
\sum_{B:l_{Bj}=1}\lambda_B\le x_j,
\qquad
\sum_{B:u_{Bj}=0}\lambda_B\le1-x_j.
\]

There are 191 weights and 2,205 rows, including the mixture-sum equality.
The exact sparse matrix has 38,333 unit coefficients. All 1,264 empty
coordinate rows remain explicit. The bounds lambda_B <= 1 are redundant
consequences of nonnegativity and the sum equality.

These inequalities describe membership in the convex hull of the boxes
exactly. For fixed feasible weights, put

\[
L_j=\sum_B\lambda_B l_{Bj},\qquad
U_j=\sum_B\lambda_B u_{Bj}.
\]

The two inequalities say L_j <= x_j <= U_j. If U_j > L_j, choose
theta_j = (x_j-L_j)/(U_j-L_j). In box B choose coordinate
l_Bj + theta_j(u_Bj-l_Bj). This is in the box, and the weighted coordinate
sum is x_j. If U_j = L_j, the endpoint inequalities force x_j = L_j, so
any theta_j in [0,1] works. The 112 omitted coordinates are zero in the point
and every box. This proves both necessity and sufficiency.

The formulation does not assume that any surviving box contains a feasible
Boolean solution. It is a relaxation obtained from the covering boxes.

## Exact outcomes

For a feasible numerical proposal, the saved basis supplies candidate
active rows and fixed bounds. The exact solve uses y = D*lambda, where D
is the accepted point denominator. A basic system therefore has only zero
or one coefficients and integer right-hand sides. Every fixed upper weight
subtracts D from each incident right-hand side.

There is at most one rational solve of dimension at most 191. A singular or
failed basis is unresolved. The reconstructed common-denominator weights
are authoritative only after nonnegativity, sum one, and all 2,204 endpoint
inequalities pass exact cross-multiplication. The independent cold checker
reconstructs these endpoint sums from the saved box states, without importing
the producer or repeating the solve.

If such a mixture passes, no linear inequality valid on all 191 boxes can
reject this point. It still does not give a Boolean incidence assignment,
a feasible original-model point inside one box, or a graph.

For an infeasible numerical outcome, an already available dual ray may
propose signed coordinate coefficients. The wrapper does not invoke a
second solve to obtain a missing ray. It rounds at a fixed list of scales
and checks both signs. For each integer vector c, it computes

\[
\alpha=\min_B\left(\sum_{j:c_j\ge0}c_j l_{Bj}
+\sum_{j:c_j<0}c_j u_{Bj}\right).
\]

The row c*x >= alpha is valid on every box. It is accepted as a separator
only if alpha*D - sum_j c_j*n_j is a strictly positive integer for the
accepted point n/D. All 191 endpoint minima and the full original-coordinate
coefficient lift are saved and independently checked. Native ray signs,
floating tolerances, and numerical infeasibility are not proof premises.

## Bounds and controls

The proposed production scope is one simplex call with a 60-second native
limit, one 60-second cooperative exact phase, and one 60-second cooperative
cold phase. Each child has a 90-second hard owner; the complete owner has a
300-second hard limit. A timer also requests interruption of the native
call. Complete numerical vectors and bases are saved before optional ray
export. Every owner reaps its child. There is no automatic retry.

The helper's exact controls passed 3,375 literal signed-endpoint tests,
729 interpolation distributions, two strict separator cases, two basis or
fixed-bound reconstruction cases, and four deliberate failures. They used
no numerical optimizer. The case preparation also checked the new point
against all six registry rows and all seven existing branch-pool append
rows; these all pass.

The helper, one-call wrapper, independent replay, model, configuration, and
owner outputs have separate immutable bindings. Production requires the
source and preparation gate. This preparation makes no native call.
