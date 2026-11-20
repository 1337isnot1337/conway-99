# Terminal H3 selector-LP query

The single authorized H3 query is terminal. Its frozen result is
`UNRESOLVED: retained numerical proposals give no accepted exact outcome`.
It does not exclude case4 or certify an exact feasible point.

The query used the complete 112-zero-face model with the one proved H3
cover. All native rows, both unit sums, four certified pair capacities,
H3, and the max-min extension started active. Every retained original
coordinate cover remained in the separation pool.

HiGHS made one call, taking 3.642833 seconds and 6,951 reported simplex
iterations. It returned numerical optimality with

\[
t\approx0.010932719234734.
\]

The full numerical scan checked all 167,113 rows and all 164,044 retained
coordinate covers. It found no violation above the fixed tolerance;
the largest numerical row residual was about (6.22\times10^{-14}).
No cover row was added, and no second optimizer call was made.

The prescribed rational-reconstruction attempts did not yield an accepted
point or dual certificate. The terminal numerical status remains unchanged.
The result, complete numerical values, active row IDs, basis statuses,
row multipliers, and native log are retained under
`rook-case4-face112-h3-generation-run01`.

The separate cold replay rebuilt every original model row, checked all
prior substitutions and the direct H3 proof, and reproduced the complete
pool scan and bounded one-call transcript. It passed in 54.786628 seconds
without an optimizer. The result SHA256 is
`328abe5e6413d2e76e943e04d1cfa225b57aa0f574eb26ccf9fca3314382192d`;
the cold replay SHA256 is
`e682e859b538e97a40786c445fa628cc26dd3a962172d0308b29d0cab48a2de5`.

The saved basis has 815 lower-bound equations (x_j=t). Substituting
these as candidate-point assumptions leaves a 288-square integer system:
286 original native rows, the H1 equality, and H3 at its lower bound.
A separately frozen exact reconstruction can test this one system without
calling an optimizer. The aliases are not universal restrictions. Any
recovered point must pass all 167,113 model rows, every original native
row, all 178,533 original coordinate covers, and all 1,214-coordinate
bound and premise checks.
