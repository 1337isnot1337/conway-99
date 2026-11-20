# Packing domains and the lightweight count query

This preparation retains the necessary count model for a globally
prism-free, F-free SRG(99,14,1,2) with a split 18+18 shell containing
component zero. Every variable ID and every constraint from the previous
external-row target remains unchanged. The two new layers intersect
integer domains with separately certified pair- and edge-packing bounds.

A feasible count assignment would still need a common literal selector
incidence and an exterior graph. The native query itself will report a
full-target-passing vector as provisional. A separate exact check against
the restored original parent must pass before any count-feasibility claim.

## Why a clique bound limits an orbit count

For a retained pair orbit, each literal pair is an object in a small
compatibility graph. Two objects are incompatible when their combined
endpoints contain a previously proved-zero selector pair. If an incidence
selects several objects, every pair of them is compatible. The selected
objects therefore form a clique. A certified upper bound on clique size
bounds that orbit's integer pair count.

The exterior-edge compatibility graphs also use the separately checked
prism, common-neighbor, and mixed-quota implications. An actual selected
edge set again gives a clique. A compatibility clique need not extend to
an incidence or graph. Only the resulting upper bound is used here.

Neither argument assumes that the hypothetical completed graph has a
symmetry. These are counts on the complete actual relabeling orbits of the
fixed core. The previous count-coordinate derivation remains unchanged.

## Two immutable domain layers

The Z layer checks all 9,353 retained pair orbits. It changes 8,251 explicit
domains, leaves 1,102 Z domains unchanged, and preserves all 9,091 other
variables. It uses the complete saved packing ledger and its independent
literal-graph/certificate cold replay. The overlay does not repeat that
census.

The Y layer sits on the frozen Z layer. It checks all 5,643 retained edge
orbits, changes 5,153 explicit domains, leaves 490 Y domains unchanged,
and preserves all 12,801 non-Y variables. Exactly 62 certified Y bounds
improve the corresponding transferred Z bounds. That comparison is
separate from the number of explicit native domains changed.

Each layer applies the exact intersection

\[
D_j^{\mathrm{new}}=D_j^{\mathrm{old}}\cap(-\infty,u_j].
\]

The code retains every hole in a flattened integer interval domain. It
records every changed and unchanged coordinate. All tables, multiplication
constraints, row maps, variable names and IDs, and the 117-row external
pool retain their old values. Restoring only the previous domains in each
new protobuf reproduces the entire previous protobuf hash.

The complete target still has 18,444 variables and 34,398 constraints.
The initial native subset still has 34,281 constraints. The omitted 117
rows remain in the mathematical target and are checked exactly at every
returned integer point.

The Z packing comparison found that 6,842 of the 8,251 explicit box
improvements were already implied by simple endpoint activation using the
current selector-population maxima. Another 1,409 improve both comparisons.
This does not invalidate any bound, and it does not prove independence
from every other existing constraint.

## Preparation and preserved timeout

The Z native preparation passed in 13.34 seconds. Its first separate cold
replay reached the stage confirming all 9,353 intersections, then exceeded
its 60-second owner limit. The owner recorded 80.31 seconds including
termination and reaping. That attempt remains `UNKNOWN_HARD_DEADLINE`;
it has no accepted cold result.

A separately authorized direct checker then passed in 4.52 seconds. It
imports no subject builder or native model constructor. It enumerates the
finite old domains, checks every certified intersection and all other
domains, compares all non-domain plan fields, and restores both previous
whole-protobuf hashes. It binds the prior successful native preparation
and the complete earlier clique-certificate cold replay.

The Y native preparation passed in 12.63 seconds. Its separate cold replay
passed in 2.35 seconds. These are measured preparation times, not expected
search times.

## Lightweight runtime and exact boundaries

The earlier external-row child exited with signal 9 before making a native
call. Its cause was not established. That failure and its narrow terminal
check remain preserved in the previous package.

The new query loads only the final plan and two archived protobufs. It
releases decompression buffers and unused proof metadata. It constructs
the initial native model with the same reviewed public constructors. It
does not call a mathematical builder's `load_inputs()` or `derive()` and
does not load the large product specification. Durable stage records save
elapsed time and current/peak RSS.

The one prepared run has a 180-second owner limit, at most 12 CP-SAT calls,
one worker, seed zero, and probing level zero. Imports, construction,
serialization, native search and arithmetic share that budget. Each later
call requires a strictly larger prefix of certified target rows. At most
16 exact violated rows are appended per returned integer vector, in the
frozen pool order. No candidate-specific visitation restriction is added.

Every returned vector is saved before expensive checks. `candidate.json`
is a plain JSON root array of 18,444 integers. The runner records both its
file hash and the hash of the canonical integer array without the trailing
newline. It checks the actual active prefix and all 117 external rows
using Python integers.

A vector with no external violation receives a complete native-target
check, including domains, linear rows, products and tables. Its status is
`PROVISIONAL_FULL_TARGET_WITNESS`, and `count_feasibility_claimed` remains
false. The accompanying record explicitly sets `accepted` and
`restored_original_parent_checks_passed` to false. It is not an accepted
receipt for literal lifting.

The later restored-parent receipt must bind the candidate file and
canonical-vector hashes, target protobuf, model preparation, query
preparation and final domain-list archive. It must explicitly confirm both
full-target and restored-original-parent checks. That arithmetic task is
separate from this search driver.

A native infeasible status remains unproved. A failed, late or incomplete
child does not establish feasibility or exclusion. Saved partial vectors
remain available for a separately scoped exact check. No unchanged query
retry is part of this preparation.

The query's parameter, row-selection, native-point and external-row
evaluation functions are AST-identical to their frozen predecessors. The
new owned cold preflight passed in 2.74 seconds without constructing a
solver. Production execution requires the separate coordinator gate.
