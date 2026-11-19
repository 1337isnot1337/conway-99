# Order-ten induced moments from six root vertices

## Prepared family

Fix an induced labelled six-vertex root graph `H`. The variable family
contains the constant flag, every admissible one-vertex extension whose
outside vertex has degree at least three, and every admissible two-vertex
extension whose two outside vertices each have degree at least three
inside the entire flag. The graph on a flag is induced.

For two outside vertices with root-neighbor masks `a,b` and mutual edge
`e`, the degree condition is

\[
|a|+e\ge3,\qquad |b|+e\ge3.
\]

It is not the stricter rule `|a|,|b| >= 3`. Adjacent outside vertices with
two root neighbors each belong to this family. Their products are part
of the new information being tested.

The preparation includes all 62 six-vertex root types. It compares every
flag domain with the existing `flag_moments.flags(root,2)` enumeration;
all 62 agree exactly. No root or flag is removed according to the test
point's counts.

| Family property | Value |
| --- | ---: |
| Root types / nontrivial blocks | 62 |
| Total flags across all root types | 14,348 |
| Largest full block | 1,248 |
| Full lower-triangle entries | 3,913,479 |
| Largest block with both root degrees at least three | 738 |
| Blocks selected by the fixed size limit 512 | 55 |
| Largest selected block | 495 |
| Selected lower-triangle entries | 1,042,819 |
| Positive-count selected roots at the test point | 54 |
| Zero-count selected roots at the test point | 1 |

The zero-count root is the prism, type 99. Its four-flag block remains
selected. The seven omitted roots are omitted because of their flag
counts, not because of their counts at the point:

| Root type | Full block order |
| --- | ---: |
| 38 | 1,248 |
| 39 | 1,093 |
| 40 | 810 |
| 44 | 938 |
| 45 | 614 |
| 46 | 676 |
| 64 | 783 |

The planned scan therefore covers a fixed 55-block subfamily. A pass
would not cover these seven omitted blocks or all conceivable order-ten
moment inequalities.

## Variables and free-label normalization

For a fixed labelled embedding of `H` into a candidate graph, let `f_F`
count the injective labelled extensions realizing flag `F`. A permutation
of only the free labels gives the same variable by relabelling those
extensions. One representative from each such orbit is retained. There
is no division by an automorphism order in the variable itself.

For a two-vertex flag, the two root masks are distinct. If they were equal
and the outside edge were absent, both vertices would have at least
three common root neighbors. If the outside edge were present, both
would have at least two common root neighbors. Either case violates a
local quota. Thus the representative can be chosen by `a < b` without
losing any flag or making a graph-symmetry assumption.

One-vertex flags are binary. A two-vertex flag need not be binary. If
both root masks have size two, each mask class can contain two vertices.
Edges between the two classes form a matching: two vertices in one
class already share their two root neighbors and cannot share another
neighbor. The flag count can therefore be two. If a flag uses a root
mask of size at least three, that vertex is unique; an adjacent
size-two mask class can supply at most one partner for the same reason.
Every retained flag count is consequently in `{0,1,2}`, with many flags
restricted to `{0,1}`.

The builder does not impose `M_FF = M_0F` for the two-vertex flags. It
computes their products by overlap enumeration.

## Exact product formula

For two flags with `s,t <= 2` free vertices, first choose the overlap of
their free vertices. Root vertices have already been identified label
by label and cannot coincide with free vertices. Choose `q` free labels
of the right flag and inject them into the left flag's free labels.

For `s=t=2`, the numbers of these injections are:

| Shared free vertices `q` | Injections | Unspecified cross edges |
| --- | ---: | ---: |
| 0 | 1 | 4 |
| 1 | 4 | 1 |
| 2 | 2 | 0 |

An identified pair of free vertices must have equal root-neighbor masks.
If both free vertices are identified, their mutual edge prescriptions
must agree. These tests check every adjacency on shared vertices.

After a consistent identification, the only unspecified pairs lie
between the left-exclusive free vertices and the right-exclusive free
vertices. Every choice of those edges is enumerated. In the two-by-two
case there are at most

\[
16+4\cdot2+2=26
\]

labelled completions before local-cap pruning. Each completion has at
most ten vertices. A completion that violates a pair quota has no copy
in a candidate graph and contributes zero.

For an admissible completed graph `K`, write
`E(K) = Aut(K) c_K` for its number of labelled induced embeddings. The
product entry is the sum of `E(K)` over the consistent overlaps and edge
choices, retaining multiplicities when several labelled completions have
the same unlabelled type.

This formula is a partition of the ordered pairs of rooted flag
embeddings by their exact overlap and remaining edges. Thus the moment
matrix is the sum, over all labelled induced root embeddings, of
`f f^T`; it is PSD. The same argument applies to every fixed principal
subfamily of flags.

## Catalogue implementation

The source uses complete one-vertex extension tables to identify
successive additions. It keeps an explicitly checked transport from the
current labelled graph to its stored catalogue representative. A missing
extension-table entry means that the proposed addition violates a local
quota.

For intermediate graphs with at most three free vertices, the source
normalizes only their free labels for cache reuse. It composes the
resulting relabelling with a verified full graph isomorphism. This does
not change the root labels or identify different flag variables.

Each two-by-two product needs at most two additions to the left flag.
The final addition is identified by an extension-table lookup without
canonicalizing every ten-vertex completion independently.

The separate scan driver will evaluate matrices and negative quadratic
forms with Python integers. Numerical eigenvectors only propose integer
directions. Any exported inequality must have a strictly negative exact
integer value at the saved count witness. Its initial form is in the
48,965 induced catalogue counts; this preparation does not load the
dense 550-coordinate reduction.

## Direct rook-graph controls

For each control, the source enumerates labelled root embeddings in the
nine-vertex rook graph, counts the flags directly, and sums their outer
products. These matrices exactly equal the product formula above.

| Root | Catalogue type | Flags | Root embeddings | Largest flag value |
| --- | ---: | ---: | ---: | ---: |
| Independent triple | 4 | 5 | 36 | 2 |
| Edge plus isolated vertex | 5 | 3 | 72 | 1 |
| Six-vertex prism | 99 | 4 | 72 | 1 |

The independent-triple control is a direct check against the invalid
binary shortcut. For each of its three adjacent two-outside flags,
`M_0F = 72` and `M_FF = 144`. The diagonal contains one coincident-copy
term and one disjoint-copy term. Both have value 72 in the rook graph.

The preparation builds only these small control matrices: 34 product
entries including the extra diagonal inspections. It verifies 15,081
label transports while constructing the full flag domains. It takes
3.619 seconds and peaks at 168,568 KiB. It calls no optimizer and starts
no large-family generation or scan.

## Files and current scope

The prepared builder is
`experiments/workspace/grid_free_order10_r6s2.py`, SHA-256:

```text
3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d
```

Its exact domain/control report is
`experiments/logs/moments-and-counts/prism-zero-order10-r6s2-preparation.json`,
SHA-256:

```text
1ff172888ebdd1a139710cb25e0a0f29c8044a1d81ba4972c0085f9827d691ea
```

The separate bounded driver is
`experiments/workspace/grid_free_order10_r6s2_scan.py`. It visits the 55
selected roots in increasing flag count, then root type, within one
180-second generation/separation budget. Completed tensors retain all
their flags and can be reused at another point. A timeout records only
completed blocks and cannot be reported as a complete-family result.

The proposed point is the new rounded prism-zero count witness from the
one-round IPM loop, SHA-256
`3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326`.
The preparation itself makes no feasibility or infeasibility claim for
this new moment family.
