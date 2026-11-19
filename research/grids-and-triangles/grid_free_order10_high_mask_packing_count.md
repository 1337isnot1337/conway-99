# Complete pair-capacity packing count on an empty six-root

The empty six-vertex root has 42 possible outside neighborhood masks of size
at least three. There are exactly **132,062** subsets of these masks that
use each root pair at most twice. The empty subset is included.

This is a count of a necessary local relaxation. It imposes root-pair
capacities and the Boolean class condition. It does not choose edges
between outside vertices. In particular, this baseline still permits two
different masks whose intersection has size at least three. Such a pair
would violate the common-neighbor bound for the two outside vertices and
can be removed by a separate, explicit condition.

## Pair-capacity model

At an induced six-root \(H\), the number of common neighbors of root vertices
\(i,j\) outside the root is

\[
q_{ij}=2-H_{ij}-(H^2)_{ij}\in\{0,1,2\}.
\]

An outside class with mask \(h\), \(|h|\ge3\), contains at most one vertex.
Its indicator \(X_h\) therefore satisfies

\[
\sum_{h\supseteq\{i,j\}}X_h\le q_{ij}.
\]

The inequality allows the omitted low-mask vertices to supply the remaining
common neighbors. For an empty root all 15 capacities are two. Every other
six-root domain is a subset of the same 42 masks with capacities at most
two, so its packings form a subset of this universal list.

Each selected mask uses \(\binom{|h|}{2}\) units of pair capacity. The total
budget is 30, which bounds the selected population by ten. The exact number
of subsets satisfying only this total-weight constraint is

\[
\sum_{j=0}^{30}[t^j]
 (1+t^3)^{20}(1+t^6)^{15}(1+t^{10})^6(1+t^{15})
=15,159,780.
\]

This weighted bound was computed before the packing enumeration. Its
per-root analogues sum to 40,361,506 across all 62 roots. These numbers are
upper bounds, not packing census results for the other roots.

## Enumeration and controls

Give each root pair one of 15 bit positions. During the search, `once`
records pairs used at least once and `twice` records pairs used twice.
A mask with pair-support `p` is allowed exactly when `p & twice == 0`.
The update is

```text
new_once  = once | p
new_twice = twice | (once & p)
```

For capacities zero or one, reserve the missing capacity initially:
`once` contains pairs with quota below two, and `twice` contains pairs
with quota zero. The full count here starts both masks at zero.

The DFS uses strictly increasing mask indices. Each node represents one
valid subset, and every valid subset occurs through its unique increasing
sequence. Thus counting nodes counts packings. The complete run also checks
that the node count equals one plus the number of accepted transitions.

The point-independent Python scope preparation compared this update with
literal integer quotas on 13,408 assignments in domains of at most twelve
masks. The C++ run independently checked all 4,096 assignments on the first
twelve masks before the full count. Its population histogram agrees with
the saved Python control.

| Selected population | Complete packing count |
|---:|---:|
| 0 | 1 |
| 1 | 42 |
| 2 | 861 |
| 3 | 6,715 |
| 4 | 25,350 |
| 5 | 44,424 |
| 6 | 38,082 |
| 7 | 14,430 |
| 8 | 2,025 |
| 9 | 120 |
| 10 | 12 |

The single authorized count took 0.008114 seconds inside the C++ process,
with a fixed ten-second deadline. It performed 1,346,729 candidate tests.
No retry occurred. No atom list was stored in this count-only package.

## Consequences for a later preparation

A sorted uint64 list of all 132,062 packings would occupy 1,056,496 bytes.
The complete degree-at-most-four monomial feature matrix on these columns
would contain exactly

\[
\sum_{k=0}^{10}n_k\sum_{j=0}^{4}\binom{k}{j}=5,804,664
\]

ones. There are 32,969 nonzero monomial supports in this baseline domain,
because every subset of size at most four that satisfies the pair quotas
is itself one of the enumerated packings. The complete unfiltered
degree-at-most-four coordinate set has 124,314 entries.

These are sizing consequences of the completed histogram. This package
does not build a moment matrix, read a count point, solve a moment-cone LP,
or assert graph feasibility.

## Frozen files

The sources are
`experiments/workspace/grid_free_order10_high_mask_packing_scope.py`,
`experiments/workspace/grid_free_order10_high_mask_packing_count.cpp`, and
`experiments/workspace/grid_free_order10_high_mask_packing_count.py`.

The scope ledger and count result are
`experiments/logs/moments-and-counts/order10-high-mask-packing-scope.json`
and `experiments/logs/moments-and-counts/order10-high-mask-packing-count01.json`.
The latter binds the exact sources, domain, compiler flags, binary hash,
raw output, and status.

Result SHA-256:
`9637c67a8e1d729a9ddc1867ca4c563e3f3f35555e6d1c1c1514df6c06e5f18d`.
