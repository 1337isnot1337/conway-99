# First bounded propagation pass over the 112-zero branch cover

No retained branch was excluded. The forward pass reached 50 exact interval-and-cover fixed points, saved one partial trace, and left 13 branches unqueried. The separate cold pass checked 28 of those fixed points before its hard deadline. A fixed point does not establish a Boolean solution.

## Complete cover and terminal partition

The two unit sums give 72 original patterns. The zero at column 663 excludes one common singleton. Four previously certified pairs and three direct violations of Gram row 584 exclude seven difference-set pairs. The remaining 64 patterns consist of 31 common singletons and 33 pairs. The scope ledger lists every pattern, its exact positive columns, and its disposition.

| Status | Count | Original branch IDs |
|---|---:|---|
| Initially certified exclusions | 8 | 16, 32, 33, 35, 40, 66, 67, 71 |
| Cold-checked fixed points | 28 | 0–15, 17–28 |
| Complete forward fixed points awaiting cold replay | 22 | 29–31, 34, 36–39, 41–54 |
| Partial forward trace | 1 | 55 |
| Unqueried | 13 | 56–65, 68–70 |

The forward owned child exited normally after 60.748 seconds, within its 65-second hard deadline. The cold child reached its 60-second deadline and was killed and reaped. Its first 28 checked records remain valid. No result is inferred for the interrupted check of branch 29.

The unchanged engine, all 2,390 common rows, all 178,533 coordinate covers, and every positive branch assumption remain bound to the preparation. No solver or optimizer was called. This attempt is frozen without repeating a completed branch.

## Conditional assignments

The 28 checked branches fix between 187 and 271 coordinates to zero and one or two coordinates to one. They leave between 942 and 1,026 coordinates unassigned.

Their common extra zeros, beyond the 112 previously proved zeros, are
\[
\{259,260,261,262,590,591,592,593,594,595,730,731,732,733,
1210,1212,1213\}.
\]
All 28 checked branches select a common singleton. In particular, the difference-set zeros are expected in this part of the cover. The incomplete cover does not justify promoting any of these shared zeros globally. There is no common positive coordinate, and the checked record ancestry yields no new literal independent of branch assumptions.

Branches 0 through 6 give the individually checked implications
\[
x_a=1 \Longrightarrow x_{535}=1,
\qquad a\in\{74,75,76,77,176,177,178\}.
\]
Their complete reason chains are retained. No new inequality has been added to a model from these implications.

## Artifacts and scope

The forward result is rook-case4-face112-branch-batch01/result.json, SHA-256 186df7589b3baf14adda7fcce8409e89e149b5268ff432f12128b7301d09ab4b. The cold result is rook-case4-face112-branch-batch01-cold/result.json, SHA-256 b789fc8ee377e1899d4de553ad7c48019fdea8913599fb3c8605bf28cb80205e.

The exact coverage and assignment summary is rook-case4-face112-branch-batch01-summary.json, SHA-256 6b8ad7701c1d8744fcf6afe45dfd8360e618d9614c43c0aa21aa52ef2d81bd59. It contains all 72 dispositions and every conditional zero and one from the 28 cold-checked traces.

A lossless archive preserves the preparation rows, all 51 saved forward traces, all 28 completed cold checks, both supervisor records, progress records, and child logs. Its 91 members are checked by the separate archive source. Packaging does not rerun propagation or replay reasons.

The 112-zero incidence case remains unresolved. The full strongly regular graph problem remains unresolved.
