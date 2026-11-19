# Column 663 vanishes on the original 99-zero face

For the fixed case4 attachment domain, the original Gram equations and one
original signature capacity imply

\[
6x_{663}\leq 5
\]

after substituting the 99 previously proved zero coordinates. Thus a
nonnegative integral attachment vector has \(x_{663}=0\). This deduction
does not need either parity equality or the twelve later zero coordinates.

## Exact row certificate

Write the 630 original Gram equations as \(A x=b\), with all 1,214 original
attachment columns present. The saved certificate gives an integer vector
\(\lambda\), supported on 143 Gram rows, for which
\(\lambda^T b=4\). Let \(s\) be the indicator of the original signature96
class, whose five columns are

\[
\{258,259,260,261,262\}.
\]

Original signature-capacity row51 states \(s^T x\leq1\). Therefore, with
\(c=A^T\lambda+s\),

\[
c^T x\leq5.
\]

The checker expands all 1,214 entries of \(c\) directly from the original
row inventory. Its eight negative entries lie among the previously proved
99 zero coordinates. The coefficient of column 663 is 6. On the 1,115
remaining columns the complete coefficient counts are:

| Coefficient | Number of columns |
| --- | ---: |
| 0 | 1,013 |
| 1 | 7 |
| 2 | 85 |
| 3 | 9 |
| 6 | 1 |

All other surviving terms are nonnegative. Dropping them gives the stated
bound. Only integrality of \(x_{663}\) is needed for its zero conclusion;
the other surviving coordinates can be arbitrary nonnegative reals.

## How the shorter premise chain was obtained

The earlier saved denominator-six bound used 110 Gram rows and
\(H_1=1\). Removing that parity-equality term leaves a relation of the form
\(6x_{663}+2\sum_{a\in S}x_a-H_1=3\) on its previously used face.
Adding the original 42-row Gram identity for \(H_2\) and the signature96
capacity produces the new 143-row combination. The final verifier does
not rely on that derivation: it recomputes the saved combination from the
original Gram rows and checks every coefficient before applying the
original 99-zero certificate.

The 99 prior zero proofs remain inherited premises. This package does not
rerun them, and it does not exclude the whole case4 incidence domain.

## Files and bindings

The standalone source is
`experiments/workspace/rook_case4_face99_zero663_gram_capacity.py`
(SHA256 `a6ac979c47622ba9773f47195da5b113eb7db3517e355ae2b246b825569a7991`).
The full coefficient vector and all 143 multipliers are in
`rook-case4-face99-zero663-gram-capacity-certificate.json`
(SHA256 `312d96f363eaad62c31ab685c50ec73f019a9d0742ddcbed9b1193a236113802`).
Separate preparation and replay both pass. The replay imports no model
builder and performs no numerical optimization.

