# Complete visible-clique screening at the integer count point

All 811 representatives from the complete visible pair-incompatibility
graphs were screened at integer count witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
No exact separator or unconfirmed numerical negative was found. The
run completed without a timeout or error.

The [frozen domain preparation](grid_free_order10_complement_visible_domains.md)
covers all 3,821 remaining maximal cliques by explicit root relabelings.
Those cliques include all 530 residual-two triple groups. The quotient
assumes no symmetry of the hypothetical 99-vertex graph. Direct scans
and coverage by root congruence are counted separately in the result.

## Exact checks and limits

The driver contracted both scalar caches with labelled induced
embedding counts using Python integers. It formed each localizer by
subtracting its conditional congruences from the parent moment matrix.
All 8,187 selected rows were checked exactly zero before deletion.
Nineteen representatives had additional exact zero quotient rows.

The negative-direction routine used normalized numerical eigenvectors
only as proposals. It would accept an integer direction only after an
exact negative quadratic evaluation and an exact induced-count form
contraction. No proposed negative required that follow-up. The smallest
reported numerical eigenvalue in a nonempty normalized quotient was
approximately 0.01859969234.

This is a completed no-separator result. It is not an exact PSD
certificate, a feasibility certificate for the full count problem, or
an existence proof for the Conway graph.

The 1,553 shared-quota-one cliques were not directly scanned. Their
localizers follow from the child PSD family and the common-neighbor
count identities. The earlier complete screening of all 916 child
scalar blocks at the same integer point is bound by hash and reused.
That screening also makes no exact PSD claim.

| Quantity | Result |
| --- | ---: |
| Direct representatives completed | 811 of 811 |
| Remaining cliques covered by root congruence | 3,821 of 3,821 |
| Retained triple groups covered | 530 of 530 |
| Selected rows checked exactly zero | 8,187 |
| Exact negative directions | 0 |
| Unconfirmed numerical negatives | 0 |
| Scan time | 5.15 seconds |
| Total time | 5.86 seconds |
| Peak resident memory | 211,888 KiB |

The budget was 120 seconds with one numerical thread. Conditional and
child count matrices were cached only for the current root. Existing
tensor domains were unchanged. No new product tensor, dense reduction,
optimizer or follow-up solve was used.

## Frozen artifacts

Source:
`experiments/workspace/grid_free_order10_complement_visible_scan.py`

Source SHA256:
`69820e86ccc281f944d9eca36864f2f1670b1dfa3e46adf128deab13911d69d4`

Preparation:
`experiments/logs/moments-and-counts/order10-complement-visible-scan01-preparation.json`

Preparation SHA256:
`d328f1a28be7d3424a0746a2e4227a418e04213611586778955603d8c52b7a6e`

Result:
`experiments/logs/moments-and-counts/order10-complement-visible-scan01.json`

Result SHA256:
`d7a59f33b162ef78a0b1b0be68ccbfaa9c36269de18e2870915bd7cb0368b82e`

The preparation binds the complete visible-domain ledger, both scalar
caches, the target integer witness, the earlier child screening and
the coordinator's source review. Each completed representative retains
its masks, orbit size, quotient order, exact zero-row check and
numerical screening value. The previous 711-representative scan and
its artifacts remain unchanged.
