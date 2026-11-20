# Exact positive point for the complete H3 selector relaxation

The complete case4 selector LP with 112 proved zero columns, both unit
sums, four certified pair bounds, and the third parity cover has an exact
rational point. Every one of the 1,102 surviving selector coordinates is
positive. This is a real relaxation witness, not a binary incidence or a
99-vertex graph.

The common denominator is 27,131,679,103. The smallest extended coordinate
is the max-min value

\[
t=\frac{296623030}{27131679103}>0.
\]

H1, H2, and H3 all equal one at this point. The full 1,214-coordinate
numerator vector is saved in
`rook-case4-face112-h3-basis-run01/candidate.json`, SHA256
`cecacaaa1cb6974dd898f1d2b69be32a06e44e9b89a1b45e35717bc347d3b4e8`.

## Reconstruction and scope

The preceding numerical H3 query remains frozen as `UNRESOLVED`: its
generic rounding did not produce an exact certificate. The new package
uses only that saved basis. It does not call an optimizer again.

The basis proposes 815 equalities (x_j=t). After these candidate-only
substitutions, 288 equations remain: 286 original native rows, H1 at one,
and H3 at one. The reduced integer matrix has 2,071 nonzeros. One bounded
FLINT rational solve completed in 0.107 seconds; the owned child, including
complete acceptance, finished in 13.426 seconds. No universal equality
between a selector and (t) is inferred from this proposal.

The child checked all 167,113 extended model rows, all 2,271 original
native constraints, all 178,533 original coordinate covers, every variable
bound, all 112 zero premises, both unit sums, all four pair bounds, and H3.
The output integers have 35 bits. The package does not claim a bound on
FLINT's internal intermediate integers.

## Preserved failed replay and separate direct verification

The prescribed cold basis replay hit its 60-second deadline while checking
the full face-row array. Its traceback and a separate failure record are
preserved. It did not report an arithmetic contradiction, and it is not
counted as a completed verification. The identical timed-out command was
not retried.

The replacement checker,
`rook_case4_face112_h3_point_direct_check.py`, has a separate source and
input binding. It imports no model or basis source and performs no model
reconstruction or elimination. It binds the already completed H3 model
and numerical cold replays, then verifies the candidate directly against
the frozen exact arrays and original inputs.

For the full sparse matrix, it first proves a Python-integer majorant on
every signed-64-bit product and partial sum. The largest majorant is
4,621,284,176,040,348, below (2^{63}-1); the scaled row endpoints also fit.
It then computes the integer row activities in bounded batches. Original
native rows are checked separately using Python integers. Every original
cover is decoded directly from the little-endian registry and checked
with a separate exact integer sum bound.

This direct check passed in 18.874499 seconds. Its report is
`rook-case4-face112-h3-point-direct-check01.json`, SHA256
`f20cb9ffe3768591cd255dd9b148881d7c3df8df80fb881a7c59a75c6758395c`.
It checks the full 167,113-row system and every original-coordinate
obligation listed above.

The positive point rules out further zero-coordinate deductions from this
particular real relaxation. Additional Boolean information may still cut
it off. The point's odd denominator also gives a direct GF(2) solution of
the projected original Gram equalities by reducing its numerators modulo
two; this proves consistency, not the rank of a chosen projected basis.
