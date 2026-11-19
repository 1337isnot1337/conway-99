# Norm-six integer Gram restriction: local result

The complete three-case experiment found 38 local count compositions that
pass the declared profile, domain, activation, and one-dimensional product
checks, and also pass PSD and divisibility by three, but fail the exact
integer Gram square condition. This is a restriction beyond those declared
local checks. It does not prove independence from the full F0 count model.

All 6,480 prepared compositions were checked once. The scan took 0.0205
seconds. Its separate complete replay passed in 0.0362 seconds. No full
count candidate, optimizer, literal-selector search, or new subset census
was used.

## Complete outcomes

| Case | Unrestricted compositions | Fail domains, zeros, or activation | Pass declared coarse checks | Fail PSD | Additional integer-square failures | Pass square test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 2,160 | 2,160 | 0 | 0 | 0 | 0 |
| 1 | 2,160 | 1,980 | 180 | 36 | 30 | 114 |
| 2 | 2,160 | 2,088 | 72 | 18 | 8 | 46 |
| Total | 6,480 | 6,228 | 252 | 54 | 38 | 160 |

Every coarse-passing determinant is divisible by three. Of the 198 cases
that also pass PSD, exactly 38 have Gram matrix

\[
B=\begin{pmatrix}6&0\\0&6\end{pmatrix}.
\]

Its determinant is 36. Two integer representation vectors would require
\(\det(B)=3d^2\) for an integer \(d\), hence \(d^2=12\), which is
impossible.

Passing the square test is not a literal realization. The local inverse
profiles can impose further cross correlations, and the rest of the native
count model is outside this experiment.

## One explicit rejected local composition

In case 1, selector orbits 2 and 3 use frozen tuple indices 23 and 24.
Both populations are three. Their signed triples are respectively
\((-1,-1,-1)\) and \((-1,1,1)\).

The nonzero specified within-orbit count coordinates are:

| Selector orbit | Native N coordinate | Within-orbit native Z coordinates equal to one |
| --- | --- | --- |
| 2 | \(C_2=3\) | \(C_{6602},C_{6663},C_{6718}\) |
| 3 | \(C_3=3\) | \(C_{7036},C_{7104},C_{7155}\) |

The other within-orbit coordinates in these two profiles are zero. The exact
prepared diagonal forms give \(B_{22}=B_{33}=6\).

Set the nonzero cross coordinates to

\[
C_{6666}=2,\qquad C_{6717}=3,\qquad
C_{6765}=2,\qquad C_{6768}=2,
\]

and set the other eight original cross coordinates to zero. All twelve
values lie in their retained exact domains and satisfy the regular-pair
activation bound of three. The four product checks are exactly
\((9,1,-1,-1)\), as required by these profiles. Their coset masses are
\((2,3,2,2)\).

The cross Gram form evaluates to zero, so the determinant-square obstruction
above applies. This is an explicitly checked local composition. It is not
an 18,444-coordinate count point and is not claimed to satisfy the other
native constraints.

## Compact conditional form

Using the four coefficient-two original pair orbits and the previously
proved zeros 942 and 946, the cross Gram entry is

\[
B_{23}=3(C_{6717}+C_{6721}-3)
\]

when \(N_2=N_3=3\). Consequently, for any actual selector incidence with
both prepared diagonal norms equal to six,

\[
C_{6717}+C_{6721}\in\{1,2,4,5\}.
\]

All 38 additional rejections have sum three. This conditional nonlinear
restriction has not been added to the frozen native target.

## Scope and proof chain

The six exact Gram-entry forms come from the previously checked literal
integer representation columns. The local profiles and all their preimages
come from the frozen inverse tables. The new preparation retains all twelve
cross-coordinate domains and all prior zeros, and verifies the four
character coefficients on every literal cross pair. The coordinator reviewed
that source and preparation before the scan.

The replay exhausts the same finite scope and checks all recorded outcome
counts, stream hashes, and exact examples. It does not independently rebuild
the earlier representation coefficients or inverse tables. Those remain
separate hash-bound premises in the preparation and its source review.

Frozen records:

- Source `root_prism_free_f0_two_dimensional_profile_pairs.py`, SHA-256
  `2b524a25818e57e97836fc5567657da862e939543f2d050268ef98590cb86899`.
- Preparation `f0-two-dimensional-norm-six-pairs-preparation01.json`,
  SHA-256 `3c7a7b045ac8580355bf33f73963cbdcac295349820d81baf603604c32d7822f`.
- Scan `f0-two-dimensional-norm-six-pairs-scan01.json`, SHA-256
  `b5e41e617831f34d63949565822718085c2b256a3e9d9678ae56abf69df5f4f2`.
- Cold replay `f0-two-dimensional-norm-six-pairs-scan01-cold.json`,
  SHA-256 `5c0b8584edbbf868424d8f6a261d741830176003f9e9046473a377931a3b85ab`.
- Coordinator source gate
  `f0-two-dimensional-norm-six-pairs-root-source-review.json`, SHA-256
  `d7c57275a5fb39f5cd41a6cf65406b46190aee9aab7cefaebc1af98fc816d80e`.

The JSON files and logs are under `experiments/logs/root-prism-free/`.
The source is under `experiments/workspace/`. The earlier group/Gram scope
and the literal-lift intake remain separate immutable packages.
