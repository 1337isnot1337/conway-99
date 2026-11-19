# Conditional native-row LP pilot for the 54 low-face boxes

## Scope

The latest accepted selector point is in the convex hull of all 191 saved axis-aligned boxes. Its exact membership certificate has 34 positive weights with common denominator 2,594,289,631. This closes separation by linear inequalities valid on those entire boxes at that point. It does not show that an original-model feasible point exists inside any individual box.

The next pilot intersects each selected box with the original native rows and the already accepted added rows. This is a stronger relaxation than the box alone. It uses no new selector-zero premise.

The saved three-row Gram identity is

\[
H_{27}+2Q=3,
\]

where

\[
Q=x_{260}+x_{399}+x_{403}+x_{406}+x_{761}+x_{762}
  +x_{763}+x_{764}+x_{765}+x_{803}.
\]

On the Boolean domain, \(H_{27}\in\{1,3\}\). The complete cold-checked cover has 54 surviving boxes with \(H_{27}=1\) and 137 with \(H_{27}=3\). The low subfamily consists of the singleton guard \(x_{764}=1\) and 53 two-coordinate guards. These are all surviving low boxes, not a selection based on the fractional point.

The 54 boxes have 875–1,028 free coordinates, with median 957. Their other values are prior exact conditional consequences. They are not global units.

## Native matrix

The preparation retains all 2,271 original native rows, including rows that become box tautologies after substituting the 112 globally proved zeros:

- 630 Gram rows;
- 186 original signature capacities;
- 1,365 core-triple capacities;
- 30 Gram conflict rows;
- 60 uncapped row cuts.

It then appends 17 already accepted rows: the two unit sums, four certified pair capacities, the inherited H3 row, two inherited weighted parity rows, the five current registered parity rows, the unconditional H42 upper-five row, the 44-term strengthening, and the 11-term box capacity.

The resulting native specification has 1,102 variables, 2,288 rows, and 26,266 nonzero coefficients. It does not load the 178,533 original coordinate-cover rows or the large retained cover matrix. Those covers already entered the proofs of the saved boxes. Exclusion by a subset of necessary rows remains valid.

A numerical feasible point for this pilot is unresolved. It is not accepted as a point of the complete selector relaxation.

## Exact exclusion

For original ranged rows \(L_r\le A_r x\le U_r\), choose any signed integer multipliers \(\lambda_r\). Define

\[
g=\sum_r\lambda_r A_r,\qquad
d=\sum_{\lambda_r>0}\lambda_rU_r+
  \sum_{\lambda_r<0}\lambda_rL_r.
\]

Every feasible point satisfies \(g\cdot x\le d\). For the complete saved box
\(\ell_j\le x_j\le u_j\),

\[
m=\min_{\ell\le x\le u}g\cdot x
  =\sum_{g_j\ge0}g_j\ell_j+\sum_{g_j<0}g_ju_j.
\]

The only accepted exclusion is the exact strict inequality \(m>d\). No numerical dual-feasibility assumption is used. Every accepted combination is restored to all 1,214 original coordinates; the 112 global zero coordinates are explicitly fixed to zero in that replay.

The numerical ray is only a coefficient proposal. The driver tests a finite declared set of integer roundings in both orientations. A native infeasible answer without a checked positive gap stays unresolved.

For a retained branch, its positive guard already contributes the entire weighted Gram quota 3. Nonnegativity therefore forces every other positive-support coordinate to zero. The prior complete branch proof then yields the saved box. A contradiction inside that box implies the original guard nogood: a singleton zero or a two-coordinate at-most-one row.

No other branch is excluded by that proof. Only exclusion of all 54 low branches would imply \(H_{27}=3\), then \(Q=0\), and hence ten new global zero coordinates.

## Runtime contract

The frozen controller uses one native matrix load and explicitly resets all 1,102 variable bounds before each branch. It has one LP call per selected branch, in the frozen whole-cover order. There is no objective, full-cover scan, hidden ray solve, retry, or branch-feedback reduction.

The frozen limits are 54 calls, two requested native seconds per branch, 120 cumulative native seconds, a 180-second forward phase under a 210-second owner, and one 60-second independent cold phase under a 90-second owner. The native time limit is set from the current cumulative native clock. The controller uses no per-call cancellation flag.

Each complete numerical record is saved before exact checking. Each accepted proof and branch record is durable before the next branch. Partial and unprocessed branches remain unresolved. Whole-low-face conclusions require all 54 exact exclusions.

