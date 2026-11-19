# Complete 64-branch propagation preparation

The two proved equalities \(H_1=H_2=1\) give a complete Boolean cover by 72 positive patterns. One common singleton is excluded by \(x_{663}=0\). Four difference-set pairs have certified upper bounds below two. A check of all 40 difference-set pairs against every original native row excludes three further pairs, \((262,594)\), \((262,595)\), and \((262,733)\), through Gram row 584. The remaining cover has 31 common singletons and 33 pairs.

The scope source and its separate replay preserve every original pattern and its disposition. The batch adds only the selected positive pattern as one or two explicit equality rows. All other variables remain free except for previously proved constraints.

## Exact rows and coverage

Every branch retains 1,214 literal primary variables, all 2,271 original native rows, both unit-sum equalities, the four certified pair rows, 112 proved zero rows, and the proved 86-column sum of two. This gives 2,390 common rows with 29,074 term occurrences. The branch has 2,391 or 2,392 rows after its assumptions.

All 178,533 original coordinate covers remain, in the unchanged 27,494,082-byte raw registry. The 14 empty-support covers seed the same exact propagation engine. No Boolean variables are identified.

Preparation serializes the common rows and checks their canonical hash against the completed scope preparation. It also checks every branch's full augmented-row hash. Production loads these saved rows and the frozen registry; it does not regenerate the parent graph or column domain. Preparation took 1.599 seconds and propagated no branch.

## Limits and acceptance

The forward batch uses one owned child. It has a 60-second cumulative cooperative budget and a 65-second hard process deadline including initialization. The unchanged engine checks time before each native row and every 128 cover records. The unchanged supervisor persists an unknown status before killing and reaping an overdue child. Already checked supervisor controls are reused.

Branches run in increasing original pattern ID. Each completed trace is saved before the next branch starts. An interrupted trace, an active branch without a saved trace, and every unqueried branch remain distinct. The forward result accepts no exclusion.

A separate owned child has a 60-second hard deadline to check saved complete traces. It uses the frozen independent reason checker, which recomputes conditional extrema without the forward row-event function. A fixed point is checked against every row and every cover. Its assignments remain conditional on the selected pattern.

A contradiction excludes only its checked branch. A fixed point does not establish a Boolean solution or graph completion. The case can be excluded only if all 64 retained patterns have cold-checked contradictions, together with the eight initial certified exclusions. Partial or unchecked coverage cannot establish that conclusion.

## Frozen preparation

- Runner: experiments/workspace/rook_case4_face112_branch_batch.py, SHA-256 cda346ce4bb34a9ccc1f5fc603485124bc0cb389b8b9cc48d169b08297a6bd60.
- Preparation: experiments/logs/grids-and-triangles/rook-case4-face112-branch-batch-preparation01/preparation.json, SHA-256 47ebe7180723ab95bdf5370c29a0be6abe80005dc5e0bd7e3df51926282b87ea.
- Common rows: the same preparation directory, rows.json, SHA-256 361f04e0176d0ac53bed09ff9c7cdf33d76608b99c3a2426f0cf35345da46a55.
- Complete branch scope: rook-case4-face112-branch-preparation01.json, SHA-256 5e8bf7a32063cda146b18de2a4b3ee7c4b2a043d5076a5d4a9a9e4ca678144c2.
- Separate scope replay: rook-case4-face112-branch-preparation01-replay.json, SHA-256 52ce504a583c86d1dd24e3841bf37d7167df970159e8b9d4862e598d0b8bb76d.

At this checkpoint no production branch propagation, solver query, or optimizer call has run. The complete graph problem is unresolved.
