# A bounded continuation using individually certified parity cuts

This is a separate continuation after the first parity cycle's incomplete scan.
The old cycle and its unresolved outcome remain unchanged. The new initial
registry contains exactly the two cuts verified by the independent direct
checker. No old search prefix is scanned again to justify those cuts.

## Model and proof boundary

The frozen 1,103-variable extended model, including its 1,102 selector variables
and max-min variable, remains a literal 167,115-row prefix. The initial two
signed cover rows append 132 nonzero coefficients. The cached-array preflight
therefore has 167,117 rows and 10,769,628 nonzeros. The existing 112 zero
coordinates are the only coordinate restrictions.

The new controller imports the numerical, exact-basis, full-point inspection,
and cold-replay functions from the reviewed v4 source. It does not copy or
modify those functions or their module globals. Their original source bindings,
state schema, native runtime binding, and preflight remain intact. A separate
continuation envelope binds the new source, the two direct cut certificates,
the new preparation, and its smaller iteration limits.

Every new inequality has a complete original-coordinate Gram-row witness.
After the proved zero substitutions, its odd support H has a fixed parity r.
For a Boolean vertex F of the opposite parity, the necessary inequality is

\[
\sum_{a\in F}x_a-\sum_{a\in H\setminus F}x_a\le |F|-1.
\]

The source point is used to find a violated inequality and measure its exact
deficit. The inequality's validity follows from the original equations and
Boolean parity. The proof checker reconstructs those equations directly.

## Discovery is separate from proof acceptance

At a newly accepted exact point, discovery uses the same three ordered parity
families: the saved original basis and two bases ordered by exact point weights.
The raw candidate bound is 123,123. Exact equations are deduplicated within the
discovery. The new point is evaluated once; previously scanned unchanged points
are not revisited.

The implementation stops after two new complete violated cuts or 45 seconds of
cooperative discovery work. Its owned child has a 60-second hard guard. A cheap
integer distance calculation screens equations; the full forbidden-vertex
certificate and row hash are constructed only after a strict violation. The
distance calculation was checked against literal forbidden vertices in 2,540
small cases, including ties.

Each complete cut is written by atomic file replacement. An independent stage
checks those complete files against the original 630 Gram rows and the exact
source point. It does not read a search basis or repeat the candidate prefix.
The controller may adopt those independently checked cuts even if discovery
stopped early. It records the searched prefix and partial files but makes no
independent exhaustion claim. An invalid or unfinished proof is never appended.

## Fixed limits and outcomes

There are at most two new LP rounds and two fresh-point discoveries, with two
new cuts per discovery. Including the initial two cuts, at most six cuts can
enter the registry. The inherited numerical limit is 120 cumulative native
seconds, at most 30 native calls per round, and a 180-second wall limit per
numerical child. Each exact reconstruction and each cold arithmetic check has
its inherited 60-second limit. Each direct discovery-proof stage has ten
seconds. The declared child-stage total is at most 740 seconds; the owning
process group has a 900-second hard guard. No retry is automatic.

The total discovery transcript allowance is 64 MiB, including a one-MiB result
and proof reserve per discovery. The exact residual basis dimension remains
bounded by 512. Aliases and fixed coordinates inferred from a numerical basis
remain proposal restrictions only. Every rational point must pass all original
native rows, all original coordinate covers, all inherited cuts and every
newly registered cut for its prefix.

A point's accepted registry size is recorded separately from later cuts that
reject it. In particular, cuts found after the final permitted LP round may be
retained for later work, but the preceding point is not claimed feasible for
those additional rows. A checked finite-box contradiction can exclude this
case-4 relaxation; a checked zero-face certificate stops the continuation
without changing its domain. Partial discovery, no new cut, repeated point,
timeout or failed exact reconstruction leaves the case unresolved.

The preparation and cached-array preflight used no optimizer. Production
requires separate source and preparation gates.
