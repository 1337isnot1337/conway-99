# Two weighted-basis parity cuts for rook case4

The declared finite scan completed and its separate exact replay passed.
It found two inequalities violated by the verified H3 rational point.
These are necessary restrictions on integer incidences. They do not exclude
case4 or construct a binary incidence.

## Point and finite search domain

The input point has common denominator 27,131,679,103 and 112 proved zero
coordinates. Every other one of the 1,214 original selectors is positive.
The independent direct checker accepted all 167,113 extended LP rows, all
2,271 original native rows and all 178,533 original coordinate covers.
That point package is separate from this scan.

The input consists of 286 original Gram parity equations projected through
the proved zeros. Two exact row reductions use decreasing
`min(numerator, denominator-numerator)` as the column order. Ties use
increasing original column ID in the first reduction and decreasing ID in
the second. Both resulting bases have rank 286. Saved forward witnesses,
reverse row-span checks and reduction of all 630 original Gram equations
certify the complete projected Gram row space. The point's odd denominator
also gives a direct consistency witness modulo two.

The scan evaluates each single basis row and each unordered XOR of two
basis rows in three families: the old basis, then the two weighted bases.
An equation repeated between families is evaluated only once. The old
family is evaluated at this new point; its earlier evaluation at another
point is not substituted.

| Family | Raw words | Newly evaluated equations | Violations |
| --- | ---: | ---: | ---: |
| Old basis | 41,041 | 41,041 | 0 |
| Weighted basis, increasing-ID ties | 41,041 | 41,034 | 2 |
| Weighted basis, decreasing-ID ties | 41,041 | 20,306 | 0 |
| Total | 123,123 | 102,381 | 2 |

There are 20,742 duplicate equations. This is a complete census of the
three stated single/pair families, not of every vector in their row space.
The forward pass took 48.469 seconds and the exact replay 49.663 seconds.
Each had a separate 60-second cooperative bound. The saved transcript is
3,612,211 bytes, below the 64 MiB limit. Both violated cuts were retained;
the maximum permitted number was 64. Neither stage called an optimizer.

## Direct integer proofs

Both retained forbidden vertices are zero on their support. Consequently
the two cuts have simpler proofs using only nonnegative integrality and
the prior 99 proved zeros.

Sum the indicated original Gram rows with coefficient one. Write the
result as

\[
\sum_j c_j x_j=b.
\]

Every coefficient is a nonnegative integer and each right-hand side is
odd. After substituting the proved zeros, define

\[
H=\sum_{j:c_j\text{ odd}}x_j,
\qquad F=\sum_j\left\lfloor c_j/2\right\rfloor x_j.
\]

The full original-coordinate identity is `H+2F=b`. Hence an integer
incidence satisfies `H>=1`, equivalently `F<=(b-1)/2`. Nonnegativity also
gives `H<=b` and `F>=0`. These claims require no upper bound of one on the
individual selectors.

| Cut ID | Original Gram row IDs | RHS | Cover size | Capacity terms | Capacity bound |
| --- | --- | ---: | ---: | ---: | ---: |
| 69,760 | 180, 264, 405, 444, 462, 517, 521 | 9 | 70 | 48 | 4 |
| 72,900 | 151, 181, 210, 291, 385, 426, 445, 463, 531, 532, 533, 534, 535, 537 | 17 | 50 | 129 | 8 |

The first capacity has 48 unit coefficients. The second has 103 unit
coefficients and 26 coefficients of two. The shorter equivalent rows
chosen for a later model are therefore the 48-term capacity in `[0,4]`
and the 50-term cover in `[1,17]`. The upper17 endpoint follows from the
same nonnegative Gram sum. Neither choice drops an integer restriction
or adds a restriction to the equivalent two-cover LP.

All odd coefficients removed from the supports lie in the old 99-zero
set. None of the later 13 proved zeros is needed for these two statements
or shortens their capacity forms. The direct verifier reconstructs every
coefficient on all 1,214 original columns, checks both identities, binds
the zero-premise certificate, and replays the exact point contractions.
It also checks 22,620 small nonnegative-integer assignments of the general
parity identity. The old zero proofs are bound, not rederived.

At the saved point the two cover deficits are

\[
\frac{16,558,664}{27,131,679,103},\qquad
\frac{8,455,479,910}{27,131,679,103}.
\]

The corresponding capacity excesses have numerators 8,279,332 and
4,227,739,955. The exact identity makes each capacity excess half its
cover deficit. No new forced-zero coordinate or whole-case contradiction
is claimed.

## Artifacts

The row-reduction helper is `rook_case4_weighted_parity_basis.py`; the
bounded driver is `rook_case4_face112_h3_weighted_parity.py`. The run
directory retains both row-space certificates, the complete distinct-word
evaluation transcript and both full original-coordinate cut witnesses.
The separate replay checks the saved bases and all evaluations without
repeating row-reduction elimination.

`rook_case4_face112_weighted_parity_covers.py` is a separate direct proof
checker. It imports no subject builder, separator or optimizer. Its
certificate records both cover/capacity forms and the proposed shorter
rows. The source review, preparation, run, replay and direct proofs are
listed in the package manifest. Any later LP append has a separate source,
model and query gate.
