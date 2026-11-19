# F0: complete Fourier coordinates and exact literal cuts

This checkpoint prepares the complete finite Fourier specification and an
independently checked literal-cut layer. It does not establish a feasible
count vector, a literal exterior incidence, or a 99-vertex graph. Native
integration and a new production query are separate stages.

## Complete Fourier specification

The construction uses the previously proved nonabelian pair factorization.
It retains all parent coordinates and adds 320 Fourier coordinates and
12,992 exact scalar products. The two complete matrix Gram blocks contribute
6,496 linear links. Of the 172 original selector equations, 151 have nonempty
Fourier expansions; the other 21 are literal zero equalities.

The 42 local tables contain all 64,144 saved local masks, including their new
coordinates. Their projections recover all 19,331 old local profiles.
No orbit receives an independent choice of phase or sign. The two existing
joint tables and all 117 external pool constraints remain part of the target.

The specification preparation and its cold replay completed in separate
owned jobs. They check 5,616 unit-vector inverse identities, 11,232 forward
equivariance identities, and 769,728 saved-mask action memberships. Neither
stage constructs an optimizer. The complete specification has 31,756
variables, 54,037 target constraints and 53,920 initial constraints.

The archived specification is
`experiments/logs/root-prism-free/f0-full-fourier-specification-ci01/specification.json.gz`,
SHA-256 `929703b3a685f95fb28bc6553aef02d5c7f6c879628154c62b8ecfa7d69ba8d5`.
The preparation and cold reports bind its complete decompressed bytes.

## Literal selector layer

All 480 literal selectors receive Boolean variables. Each is linked directly
to its Fourier inverse by an integer equation with denominator 12. These
variables retain the original selector indices through the offset 31,756.

All 4,416 authoritative literal inequalities are imported from the original
Boolean validation model. They contain 442,308 nonzero terms. A direct native
inequality suffices for 4,404 rows. The remaining 12 rows have coefficients
too large for direct native arithmetic. Each uses three base-2^30 limbs,
three slack digits and two signed carries. Weighted contraction of the
three equalities recovers the original inequality exactly. Every satisfying
Boolean input has the corresponding slack-and-carry witness.

The twelve large rows have original IDs 4,164 through 4,175. An initial
source incorrectly asserted that they were the final twelve rows. Its first
preparation stopped at that assertion before creating an output directory.
The failed source, unrun checker, original source review and failure record
are retained. The corrected sources change only the row-position assertions
and the checker's producer hash. The independent replay then passes against
the complete authoritative archive.

The replay checks every inverse link, every original and shifted row hash,
all 4,404 direct inequalities and every coefficient contraction in the 12
radix encodings. It also checks fresh variable allocation, exact integer
activity bounds and the domain budget of the complete combined target.
Synthetic binary inputs exercise the actual large-row auxiliary witnesses;
these are controls, not production candidates.

| Quantity | Added by literal layer | Combined target |
| --- | ---: | ---: |
| Variables | 540 | 32,296 |
| Linear constraints | 4,920 | 42,633 |
| Exact product constraints | 0 | 16,280 |
| Table constraints | 0 | 44 |
| All target constraints | 4,920 | 58,957 |
| Initial constraints | 4,920 | 58,840 |
| Deferred pool constraints | 0 | 117 |

The layer archive is
`experiments/logs/root-prism-free/f0-literal-cut-native-layer01/layer.json.gz`,
SHA-256 `dcb44159712f9c9a4f61cc61950c23d62b804a0d57709ca43afb33e3711d2b33`.
The producer completed in 13.338 seconds. The independent Node replay
completed in 5.657 seconds and has SHA-256
`7bed3fffebe2bf026eac13961bbee1c2ba25ac04913a11b4b3f9f7dc8d6fa44b`.

## Remaining acceptance conditions

The native adapter must copy this exact layer, replace the 42 local tables,
and append the complete Fourier specification. Reversing those changes must
recover both complete parent protobuf hashes. Public native construction
must validate and export byte-identical initial model data.

A native candidate must subsequently satisfy the full target, including
the deferred pool, the original parent acceptance checks, and the exact
literal decoder. Even a passing candidate does not realize the exterior
edges. This entire F0 branch is conditional on the specified prism-free
component; it does not cover every hypothetical Conway-99 graph.
