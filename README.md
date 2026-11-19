# Conway's 99-graph problem

Does a simple graph on 99 vertices exist in which every vertex has degree 14, every adjacent pair has one common neighbor, and every nonadjacent pair has two? **The existence question remains open.** This repository records structural bounds, exact certificates, and construction searches for this graph. The work is unrefereed.

| Research topic | Main result |
| --- | --- |
| [Grids and triangles](research/grids-and-triangles/grid_intersections.md) | At most **120** induced 3 × 3 rook grids, improving the published bound of 231. At least **1,998** nonadjacent pairs percolate, and at least **1,188** disjoint triangle pairs have exactly two cross-edges. |
| [Independent sets](research/independent-sets/hemisphere.md) | For every root, an independent set of size **14** can be chosen to contain seven of its neighbors. |
| [Eigenlattices](research/eigenlattices/level_seven.md) | Theta-series certificates independently recover the previously reported exclusions of **ranks 28, 30, and 32** over the field of seven elements. |
| [Binary triangle incidence](research/grids-and-triangles/triangle_incidence_binary_code.md) | The point-triangle incidence matrix has rank at least **82** over the field of two elements. Its kernel has only seven possible nonzero weights; an exact coding certificate gives the rank bound. |

- [Research catalog](CONTENTS.md) links the arguments, supporting notes, and certificates by topic.
- [Reproduce the checks](experiments/README.md) with `make verify` and browse the experiment logs.
- [Research ledger](STATE.md) records the scope of each search, prior work, and unresolved cases.
