# At most 104 grids

A hypothetical Conway graph has at most **104** induced rook grids and at least **2,286** percolating nonedges. Every vertex lies on a triangle of grid degree at most two, so there are at least **33** such triangles. The [near-minimal cover argument](low-triangle-cover.md) raises this number to 36.

Write $D_p$ for the graph on the seven axes through $p$, with one edge per grid through $p$. Its edge count $e_p$ is [at most ten](ten-grid-bound.md). The sum of its seven degrees is at most 20, so at least one axis has degree at most two. This proves the covering assertion.

## Counts on a full triangle

Full triangles lie on six grids and are [pairwise disjoint](two-full-axes.md). The other grids through a vertex of such a triangle define pairs among six prism indices. At a ten-grid root their four pairs form a four-cycle or a triangle with a pendant edge. The [three-root table calculation](full-triangle-cross-grids.md) forces a common index pair if all three roots have ten grids. The [common-pair exclusion](full-triangle-common-pair.md) makes this impossible.

If two roots have ten grids and the third has nine, the third has three extra pairs. The same table calculation tests every three-edge graph on six indices for this root, allowing both kinds of ten-grid root. Preserve the order of the three roots, identify choices under permutations of the indices, and discard choices failing the split condition or having a common pair. Of 372 remaining triples, two support an integer table. In both, the three edges at the nine-grid root form a perfect matching. In fact the [five-missing-pair bound](four-missing-cones.md) excludes this matching as well. For a matching edge the ten disjoint pairs include four incident to the full axis and the other two matching edges, leaving only four nongrids.

## Sum of root weights

For a root $p$, let $f_p$ indicate membership in a full triangle, $n_p$ membership in a full triangle with $e_p=10$, and $q_p$ membership in a full triangle with $e_p\le8$ or with $e_p=9$ and three extra pairs forming a perfect matching. Keeping the matching case in this count lets the last arithmetic step use a larger set of supports. With $t$ full triangles the preceding cases give
$$
\sum_p(n_p-q_p)\le t.
$$
Indeed three ten-grid roots are impossible and two ten-grid roots force the remaining point to contribute one to $q_p$.

For axis degrees $d_1,\ldots,d_7$ and $m_p$ unordered pairs of disjoint edges in $D_p$, write
$$
C_p=2m_p-\sum_i\min(2,d_i)(6-d_i)+2\#\{i:d_i=2\}.
$$
The [double-partner witness bound](double-partner-witness.md) gives $\sum_p C_p\le0$ and $t\le20$.

The [integer root enumeration](../../experiments/workspace/full_triangle_global_bound.py) checks
$$
13e_p\le120+6f_p+C_p+2n_p-2q_p.
$$
It starts from all 1,044 unlabelled graphs on seven vertices. Use the ten-grid bound, the four classified supports at ten, at most one full axis, and the [signless incidence condition](grid_intersections.md) that deleting any missing edge preserves the number of bipartite components of the missing graph. All 322 remaining graphs satisfy the inequality.

Each grid has nine points and $\sum_p f_p=3t$. Hence
$$
117g\le11880+20t\le12280<12285=117\cdot105.
$$
The [percolation count](grid_intersections.md) gives $4158-18g\ge2286$. Run `make verify-104-grid-bound` to replay the common-pair obstruction, both table enumerations and the integer weight check.
