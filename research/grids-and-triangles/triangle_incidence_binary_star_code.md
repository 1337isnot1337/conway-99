# Forced star words in the binary dual code

This extends the [binary incidence rank proof](triangle_incidence_binary_code.md).
The code C is the binary kernel of the point-triangle incidence transpose.
The span of the triangle words is C-perp.

At a point c, choose k of its seven triangles and sum their binary words.
Their other vertices are disjoint. The resulting support has weight 2k
when k is even, and weight 2k+1 when k is odd.

For even k>=2, the support induces k disjoint edges. Any one of these
edges determines c as its unique common neighbor. Thus the support
determines the chosen star and its triangles.

For odd k>=3, the support is k triangles with a common center. Its
center has induced degree 2k and every other vertex has induced degree
two. Thus its center and chosen triangles are again determined by the
support. The case k=1 counts each triangle at its three points, giving
231 words rather than 693.

Together with the previously proved disjoint-triangle-pair words, this
gives the following lower bounds on dual weight counts.

| Weight | Number of distinct forced words |
| --- | --- |
| 3 | 231 |
| 4 | 2,079 |
| 6 | 24,486 |
| 7 | 3,465 |
| 8 | 3,465 |
| 11 | 2,079 |
| 12 | 693 |
| 15 | 99 |

The count for weight six is from disjoint triangle pairs. Each other
entry is 99*binom(7,k), with the stated adjustment at weight three.
Words at different weights cannot coincide. The uniqueness arguments
establish the required distinctness within every row.

If these lower bounds are L_j, MacWilliams gives

    sum_w (L_j-K_j(w)) A_w <= binom(99,j)-L_j.

The seven variables still correspond to weights 36,40,44,48,52,56,60.
The previous positive dual can be rescaled to a valid bound, but its
seven active equalities give negative primal coordinates in the new
model. A separately prepared bounded LP therefore seeks a better
certificate. Only exact rational dual checks establish a new bound.

The source `triangle_incidence_binary_star_code.py` freezes all 99
integer rows, checks all 128 subsets of an abstract seven-triangle
star, and retains every numerical proposal and exact reconstruction.
The scalar bound alone cannot exclude a graph with a zero-dimensional
binary kernel.

The completed query has exact optimum

    |C| <= 5471926272/290905 < 2^15.

Thus rank_F2(B)>=85. Only degrees four and six have positive dual
multipliers: 6743/18327015 and 19/1221801. These use the previously
proved 2,079 weight-four and 24,486 weight-six words. The additional
star counts do not improve this optimum. The exact primal uses only
weights 36 and 48 and satisfies all 99 rows, so this finite limitation
is certified rather than inferred from a numerical status.

Three-triangle chains provide further weight-five words. They give a
stronger [rank bound of 88](triangle_incidence_binary_chain_code.md)
in a separate model.
