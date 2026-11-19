# Order-ten flags with three or four free vertices

The complete induced r4s3 family has nine blocks, 883 flags, and 90,240
lower-triangular entries. Its largest block has order 332. The complete
r2s4 family has only two blocks, of orders four and three. No moment
tensor was generated in this preparation.

These are the same flag domains used by `flag_moments.flags`: the root
vertices are individually labelled, there are at most s free vertices,
and every free vertex has degree at least three in the entire flag.
Edges among free vertices contribute to that degree. One graph pattern
is retained from each permutation orbit of the free labels.

## Complete domain census

The direct enumeration chooses a nondecreasing list of root-neighbor
masks, enumerates every graph on the free vertices, and applies all
local bounds A²+A≤2. It checks the degree condition in the complete
flag. It then identifies patterns under permutations within equal-mask
classes. This is exactly the remaining free-label symmetry after the
masks are sorted. No permutation of root labels is used.

Every resulting domain agrees with `flag_moments.flags` after the same
normalization. The preparation takes 1.503 seconds and peaks at
155,060 KiB. It uses only the small graph catalogue.

### Four root vertices, at most three free vertices

| Root type | Constant | One free | Two free | Three free | Block order | Lower entries |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 1 | 5 | 33 | 293 | 332 | 55,278 |
| 9 | 1 | 5 | 22 | 178 | 206 | 21,321 |
| 10 | 1 | 3 | 12 | 87 | 103 | 5,356 |
| 11 | 1 | 0 | 3 | 34 | 38 | 741 |
| 12 | 1 | 5 | 11 | 92 | 109 | 5,995 |
| 13 | 1 | 2 | 5 | 39 | 47 | 1,128 |
| 14 | 1 | 0 | 3 | 16 | 20 | 210 |
| 15 | 1 | 0 | 1 | 11 | 13 | 91 |
| 16 | 1 | 0 | 2 | 12 | 15 | 120 |
| Total | 9 | 20 | 92 | 762 | 883 | 90,240 |

Every flag has distinct root-neighbor masks and free-label stabilizer
one. This follows from the local bounds, rather than from an assumption
used to reduce the search.

**Distinct-mask lemma.** Suppose two free vertices u,v have the same
root mask S, there are at most three free vertices, and each free vertex
has degree at least three. If |S|≥3, u,v have too many common neighbors.
If |S|=2, u,v cannot be adjacent. Each must then be adjacent to the only
possible third free vertex, giving three common neighbors. If |S|=1,
both must be adjacent to both other free vertices. The adjacent pair
u,v then has the third free vertex and the root vertex in common.
Finally, |S|=0 leaves at most two neighbors. Each case is impossible.

A root-fixing automorphism preserves every root mask. Distinct masks
therefore force it to fix every free vertex.

### Two root vertices, at most four free vertices

There are no flags with one, two, or three free vertices. The five
nonconstant flags all have four free vertices:

| Root type | Root relation | Free masks | Induced graph type | Root-fixing stabilizer |
|---:|---|---|---:|---:|
| 2 | Nonedge | 1, 1, 2, 2 | 98 | 2 |
| 2 | Nonedge | 0, 1, 2, 3 | 95 | 1 |
| 2 | Nonedge | 1, 2, 3, 3 | 99 | 1 |
| 3 | Edge | 1, 1, 2, 2 | 99 | 2 |
| 3 | Edge | 0, 1, 2, 3 | 99 | 1 |

Including the constant flag gives block orders four and three, with ten
and six lower entries. Masks use bit zero and bit one for the two fixed
root vertices. Type 99 is the triangular prism. Types 95 and 98 are its
two edge-deleted forms, with the deleted edge's endpoints used as roots.

Repeated masks occur in three flags. Only two of those flags have a
nontrivial stabilizer. In both, the stabilizer simultaneously exchanges
the two vertices with mask one and the two vertices with mask two.

The absence of smaller nonconstant flags can also be seen directly.
One free vertex cannot have three root neighbors. Two free vertices
would both need the same two-bit mask and their mutual edge, violating
the adjacent common-neighbor bound. With three free vertices, the
distinct-mask lemma forces the masks 1,2,3. The first two vertices would
each need both free neighbors. Their triangles with the mask-three
vertex then violate the adjacent common-neighbor bound.

## Keep labelled extension multiplicities

