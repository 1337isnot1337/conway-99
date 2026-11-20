# Case4 Boolean row-cut query: unresolved

## Terminal result

The one authorized query returned UNKNOWN at its 60-second limit. Indexed
35-core case4 remains unresolved. No second query was made.

The full formula contains all 218,863 original incidence clauses, the 30 exact
Gram conflicts, and 42,178 clauses encoding all 60 exact exterior-row
inequalities. Its 1,214 primary selectors remain free. The complete formula
has 134,852 variables and 261,071 clauses.

Bootstrap took 0.628 seconds. The solver returned after 60.022 seconds, and the
full run took 60.063 seconds. It recorded 92,299 conflicts and 287,445 decisions.
Peak process RSS was 98,292 KiB. The run produced neither a partial SAT
incidence nor an UNSAT proof.

The exact cold preflight had already rebuilt the complete formula and matched
SHA-256 `b0ca3f15a6d2c9e27f82af783cb62c1ecc27376e53f5820105c49d6fd7b72738`.
The terminal binding links that formula, the unchanged source and model, the
coordinator gate, and the UNKNOWN result. No proof check applies to an UNKNOWN
answer. The frozen replay command can independently rebuild the formula with
the terminal result attached:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_row_cut_boolean.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-model.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-run01/result.json \
  --output /tmp/conway99-case4-row-cut-boolean-run01-replay.json
```

## Two elementary column exclusions already present

The 60-cut package already forbids zero-based columns 1080 and 1081. Both admit
a simpler proof using just two mixed-row coordinates. This proves the same
two exclusions; it does not add a new exclusion to the Boolean formula.

Use the core coordinates R3=3 and S1=10. For either target column a, its complete
eligible neighbor domain satisfies

\[
h_b(R3)\leq h_b(S1)\qquad\text{for every eligible }b.
\]

Its mixed target instead has q_a(R3)=2 and q_a(S1)=1. Summing the support
inclusion over actual exterior neighbors would give 2 at most 1. Equivalently,
the integer potential e_R3 minus e_S1 has target product 1 and nonpositive
product on every eligible neighbor, forcing x_a=0.

| Zero-based column | Original signature | Attachment mask | Eligible neighbors | R3 support size |
| --- | ---: | ---: | ---: | ---: |
| 1080 | 232 | 144 | 365 | 15 |
| 1081 | 232 | 160 | 347 | 11 |

The standard-library verifier
`experiments/workspace/complement_rook_35core_case0004_row_cut_units.py`
rebuilds all 1,214 mixed targets and independently tests all 1,214 potential
neighbors for each of these two columns. It checks the two support inclusions,
the targets 2 and 1, and the original frozen integer potentials. Its report is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-units.json`.

These local contradictions suggest testing the same necessary row conditions
over the complete optional-column domain. No such wider census or further
solver result is part of this terminal checkpoint.

## Frozen files

The terminal manifest is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-terminal-artifacts.json`.
It includes the original preparation and cold preflight, the independent
arithmetic and clause-binding audit, the coordinator review, the terminal
query log and result, and the two-coordinate explanation.

The original incidence model and all earlier cut certificates remain unchanged.
