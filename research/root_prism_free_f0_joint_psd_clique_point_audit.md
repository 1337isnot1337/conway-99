# Exact audit of the time-limited joint PSD/clique proposal

The saved vector fails the stored linear model by large residuals. This conclusion comes from exact evaluation of its binary64 values, not from the solver's false validity flag. The bounded query remains UNKNOWN; the audit does not show that the model is infeasible.

The standalone audit reads the frozen 15,200 column hex values and converts them exactly to one dyadic vector with denominator \(2^{65}\). It then evaluates every one of the 28,043 mathematical rows and every unit-box bound using integers. It records every signed residual numerator. For size comparisons it also divides each residual by the row's stored positive numerical scale.

| Check | Exact violations | Largest absolute violation |
|---|---:|---:|
| 15,200 unit-box bounds | 0 | 0 |
| 6,135 equalities | 6,135 | 4.633202964224393 |
| 21,908 inequalities | 1,110 | 570,950.6910061631 before row scaling |
| Inequality violations after stored row scaling | 1,110 | 0.1716892448443582 |

All 7,245 violated rows have scale-normalized violation greater than \(10^{-8}\). Every violated inequality exceeds \(10^{-6}\) after scaling. Of the equalities, 6,134 exceed \(10^{-6}\); the remaining equality still exceeds \(10^{-8}\). These thresholds describe magnitudes only. Exact acceptance requires zero equality residual and nonpositive inequality residual, without a tolerance.

## Where the violations occur

All equality families fail:

| Equality family | Rows | Largest scale-normalized residual |
|---|---:|---:|
| Original selector Gram | 18 | 0.920784451548247 |
| Mixed incidence/edge | 667 | 0.9719445068095959 |
| Population | 1 | 0.820201566396084 |
| Selector RLT | 5,287 | 4.633202964224393 |
| Proved edge-zero equations | 162 | 0.04207030146991165 |

The largest equality defect is combined row 3,645, a 38-term RLT row with right-hand side zero. Its exact residual is

\[
\frac{2670859666331245003}{576460752303423488}.
\]

The largest scale-normalized inequality defect is combined row 27,777, one of the newly appended PSD inequalities. Its raw residual is

\[
\frac{6334215119704666127}{36028797018963968},
\]

and its numerical row scale is 1,024. The old augmented-selector PSD row 21,881 has the largest unscaled inequality defect, about 570,950.69, but its scale is \(2^{25}\). Raw coefficient magnitude therefore should not be used alone to compare these two violations.

The 1,110 violated inequalities include 625 edge-to-second-moment links, 378 two-edge prism inequalities, 35 core-pair clique inequalities, 30 upper activations, 27 one-edge prism inequalities, 11 stored PSD directions and four Fréchet bounds. No new inequality is needed to reject this vector.

All 162 coordinates constrained by the proved edge-zero equalities are nonzero in the saved vector. A separate direct `Fraction` calculation checked the first such equation and the two largest-residual rows against the audit's common-denominator ledger. No numerical zero was substituted during the audit.

## The native row values do not certify this vector

The audit also compares each stored native row value with the exact scaled matrix product at the saved column vector. All 28,043 comparisons differ exactly; the largest difference is about 146.5513 at combined row 6,148. Small exact differences could arise from rounding, but this maximum is large. The native row and column arrays cannot be treated as a consistent feasible solution of the stored model.

The IPM iteration log reports residuals for its numerical solve. Those residuals do not establish a bound on the original-model residuals of this invalid returned vector. The audit does not infer the internal cause of the mismatch. It uses only the saved values, the bound exact matrix, and the bound row scales.

## Consequence for the next preparation

A PSD direction scan at this vector could still produce mathematically valid inequalities: validity of an integer quadratic direction does not depend on proposal feasibility. It is not the useful next step here, because the vector already violates thousands of stored rows and all 162 proved-zero equations.

The next authorized preparation is an equivalent smaller model. It will eliminate exactly the 162 edge coordinates proved zero independently of this point. It will retain explicit old/new column and row maps, certify each duplicate or box-tautological row removal, and keep provenance for every original obligation and all 92 held PSD directions. Eliminating those columns does not justify eliminating their corresponding selector-pair moments. No zero from the numerical vector is a premise.

This reduction may reduce native work, but no speed improvement is established. No new optimizer call or eigenscan belongs to this audit package.

## Reproducible records

The source is `root_prism_free_f0_joint_psd_clique_point_audit.py`, SHA256 `eebaa32087136f601fa9996943f1e2f958129dc2fa1f7c056a66aef854f03036`.

The complete compressed audit is `f0-joint-psd-clique-query-run01-point-audit.json.gz`, SHA256 `0d159468ea5d14557d97a78064241ca2cb935524c9ba95729ddc25d66bedbc91`. It contains the exact dyadic vector, all 28,043 signed row residuals, all singleton-zero checks, family summaries and largest-row details.

The fresh cold audit reproduced that complete record. Its report is `f0-joint-psd-clique-query-run01-point-audit-cold-replay.json`, SHA256 `2084ebda24e2dd18ed3f6ccfe9675575d76882d4eb356caaacb16b2153e2feb0`. Both audit modes use only standard-library exact arithmetic and perform no optimizer or spectral call.
