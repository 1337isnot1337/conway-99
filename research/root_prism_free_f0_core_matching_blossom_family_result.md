# Core matching blossom family: complete result

The complete finite census and its separate cold replay passed. The family
contains 8,894 normalized integer inequalities on the existing reduced
exterior-edge count coordinates. Of these, 6,854 are not implied by the
specified saved packing and variable bounds alone. This comparison is not
a proof of independence from the full F0 model.

## Coverage and arithmetic

| Item | Exact count |
|---|---:|
| Fixed core sites | 18 |
| Literal three-sets classified | 549,480 |
| Three-sets missing an eligible edge | 411,024 |
| Remaining three-sets with a proved-zero edge | 31,872 |
| Live three-edge cliques | 106,584 |
| Distinct normalized rows | 8,894 |
| Rows implied by the saved packing/domain boxes | 2,040 |
| Rows outside that box comparison | 6,854 |
| Nonzero coefficients in all rows | 26,662 |
| Nonzero coefficients in the selected 6,854 rows | 20,542 |

All 18 core chunks completed. There are 8,874 three-column rows and 20
two-column rows. Coefficients are positive and at most two. Right-hand
sides are twelve for 8,870 rows and six for 24 rows.

The raw certificates occupy 13,718,529 bytes; the eighteen compressed
chunks occupy 2,871,607 bytes. Every live literal clique has a row
reference. Every distinct row has a literal witness and all twelve actual
core transports. No row was dropped because of its value at a point.

The census took 15.51 seconds under its 60-second owner, including a
15.22-second child. The separate cold owner took 20.80 seconds, including
a 20.55-second child. Both children exited with code zero and were reaped.
There was one invocation of each stage and no retry.

The cold pass checked all 549,480 triple dispositions, all 106,584 live
clique references, and all 8,894 normalized rows. Its independent
coefficient contraction transported 17,730 distinct literal edges through
the actual core actions.

## Mathematical scope

For each fixed core site, eight selected exterior neighbors require
pairing inside their common neighborhood. A matching contains at most
one of the three possible edges on any three vertices. Summing this
inequality over the twelve core relabelings yields an integer population
row. The [single-row proof](root_prism_free_f0_core_matching_blossom.md)
and [family preparation](root_prism_free_f0_core_matching_blossom_family.md)
give the normalization and coverage argument.

The original 4,416 literal inequalities contain selector variables only,
so none is an identical edge-count row. No new row is identical to a
saved unary packing row. Exactly 2,040 rows are implied by the saved
single-orbit packing boxes; the same 2,040 are implied by the explicitly
bound final domain boxes. All remain in the full certificate.

Other combinations of old rows, local tables, and Fourier relations were
not tested for implication. No production point was evaluated. The
current native model was not changed.

## Compact inventory and omission proof

The [inventory producer](../experiments/workspace/root_prism_free_f0_core_matching_blossom_inventory.py)
copies rows from the cold-checked chunks. It does not regenerate the
family. Its output is
[the compact inventory report](../experiments/logs/root-prism-free/f0-core-matching-blossom-inventory01/report.json),
which binds three compressed files:

- `all-rows.json.gz`: all 8,894 rows;
- `selected-rows.json.gz`: the 6,854 rows outside the explicit-box comparison;
- `omitted-rows.json.gz`: the complete complementary 2,040 rows, each with
  the actual saved coordinate upper bounds and exact activity at those bounds.

Each row retains its global ID and a witness reference containing the
proof-chunk index and the index in that chunk's `new_rows` list. Every
chunk's compressed and raw SHA256 is bound in each compact file.

The extraction checked that the two selections partition all 8,894 row
IDs exactly. Since every coefficient is positive, an omitted row is
valid on the saved box whenever its exact upper-bound activity is at
most its right-hand side. A later native overlay must verify that its
actual coordinate upper bounds do not exceed the saved bounds. The
inventory report has SHA256
`5e5ba4687a85c30d75647c54e76b5713caa295f2a9e77f8722f10c3e8dd4382d`.

The [bound point-scan adapter](../experiments/workspace/root_prism_free_f0_core_matching_blossom_point_scan.py)
fixes that report hash and the inventory source hash. It can later
contract all 8,894 rows against a plain array of exactly 32,296 integers.
This is an exact row evaluation only. It does not replace the count
acceptance receipt, literal decoder, or exterior-edge realization.
No candidate has been supplied and this adapter has not been run.

## Immutable records

The complete census is
[the family result](../experiments/logs/root-prism-free/f0-core-matching-blossom-family-run01/result.json),
SHA256 `901ead85d602598336d1031f1ebc58cacf18ab9c258cd73654b04c6eca635b86`.

The separate
[cold record](../experiments/logs/root-prism-free/f0-core-matching-blossom-family-run01-cold.json)
has SHA256 `664074cc423d925778e3e4e4898db996fdec0f30c6e0bf633b5e2a74ca796bc1`.
It records both complete producer coverage and complete checked coverage.

The coordinator's source gate is
[the frozen review](../experiments/logs/root-prism-free/f0-core-matching-blossom-family-root-gate01.json),
SHA256 `976e31eec53c14dd95ab21137935b9b7c052891de0bce72f11dabd25fdcc4331`.