## Comparison with the existing SAT path

The existing 112-zero CNF has 135,022 variables, 441,164 clauses, and 57,922,938 bytes. It includes the original coordinate covers and the earlier unit-sum/pair/86-term cardinality constraints. It predates the newer registered parity rows and the 11-term box capacity.

The proof-capable CaDiCaL 3.0.0 path can certify a conditioned branch if the exact branch units are part of the DRAT input, every retained input clause is checked against that full conditioned formula, and the proof passes an independent cold check. An assumption-only UNSAT status is insufficient.

The two prior unconditioned 180-second CNF queries were UNKNOWN. The 112-face query spent 6.526 seconds bootstrapping its clauses before solving. Repeating that bootstrap separately for all 54 boxes would alone cost about 352 seconds at the observed rate; this is an extrapolation, not a benchmark of conditioned search. Search and proof-check time would be additional.

The small native pilot avoids those repeated CNF bootstraps. The prior six-cut native-row LP took 1.112 seconds for one call, but that measurement does not predict the conditioned branch times. The fixed two-second per-branch request and cumulative cap are the proposed resource limits, not a feasibility claim.

## Current preparation state

The first local invocation produced no observed preparation directory or owner receipt during the environment outage. Recovery found the session unknown and no matching preparation child visible. That observation is preserved separately.

The fresh optimizer-free preparation02 passed in 0.779 seconds; its owner reaped in 0.918 seconds. It checked 3,375 signed endpoint controls, 675 ranged-row combination controls, and four malformed-multiplier rejections. No native optimizer was imported or called.

The independent small-model audit01 failed before child creation with ENOSPC. That invocation produced no mathematical result or owner receipt. The fresh audit02 passed: it independently reconstructed every native row and every box, checked three full-coordinate certificate controls, and rejected 18 altered certificates. Its owner reaped in 3.496 seconds.

The first native preflight02 stopped after `passModel` because HiGHS returned column storage while the draft audit required row storage. It made no solve call. The old source and failure logs are preserved. A separate narrow change caches each sparse array once and independently restores either CSR or CSC to the same exact rows. Two positive format controls and six malformed transport controls passed; all other eleven query functions and the module-level AST remain unchanged.

The corrected native preflight03 passed in 0.485 child seconds and 0.732 owner seconds. It checked every coefficient and endpoint, then reset and read back all 1,102 bounds for each of the 54 branches. Its native solve count is zero. The configuration freezes this preflight, runtime, sources, complete order, and limits. No production LP had run when this note was frozen.

## Artifact bindings

All paths below are under `experiments/logs/grids-and-triangles/` unless stated otherwise. The files retain complete hashes and input ancestry.

| Artifact | SHA-256 |
| --- | --- |
| `experiments/workspace/rook_case4_low54_native_lp.py` | `174c084dc9df3e3e0eed5e028ad18b6c89957c51b4ddfe7c0e4bbeaaa70d5380` |
| `experiments/workspace/rook_case4_low54_native_lp_query.py` | `2ab88406370bb1f0a695fd3d191aee411e35bec0f3ced13758266811958dbefe` |
| `experiments/workspace/rook_case4_low54_native_lp_replay.py` | `12906b10154ea48871ee659fb4553a7aa9c5d28846d2a5e124c152d557dfb144` |
| `rook-case4-low54-native-lp-preparation02/preparation.json` | `a2b840b62891ff7f562e21138bcbd60b589677bc106db77e49b90be23f60eee4` |
| `rook-case4-low54-native-lp-preparation-audit02.json` | `e9a1bd2947e4e2992640a26e85b62afbbbcbdf355bb302227e2aff58c9534f33` |
| `rook-case4-low54-native-lp-preflight03/child/result.json` | `70a6e20b06949b58ebefbd54ecc6214ff5b3df970dd1c2bd341d7f0b845aea32` |
| `rook-case4-low54-native-lp-query-configuration01.json` | `a0ac53ac6969ceeaaeedd2fabfa38d8944dd856c85bb461113a70cd92784c272` |
| `rook-case4-low54-native-lp-independent-source-review01.json` | `1203b6ef5a6075a03178ca7843c490ac5e43d2226eef904b654542a5cbf0edc6` |
| `rook-case4-low54-native-lp-native-format-delta01.json` | `b01f8b5051a9fb0fc1a3dc630b7bcf455cdf7b3fca855befc6da1ce135b321e7` |

Root owns the final production gate. This preparation note asserts no branch exclusion.

