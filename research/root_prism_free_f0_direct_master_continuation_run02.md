# Second direct-master continuation: eight exact refutations

The second continuation produced eight further exact incidence candidates.
Each passed the original equations and cuts, all current selector rows, and
all 18 local matching checks. Each then failed the exact shared-row box
system. The eight integer certificates supplied 96 new necessary rows.

The starting 157-row registry retained every previously accepted row and
the 24 accepted local pair-packing rows. The registry grew to 253 additional
rows. The final 253-row prefix has not been queried. This run constructs no
completed graph and does not exclude the declared F0 component type.

## Accepted execution

The run owner accepted the result after 222.329297 seconds. The eight
CP-SAT calls used 150.050339 seconds in total. Each later call had a
strictly larger certified row prefix. The source, seed configuration,
per-call bound, cumulative native bound, and row cap remained frozen.

| Iteration | Queried additional rows | CP seconds | Shared seconds | Exact normalized gap | New rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00 | 157 | 22.726210 | 3.825141 | 3 | 12 |
| 01 | 169 | 17.286449 | 0.979292 | 4 | 12 |
| 02 | 181 | 16.864222 | 6.280681 | 447 | 12 |
| 03 | 193 | 19.628222 | 0.682251 | 1 | 12 |
| 04 | 205 | 17.955711 | 3.543021 | 1 | 12 |
| 05 | 217 | 23.485390 | 3.489410 | 1 | 12 |
| 06 | 229 | 16.029301 | 1.190538 | 2 | 12 |
| 07 | 241 | 16.074835 | 4.412484 | 49 | 12 |

The shared separators made 8 original feasibility calls and
0 bounded-potential fallback calls. Exact integer replay preceded every
12-action universal lift. No native infeasibility status supplied a proof.

## Separate replay

The cold owner accepted its report after 21.853439 seconds. It invoked
no optimizer and constructed no CP solver. It reconstructed every called
native prefix, checked every saved 540-integer candidate, repeated the
matching checks, and replayed all eight exact shared certificates, lifts,
and registry transitions. Both owners reaped their children and recorded
no deadline overrun.

The final run registry and cold replayed registry are byte identical. Their
file SHA256 is
`b19c520815cb657184625ee8c7cd57b794364a71eff9fcfb57f0e7429604a11b`.
The canonical registry value SHA256 is
`60b1fb603fac83d953f87a51ae5e9675c40f1a79d0e1a4855d70839e2255dc98`.

The unqueried final prefix has 4,934 native linear rows. A later prefix
must preserve all 253 accepted additional rows. The frozen 256-row cap
leaves only three places, so a larger later batch requires an explicit
source adaptation. It cannot be truncated to fit.

## Evidence

- [Complete run result](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02/result.json)
- [Run owner](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02/owner.json)
- [Cold report](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02-cold/report.json)
- [Cold owner](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02-cold/owner.json)
- [Compact exact summary](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02-summary.json)
- [Final certified registry](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02-cold/replayed-registry.json)
- [Native restoration records](../experiments/logs/root-prism-free/f0-direct-master-continuation-run02-native-restoration.json)
