# Exact ranges of r6s2 flags

Both saved integer count witnesses pass all 7,812,610 ordered flag-range
inequalities in the full 62-root r6s2 cache. This scan produces no new
cut. It is separate from the PSD scan, whose 18 saved cuts reject the
first witness and whose 16 negative evaluations reject the second.

## Flag bounds

Fix a labelled root embedding. Let f_F be the number of extensions to a
flag F in the prepared family.

If an outside vertex of F has at least three root neighbors, that vertex
is unique: two distinct vertices with the same three root neighbors
would have at least three common neighbors. For a two-vertex flag, the
other vertex is then also unique, since it has at least three prescribed
neighbors in the root together with the first vertex. Thus f_F is zero
or one. The constant flag also has value one.

The remaining flags have two outside vertices, each with two root
neighbors, joined by an edge. Their two root-neighbor masks are distinct.
Each mask has at most two realizations. Edges between the two classes
form a matching: if one vertex were adjacent to two vertices in the
other class, those two vertices would share their two root neighbors
and this additional vertex. Consequently 0≤f_F≤2.

Let b_F be one in the first case and two in the second. For every pair
of flags F,G, the pointwise inequality

\[
(b_F-f_F)f_G\geq0
\]

gives the exact linear moment inequality

\[
b_F M_{0G}-M_{FG}\geq0.
\]

The diagonal case is b_F M_{0F}−M_{FF}≥0. These inequalities use the
full product tensor; no binary-diagonal replacement is made.

## Why the diagonal inequalities add no count constraints

All 11,350 binary flags in the full cache satisfy the exact product
identity M_FF=M_0F. Their diagonal range inequalities vanish identically.

For a nonbinary flag F, write its two masks as A and B. A repeated
extension that overlaps one outside vertex would give that shared
vertex two neighbors in the opposite mask class. This is forbidden by
the common-neighbor bound. Therefore its square has only the identical
copy and, when admissible, the disjoint double copy D:

\[
M_{FF}=E(F)+E(D),\qquad M_{0F}=E(F),
\]

where E denotes the labelled induced-embedding count. All cross edges
between the two copies are forbidden for the same common-neighbor
reason. The code checks this literal product identity for every
nonbinary flag.

For 1,784 nonbinary flags, D is forbidden. The diagonal range inequality
is then E(F)≥0, already included among the induced-count constraints.

For the remaining 1,214 flags, first add the second A-profile vertex to
F, obtaining the nine-vertex graph C. The two root vertices in A have
exactly one remaining common-neighbor place. The original marked-pair
extension equation and nonnegativity of every other extension term give
E(C)≤E(F). Add the second B-profile vertex, adjacent to the newly added
A-profile vertex, to obtain D. The two root vertices in B again have
exactly one remaining common-neighbor place, so the next marked-pair
equation gives E(D)≤E(C). Hence

\[
2M_{0F}-M_{FF}=E(F)-E(D)\geq0.
\]

Both extension equations occur by order ten. The audit constructs C and
D explicitly, verifies their induced types and local caps, and checks
both residual common-neighbor quotas equal one. This establishes the
diagonal range inequalities from existing count rows; it does not prove
the general cross-range inequalities redundant.

## Exact point checks and scope

The source is
`experiments/workspace/grid_free_order10_r6s2_ranges.py`, SHA256
`43117dabd1c2983a78a806ee79e68dde1f598786eae6a67b04bd2957bad7b7e8`.
The output is
`experiments/logs/moments-and-counts/prism-zero-order10-r6s2-ranges.json`,
with a matching `.log` file.

The two inputs are the exact integer count witnesses with SHA256:

- `3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326`,
  whose x521 coordinate is 116;
- `ee8e22f070e0529be5be8bf14c853c6ad9ed97127570223abf6e1529ab8857f9`,
  whose x521 coordinate is zero.

For each point, all 7,812,610 ordered ranges are nonnegative. The scan
took 15.842 seconds and loaded no dense reduction. It used no numerical
eigensystem or optimizer. A passing range scan is neither a PSD
certificate nor a graph construction. The earlier PSD cuts still
exclude both particular count points.
