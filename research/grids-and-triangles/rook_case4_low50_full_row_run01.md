# Complete-row conditional LP: first bounded batch

This experiment produced no new mathematical exclusion. All 36 attempted
branches ended at the native time limit. No existing infeasibility ray was
available, so no integer exclusion certificate was proposed or accepted.
Fourteen of the 50 selected low branches were not attempted. The 137 high
branches were outside this batch.

The independent cold replay accepted the complete retained transcript
prefix. This acceptance verifies the frozen matrix and branch bindings,
the saved numerical records, and the absence of an unchecked exclusion
claim. It does not establish feasibility of any branch.

## Frozen scope

The matrix has 1,102 selector coordinates, one artificial floor fixed to
zero, 167,127 rows, and 10,769,860 nonzero entries. It preserves the old
167,121-row six-cut relaxation and appends the two proved H42 bounds and
the four pair inequalities from the smaller native-row pilot. The full
retained cover pool is present. Every attempted branch received one
complete reset of all 1,103 bounds and one native call. No branch feedback,
second ray solve, or retry occurred.

The native matrix coefficient audit completed at 38.631289487 seconds.
The first branch then received the same two-second requested cap used for
later calls, subject to the remaining cumulative budget. The solver
returned all attempted calls with kTimeLimit and kWarning. A numerical
value vector and basis were available and saved for each call, but these
are observations only.

## Timing and retained data

| Measurement | Observed value |
|---|---:|
| Attempted branches | 36 |
| New exact exclusions | 0 |
| Unprocessed low branches | 14 |
| Cumulative measured native time | 121.373805144 seconds |
| Cumulative native target | 120 seconds |
| Measured cumulative overrun | 1.373805144 seconds |
| Forward phase | 166.170976556 seconds |
| Forward owner | 167.024775170 seconds |
| Independent cold replay | 3.365663263 seconds |
| Cold owner | 3.633909637 seconds |
| Full wrapper | 170.852467093 seconds |
| Peak forward RSS | 1,336,820 KiB |
| Complete saved numerical bases | 36 |
| Complete saved value vectors | 36 |
| Complete existing rays | 0 |
| Compressed numerical archives | 237,933 bytes |

Both owned children exited and were reaped without a hard timeout. The
last call crossed the cumulative native target; the driver recorded that
overrun and stopped without another call. The 240-second forward and
300-second owner limits were not crossed. The replay finished within its
separate limits. No incomplete transcript tail remains.

The unprocessed whole-cover box indices are
42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 57, and 60.
The previously certified exclusions at indices 10, 11, 15, and 64 remain
valid. This batch does not remove any further box from the complete cover
and does not prove a global zero, H27 equal to three, or case4 exclusion.

## Artifact bindings

The production configuration is
`rook-case4-low50-full-row-query-configuration01.json`, SHA256
`1420c4a2b7dff1248ea53083ffeba31dcf7a42755810db50603f46130b633626`.
The preparation map is
`rook-case4-low50-full-row-preparation-git-blobs01.json`, SHA256
`50ec4f1109aff07468d836a5804ab31b33e1781bf20bda2b34877b5af6103775`.

The terminal result has SHA256
`749e15da5a0062da3f2941b15e2350faa83861419cbffea8ab7810e4914a6e6d`.
The independent cold record has SHA256
`d9d92efcb4f7db45c19372149c59c35942139709e77eab20c838df2d6fe68171`.
The separate artifact-only accounting report has SHA256
`e8d19d5e398182be3bb6400456f59f210e52f6056dad3ee7b301c59fd64db2c2`.
That accounting reads the saved transcript and hashes; it does not reload
the case matrix, repeat proof arithmetic, or invoke an optimizer.
