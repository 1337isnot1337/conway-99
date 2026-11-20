# A third parity cover for case4

The fixed family of 286 saved mod2 rows and their 40,755 unordered pairwise
XORs was evaluated at the new exact 112-zero-face point. The complete scan
found one violated inequality. A separate exact replay checked all 41,041
evaluations and its original-row derivation.

The inequality is

\[
H_3:=\sum_{a\in S}x_a\geq1,
\]

where the complete 27-column support is

\[
\begin{split}
S=\{&23,45,123,260,339,401,402,405,539,\\
&590,591,592,593,594,595,764,780,781,782,\\
&800,801,802,1175,1176,1177,1180,1183\}.
\end{split}
\]

At the accepted exact point, its numerator is 121,793,213 at denominator
145,446,009. The violated margin is therefore 23,652,796 at that same
denominator. This separates that real point from the necessary Boolean
conditions; it does not exclude all case4 incidences.

## Five original equations

The certificate uses these original Gram rows, each with multiplier one:

| Original row | Core pair | Quota |
| ---: | --- | ---: |
| 124 | (3, 25) | 1 |
| 214 | (6, 25) | 1 |
| 320 | (10, 25) | 1 |
| 344 | (11, 25) | 1 |
| 582 | (25, 32) | 1 |

Their sum has right-hand side five. After deleting the already proved
zero coordinates, its odd coefficients occur exactly on \(S\). Thus
\(H_3\) is odd for every integral incidence. Nonnegativity gives
\(H_3\geq1\). The full coefficient vector on all 1,214 columns is saved;
the proof is not inferred from a modular rank report.

The thirteen odd-coefficient columns deleted in this argument are

\[
\{396,397,400,404,779,799,1065,1125,1126,1127,1128,1129,1130\}.
\]

All are among the earlier 111 proved zeros. The later zero at column663
is not needed for this parity inequality.

## Sparse equivalent and upper bound

Let

\[
U=x_{401}+x_{402}+x_{405}+\sum_{a=590}^{595}x_a.
\]

The direct original-coordinate expansion verifies

\[
H_3=1+2(U-x_{803})
\]

on the proved face. This identity uses Gram rows 582, 214 and 344 together
with \(H_1=H_2=1\). Every discrepancy before substituting zeros is recorded
explicitly in the certificate.

A second exact expansion, from Gram row344 plus \(H_2-H_1\), gives

\[
U+x_{399}+x_{403}+x_{406}
 +\sum_{a=730}^{733}x_a+\sum_{a=761}^{765}x_a=1.
\]

It follows that \(U\leq1\), and hence \(H_3\leq3\). The new cover is
therefore equivalent, under the existing equations, to the ten-term row

\[
x_{803}-x_{401}-x_{402}-x_{405}-\sum_{a=590}^{595}x_a\leq0.
\]

This sparse row is violated by 11,826,398 at denominator 145,446,009.
Integral \(H_3\) can take the values one or three under these bounds.
This package derives no additional coordinate-zero certificate.

## Coverage and scope

The projected parity family still has 41,041 distinct nonempty equations,
with supports of size3 through447. Its exact census covers 7,236,294
coordinate visits. One old pivot column is among the new zeros, so the
preparation verifies distinctness by a complete set comparison rather than
reusing the old pivot-visibility argument.

The scan took 15.99 seconds and its separate replay took 15.96 seconds.
No optimizer or larger XOR family was used. All earlier results and the
accepted exact real point remain unchanged.

The standalone direct proof source is
`rook_case4_face112_third_parity_cover.py`, SHA256
`9da8c7edc60429b6a7bee6cd15da447e08a6ae1656a4be5b77b1dd2f5ba5bdb3`.
Its certificate has SHA256
`4ab891e2d809847804b4b3d3626f9c4e498d32788d90ddb865da2ed4c98b6ef7`.
Preparation and fresh replay both expand all original coefficients.
