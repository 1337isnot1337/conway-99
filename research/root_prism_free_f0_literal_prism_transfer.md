# Literal transfer of the existing three-exterior prism families

The complete inventory and a separate independent replay accept 59,220
necessary inequalities for the literal Boolean shared-edge model:
1,224 one-edge/third-selector rows and 57,996 two-edge path rows. These
are transfers of existing certified prism families. The path remainder
already appears in the
[local conflict inventory result](root_prism_free_f0_local_conflict_inventory_result.md).

This package certifies the rows and their relationship to the accepted
168,050-row parent. It does not build or query an enlarged native model.
It does not establish feasibility, infeasibility, a graph construction,
or exclusion of the F0 component. The parent has 68,934 variables,
including all 68,394 eligible exterior edges; this transfer introduces
no new variable and imposes no graph symmetry.

## Literal inequalities and their premises

Write `x_a` for selection of exterior signature `a`, and `y_ab` for its
literal Boolean edge to `b`. Both endpoint activation inequalities
`y_ab <= x_a` and `y_ab <= x_b` are already present in the parent.

Each accepted one-edge witness gives

```text
y_ab + x_c <= 1.
```

The two possible additional exterior chords `ac` and `bc` are forbidden:
each endpoint pair has two common core neighbors. If edge `ab` and
selector `c` were both present, the witness's six sites would induce a
triangular prism. The independent replay reconstructs all 9,360 saved
six-site graphs and checks those nonedge premises. This is the literal
Boolean consequence of the older moment-variable inequalities; it does
not introduce the older `Z` variables.

Each accepted two-edge path witness gives

```text
y_ab + y_bc <= x_b.
```

When both edges occur, the remaining chord `ac` is forbidden because `a`
and `c` share both `b` and the witness's core site. The saved six sites
then induce a prism. When `x_b = 0`, the endpoint activations set both
edges to zero. The checker reconstructs all 107,520 saved path witness
graphs. This argument proves a necessary graph inequality even though
the current relaxation does not contain every general exterior-pair
common-neighbor cap.

The original witness families and their cold replays are bound by the
[inventory configuration](../experiments/logs/root-prism-free/f0-boolean-shared-prism-transfer-inventory-configuration01.json).
The
[mathematical transfer review](../experiments/logs/root-prism-free/f0-boolean-shared-prism-transfer-mathematical-review01.json)
records the literal conversion and its relation to the original
[one-edge](root_prism_free_f0_three_vertex_prism_cuts.md) and
[path](root_prism_free_f0_path_prism_results.md) results.

## Exact pruning against the accepted parent

The inventory checks actual native row receipts. It removes a proposed
row only when one of the audited implications proves that row from the
current parent and Boolean domains. It retains every other row. Failure
of these sufficient tests is not a claim of logical independence.

| Family | Distinct cases | Existing edge zero | Quota-one mixed equality | Inherited selector-pair conflict | Existing core-pair clique | Retained |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| One edge and third selector | 9,360 | 228 | 0 | 7,908 | 0 | 1,224 |
| Two-edge path | 107,418 | 8,664 | 37,278 | 2,112 | 1,368 | 57,996 |

The implication checks include all 4,410 inherited zero selector pairs:
4,320 follow from quota-one original Gram equations and 90 are explicit
motif conflicts. They also bind the current 1,884 literal edge zeros and
3,096 core-pair clique rows. The checker validates 28,690 distinct native
premise rows. It checks all 61,488 saved action references, covering the
61,476 paths retained in the older quotient census.

The one-edge disposition is counted per distinct edge/third-selector
case. It does not reuse the older counts of two endpoint moment
inequalities. Likewise, repeated quotient coordinates do not identify
distinct literal edge variables here.

The complete inventory retains every original witness origin, every
disposition, and its actual native premise rows. Its two proposal arrays
are deterministic and sorted. The intended append order is all 1,224
one-edge rows followed by all 57,996 path rows. Their literal native
definitions are:

| Family | Variable indices | Coefficients | Linear domain |
| --- | --- | --- | --- |
| One edge | `third`, `540 + edge_id` | `1, 1` | `[0, 1]` |
| Path | `center`, `540 + edge_min`, `540 + edge_max` | `-1, 1, 1` | `[-1, 0]` |

These rows contain 176,436 nonzero terms. Appending this family alone
would produce 227,270 rows with the same 68,934 variables. That count is
an inventory consequence, not acceptance of a newly constructed model.

## Completed execution and independent replay

The inventory owner completed in 6.067972451 seconds; the exact check
phase took 4.874730514 seconds. Its child exited successfully and was
reaped within the 45-second owner bound. The producer used a standard
protobuf decoder but built no native model and made no optimizer call.

The independent checker imports neither producer nor `CpModel` nor
`CpSolver`. It reconstructs all 116,880 saved six-site graphs, checks the
forced nonedges, native implications, complete origins, actual action
images, and both sorted proposal arrays. It reuses the hash-accepted
completeness of the old censuses rather than reenumerating their original
search spaces. Its check took 11.727374673 seconds and its owner took
12.120969063 seconds. The child exited with code zero and was reaped.

The independent terminal status is
`PASS_INDEPENDENT_COMPLETE_LITERAL_PRISM_TRANSFER`.
The accepted report and owner are
[report.json](../experiments/logs/root-prism-free/f0-boolean-shared-prism-transfer-inventory01-cold/report.json)
and
[owner.json](../experiments/logs/root-prism-free/f0-boolean-shared-prism-transfer-inventory01-cold/owner.json).
Their SHA-256 values are, respectively,
`be7b4c812e50fa9575d961022e05f8cdbe2f414f9d5c4c522eecf23faa7bd214`
and
`59fac819b0b425befc8107df85ecf972a425a8e9954e042121f92c07bbe77956`.

## Immutable publication

The
[artifact map](../experiments/logs/root-prism-free/f0-boolean-shared-prism-transfer-artifacts.json)
records both sources, configuration, mathematical and source reviews,
controls, root gates, complete inventory, all execution logs, and both
owner receipts. It excludes later append drafts and other prism families.

The complete inventory is stored as the lossless gzip
`f0-boolean-shared-prism-transfer-inventory01/complete-inventory.json.gz`.
Its 1,267,287 compressed bytes have SHA-256
`71d7f95f4c84e6b78192a9131f7934ce9eebbbdaf051c1b7580925317c4ed02b`.
Decompression gives exactly 6,530,786 bytes with SHA-256
`cde8cf5873e3bd224f188258f92060cdb029bff07e00bd571e86eda70cb0a8c6`.
Both source and replay read this compressed artifact directly.

The independent report also binds canonical JSON values of the two
proposal arrays. The one-edge array has SHA-256
`9b441e477b5efb86c197f01bbb8308b4bb1a6813c82896b2c5ca32306486720b`;
the path array has SHA-256
`afa12b69bfdcfc5c7265712c4704dac26d5a9f67465f3ba2ee2ad83c9ba6085c`.
These hashes allow a later append producer to reuse the complete accepted
transfer without repeating this graph reconstruction.
