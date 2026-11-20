# Six-root clique-pair scan at the 48-cut integer point

## Result

The corrected scan completed all 347 representatives of the six-root
clique-pair family. Their verified root actions cover all 3,283 candidate pairs.
All 3,785 union rows were checked to be zero with integer arithmetic before
their deletion. No additional quotient row was zero.

The scan found no exact negative direction and no unconfirmed numerical
negative. The smallest reported normalized numerical eigenvalue was
0.04029331716240285. This is a completed discovery scan, not an exact PSD
certificate or a graph-existence result.

The unchanged count point is
`prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json`,
SHA-256 `0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
The result does not rescan the 1,405 pairs covered by the separate quota-one
redundancy proof. It makes no pointwise PSD certification for those cases.

## Exact arithmetic and coverage

The domain is the complete frozen preparation in
[the clique-pair note](grid_free_order10_clique_pairs.md). All root, mask, clique,
and pair records remain present. Only the proved root-automorphism quotient
reduces direct scanning.

The driver contracts the existing six-, seven-, and eight-root scalar product
tensors using Python integers. Each representative matrix is the parent matrix
minus its single-class matrices plus its compatible double-class matrices.
Both allowed mutual-edge choices are included in each double matrix. Conditional
matrices and child matrices are cached only for the current root.

After exact symmetry and union-row checks, the driver tests the quotient. Its
numerical eigenvectors can only propose integer vectors. Any proposed separator
must have an exactly negative quadratic value in the full matrix. The signed
parent and child tensor contractions must then give the same exact value as an
induced-count form. Such a form remains ineligible for an optimizer until a
separate literal supported-product replay succeeds. No separator was found here,
so that reconstruction stage was not needed.

| Quantity | Result |
| --- | ---: |
| Direct representatives | 347 of 347 |
| Candidate pairs covered by congruence | 3,283 of 3,283 |
| Candidate roots completed | 18 of 18 |
| Union rows checked exactly zero | 3,785 |
| Exact negative directions | 0 |
| Unconfirmed numerical negatives | 0 |
| Scan time | 1.079 seconds |
| Total time including input loading | 3.047 seconds |
| Peak RSS | 276,448 KiB |

The run used one thread and a 60-second internal scan limit. It completed without
a timeout or error. It did not load the dense count reduction, generate a new
product tensor, or call an optimizer.

## Preserved first attempt and correction

The first driver asserted a minimal width of 1,224 columns for the six-root
scalar cache. The frozen cache instead has 6,535 columns because it retains
order-nine padding. Its actual nonzero support still lies within the first
1,224 order-eight columns.

That assertion stopped the first attempt at root 38, before any matrix
contraction or representative scan. It completed zero representatives and
provides no evidence about the point. Its source, preparation, result, and log
remain unchanged.

The separately named v2 driver accepts the actual padded width and checks the
order-eight support explicitly. Its complete diff passed coordinator review
before the single corrected run. The point, tensors, localizer formula, exact
acceptance conditions, and time limit were unchanged.

## Frozen files

All paths below are relative to `experiments/`.

* Original source: `workspace/grid_free_order10_clique_pair_scan.py`.
* Original preparation and result: `logs/moments-and-counts/order10-clique-pair-scan01-*`
  and `logs/moments-and-counts/order10-clique-pair-scan01.json`.
* Corrected source: `workspace/grid_free_order10_clique_pair_scan_v2.py`, SHA-256
  `683601c8f9d4a4bc26a5edbded76bdb447cca9e4b860f0bf191cb3fd60efc8f1`.
* Corrected preparation: `logs/moments-and-counts/order10-clique-pair-scan02-preparation.json`,
  SHA-256 `f21c8c93198bbfd4f4c1f10adfdb018b05118f1479bd77044c958eb321f2986c`.
* Corrected result: `logs/moments-and-counts/order10-clique-pair-scan02.json`,
  SHA-256 `c9fd07ed93b705e0ff5af393494f56cd63f0c975fb3cd5569729d8b84f573321`.
* The manifest `logs/moments-and-counts/order10-clique-pair-scan-manifest.json`
  binds both attempts, both coordinator reviews, and this note.
