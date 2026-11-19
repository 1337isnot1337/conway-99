# Two integer cover inequalities for case 4

The complete fixed scan of 41,041 parity equations found two inequalities
violated by the saved exact interior point on the 99-zero face. Both are
42-column covers. They strengthen the real selector relaxation. They do not
exclude case 4 or establish the existence of a binary incidence.

The scan considered all 286 rows of the published reduced mod-2 basis and
all 40,755 unordered XORs of two distinct basis rows. Its preparation proves
that these 41,041 equations have distinct nonempty supports by their pivot
coordinates. No larger combinations, new assumptions, optimizer calls, or
symmetry restrictions were used.

The exact scan completed in 9.374 seconds. A separate cold replay completed
in 9.166 seconds, checking every distance and rebuilding each emitted
equation from the original 1,214-coordinate native rows. The transcript
contains 1,021,683 bytes. The terminal scan record retains its original
"cold replay pending" wording; the separate replay file records the completed
verification.

## The covers

Indices below are zero-based original attachment-column IDs. Let

```
H1 = [74,75,76,77,176,177,178,259,260,261,262,
      536,537,538,539,540,541,658,660,662,663,
      762,763,764,765,1125,1126,1127,1128,1129,1130,
      1174,1176,1177,1179,1180,1182,1183,1208,1210,1212,1213]

H2 = [74,75,76,77,176,177,178,536,537,538,539,540,541,
      590,591,592,593,594,595,658,660,662,663,730,731,732,733,
      762,763,764,765,1174,1176,1177,1179,1180,1182,1183,
      1208,1210,1212,1213]
```

Every nonnegative integer incidence satisfying the original Gram equations
and the 99 proved zero coordinates obeys

\[
\sum_{a\in H_1}x_a\geq1,\qquad
\sum_{a\in H_2}x_a\geq1.
\]

The saved exact real point has common denominator
\(D=1,661,041,997\). Its two cover sums and exact deficits are:

| Cover | Sum numerator | Deficit numerator |
| --- | ---: | ---: |
| \(H_1\) | 1,447,020,941 | 214,021,056 |
| \(H_2\) | 1,232,999,885 | 428,042,112 |

All entries in the table have denominator \(D\). The point still satisfies
the previously frozen real model; these are new integer consequences.

## Direct proof from original Gram equations

The direct verifier `rook_case4_face99_parity_covers.py` imports no modular
eliminator and does not repeat the scan. It rebuilds the 630 original Gram
supports from the 35 diagonal incidence rows, checks the saved point against
every Gram equation, and expands each displayed row sum on all 1,214 columns.

For the first cover, sum the following 33 original native Gram equations,
each with coefficient one:

```
[54,119,139,141,145,147,148,149,151,153,154,156,180,209,237,
 252,262,263,265,266,267,268,290,295,315,344,362,405,425,430,
 444,462,577]
```

Their right-hand sides sum to 45. After substituting the 99 previously
proved zeros, the exact coefficient identity is

\[
2q_1^{\mathsf T}x+\sum_{a\in H_1}x_a=45,
\]

where \(q_1\) is an explicitly saved nonnegative integer vector. The full
certificate records every original coefficient, every removed zero term,
and every coefficient of \(q_1\). Thus the cover sum is an odd nonnegative
integer and is at least one. Equivalently, integer rounding gives
\(q_1^{\mathsf T}x\leq22\).

For the second cover, add original Gram rows 124 and 320 to those same 33
equations. These are the core-pair quotas \((3,25)\) and \((10,25)\), each
equal to one. The resulting identity is

\[
2q_2^{\mathsf T}x+\sum_{a\in H_2}x_a=47.
\]

It gives the second cover, or equivalently
\(q_2^{\mathsf T}x\leq23\). No upper bound \(x_a\leq1\) is needed for
these two proofs: nonnegative integral coordinates suffice. All 99 zero
premises come from the frozen seed certificate; no branch values or new
zero assumptions enter either identity.

The independent direct expansion and its separate replay both passed.
Their certificate is
`rook-case4-face99-parity-cover-certificate.json`. The other saved scan
records retain the mod-2 combination and exact nearest-forbidden-vertex
proof, providing a separate route to the same inequalities.

## Replay

Run from the repository root with its existing Python environment:

```sh
python experiments/workspace/rook_case4_face99_parity_separation.py replay \
  --preparation experiments/logs/grids-and-triangles/rook-case4-face99-parity-preparation01 \
  --directory experiments/logs/grids-and-triangles/rook-case4-face99-parity-run01 \
  --output /tmp/rook-case4-parity-cold.json

python experiments/workspace/rook_case4_face99_parity_covers.py replay \
  --certificate experiments/logs/grids-and-triangles/rook-case4-face99-parity-cover-certificate.json \
  --output /tmp/rook-case4-parity-covers-cold.json
```

Output paths must be new. These commands perform exact verification only.
No later LP preparation or query is part of this frozen package.
