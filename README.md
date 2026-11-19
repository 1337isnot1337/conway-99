# Conway's 99-graph problem

Does a simple graph on 99 vertices exist in which every vertex has degree 14, every adjacent pair has one common neighbor, and every nonadjacent pair has two? This repository archives research on that question. The existence problem remains open. The local arguments and computations are unrefereed.

## Main results

- A hypothetical Conway graph contains at most **120 induced 3 × 3 rook grids**, improving the published upper bound of 231. At least **1,998 nonadjacent pairs** then percolate under the two-neighbor rule. The same analysis gives at least **1,188 pairs of disjoint triangles joined by exactly two edges**. [Proofs and prior work](grid_intersections.md)
- For any choice of root, there is an **independent set of size 14 containing seven of its neighbors**. Such a set extends to a maximal independent set of size 14 through 20. [Proof](hemisphere.md)
- Exact theta-series certificates exclude **ranks 28, 30, and 32** of $27I-9A+J$ over $\mathbb F_7$, where $A$ is the adjacency matrix and $J$ is the all-ones matrix. This is an independent derivation of earlier reported exclusions. The remaining ranks are 34, 36, 38, 40, and 42. [Derivation, certificates, and credits](level_seven.md)

[STATE.md](STATE.md) records the other results, the assumptions behind each construction search, the numerical experiments, and prior work. The archive includes source code, human-readable run logs, exact certificates, candidate arrays, and cached moment data.

## Replay the main finite checks

Run these commands from the repository root with Python and a C++20 compiler. The checks were replayed with Python 3.14 and GCC 16.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install 'numpy>=2' scipy threadpoolctl pynauty

python grid_intersections.py
python root_cover_audit.py
python level_seven_check.py

build_dir=$(mktemp -d)
c++ -O3 -std=c++20 grid_support.cpp -o "$build_dir/grid_support"
"$build_dir/grid_support"
```

The grid checks enumerate 2,097,152 labeled seven-vertex graphs and replay the 21-grid root exclusion. The theta-series check verifies the three stored rational certificates and tests the transform against five explicit positive controls.

Some exploratory scripts reference intermediate files or solver builds in the original `/tmp/conway99-tools` scratch directory. That directory was unavailable when this archive was prepared. The checks above run from the files in this repository. See [STATE.md](STATE.md#sources-and-replay) and the individual experiment scripts for other dependencies and controls.
