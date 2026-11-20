# Scope of five- and six-root intersecting triangle blocks

This is a point-independent dimension census. It builds no pair tensor
and reads no count point.

For each catalogue root H of order 5 or 6 that contains a triangle, retain
every triangle class meeting H. A class consists of a nonempty root
intersection S and the multiset of root-neighborhood masks of the
remaining 3-|S| vertices. The literal H-plus-triangle graph must satisfy
the visible common-neighbor caps. All such classes are retained.

Condition on all triangles contained in H. If C is their Q principal
matrix and q_U lists their Q values against triangle U, the integer
conditioned kernel is

```
det(C) Q(U,V) - q_U^T adj(C) q_V.
```

All retained roots have one or two core triangles, and every C is exactly
positive definite. The census verifies its leading principal
determinants, adjugate identity, and all 2,984 core-triangle zero-row
identities. It also independently enumerates the root automorphisms.

| Root order | Catalogue roots | Roots containing triangles | Classes | Largest block | Lower entries |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5 | 21 | 8 | 257 | 56 | 4,859 |
| 6 | 62 | 30 | 2,374 | 220 | 127,647 |

The eight order-five blocks are:

| Root type | Core triangles | Classes | Lower entries |
| --- | ---: | ---: | ---: |
| 26 | 1 | 56 | 1,596 |
| 27 | 1 | 44 | 990 |
| 28 | 1 | 26 | 351 |
| 32 | 1 | 34 | 595 |
| 33 | 1 | 34 | 595 |
| 34 | 1 | 28 | 406 |
| 35 | 2 | 19 | 190 |
| 37 | 1 | 16 | 136 |

Every class has at most two vertices outside its root. Pair unions
therefore have at most 9 vertices for order-five roots and at most 10
for order-six roots.

## Enumeration estimates

For flags with a and b outside vertices, a conservative direct-product
bound is

```
sum over q=0..min(a,b) of C(a,q) C(b,q) q! 2^((a-q)(b-q)).
```

It includes every partial injection and every edge choice between the two
exclusive free sets. Mask compatibility and visible caps can only remove
choices. Its values for (a,b)=(0,0),(0,1),(0,2),(1,1),(1,2),(2,2) are
1, 1, 1, 3, 6, and 26.

Summed over all lower entries, the bounds are 108,481 candidate
completions for order-five roots and 2,967,175 for order-six roots.
These are workload bounds, not actual tensor term counts.

Conditioning makes the core-triangle class vectors vanish. The root
point-star vectors also vanish because Q B^T=0 and every triangle through
a root vertex is retained. The exact rank of these specified generators
gives quotient lower-entry totals 3,424 and 111,381 respectively.
The census retains the full domains; it does not delete classes.

## Saved outcomes

The corrected source is
`experiments/workspace/triangle_projector_intersecting_root_scope_v2.py`,
SHA256 `d25c7cfdb94fa79f0100990752a3c941011dd62e230c02b71472657f715f1b65`.

Its complete ledger is
`experiments/logs/moments-and-counts/order10-intersecting-triangle-root-scope-v2.json`,
SHA256 `78e62efc423f7acd498368207607c5dfc5572dd1840accebe46c38141aeb331f`.
It completed in 1.134679432005214 seconds.

The first version and its incomplete result are preserved separately.
That version converted the outside-size Counter to a plain dict; a root
with no size-one class then caused a KeyError in the workload estimate.
Version 2 changes only that dict conversion to Counter. No count query
or mathematical exclusion occurred in the failed attempt.

The order-five tensor construction is a separate next stage. The
order-six tensor construction remains unstarted.
