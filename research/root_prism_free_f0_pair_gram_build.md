# Built complete incidence formula for the component-zero pair

The complete unfixed incidence formula is built and its cold replay
passed. This note records the pre-query build checkpoint. The subsequent
[single bounded query](root_prism_free_f0_pair_gram_run01.md) ended UNKNOWN.
The formula covers every compatible
incidence design for two copies of component zero with the identity
relative fiber alignment, in the conditional globally prism-free
\(x_{521}=0\) split-shell case.

It retains all 39,168 independent six-neighbor columns. The 960
component selectors are derived from those columns. They do not fix
either component's sixty-triple design. No graph symmetry, fixed
matching of exterior vertices, or saved fractional incidence is imposed.

The mathematical reduction and exact support coverage are in the
[model preparation note](root_prism_free_f0_pair_gram_model.md).
The preparation's 576 mixed-triple capacities, component links, and
quota-one Gram equations cover all 7,140 shell triples. The full
thirty-nine-vertex Gram matrix is represented by the local and cross
equations.

## Actual formula

| Quantity | Built value |
|---|---:|
| Independent complete-column selectors | 39,168 |
| Derived component-triple selectors | 960 |
| Total variables | 1,478,076 |
| Clauses | 3,173,640 |
| Literal occurrences | 7,370,472 |
| Counter rows | 2,160 |
| Direct component motif clauses | 180 |
| DIMACS bytes | 60,721,371 |

All counts agree with the separate preparation. The build took
14.408 seconds. The source creates one counter at a time and writes
its clauses directly to the output file. It never accumulates the
full CNF as a second Python clause list.

All counters share one monotone ID pool beginning after the 40,128
primary and derived selectors. The model manifest records each
contiguous clause block, its exact clause and literal counts, its
auxiliary interval, and its body hash. The blocks are component links,
component Gram equations, cross Gram equations, mixed-triple packing,
and the direct component motif clauses.

The complete CNF SHA256 is

`31a59090b935889b97515d20f5d03cdb02f5fc9b33a321ea30ded8b20c16b4b8`.

The [built model manifest](../experiments/logs/root-prism-free/f0-pair-gram-built-model.json)
has SHA256

`a87cac772964ec5af7415f327f0a2f52713ac9ca87767c1ae7b3ac0db2fa0728`.

The large DIMACS file is reproducible from these bound sources and
certificates; it is not needed as a committed source artifact.

## Exact primary-assignment inspection

The builder includes a standalone inspector accepting all true
primary IDs in `true_primary_variables`. IDs not listed are false;
counter auxiliaries are excluded from this input. The inspector
checks every prepared counter condition directly, including the
negative literal in each component link, and every direct motif
clause.

It then independently reconstructs the incidence matrix and checks:

- Exactly sixty distinct six-neighbor columns and sixty distinct
  component triples on each side.
- Exactly two neighbors in each global fiber.
- All 1,521 full Gram entries and all core-to-exterior known caps.
- All 1,770 exterior signature overlaps and all core-triple capacities.
- All 4,851 known caps in the resulting partial ninety-nine-vertex
  graph.

The core vertices must all have degree fourteen, while the sixty
exterior vertices have their six specified core neighbors. The
inspector scans the known partial graph for additional visible
prisms and \(F\) motifs. For each found motif, it explicitly checks
that adding any missing chord violates a common-neighbor cap. Thus
an unmodeled exterior edge cannot remove that particular obstruction
by adding a chord.

These additional visible motif restrictions are not all included in
the CNF. Their presence is reported as a defect of a SAT incidence
candidate. Their absence would still leave the exterior adjacency
unresolved: an additional 240 edges are required, and future motifs
or common-neighbor defects remain possible.

## Controls and replay

The actual nine-vertex rook graph supplies a positive incidence
control. Removing or repeating a nonzero column is rejected. Small
direct motif controls check all six missing prism chords and all
28 missing \(F\) chords. The controls call no solver.

The mathematical preparation has a separate coordinator review, and
the exact one-column Gram screen has an independent integer-matrix
review. The build's cold replay separately reconstructs the complete
domain, every constraint support, all counter encodings, and the
whole streamed DIMACS file. It reproduces the recorded hash and
every clause-block record.

Source:
[root_prism_free_f0_pair_gram_build.py](../experiments/workspace/root_prism_free_f0_pair_gram_build.py).
Replay result:
[f0-pair-gram-build-replay.json](../experiments/logs/root-prism-free/f0-pair-gram-build-replay.json).

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_pair_gram_build.py replay \
  --model experiments/logs/root-prism-free/f0-pair-gram-built-model.json \
  --output /tmp/f0-pair-gram-new-replay.json
```

The output path must not already exist. This command writes a temporary
rebuilt CNF, checks its hash, and removes the temporary file. It does
not invoke a SAT solver.

A later checked UNSAT result would exclude this complete component
pair and alignment. It would not exclude the other component pairs,
the other alignments, or the connected shell case. At this checkpoint,
no such feasibility decision has been made.
