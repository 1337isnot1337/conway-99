# Four-variable Boolean atoms over six roots

This family tests necessary nonnegative atom counts for every set of at
most four high-mask classes over a six-vertex root. It uses the complete
frozen six-root, two-free-vertex product cache. It does not construct new
products or assume an automorphism of the hypothetical graph.

## The necessary inequality

Fix a labelled embedding of a six-vertex root. Let `X_h` count outside
vertices with exactly the root-neighbor mask `h`. When `|h|>=3`, `X_h`
is zero or one: two vertices in that class would have at least three
common neighbors. The target graph permits at most two.

For a set `Q` of at most four distinct high masks and a subset `P` of
`Q`, the product

```
product(h in P) X_h * product(h in Q\P) (1-X_h)
```

is zero or one. Its sum over all labelled root embeddings is nonnegative.
Write `m(T)` for the sum of `product(h in T) X_h`. The atom inequality is

```
sum(T subset Q\P) (-1)^|T| m(P union T) >= 0.
```

All sixteen inequalities are tested for each four-element set. If a root
has fewer than four high masks, its entire smaller marginal is tested.
Every smaller marginal for the other roots is a sum of tested atoms.
Thus the family covers all Boolean marginals on at most four high masks.

These inequalities apply to every target graph. The count point selected
for testing is the existing integral point on the prism-zero, `x521=0`
face. The face assumptions are not used to omit any root or flag.

## Reading the monomials from the frozen cache

Let `F_ab^e` be the two-free-vertex flag with distinct high root masks
`a,b` and mutual edge value `e`. Each class has at most one vertex, so

```
X_a X_b = F_ab^0 + F_ab^1.
```

A cap-incompatible edge choice contributes zero. The constant flag is
denoted by `1`. The cached moment entries supply the monomials as follows.

| Monomial | Cached entries |
|---|---|
| `m(empty)` | `<1,1>` |
| `m(a)` | `<X_a,1>` |
| `m(a,b)` | `sum_e <F_ab^e,1>` |
| `m(a,b,c)` | `sum_e <F_ab^e,X_c>` |
| `m(a,b,c,d)` | `sum_e,f <F_ab^e,F_cd^f>` |

The masks in each monomial are distinct. Thus a free vertex cannot
coincide with one in a different factor. The fixed masks determine its
label, and neither a factorial nor an automorphism divisor belongs in
these formulas. The cache uses labelled induced embeddings. Conversion
to induced-copy counts multiplies each coefficient by the corresponding
graph automorphism count.

The larger cache also contains flags with only two root neighbors that
can take value two. Those flags and their products remain in the cache.
The Boolean assertion here applies only to the selected high-mask
classes; it does not impose binary diagonals on other flags.

## Complete prepared coverage

The source reconstructs every allowed high mask by direct common-neighbor
cap checks. It checks both mutual-edge choices for every pair and binds
each monomial to a deterministic list of existing product rows.

| Quantity | Count |
|---|---:|
| Six-vertex root types | 62 |
| High-mask classes | 829 |
| Distinct-mask pairs | 9,118 |
| Distinct-mask triples | 85,492 |
| Distinct-mask quadruples | 679,045 |
| Tested maximal marginals, including smaller roots | 679,054 |
| Atom inequalities | 10,864,739 |
| Product-row references across all degree-zero to degree-four monomials | 327,655 |
| Sparse coefficient reads in those references | 229,779 |

Many monomials are identically zero because a pair is incompatible.
Those monomials remain in the domain. The complete cache retains 14,348
flags and 3,913,479 lower-triangle product rows.

Preparation took 3.909 seconds. A separate cold regeneration reproduced
the full domain record. Small controls check all 31 Boolean assignments
of orders zero through four and five literal cap-compatible hosts.

## Exact scan arithmetic

The scanner uses integer matrix contractions and a superset Möbius
transform. Before each contraction, Python integers bound the coefficient
sums and every potentially nonzero embedding contribution. Before the
transform, a stronger bound covers its subtractions and atom row sums.
An exceeded bound stops the scan; floating-point arithmetic is not a
fallback.

Every tested marginal must sum back to the exact labelled root count.
A negative atom is expanded into an explicit signed combination of
cached product rows and then into a primitive induced-count inequality.
That inequality remains ineligible for an optimizer until a separate
literal construction reproduces its supported products.

The completed scan calls neither an eigensystem nor an optimizer. It
checks all 10,864,739 atoms in 8.420 seconds and finds no negative atom.
Exactly 4,161,868 atoms are zero; the other 6,702,871 are positive.
All 62 roots finish, with no timeout or error. Peak process memory is
265,856 KiB. The whole run, including input preparation, takes 9.220 seconds.

This is an exact nonnegativity certificate for the specified finite
atom family. It does not certify a joint distribution over all high
masks or the existence of a graph. In particular, it cannot decide a
constraint that couples five or more distinct high-mask classes.

## Files and replay

- Domain source: `experiments/workspace/grid_free_order10_four_boolean_domains.py`.
- Domain certificate: `experiments/logs/moments-and-counts/order10-four-boolean-domains.json.gz`.
- Cold replay: `experiments/logs/moments-and-counts/order10-four-boolean-domains-replay.json`.
- Scan source: `experiments/workspace/grid_free_order10_four_boolean_scan.py`.
- Scan preparation: `experiments/logs/moments-and-counts/order10-four-boolean-scan01-preparation.json`.
- Exact scan result: `experiments/logs/moments-and-counts/order10-four-boolean-scan01.json`.
- Independent source/arithmetic review: `experiments/logs/moments-and-counts/order10-four-boolean-independent-review.json`.

The frozen domain SHA-256 is
`5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35`.
The count-point SHA-256 is
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
The complete result SHA-256 is
`ea11c72c812f8f135c43b07df5a0f8d72672a3f47bd8afcd371cd5199265aa73`.

```sh
.venv/bin/python experiments/workspace/grid_free_order10_four_boolean_domains.py \
  --replay experiments/logs/moments-and-counts/order10-four-boolean-domains.json.gz \
  --output /tmp/order10-four-boolean-replay.json
```
