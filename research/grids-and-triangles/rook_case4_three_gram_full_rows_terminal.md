# Full-row H27 branch refinement: checked terminal

The single full-row sweep and its separate cold replay completed all 260 prepared
branches. They produced 69 additional contradiction proofs and 191 complete
fixed-point boxes. There were no partial or unprocessed branches. No new zero or
one is common to all surviving boxes. Rook case 4 remains open.

The complete H27 branch cover originally has 2,835 positive-support patterns.
Original native row capacities rejected 2,391. The first, separately cold-checked
native propagation rejected 184 of the remaining 444. This full-row refinement
rejects a further 69. Thus 2,644 patterns are excluded and every remaining actual
case-4 incidence must lie in one of the 191 saved boxes. A fixed-point box is an
outer approximation; this calculation does not assert that any of the boxes has
a feasible incidence or graph completion.

The pool has 1,102 surviving selector coordinates, 166,020 rows and 10,767,637
integer terms. It preserves the complete 166,013-row parent prefix and appends
the five final registered parity cuts, unconditional H42 <= 5, and
H42 + 2(x600 + x922) <= 5. The only global zero premises are the previously
proved 112 zeros. H42 = 5 and its conditional zeros are absent.

The preparation checked all 444 original trace hashes, reconstructed the 260
native final boxes, and checked exact projection and lifting through the removed
coordinates. It reused the prior completed native cold certificate rather than
repeating native propagation. Its owner completed in 6.095 seconds.

The forward owner completed normally in 182.848 seconds, with 176.152 seconds of
branch work and a recorded peak RSS of 567,116 KiB. The cold owner completed
normally in 149.826 seconds, with 146.463 seconds of checking. Both owned children
were reaped. No deadline, transcript or sampled-memory gate was reached.

Cold replay checked each new trace reason using Python-integer row extrema on
the current Boolean box. It independently recomputed all row extrema and all
potential one-bit implications at every claimed fixed point. Only after all
260 records passed did it compute the common-literal intersection; both lists
were empty. No optimizer or SAT call was made.

## Frozen bindings

| Record | SHA-256 |
| --- | --- |
| Source | fc8d48f1632442daee5d186156874ba50fe46fc55e01a36010525f27bf21cfd1 |
| Preparation | 989ab22a2c2f78cb65b622dfdb4e0aabe8f0353d4616437e736755d4640b7ac1 |
| Forward result | 5e6699c39de0ab165fa6396108ce8c11a9a9e4ca250ef557b7d3f16e7a1ac180 |
| Forward owner | 88e1fdee61b3edabd758cc76321cd4aafd468bb327989f49f360db0a868e609b |
| Cold result | cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e |
| Cold owner | 76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd |

The preparation has its own immutable ten-file publication map. The terminal
package preserves all 260 forward records, all 260 cold records, both complete
outcomes and owners, and their progress/log files. Later searches must bind these
records and keep any new numerical proposal separate from this exact result.
