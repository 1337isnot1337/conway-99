# Complete six-root high-mask packing domains

The complete universal pair-capacity domain has **132,062** atoms. A separate
common-neighbor condition leaves **90,776** atoms for the empty six-root.
These are necessary local domains. Their atoms are not asserted to extend to
a Conway graph.

## Definitions and coverage

Fix a labelled induced graph \(H\) on six vertices. For a neighborhood mask
\(h\subseteq V(H)\) of size at least three, let \(X_h\) count outside vertices
whose neighbors in \(H\) are exactly \(h\). Two vertices in the same class
would have at least three common neighbors. Thus \(X_h\in\{0,1\}\).

For a pair \(i,j\in V(H)\), define

\[
q_{ij}=2-H_{ij}-(H^2)_{ij}.
\]

Every Conway graph therefore satisfies

\[
\sum_{h\supseteq\{i,j\}}X_h\le q_{ij}.
\]

Each catalogue root has \(q_{ij}\in\{0,1,2\}\). Its allowed high masks are
checked directly by adjoining one vertex and testing every visible
common-neighbor cap. The empty six-root allows all 42 masks of size at least
three, with all 15 pair capacities equal to two. Every other root domain is
therefore a subset of this universal domain. The empty atom is retained.

The frozen C++ census uses two 15-bit capacity sets. The new Python census
uses an independent representation: 15 integer residual capacities. It
visits masks in increasing order and records every visited subset. Including
a mask subtracts one from each pair it contains; returning restores those
capacities. This visits each admissible subset exactly once.

Both censuses give the following population counts.

| Selected classes | Atoms |
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

The independent census also agrees on all 1,346,729 candidate tests and the
full histogram of consumed pair capacities. Sorted atoms use one uint64
word each, with bit positions indexed by the 42 increasing masks. The file
has 1,056,496 bytes. A separate array records all 15 pair usages per atom.

For each of the 62 roots, the preparation checks mask membership and every
pair capacity directly. It then verifies the same filter with the two-bitset
representation. The 62 baseline domains contain 350,963 atoms in total.

## Additional outside-pair condition

If distinct selected classes \(h,k\) have \(|h\cap k|\ge3\), their two
outside vertices already have at least three common neighbors in the root.
Their mutual adjacency cannot repair this. Hence every actual graph obeys

\[
X_hX_k=0\qquad\text{when }|h\cap k|\ge3.
\]

This condition is separate from the root-pair capacities. The preparation
retains the baseline list, removes 41,286 universal atoms by this condition,
and saves an explicit incompatible class pair for every removed atom. It
checks all 1,722 literal two-vertex extensions of the empty root, covering
every pair of distinct high masks and both mutual-edge choices.

The filtered 62 root domains contain 266,159 atoms in total. No outside
adjacency value is fixed, no count point is loaded, and no symmetry quotient
is imposed.

## Artifacts and scope

The complete result is
`experiments/logs/moments-and-counts/order10-high-mask-packing-domains02.json.gz`.
Its SHA256 is
`27c27163aa7429d75df5d430072ece5dd045df2d54caa8a6d57a28db45db0a71`.
The atom and pair-usage files are bound inside that result. Preparation took
16.12 seconds with peak RSS 83,212 KiB.

The original `domains.json.gz` result records a metadata-only failure:
relative output paths were passed to `Path.relative_to` with an absolute
repository path. Its already-written atom file matches the complete rerun
byte for byte. The source was unchanged; the second invocation used absolute
output paths. The failed result remains preserved and is not presented as a
completed root-domain census.

The domain preparation does not test the count witness, construct moment
tensors, call an optimizer, or decide graph existence. The subsequent feature
matrix and fixed-point zero filters are separate artifacts.
