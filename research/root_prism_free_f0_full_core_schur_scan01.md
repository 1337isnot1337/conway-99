# First full21-core Schur scan

The single authorized scan finished in 40.923 seconds and retained 22 exact
necessary inequalities. A separate cold replay checked all 68 attempted
integer vectors and every accepted full480 quadratic and quotient identity.
No linear optimizer was called.

The [full-core preparation](root_prism_free_f0_full_core_schur_cuts.md) states the
conditional scope: component zero of a globally prism-free and $F$-free
split18+18 edge shell, with the second component and alignment free. The scan
used the original 480 selectors and 68,394 eligible edges. It did not add any
edge-zero equalities from the separate pair-minor or visible-motif work.

| Family | Retained cuts | Directions visited | Terminal coverage |
|---|---:|---:|---|
| plus | 16 | 4 | Cut limit reached during the fourth direction. |
| minus | 6 | 8 | All eight directions and all six scales checked. |

There was one full480 eigendecomposition per family. The 60-second limit was
not exceeded. The plus cut cap did not skip the minus family.

## Exact scope of the result

The numerical input remains the previously saved proposal with SHA256
`ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf`.
Its exact feasibility is unresolved. Integer vectors extracted from its
eigensystems produce valid cuts because the full21-core Schur forms are
necessary for an actual graph, not because the proposal is feasible.

All six minus-family rows are retained with a possible-redundancy flag. Their
numerical proposing negative modes were near rounding scale. Both full-core
matrices have exact null directions under the lifted linear identities, so
small equality defects can produce such modes. The stored negative quadratic
evaluations are exact at the binary64 point viewed as rational coordinates;
they do not establish that these six rows remove any previously feasible point.

The plus rows also carry no claim of proved strict improvement of the linear
feasible set. The package proves validity of the inequalities and their exact
violation by the saved proposal. It proves neither feasibility nor exclusion
of the component case and does not resolve Conway99.

## Coefficients and verification

The 22 primitive rows contain 285,594 coefficient terms. The maximum coefficient
length is 31 bits. After the recorded positive dyadic row scaling, the smallest
nonzero absolute coefficient is $9/1073741824$. All coefficient conversions are
exact binary rationals; this is not a conditioning guarantee.

Cold replay reconstructs both complete kernels from the exact old18-core
inverse and root-triangle residual blocks. It checks all 114,960 pair positions,
all 68,394 edge positions, the 389 certified zero pair substitutions, all cut
gcd normalizations, every accepted gap, and deduplication.

The supplemental full source/mathematics review is
`f0-full-core-schur-peer-source-review.json`, SHA256
`876de39bdcaebad4d1c3c5188de6c8547ce6790796d3903b3ca4d4039fc0dc9c`.
It did not repeat the scan or its arithmetic.

| Artifact in `experiments/logs/root-prism-free/` | SHA256 |
|---|---|
| `f0-full-core-schur-cuts-scan01.json.gz` | `d28ee0220975500373085c5913071490f1eb4b31a351aa108501cc6bd5c70a54` |
| Uncompressed scan bytes | `388597c739dd7dd3889e8f0ecd118ba83fb78e631d014045ac14ae323b290c00` |
| `f0-full-core-schur-cuts-scan01-cold-replay.json` | `150f2eae6abb9d1f8ccebd2fe47f7823d708829f08119906c053a10323297c51` |
| `f0-full-core-schur-cuts-scan01-summary.json` | `3328472000f0404fce598800d6358feabd915febf18d000efcb4401889b69f70` |

The compressed record contains every integer cut, exact evaluation, numerical
direction, and attempt. Its preparation remains unchanged. No subsequent
linear query is included in this package.