For a fixed root embedding φ, let f_F(φ) count all injective assignments
of the free labels that realize the induced flag F. If a particular
unlabelled free subset realizes F, it contributes exactly
|Aut_root(F)| such assignments.

Choosing one pattern under permutations of free labels removes equal
functions from the variable list. It does not divide the remaining
function by its stabilizer. We retain f_F as a labelled extension
count, so its first moment is the usual labelled induced-embedding
count E(F)=Aut(F)c_F.

Likewise, every ordered pair of labelled extensions determines exactly
one overlap map between the two free label sets. All those partial
injections belong in the product formula. No free-stabilizer divisor
is applied to the product coefficients.

The nine-vertex rook graph supplies an exact control. Take the prism
flag rooted at a matching edge, with free masks 1,1,2,2 and stabilizer
two. For each of the 36 labelled edge roots in the rook graph, it has
one qualifying free subset and two labelled extensions. Thus its first
moment is 72 and its second moment is 144. The source enumerates these
assignments directly. A full-overlap term in its square has coefficient
two, corresponding to the two root-fixing automorphisms.

## Product complexity before local pruning

For left and right free sizes a,b, an overlap of size q has

\[
\binom{a}{q}\binom{b}{q}q!
\]

partial injections. After both induced patterns are prescribed, only
the edges between their disjoint free parts are unknown. There are
(a−q)(b−q) such edges. A general bound on the number of candidate
completions is therefore

\[
\sum_{q=0}^{\min(a,b)}
\binom{a}{q}\binom{b}{q}q!\,2^{(a-q)(b-q)}.
\]

| Maximum free sizes | Overlap-map counts by q | Completion bound per entry |
|---|---|---:|
| 3 and 3 | 1, 9, 18, 6 | 698 |
| 4 and 4 | 1, 16, 72, 96, 24 | 75,096 |

Distinct masks in r4s3 reduce the possible size-q overlaps to choosing
q shared masks. With at most three shared masks, the corresponding
completion bound is 567. An overlap must also preserve every prescribed
edge and nonedge on its shared vertices; these bounds do not yet use
that test or any local cap pruning.

For repeated masks, the polynomial

\[
\prod_m\left(\sum_q
\binom{a_m}{q}\binom{b_m}{q}q!x^q\right)
\]

counts mask-compatible partial injections, where a_m,b_m are the mask
multiplicities. Applying it to every pair of prepared flag profiles
gives the following aggregate upper bounds on raw candidate completions:

| Family | Lower entries | General bound | Bound after root-mask matching |
|---|---:|---:|---:|
| Full r4s3 | 90,240 | 49,566,257 | 37,180,575 |
| Full r2s4 | 16 | 675,871 | 614,775 |

These are finite work bounds, not measurements of tensor nonzeros or
runtime. Shared-edge consistency and cap pruning should remove many
candidates, but that reduction has not been measured here.

## Bounded next targets

For the current prism-free count model, all three flags with underlying
type 99 vanish identically. The entire edge-root r2s4 block becomes its
constant entry. The nonedge-root block has the point-independent
principal domain consisting of the constant, type 98, and type 95.
This gives a 3×3 matrix with six lower entries; only three entries are
products of two four-free-vertex flags. It is a small complete target
for the nontrivial prism-free r2s4 family. The stabilizer-two type-98
flag must keep its labelled multiplicity.

A second bounded target is the seven complete r4s3 blocks with order at
most 128, namely roots 10 through 16. They contain 345 flags, 13,641
lower entries, and a root-mask-matched completion bound of 5,309,237.
This choice depends only on the prepared domains. It retains all flags
for those seven roots. The two larger blocks can remain a separately
reported continuation. The full nine-root family is still modest in
matrix size, so an efficient product implementation may make that
split unnecessary.

No next target was generated or optimized in this preparation. Passing
one selected family would not certify all order-ten moment inequalities.

## Artifacts

Source:
`experiments/workspace/grid_free_order10_higher_flags_domains.py`

Source SHA256:
`a2fb1b18940423cdd6d36bce91bac54cbe3eecc8622c2418642b8a9559c8c6f0`

Complete domains, explicit free stabilizers, work bounds, and the rook
control are saved in
`experiments/logs/moments-and-counts/order10-higher-flags-domains.json`,
with a matching `.log` file. The source records the catalogue and
reference-source hashes. It loads no dense reduction, generates no
moment tensor, and invokes no optimizer.
