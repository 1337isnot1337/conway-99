# Prism-free clique screening at the integer count point

All 1,225 prepared prism-free clique representatives were screened at
integer count witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
The run found no exact separator or unconfirmed numerical negative.
It completed within the 60-second limit, without a timeout or error.

The [conditional domain preparation](grid_free_order10_complement_prism_domains.md)
proves these representatives cover all 4,584 remaining cliques by root
relabeling. It also records covers for all 530 residual-two triple
groups. The scanner retains the multiplicities of those covers,
including the 12 groups that ceased to be maximal.

## Scope and exact checks

These inequalities assume global prism-freeness, meaning ordinary core
coordinate x₁ is zero. The scanner checked that coordinate and all
1,443 required prism-containing induced counts exactly. It bound the
proved zero-closure ledger and the successful cold replay of the raw
conditional-row supports.

Every scalar tensor contraction used Python integers. The scanner
checked structurally absent parent rows at every processed root and
all 10,672 selected rows before deleting them. It then used numerical
eigensystems only to search for negative integer directions. Any
accepted direction would require both a strictly negative exact
quadratic value and the same value from its expanded induced-count
form. No direction reached that stage.

Three representatives had additional exact zero rows in their
quotients. The smallest reported numerical value was zero. This
screening is not an exact PSD certificate, and it does not establish
feasibility of the complete moment problem or existence of a graph.

The 1,378 shared-quota-one cliques were not directly scanned. Their
localizers are positive sums of child congruences using the exact
common-neighbor identities. The earlier scalar-child screening at the
same integer point is bound by hash and reused; it is not an exact
PSD certificate either.

| Quantity | Result |
| --- | ---: |
| Direct representatives completed | 1,225 of 1,225 |
| Remaining cliques covered by root congruence | 4,584 of 4,584 |
| Triple groups covered, with multiplicity | 530 of 530 |
| Required prism counts checked exactly zero | 1,443 |
| Selected rows checked exactly zero | 10,672 |
| Exact negative directions | 0 |
| Unconfirmed numerical negatives | 0 |
| Scan time | 24.12 seconds |
| Total time | 30.58 seconds |
| Peak resident memory | 240,496 KiB |

The run used one numerical thread and per-root child/conditional
matrix caches. No existing domain was changed. It generated no new
product tensor, loaded no dense reduction, called no optimizer and
launched no follow-up scan. Earlier unconditional clique packages
remain unchanged.

## Frozen artifacts

Source:
`experiments/workspace/grid_free_order10_complement_prism_scan.py`

Source SHA256:
`a03e862589bea386e8fb65a10ed38e3649abbc953cf55880ea18cd8176b0a2b9`

Preparation:
`experiments/logs/moments-and-counts/order10-complement-prism-scan01-preparation.json`

Preparation SHA256:
`ee8ba618b895ec14a6a605c31918a04d6954b3d5d7946a4526d507c9c8388de7`

Result:
`experiments/logs/moments-and-counts/order10-complement-prism-scan01.json`

Result SHA256:
`aa24b79ae676444b10327327a284f54da5dc78f9efe3070c91381830176c4c4a`

Every representative record retains its selected masks, orbit size,
quotient order, exact zero-row check and numerical screening value.
Direct scans and coverage by congruence are recorded separately.
Any future negative form from this family must retain its prism-free
scope and pass a fresh supported-product reconstruction before use
in an optimizer.
