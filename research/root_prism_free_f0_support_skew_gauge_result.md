# Complete skew-gauge census and independent replay

All 306 signed support-restricted skew gauges preserve the accepted
candidate's demand 176, internal positive capacity 172, and gap 4. Their
twelve core transports give 3,672 distinct normalized rows. Every row is
new relative to the complete 12,481-row parent registry.

The finite producer completed in 15.621 seconds of owner time. Its largest
absolute coefficient is 225; its largest row absolute activity is 34,259.
It made no optimizer call or native solver import. All proposed rows, all
306 raw coefficient vectors, and all 3,672 transport coverage records were
preserved. No parent row was changed or removed.

The separate replay imports neither the producer nor its allocator. It
reconstructed each potential array and checked 20,928,564 base edge weights.
It also rebuilt 25,992,852 positive transported allocations, retaining the
original endpoint allocation order through every action. It verified all
rows, complete row origins, exact deduplication, and all parent comparisons.
The replay completed in 26.937 seconds of owner time, with no optimizer or
`CpSolver`, no overrun, and all children reaped.

The accepted new row-list value SHA-256 is
`c132b5052d7a45f8fa25242533fb927b1dc0d65f443eb938479ebaa44bfe5a30`.
The complete proposed export remains immutable. Its original status asks
for independent cold acceptance; the separate accepted cold report now
supplies that authority. Any consumer must bind both records.

Appending every new row would give a 16,153-row registry. This fits the
existing 16,384-row capacity and leaves 231 slots, sufficient for the
planned 96 later rows. This is an available seed family; no new master or Boolean shared-edge query was run
as part of the census.

## Exact sufficient dominance audit

The separate audit reconstructed the baseline allocation and bound every
one of the 171 original Gram rows to its original native-plan row. It
constructed explicit Gram-row multipliers for all 153 global skew identities
and checked their 480 coefficients and zero right-hand sides.

For each raw gauge `g`, baseline `b`, sign `t`, and corresponding global
identity vector `z`, the audit checked every coefficient of `g - b - t*z`.
If all coefficients were nonpositive, the baseline cut and Gram equations
would imply the gauge cut. None of the 306 gauges met this sufficient
criterion. This result does not prove that the rows are independent or
undominated by other combinations of existing constraints. No rows were
removed. The audit completed in 1.455 seconds of owner time.

## Evidence

The producer package is
`f0-support-skew-gauge-producer-artifacts.json`. It includes the frozen source,
configuration, preparation, source review, root gate, complete census and
proposed export.

The independent cold report is
`f0-support-skew-gauge-run01-cold/report.json`, SHA-256
`4e82b71311d72424443fbb62c3c07b8ca0f7f274f85ef9189f3ef1b70f0681e8`.
The dominance report is `f0-skew-gauge-dominance-run01/report.json`, SHA-256
`3fb820602a123bab523205e81a8098f256b6f02d2fb84942831caf99768f262f`.
Its compressed proof preserves every Gram identity and every tested
480-coordinate remainder.

These are necessary inequalities in the existing F0 scope. They do not
construct a strongly regular graph or exclude the whole component.
