# Compact continuation: nine incidences and a later exact ray repair

The one authorized compact continuation stopped after 19.478958
seconds. It generated nine exact incidence selections. Fifteen
individual-row certificates rejected the first eight. The ninth
passed all sixty individual row boxes, but the original shared-edge
helper did not reconstruct an exact ray from its numerical
infeasibility answer. The run therefore stopped as UNKNOWN.

All sources, numerical evidence, cut registries, candidates, and
the UNKNOWN result remain unchanged. A separate optimizer-free
calculation later recovered an exact shared-row certificate for
the ninth selection. It is documented in
`root_prism_free_f0_shared_ray_repair.md`.

## Bounded run

| Iteration | SAT seconds | Exact individual obstructions | Exact row boxes | Added transported cuts |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0.142407 | 2 | 58 | 24 |
| 1 | 0.038536 | 1 | 59 | 12 |
| 2 | 0.032220 | 1 | 59 | 12 |
| 3 | 0.032361 | 3 | 57 | 36 |
| 4 | 0.039208 | 3 | 57 | 36 |
| 5 | 0.032864 | 2 | 58 | 24 |
| 6 | 0.100691 | 2 | 58 | 24 |
| 7 | 0.053134 | 1 | 59 | 12 |
| 8 | 0.062819 | 0 | 60 | 0 |

Every candidate passed the original exact Gram, occupancy, and
motif checks and all inequalities present at its generation. The
nine complete row passes contain fifteen exact integer obstructions
and 525 exact rational boxes. The obstructions supplied 180 new
transported inequalities. No numerical-only cut was added.

The loop retained its prepared limits: twenty incidences, ten
seconds per SAT query, sixty seconds per row pass or shared LP,
and 180 seconds overall. It stopped at the uncertified shared
answer, not at an encoding or time limit. Peak recorded memory
was 341,520 KiB.

The terminal formula has 142,980 variables and 951,630 clauses.
It retains 348 individual weighted inequalities and 24 signed
shared inequalities, plus the twelve earliest direct row cuts.
Its SHA256 is
`54f953de7e126071714a2b42b01328f2578d382178ad599500cf47c27a693cd7`.
The result file SHA256 is
`ecc80a941a1b0d9e152788167210a5e8b7936f28b03ee50c35658895b453d3d3`.

## Separate later certificate

The frozen numerical ray for iteration eight has 2,368 entries.
Rounding only its 1,140 unrestricted equality multipliers and
setting each upper-bound multiplier to the exact primary-column
deficit gives a valid integer Farkas certificate. Its exact right
side is $-26$. This uses the saved numbers only as proposals;
every accepted sign and strict inequality is checked in integers.

The certificate excludes the ninth fixed selection. Its potential
lift gives twelve necessary inequalities over the complete free
480-signature domain. None is inserted into the frozen terminal
formula. A later continuation must explicitly seed and encode
them under a new source and model hash.

## Cold replay and limits of the conclusion

The cold terminal replay regenerated the prior provenance chain,
the exact compact starting formula, all nine candidate prefixes,
the fifteen accepted individual obstructions, 525 rational boxes,
and the final CNF hash. It also checked the stored unresolved
shared-row record. No solver or optimizer was called during this
replay. The later repaired certificate has its own separate pure
exact replay.

No incremental or fresh UNSAT answer occurred, so no DRAT proof
or component exclusion is claimed. The run concerns component
zero in the globally prism-free and $F$-free split $18+18$ case.
All 480 selectors remain free; neither a second component nor
its incidence or alignment was fixed. No full graph or completed
exterior graph was constructed.
