# Complete branch propagation and disjoint-guard inequalities

All 64 retained Boolean patterns now have separately checked interval-and-cover fixed points. None was refuted. Their common forced literals are exactly the 112 previously proved zeros; no positive coordinate is common to all branches.

The computation does not establish Boolean feasibility. It verifies that this propagation procedure finds no contradiction in the complete 64-pattern cover.

## Completion without repeated work

The original pass completed 50 forward branches and 28 cold checks. The continuation used the same engine, row inventory, cover registry, and owned-child supervisor.

| Continuation stage | Scope | Elapsed seconds | Outcome |
|---|---:|---:|---|
| Forward | 14 unfinished branches | 20.855 | 14 fixed points |
| Cold check of old results | 22 unchecked complete traces | 43.149 | All 22 passed |
| Cold check of new results | 14 new complete traces | 34.943 | All 14 passed |

Each stage stayed within its declared bound. No completed forward branch or cold check was repeated. The earlier partial trace of branch 55 remains preserved, alongside its completed continuation. The original timeouts and incomplete coverage records remain unchanged.

Across all 64 checked branches, between 187 and 383 coordinates are zero. There are 24 branches with one forced positive coordinate, 32 with two, seven with three, and one with four. These assignments are conditional on the selected branch pattern.

## Exact grouped inequalities

Let \(C\) be any set of the 31 common-singleton guards. The proved unit sum gives
\[
\sum_{c\in C}x_c\leq 1.
\]
For a target coordinate \(j\), let \(C_0(j)\) contain checked guards whose branches force \(x_j=0\), and let \(C_1(j)\) contain checked guards whose branches force \(x_j=1\). Then every Boolean completion on the proved face satisfies
\[
\sum_{c\in C_0(j)}x_c+x_j\leq 1,
\qquad
\sum_{c\in C_1(j)}x_c-x_j\leq 0.
\]

For the first inequality, selecting the target prohibits every guard in the sum. If the target is absent, the unit-sum bound applies. For the second inequality, any selected guard forces the target, and at most one guard can be selected.

These implications do not require the guard set to cover every branch. Self-guard tautologies are removed. Every retained literal implication cites its exact forward record, cold record, and literal index. The certificate retains the complete target/value ledger.

Of the 2,428 target/value cases, 1,551 have no nontrivial implication, 538 are already bounded by retained native capacity rows, and 112 follow from a proved zero and the guard unit sum. The remaining 227 rows contain 1,681 term occurrences: 226 rows force a target absence and one forces a target presence. Exhaustive controls check both algebraic forms on 2,044 small Boolean assignments.

The positive-target row is
\[
x_{74}+x_{75}+x_{76}+x_{77}+x_{176}+x_{177}+x_{178}\leq x_{535}.
\]
Its seven implications come from cold-checked branches 0 through 6.

## Exact evaluation at the shared fractional point

The shared 112-zero rational point has denominator \(145{,}446{,}009\). It has an independent exact replay against all original native constraints and coordinate covers.

All 227 grouped inequalities are strictly satisfied. The smallest slack is
\[
\frac{6{,}230{,}972}{145{,}446{,}009}.
\]
The seven-guard inequality has slack
\[
\frac{69{,}286{,}986}{145{,}446{,}009}.
\]
Every generic sparse-row contraction agrees exactly with its guard-form contraction.

The first evaluator stopped before evaluating any row because the point stores its integers as decimal strings. That source and zero-coverage failure are preserved. A separate v2 accepts canonical decimal strings and converts them to Python integers; it uses no floating point. The cuts and point are unchanged.

This point is fractional. Its survival does not establish an integer incidence design or a graph. The new inequalities do not separate this point, so the computation does not justify another continuous optimization call.

## Files and exact scope

The continuation source is rook_case4_face112_branch_continue.py, SHA-256 71e27c5a8b0ff9e268979637d45f6e919806e3653228ece88b69764834d9f478. Its preparation is bound by SHA-256 6d307ce3cea403d8ba4f37b3b1acd78bf9bc7111ab620a3a22c275f7d49e7ca5.

The complete cut certificate is rook-case4-face112-disjoint-guard-cuts01.json, SHA-256 9ef2b90b12a08911970952fca73da4d788f99997e71349433d54429c02c49efc. Its separate deterministic derivation replay passed. That replay reconstructs the certificate from immutable records and does not repeat propagation or reason checking.

The point result is rook-case4-face112-disjoint-guard-point02.json, SHA-256 e8e957a36c408e0988fea1cce53d3a69cc28be505f3bef13324b895b7991b0ea.

A lossless archive preserves all 65 raw files from the three continuation stages. Its restoration checks every member byte for byte. The original partial archive remains a separate dependency.

The 112-zero incidence case and the full strongly regular graph problem remain unresolved.
