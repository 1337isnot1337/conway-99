# Proposed complete-row LP pilot on the 50 remaining low boxes

The small native-row pilot excludes four of the 54 low-face boxes. All other 50 returned numerically optimal. Their feasibility in the complete retained-row model is still unknown. The four accepted pair inequalities also pass the latest exact global point, so they do not justify another unconditioned LP on that point.

## Exact model scope

Retain the full 167,121-row six-cut matrix and its 1,103 coordinates. Set the artificial coordinate `t` to zero and set every objective coefficient to zero. The 1,102 original selector coordinates retain each branch's complete saved box. Every original solution embeds with `t=0`; no positive-floor assumption is used.

Append six accepted rows:

1. `H42 <= 5`;
2. `H42 + 2*(x600+x922) <= 5`;
3. `x261+x803 <= 1`;
4. `x262+x803 <= 1`;
5. `x339+x765 <= 1`;
6. `x761+x1183 <= 1`.

The first two are present in the small pilot but absent from the frozen six-cut matrix. Including them keeps the next model at least as strong as the completed small pilot. The resulting inventory is 167,127 rows and 10,769,860 nonzeros. The old 164,044 retained cover rows remain intact. Their original complete-cover accounting is inherited from the accepted matrix, without regenerating supports.

Use exactly the 50 surviving low boxes. The complete case cover still includes the unchanged 137 high boxes, for 187 total. No further selector is globally fixed.

## Why the earlier fast LP is not a full-matrix benchmark

The latest six-cut solve took 1.112 seconds, but its native model contained only 3,077 rows and 28,337 terms. It subsequently scanned all 167,121 rows and needed no new cover. A full native model has about 380 times as many matrix terms. That earlier duration cannot predict the conditioned complete-row times.

The new preparation should load the frozen integer matrix once, preserve and verify its exact prefix, and append only the six small rows. Each branch must reset and read back every bound, including `t=0`. No bound or row may silently carry over from a different branch.

## Transport and storage

The proposed primary integer CSR arrays occupy 133,251,580 bytes, before provenance arrays and native solver storage. A separate float64 coefficient copy adds 86,158,880 bytes.

Reading the full native coefficient and index vectors through Python list getters can allocate hundreds of megabytes: about 344.6 MB for coefficient objects and pointers and up to 387.7 MB for index objects and pointers. The installed HiGHS type declarations expose `getRows` and `getRowsEntries` with NumPy outputs. The proposed preflight should first verify those APIs on a tiny signed matrix, then audit the complete native matrix in bounded row blocks. This avoids large Python lists and repeated getter copies. Actual peak memory still needs measurement.

One full float64 row ray requires 1,337,016 bytes. Fifty would require 66,850,800 bytes before bases and metadata. The previous raw JSON layout is unsuitable for a full-row batch. Preserve complete native rays, selector values, and basis statuses in lossless compressed binary records; derive sparse integer row multipliers separately for exact proof checking. Do not discard numerical data before the durable record is complete.

For comparison, the completed small pilot's 54 numerical JSON records total 7,288,509 bytes and compress to 298,287 bytes. Its four saved rays have 352, 351, 473, and 354 nonzero entries. These observations do not bound future ray sparsity or compression.

## Proof contract

For signed integer row multipliers, choose each row's upper endpoint for a positive multiplier and its lower endpoint for a negative multiplier. Sum the forms and endpoints exactly. A branch is excluded only when the minimum of the combined form over its entire saved box exceeds that combined upper bound.

Use Python integers or an explicitly checked integer-arithmetic bound for the contraction. The artificial coordinate contributes zero. Preserve the 112 original zero premises, the complete prior branch-proof binding, and all original row identifiers. The saved row combination must be interpretable on the original 1,214 selector coordinates modulo those proved zero equations.

A numerical infeasible status without a checked positive gap is unresolved. A numerical feasible status is also unresolved unless a separately specified exact primal gate is added. This proposal adds no such gate and repeats no prior branch propagation.

## Proposed finite resources

These are planning values, not an execution authorization:

| Stage | Cooperative/native limit | Hard owner |
| --- | ---: | ---: |
| New zero-solve transport preflight | 60 s | 90 s |
| One-call-per-branch forward pass | 50 calls; 2 s requested each; 120 s cumulative native; 240 s phase | 300 s |
| Independent exact certificate replay | 120 s | 150 s |

Use one worker, no retry, and no hidden ray-generating solve. Preserve incomplete and unprocessed branches as unresolved. A 128 MiB compressed transcript cap covers a complete finite pass more sensibly than the old raw-JSON scheme, but cap failures must still stop honestly.

The source-bound inventory is `experiments/logs/grids-and-triangles/rook-case4-low50-full-row-scope01.json`, SHA-256 `2e04787dc089be866fa25d766e7c55f965411941a7d1cce94caa0d0aacf98e84`. It binds all current inputs and sources, the exact branch list, array headers, storage arithmetic, and the observed previous native sizes. It performs no native import, model build, large-matrix coefficient decompression, or optimizer call.

