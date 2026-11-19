# Eight exact refutations in the direct literal master

The approved continuation produced eight distinct exact incidence candidates.
Each candidate passed the original equations and cuts, all current selector
rows, and all 18 local matching checks. Each then failed the exact shared-row
box system. The eight certificates supplied 96 new necessary selector rows.

The registry grew from 37 to 133 additional rows. The final 133-row prefix
has not been queried. No completed graph or whole-component exclusion was
obtained. The result applies to the declared F0 component type only.

## Accepted execution

The run owner accepted the result after 132.683472 seconds. The eight
CP-SAT calls used 90.538988 seconds in total. Each used a strictly
larger necessary-row prefix. There was no same-prefix retry, objective, hint,
fixed selector, exterior SAT call, or visit-based exclusion.

All eight shared separators used one original feasibility LP each. None
used the bounded fallback. Integer replay established each strict gap before
the 12 verified core transports were appended.

| Iteration | Queried additional rows | CP seconds | Shared seconds | Exact normalized gap | New rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00 | 37 | 10.591562 | 3.608930 | 1 | 12 |
| 01 | 49 | 12.653589 | 1.026611 | 1 | 12 |
| 02 | 61 | 11.518359 | 1.047130 | 1 | 12 |
| 03 | 73 | 10.456359 | 2.239023 | 1 | 12 |
| 04 | 85 | 11.626036 | 0.535798 | 3 | 12 |
| 05 | 97 | 10.762974 | 0.639714 | 2 | 12 |
| 06 | 109 | 12.060383 | 0.582039 | 1 | 12 |
| 07 | 121 | 10.869725 | 0.760152 | 1 | 12 |

## Separate replay

The separate cold owner accepted its report after 24.047594 seconds.
It invoked no optimizer and constructed no CP solver. It rebuilt every
called protobuf prefix, checked each saved 540-integer candidate, repeated
the 18 matching checks, replayed all eight shared certificates and lifts,
and checked every registry transition. Both owners reaped their children
and recorded no deadline overrun.

The final run registry and the independently replayed registry are byte
identical. Their file SHA256 is
`044d0a3fd566275a7bad263df9f11c35b065e8df250b2389e690d228731749ee`.
The canonical registry value SHA256 is
`8b0459cabaa9676f2591a4ad2251fad269a1ed05f8f687e0bbb4204a5b8ea2bd`.

The 133 additional rows imply 4,814 total native linear rows for the next
prefix. That prefix is a new strengthened model and requires its own bound
preparation before a query. The original 480 selectors and 60 radix variables
remain unchanged.

## Evidence

- [Complete run result](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01/result.json)
- [Run owner](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01/owner.json)
- [Cold report](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01-cold/report.json)
- [Cold owner](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01-cold/owner.json)
- [Compact exact summary](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01-summary.json)
- [Final certified registry](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01-cold/replayed-registry.json)
- [Raw protobuf restoration records](../experiments/logs/root-prism-free/f0-direct-master-continuation-run01-native-restoration.json)
