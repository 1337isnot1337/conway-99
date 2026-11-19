# Strengthened three-Gram branch propagation

The complete weighted branch cover for rook case 4 now has 260 surviving patterns. Exact propagation rejects 184 of the 444 patterns that passed the earlier native capacity census. A separate cold replay checks every contradiction and every surviving fixed point. No new global zero or one literal follows from their intersection, and case 4 remains open.

## Domain and proof scope

Original Gram rows 214, 344 and 582 give H27 + 2Q = 3 on the 112 proved-zero face. The positive coefficient support contains 26 weight-one columns, nine weight-two columns and the weight-three column 764. The complete Boolean alternatives are a singleton 764, one weight-one/weight-two pair, or a weight-one triple. Every other positive-support column is zero within its branch; columns outside this support remain free apart from the 112 common zeros.

The earlier frozen preparation checked all 2,835 raw alternatives and rejected 2,391 using original native capacities. The present driver starts from the exact remaining list of 444 initial boxes. It retains all 2,271 native rows byte for byte and appends seven proved rows: the five final cycle parity inequalities, the unconditional upper bound H42 <= 5, and H42 + 2(x600 + x922) <= 5. This gives 2,278 rows and 29,129 terms on the original 1,214 coordinates.

H42 = 5 is not a premise. The loader uses the previously reviewed original-coordinate proof checker and deliberately discards its conditional equality row. It separately verifies the four-Gram-row identity for the unconditional upper bound. The 31 zeros conditional on H42 = 5 are not used.

The propagation and cold reason-checking functions are imported unchanged from the frozen exact integer kernel. Its signed integer activity bound is checked before NumPy arithmetic. Every forced assignment has a row reason in the preceding Boolean box. The cold pass checks those reasons with Python integers and checks the complete fixed-point condition for every surviving box.

## Complete result

| Pattern type | Initial retained patterns | Checked contradictions | Surviving fixed points |
| --- | ---: | ---: | ---: |
| Weight-three singleton | 1 | 0 | 1 |
| Weight-one/weight-two pair | 80 | 15 | 65 |
| Weight-one triple | 363 | 169 | 194 |
| Total | 444 | 184 | 260 |

The forward pass saved all 444 records, with no partial or unprocessed branch. It recorded 9.737 seconds for propagation and 4.130 seconds for initialization; its owned process completed in 44.943 seconds. The separate cold process completed in 15.039 seconds, including 12.131 seconds for replay and 2.380 seconds for initialization. Both children exited normally and were reaped. The frozen limits were 60 seconds for each forward/replay phase, one second per forward branch, and a 90-second hard owner for each phase. No optimizer was called.

The cold pass verifies 57,825 forced assignments across the complete record set. Only after all 184 contradictions and all 260 fixed points pass does the driver intersect surviving boxes. That intersection adds no global zero or one. The global scope does not rely on an incomplete branch prefix.

## H42 inspection

A separate artifact-only checker rebinds the complete records and cold report, reconstructs each final box from its saved initial assignments and trace, and counts its fixed/free H42 coordinates. In every surviving box, the interval still contains all three necessary odd values 1, 3 and 5. There is no empty odd interval and no new conditional equality for H42 from this inspection.

These intervals are necessary projections, not feasible incidences. A fixed point means only that the stated bound-propagation rules found no further assignment or contradiction in that box. The complete coordinate-cover pool was not included in this small model.

## Frozen artifacts

The v1 driver is preserved unrun. The v2 source, exact text/AST reuse record, actual preflight, coordinator gate, all 444 branch traces, both owner/result records, the cold checks, and the branch-box inspection are listed in the publication manifest. The earlier weighted branch preparation and its cold replay are separate frozen dependencies.

No later propagation, branch extension, optimizer retry or changed assumption is part of this result.
