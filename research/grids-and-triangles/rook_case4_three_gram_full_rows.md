# Full-row refinement of the H27 branch cover

This is a finite, exact Boolean bound-propagation preparation for rook case 4.
No optimizer, SAT query, new branch enumeration, or repeated native propagation
is part of the preparation. The forward sweep remains a separately gated action.

## The complete branch cover

The sum of original Gram rows 214, 344, and 582 has right side 3. On the proved
112-zero face, its positive coefficients consist of 26 coefficients equal to 1,
nine equal to 2, and one equal to 3. Thus every Boolean solution lies in exactly
one of 2,835 positive-support patterns: one singleton, 234 pairs, or 2,600 triples.
Every other positive-support coordinate is zero in its respective pattern.

The frozen preparation and its separate cold replay reject 2,391 patterns using
original native row capacities. The resulting 444 patterns were propagated once
against all 2,271 original native rows and seven proved additional rows. The
separate cold replay checked all 444 traces: 184 contradictions and 260 complete
fixed-point boxes. The surviving boxes consist of one singleton pattern, 65 pair
patterns, and 194 triple patterns. No common new zero or one was obtained.

The new sweep refines those 260 boxes. It retains both earlier stages of the
branch-cover argument. It does not assume that any fixed-point box contains an
actual incidence solution. A fixed point means only that the stated one-row
Boolean interval rules find no further implication in that box.

## Full row pool and coordinate map

The unchanged parent is the complete, cached 112-zero-face model:

| Quantity | Parent | New pool |
| --- | ---: | ---: |
| Surviving selector coordinates | 1,102 | 1,102 |
| Rows | 166,013 | 166,020 |
| Integer nonzero coefficients | 10,767,292 | 10,767,637 |

The parent accounts for all original 2,271 native rows, all original 178,533
coordinate covers, and the previously proved integer consequences. Its saved
omission and column-substitution proofs remain bound by the passed parent cold
record. This preparation hashes the actual NPZ archive, checks every raw array
hash, and checks exact equality of every retained parent array prefix. It does
not regenerate the original cover supports.

The seven appended rows are the five final registered parity cuts, the
unconditional bound H42 <= 5, and the unconditional inequality
H42 + 2(x600 + x922) <= 5. The frozen seven-row verifier rechecks the original
1,214-coordinate proofs and proved-zero substitutions. H42 = 5 is not a premise;
none of the conditional zeros from that separate face is imported.

Exactly the 112 globally proved zero coordinates are removed. Each saved native
box is reconstructed from its original positive-support pattern and its complete
saved trace, then compared with its previously checked final-state hash. Its
1,102-coordinate projection is lifted back to all 1,214 coordinates and compared
exactly. The preparation binds all 444 original record hashes and the completed
native cold report; it does not rerun their propagation or reason checks.

## Exact propagation and replay

The new source imports the frozen `Pool`, `propagate`, `verify_record`, and
`literal_bounds` functions from the previously reviewed full-row kernel. It
does not call that module's H42 = 5 matrix builder or conditional state loader.
There is one loaded row pool per child process, shared by all branch attempts.

For each row, the kernel computes the minimum and maximum over the current
Boolean box. It fixes a free bit only when one of its two values makes that row's
interval disjoint from the row bounds. A row whose interval is already disjoint
proves a contradiction. A row that excludes both values also proves a
contradiction. All activity, update, and endpoint arithmetic is integer arithmetic.

Before NumPy reductions, the pool checks a Python-integer bound of the form
`nnz * max_abs_coefficient + max_abs_endpoint + max_abs_coefficient < 2**62`.
Each row's columns must be strictly increasing. Therefore a column incidence
update touches each affected row once, and no duplicate-index update is lost.

Cold replay checks every trace reason in sequence using Python integers and the
current box. At a claimed fixed point, it independently recomputes every row's
extrema, rejects any violated row, and checks every row that could force a bit.
Each checked branch gets a separate durable replay record.

## Finite budgets and partial outcomes

| Stage | Cooperative work budget | Hard owned-child budget |
| --- | ---: | ---: |
| Matrix and saved-box preparation | 60 seconds | 90 seconds |
| All 260 forward branch attempts | 900 seconds | 1,000 seconds |
| Cold replay of saved attempts | 1,200 seconds | 1,300 seconds |

Each forward branch has a 10-second cooperative budget within the shared
900-second budget. These cooperative deadlines are checked by the frozen kernel;
they are not independent operating-system timers. The owner includes imports,
matrix loading, all work, and output handling in its hard deadline and kills and
reaps its child on an overrun. Peak RSS is checked after preparation and each
completed branch/check against 1 GiB; this is a sampled resource gate, not a hard
allocation ceiling. Forward transcript size is limited to 64 MiB.

The earlier, separate H42 = 5 full-row run provides the cost estimate only. Its
12 completed forward branches averaged about 2.43 seconds. Its cold run checked
those 12 fixed points and one partial trace in 44.78 seconds. These observations
suggest roughly 630 seconds forward and roughly 970 seconds cold for 260 boxes;
they are not guarantees about the new boxes. They motivated a finite complete
sweep rather than another short prefix.

A partial branch is saved once and the next distinct branch is attempted while
budget remains. No branch is retried. If the shared time, transcript, memory, or
owner bound prevents completion, the unprocessed branches remain unknown. The
owner preserves all complete files even when the child does not finish normally.

No global literal or case exclusion follows unless all 260 branches have
nonpartial terminals, all are cold-checked, and the forward owner completed
normally. Only then may a common literal of every surviving box be promoted.
If all 260 branches contradict, their proofs together with the prior 184
contradictions and the original capacity exclusions exclude this case. An empty
survivor collection never produces vacuous literal claims. No outcome alone is
a resolution of the whole graph problem.

## Current preparation status

The standalone scope mode uses only the Python standard library. It checks the
frozen source/input hashes and 5,460 literal projection/signed-box controls,
363 missing-or-partial coverage controls, and the empty-family/nonconsecutive-ID
intersection cases. It does not import the NumPy kernel, construct the matrix,
or propagate a case branch. The source binds that saved control report for later
preparation rather than repeating these controls in each child.

Actual matrix preparation and the forward/cold sweep are separate actions. The
source and scope record must be reviewed before those actions are started.
