# Clique-complement screening at the integer count point

All 711 prepared clique-complement representatives were screened at
the exact integer count witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
No exact separator or unconfirmed numerical negative was found.
The scan completed without a timeout or error.

The [complete domain and orbit preparation](grid_free_order10_complement_cliques.md)
shows these representatives cover all 3,939 remaining intersection
cliques, including all 530 retained triple groups. Each orbit transport
relabels root embeddings; no symmetry of a hypothetical 99-vertex
graph is assumed. Direct representative coverage and coverage by these
transports are stored separately in the result.

## Exact and numerical parts

Every cached tensor was contracted with labelled induced embedding
counts using Python integers. For each root, the driver formed its
parent moment matrix and the required sparse conditional congruences.
It then subtracted the selected conditional matrices for each clique.

All 7,607 designated selected rows in the representative matrices were
checked exactly zero before deletion. Sixteen representatives had
additional exact zero rows in the quotient. The separator routine
removed only exact zero rows, used a normalized numerical eigensystem
to propose negative directions, and would accept a proposed integer
vector only after its quadratic value was checked exactly negative.
No such direction occurred.

The smallest reported numerical eigenvalue among nonempty normalized
quotients was approximately 0.01859969234. This numerical screening is
not an exact PSD certificate. The result does not establish feasibility
of the whole moment cone or existence of an SRG(99,14,1,2).

The 3,245 shared-quota-one cliques were not directly scanned. Their
localizers are positive sums of child congruences using the SRG count
identities. The separate earlier scan screened all 916 scalar child
blocks at this same integer point without finding a separator. That
earlier result is bound by hash and reused here; it is also not an
exact PSD certificate.

## Coverage and runtime

| Quantity | Result |
| --- | ---: |
| Direct representatives completed | 711 of 711 |
| Remaining cliques covered by root congruence | 3,939 of 3,939 |
| Retained triple groups covered | 530 of 530 |
| Selected rows checked exactly zero | 7,607 |
| Exact negative directions | 0 |
| Unconfirmed numerical negatives | 0 |
| Scan time | 5.94 seconds |
| Total time | 6.96 seconds |
| Peak resident memory | 218,072 KiB |

The budget was 120 seconds with one numerical thread. Conditional and
child count matrices were retained only for the current root and then
released. Existing tensor domains were unchanged. No new tensor,
dense reduction, optimizer, or follow-up solve was used.

## Frozen artifacts

Source:
`experiments/workspace/grid_free_order10_complement_clique_scan.py`

Source SHA256:
`47b796f8b1610856ebb574c1332af2b1a1f72e81c3f61b72fb50acdb418dd73c`

Preparation:
`experiments/logs/moments-and-counts/order10-complement-clique-scan01-preparation.json`

Preparation SHA256:
`42a5560c13261329bc8f97f541b73d7ab1400d447ef0b735349c3e088ecede2f`

Result:
`experiments/logs/moments-and-counts/order10-complement-clique-scan01.json`

Result SHA256:
`fa29f914ac90bf06714df0e65a4a02d11bf972138d32a4c24ed14e91f2455467`

The preparation binds the domain, coefficientwise lift and orbit
ledgers; both scalar caches; the target integer witness; the earlier
child screening; and the coordinator's domain review. Every completed
representative has its selected masks, orbit size, quotient order,
zero-row check and numerical screening value saved.
