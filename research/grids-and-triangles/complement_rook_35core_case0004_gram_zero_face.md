# Case4: 46 zeros from three Gram equations

This certificate forces 46 of the 1,214 optional attachment columns to zero.
Forty-four are additional to the 14 earlier zeros. It applies to nonnegative
real incidence weights, so it uses no Boolean assumption, coordinate cover,
exterior-row cut, or failed-literal premise. It does not exclude the entire
case4 incidence system.

All indices below are zero based. Let `h_a` be attachment column `a` in the
complete frozen 35-core domain, and let

\[
S_{ij}=\{a:h_a(i)=h_a(j)=1\}.
\]

The Gram equations are

\[
\sum_{a\in S_{ij}}x_a=G_{ij},\qquad
G=12I+2J-B^2-B,\qquad x_a\ge0,
\]

where `B` is the fixed 35-core adjacency matrix.

Three rows have the following exact values:

| Core pair | Gram quota | Number of candidate columns |
| --- | ---: | ---: |
| `(3,27)` | 1 | 8 |
| `(4,27)` | 1 | 50 |
| `(17,27)` | 2 | 12 |

The complete column list verifies

\[
S_{3,27}\cap S_{4,27}=\varnothing,
\qquad S_{17,27}\subseteq S_{3,27}\cup S_{4,27}.
\]

Subtracting the third Gram equation from the first two gives

\[
\sum_{a\in (S_{3,27}\cup S_{4,27})\setminus S_{17,27}}x_a
=1+1-2=0.
\]

Every summand is nonnegative. Every column in that difference is therefore
absent. The complete difference has 46 columns:

```text
235, 241, 252, 258, 263, 302, 309, 315, 329, 335,
342, 348, 352, 354, 356, 359, 363, 367, 368, 371,
375, 385, 387, 388, 392, 396, 397, 398, 400, 404,
408, 410, 413, 415, 417, 420, 424, 428, 430, 435,
437, 442, 457, 459, 461, 465
```

Only 352 and 354 were in the previous 14-column zero list. Combining the two
separately proved lists gives 58 absent columns. The older zeros are not used
to prove this row identity.

Column 359 has support `{4,11,19,27,33}`. The failed-literal trace first exposed
its impossibility through a longer sequence of quota propagation. The identity
above proves the same exclusion and the other 45 directly.

## Verification

`complement_rook_35core_case0004_gram_zero_face.py` uses only the standard
library. It binds the complete frozen column domain and original Gram inventory,
checks the 35-core adjacency, derives the three quotas directly from `B`, and
computes the signed coefficient at every one of the 1,214 columns. All
coefficients are zero or one; the right-hand side is zero. The certificate saves
the complete supports, coefficient vector, and every forced column mask.

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_gram_zero_face.py \
  --replay experiments/logs/grids-and-triangles/complement-rook-35core-case0004-gram-zero-face.json
```

The frozen domain's earlier completeness proof remains an input. This small
verifier does not repeat the attachment census or run an optimizer.
