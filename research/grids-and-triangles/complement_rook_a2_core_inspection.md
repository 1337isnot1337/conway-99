# The retained a=2 proof cores

The [four complete-edge certificates](complement_rook_a2_fixed_completion.md)
exclude all 576 incidence designs with `a=2`. Their retained input clauses
can be traced back to the mathematical constraints that generated them.

`experiments/workspace/complement_rook_a2_core_inspection.py` regenerates
each full formula as a stream. It verifies the exact original SHA256 and
then assigns every retained input clause to an original mixed equation,
packing clause, path implication, or exterior cap. If a clause occurs in
several source rows, the first occurrence supplies its attribution.

| Orbit | Mixed rows | Packing clauses | Path implications | Exterior cap rows | Graph-edge variables in retained formula |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 29 | 10 | 0 | 0 | 60 |
| 1 | 69 | 11 | 8 | 3 | 138 |
| 2 | 80 | 32 | 5 | 4 | 139 |
| 3 | 183 | 25 | 49 | 23 | 315 |

None of these attributions uses an explicit exterior-degree equation.
This does not assert that the displayed row sets are minimal.

The first retained proof has a particularly local support. Its mixed rows
are centered at the signatures `(7,0,4)` and `(7,0,8)`, which share the
same first and second core neighbors. Four mixed rows come from the first
vertex and 25 from the second. The ten packing clauses prohibit a common
exterior neighbor of a pair already sharing two core vertices. The whole
retained formula uses only 60 graph-edge variables.

Packing clauses use existing edge variables and allocate no auxiliaries.
Consequently, a low maximum variable number in a retained proof does not
show that the proof uses only the mixed equations. The exact attribution,
rather than a variable-number cutoff, establishes the table above.

The other three proofs use ordinary exterior caps and mixed rows centered
at seven, seventeen, and thirty-two exterior vertices, respectively. This
inspection has not produced one common obstruction for all larger values
of `a`. The certificates establish the stated `a=2` exclusions; no broader
exclusion follows from the row counts alone.

The saved attribution is
`experiments/logs/grids-and-triangles/complement-rook-a2-core-inspection.json`.
It can be regenerated without invoking a solver:

```sh
.venv/bin/python experiments/workspace/complement_rook_a2_core_inspection.py \
  --output experiments/logs/grids-and-triangles/complement-rook-a2-core-inspection.json
```
