# Computations and replay

## Main checks

From the repository root, use Python, GNU Make, and a C++20 compiler. The archived checks were replayed with Python 3.14 and GCC 16.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r experiments/requirements-verify.txt
make verify
```

`make verify` uses the repository's `.venv` when present. Set `PYTHON` to the absolute path of a different interpreter or set `CXX` to select the compiler.

| Check | Scope |
| --- | --- |
| [`grid_intersections.py`](workspace/grid_intersections.py) | Enumerates all 2,097,152 labeled seven-vertex graphs for the grid-count inequalities and equality case. |
| [`grid_support.cpp`](workspace/grid_support.cpp) | Computes disjoint-pair minima and the weighted minimum of 97 for the triangle-pair bound. [Log](logs/grids-and-triangles/grid-support.log) |
| [`grid_agreements.py`](workspace/grid_agreements.py) and [`grid_leaf.py`](workspace/grid_leaf.py) | Check the four-point maps and eight-point possibilities for a fifteen-grid root. |
| [Four-point cell profiles](workspace/root_cell_profiles.py) | Checks all 41 populations of the seven-edge theta graph on the axes. |
| [Two-full-axis checks](../research/grids-and-triangles/two-full-axes.md) | Test sign transports and the rank of the 59-vertex core. The C++ template verifier uses Boost.Multiprecision headers. |
| [`root_cover_audit.py`](workspace/root_cover_audit.py) | Replays the parity and transport cases used to exclude a root contained in 21 grids. [Log](logs/grids-and-triangles/root-cover-audit.log) |
| [`level_seven_check.py`](workspace/level_seven_check.py) | Replays the rational rank certificates and checks the theta transform on five explicit lattice controls. [Log](logs/eigenlattices/level-seven-check.log) |

The full proof that two triangles on six grids cannot intersect is an additional computation. Run `make verify-full-axes` for the complete interface enumeration. Its [reference output](logs/grids-and-triangles/two-full-exhaustion.log) lists every even support size.

## Explore the archive

Run the individual research scripts from [`experiments/workspace/`](workspace/). The Python and C++ sources, certificate JSON, candidate arrays, and cached moment data share this directory because the scripts use sibling paths.

The archived logs cover [grids and triangles](logs/grids-and-triangles/), [independent sets](logs/independent-sets/), [eigenlattices](logs/eigenlattices/), [moments and counts](logs/moments-and-counts/), and [construction searches](logs/construction-searches/). The [research ledger](../STATE.md) explains which runs concern relaxations or particular construction families.

Some exploratory scripts refer to solver builds and generated inputs in the original `/tmp/conway99-tools` directory, which was unavailable when the archive was published. The checks above use the archived files and the dependencies listed here. The [initial publication](https://github.com/1337isnot1337/conway-99/tree/270ae4f8c4cfb751f9c4b5b74949c41263b645ba) preserves the original paths.
