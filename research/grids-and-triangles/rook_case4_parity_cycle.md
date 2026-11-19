# Bounded parity, LP and exact-basis cycle for rook case 4

This is a prepared continuation, with no production scan or optimizer run. It starts from the exact point with denominator 337,510,679 and positive max-min numerator 3,684,393, accepted in the weighted-parity basis package.

The complete current extended matrix has 1,103 variables, 167,115 rows and 10,769,496 nonzero coefficients. All of these rows, including the 1,102 max-min extension rows, remain an immutable prefix. New parity inequalities are appended after that prefix. No previously proved zero, native row, coordinate cover, parity equality, pair bound, H3 row or weighted parity cut is removed.

## Exact parity implication

Let a saved witness select original Gram equations. Their integer sum is

\[
\sum_j c_j x_j=b.
\]

The checker reconstructs every one of the 1,214 coefficients directly. After substituting only the 112 proved zeros, the odd coefficients give a support H and the parity equation

\[
\sum_{j\in H}x_j\equiv b\pmod 2.
\]

For a forbidden Boolean vertex whose one-set is F, with parity opposite to b, every feasible Boolean selector vector has Hamming distance at least one:

\[
\sum_{j\in F}(1-x_j)+\sum_{j\in H\setminus F}x_j\geq1.
\]

The appended form is

\[
\sum_{j\in F}x_j-\sum_{j\in H\setminus F}x_j\leq |F|-1.
\]

This permits both signs. Its stored lower endpoint is the exact unit-box minimum, \(-|H\setminus F|\), so adding that lower endpoint imposes no further restriction.

The closest forbidden vertex is selected with exact integer numerators. The distance deficit must be strictly positive at the particular saved point. Every cut stores the full original Gram-row witness, all original coefficients, removed zero columns, forbidden vertex, denominator and exact deficit. The cut's validity does not depend on any numerical LP value.

Each fresh exact point is scanned using the old 286-row basis and two new exact RREF bases. Each family contains the single rows and unordered XORs of two rows. The weighted column order first eliminates larger exact \(\min(x_j,1-x_j)\), with ascending and descending original-ID tie orders. All 630 original Gram rows must lie in each checked output span. Identical equations are evaluated once within the scan. The old family is evaluated at each changed point; equations that passed an earlier point are not silently skipped.

## Numerical proposals and exact acceptance

An LP round is permitted only after a complete scan and its exact cold replay produce a new cut. It uses the unchanged native row assembly, optimizer-call helper and cover selection rule. All non-cover rows start active. The complete frozen cover pool is scanned after each numerical point; violated covers are inserted in batches of at most 512, ordered by decreasing numerical violation and then immutable row ID. Carried cover rows are retained across rounds.

A saved basis supplies candidate equalities \(x_j=t\) from lower-active max-min rows and candidate nonbasic variable bounds. These restrictions describe one proposed point; they are never installed in the search model. The reduced square size is computed from the actual saved statuses. A residual system above 512 variables, a non-square or singular system, an unsupported status, a failed arithmetic check or a timeout yields no exact point. There is at most one FLINT Dixon solve per LP round.

Point acceptance checks every frozen and appended row, every unit bound, all 2,271 original native constraints, all 178,533 original covers, all 1,214 original coordinates and the 112 zeros. It also checks population 64, both unit sums, all four pair bounds, H3 and the two inherited weighted-parity rows. Every surviving selector must be positive. The separate cold stage rechecks the saved-basis restoration and full point without elimination.

The existing finite-box certificate checker handles numerical dual proposals. It reconstructs an exact signed sum of ranged-row and variable-bound slacks. An accepted negative bound can exclude this case4 relaxation; an exact zero max-min bound can expose another face. Either outcome stops the cycle. The cycle does not silently change its fixed domain.

## Scope and limits

| Quantity | Bound |
|---|---:|
| Fresh exact-point scans | 3 |
| New LP rounds | 2 |
| Raw parity candidates per scan | 123,123 |
| Total newly retained parity cuts | 64 |
| Native calls per LP round / whole cycle | 30 / 60 |
| Cumulative native time budget | 120 seconds |
| Numerical phase per round / both rounds | 180 / 360 seconds |
| Each scan and its separate cold replay | 60 seconds each |
| Each exact stage and its separate cold replay | 60 seconds each |
| Declared stage budget total | 960 seconds |
| Whole process-group watchdog | 1,080 seconds |
| Scan transcript budget across the cycle | 64 MiB |
| Dynamic exact residual dimension | 512 |
| Accepted output integer bit length | 4,096 |

The transcript budget charges exact basis/evaluation/cut bytes plus a one-MiB result reserve for each completed scan. Native requests use the remaining measured cumulative budget; cancellation and actual elapsed times are recorded, and no later call is made after the budget is used. The outer watchdog terminates and reaps the owned process group.

A partial scan, complete no-cut scan, repeated exact selector point, exhausted budget or failed exact stage terminates as unresolved. Complete no-cut coverage concerns only the declared three finite families, not the full parity row space. A real point is not a Boolean incidence or graph.

## Preparation and version record

The arithmetic kernel is \`rook_case4_parity_cycle_exact.py\`, SHA-256
\`2f10a42f546623cb1840d228101537e6f4f4bc584776407140ae0c36b08c99b7\`.

The frozen driver is \`rook_case4_parity_cycle_v4.py`, SHA-256
\`345e091ef71dde96b3423773d5315b8733c275f0af142ab0f88ac03570ca263e\`.

Preparation04 is SHA-256
\`61c56185b99adba1b56728b96b34e3c3ec9a25e1708c9e5e53bf4413b9f1e5f0\`.
Preflight04 is SHA-256
\`d3827408d08dd443093cba2d0c19e250391c142c6e97a4f04f316567c04bf264\`.

Preparation passed 10,935 alias/fixed-group substitutions, 32 signed parity assignments, eight immutable-prefix appends and two synthetic saved-basis cases. Preflight used the frozen native helper on four toy rows and read the published matrix cache. It reproduced every row of the already accepted 290-square system with 813 aliases and 2,087 terms and verified its known point. It did not rebuild original cover supports, construct a full native case model, call an optimizer or perform an exact solve.

Earlier versions remain unqueried. V1's preparation passed; V2 added conservative transcript accounting and stronger final transcript checks. V2's native/cache checks finished but metadata serialization failed on a relative path. V3 changed only path resolution and passed preflight. V4 adds explicit equality of the actual native runtime binding and the frozen preflight binding. The exact substitution/AST records and failed metadata log remain separate.
