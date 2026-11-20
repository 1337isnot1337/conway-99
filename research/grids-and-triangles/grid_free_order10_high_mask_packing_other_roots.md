# Complete packing scope for the other six-root types

The point-independent scope covers all 61 six-vertex catalogue roots other
than the empty root. It uses each root's actual automorphism group, not
the full \(S_6\) unless that group preserves the root. No count point,
product tensor, optimizer, or outside graph is used.

The complete structural domains contain 175,383 atoms in total. Root-label
quotients have 19,555 atom columns and 11,502 supported monomial rows in
total, with 408,833 nonzero coefficients.

| Root type | Root automorphism order | Structural atoms | Quotient rows | Quotient columns | Nonzeros |
|---:|---:|---:|---:|---:|---:|
| 39 | 48 | 54,024 | 438 | 1,415 | 38,447 |
| 40 | 12 | 21,119 | 836 | 1,970 | 52,241 |
| 44 | 16 | 31,545 | 830 | 2,256 | 62,197 |
| 45 | 4 | 8,646 | 1,257 | 2,287 | 52,597 |
| 46 | 4 | 11,879 | 1,623 | 3,115 | 75,997 |

Root 46 has the largest quotient row and column counts. The complete
per-root table, including constant-only domains, is in the saved result.

## Coverage and quotient construction

For each root, the source tests all 720 permutations of its six vertices
against the literal adjacency matrix. The resulting group order must also
match the small catalogue. A deterministic generator set is checked by
full group closure. There are 43,920 literal permutation tests in total.

Each generator acts on the universal 42-mask index and preserves the
root's allowed masks and complete structural atom list. Breadth-first
search gives orbit labels, representatives, and explicit predecessor
transports. The source checks 536,662 atom-generator images.

The packing domain is downward closed: deleting a selected class preserves
mask membership, pair-capacity inequalities, and every outside-pair
intersection condition. The source also checks every one-class deletion
directly, giving 823,093 checks.

Consequently, a supported monomial of degree at most four is precisely an
atom of size at most four. Its automorphism orbit is the corresponding atom
orbit. This gives all supported monomial rows without selecting them from
a count point. The 61 roots have 650,232 formal monomials through degree
four, of which 74,659 are structurally supported.

For each representative atom, the source enumerates every subset of size
at most four and counts its monomial orbit. These counts form the exact
integer quotient matrix. Choosing the atom orbit corresponding to each
monomial orbit gives a matrix triangular by population, with identity
diagonal blocks. This proves full row rank for every quotient.

The integer divisibility required by the uniform-lift incidence identity
is checked for every matrix entry. This scope does not independently
recount the fixed-monomial side of that identity, evaluate moment
constancy, or perform a feasibility query. Those are separate gates for
each future single-root model.

## Saved result

The preparation completed in 7.65 seconds with peak RSS 355,996 KiB.
It retained every complete domain and every quotient array.

Source: experiments/workspace/grid_free_order10_high_mask_packing_root_scope.py,
SHA256
9b0dd3a021cdb40e1c9ad0c8fe8f24144ad66b848d247fb134225f78fcdde5ac.

Result: experiments/logs/moments-and-counts/order10-high-mask-packing-other-roots-scope01.json,
SHA256
fd577aca265beb46bee2206ea8d474edcd048d6d0bdc12f4d4d7d4709e607142.

Arrays: experiments/logs/moments-and-counts/order10-high-mask-packing-other-roots-scope01-arrays.npz,
SHA256
4af4af187681c33af2ce0d64fc1e7c3e7afb30e37eec181c741776883d602533.

The empty-root rational witness is unchanged. No feasibility statement is
made for any of these 61 other-root models.
