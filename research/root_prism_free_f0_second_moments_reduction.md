# Exact reduction of the F0 second-moment linear model

The reduced model is equivalent to the frozen second-moment linear model. It introduces no new inequalities, fixed selectors, or graph assumptions. All 4,416 Boolean-normalized selector inequalities remain enforced. The reduction changes the representation after the first bounded query returned UNKNOWN.

| Quantity | Original | Reduced |
|---|---:|---:|
| Variables | 15,589 | 15,200 |
| Equalities | 7,165 | 5,973 |
| Inequalities | 46,122 | 15,719 |
| Total rows | 53,287 | 21,692 |
| Nonzero coefficients | 279,627 | 183,702 |

No optimizer was called to construct or verify this reduction. PSD conditions remain unenforced. The conditional scope remains component zero in a split \(18+18\) shell with global \(P=F=0\); the other component and its alignment are free.

## Exact selector-row rank

The 171 original Gram equations and the population equation form a \(172\times480\) coefficient matrix. Its exact rank is 132.

The certificate gives a linear expression for every original coefficient row in 132 original rows, and verifies the corresponding right side using the same coefficients. This gives rank at most 132 and proves that the selected equations imply all original equations. A \(132\times132\) integer minor has determinant \(3\) modulo the verified prime \(65,521\), so the rank is at least 132. No floating-point rank estimate is used.

Python-flint only proposes the row basis and relations. The replay uses the Python standard library, checks all \(172\times481\) coefficient and right-side identities, and recomputes the nonzero modular minor.

For each target selector \(a\), the same row relations apply after lifting:

\[
\sum_{b\in S_i} Z_{ab}=q_i x_a.
\]

In the invariant quotient, the 172 rows at each of 42 representative targets cover all 6,090 original quotient RLT rows. Lifting the chosen 132 equations at these representatives retains 5,360 distinct quotient rows. The other 730 rows have explicit exact dependencies on those retained rows. The preparation checks all 82,560 literal-to-quotient RLT scalings. It does not infer that each dropped row is redundant merely because a floating-point factorization omitted it.

## Certified zero substitution

The original model already contains 389 quotient zero-moment equations, representing 4,410 literal zero products. The reduced model substitutes zero for precisely these 389 variables. It fixes no selector variable.

After substitution, 462 original equality rows are identically zero. This count includes the 389 explicit zero equations and 73 retained-basis lifted equations. Every other retained row is divided only by an exact common factor; inequalities use a positive divisor.

## Moment upper bounds

There are 468 signatures \(b\) contained in at least one original quota-one Gram support \(S\). For every target \(a\), the lifted equality

\[
\sum_{c\in S}Z_{ac}=x_a
\]

and nonnegativity imply \(Z_{ab}\le x_a\). The diagonal case uses \(Z_{aa}=x_a\), which is already part of the model.

The certificate saves an original support and a literal lifted-row witness for each removed upper-bound row. The difference between that lifted equality and the upper bound has only nonnegative coefficients. The 12 signatures without such a support are retained explicitly in the coverage certificate.

This argument removes 17,909 quotient upper-bound rows. Another 740 inequalities are unit-box tautologies after the zero substitution. The reduced model keeps 477 moment upper bounds for which this procedure supplies no implication.

## Exterior-edge activation

Every original edge activation inequality follows through its pair moment:

\[
Y_{ab}\le Z_{ab}\le x_a,\qquad
Y_{ab}\le Z_{ab}\le x_b.
\]

All 5,805 quotient edge-to-moment inequalities are kept. For each of the 11,365 removed edge activation rows, the certificate identifies that retained row and the required moment upper bound. The latter is either retained, a certified quota-one implication, or a direct box tautology after substitution. The implication graph has no cycle.

## Fréchet lower bounds

For a pair in an original quota-one support, the selector equation gives \(x_a+x_b\le1\). The same inequality is explicitly available for each component motif pair. Thus

\[
x_a+x_b-Z_{ab}\le1
\]

follows from the selector inequality and \(Z_{ab}\ge0\). The certificate removes 389 quotient Fréchet rows on this basis, retaining 9,353 others. Each removed row has its original Gram or motif witness.

## Row accounting

| Disposition | Number |
|---|---:|
| Retained equality rows | 5,973 |
| Equality rows zero after substitution | 462 |
| Exact lifted equality dependencies | 730 |
| Retained inequality rows | 15,719 |
| Removed edge activation implications | 11,365 |
| Removed moment upper implications | 17,909 |
| Removed box tautologies | 740 |
| Removed Fréchet implications | 389 |

These dispositions cover all 53,287 original rows.

An original feasible point restricts to a reduced feasible point because every new row is a scaled original row after substitution of explicit zeros. Conversely, a reduced feasible point restores the zero variables, satisfies all retained original rows, and satisfies every omitted row by its saved exact witness. This proves equivalence over the real unit box, without an integrality assumption.

## Replay and acceptance

The rank source is root_prism_free_f0_second_moments_rank.py. Its certificate is f0-second-moments-selector-rank.json.gz. The pure-integer rank replay passed.

The reduction source is root_prism_free_f0_second_moments_reduced.py. Its model is f0-second-moments-reduced-model.json.gz. A fresh standard-library rebuild reproduced the complete model and all omission witnesses exactly in 6.447 seconds.

The inspector expands any proposed reduced rational point by inserting the 389 exact zeros, then calls the unchanged original full inspector. Final point acceptance still requires all 650,350 original literal rows and 183,834 bounds. A future numerical query must use a separately reviewed bounded driver. This preparation does not establish feasibility or infeasibility.

