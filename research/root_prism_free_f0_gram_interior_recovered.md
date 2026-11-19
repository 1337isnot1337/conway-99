# Recovered F0 base Gram interior point

## Result and scope

The component-0 base Gram and motif constraints cannot fix any of the 480 selectors.
An exact average of 1,836 binary feasible incidences proves this.
Every coordinate is strictly between zero and one, and every motif inequality has strict slack.

This result concerns the base system only.
It does not claim that the point satisfies later capacity cuts.
It does not construct a graph or exclude the F0 component.

## Exact point

The published quadratic-allocation preparation contains 153 saved incidences and twelve checked core actions.
Each incidence selects sixty triple signatures.
The new [JavaScript checker](../experiments/workspace/root_prism_free_f0_gram_interior_recovery.js)
applies every action and checks each resulting incidence directly.

All 1,836 incidences are distinct.
Every incidence satisfies the complete 18-by-18 exterior Gram matrix and all ninety motif conflicts.
The checker reconstructs all 480 triples from the literal 21-vertex core.

Let c_a be the number of incidences containing selector a.
The exact point is x_a=c_a/1836.
The [certificate](../experiments/logs/root-prism-free/f0-gram-interior-recovery-certificate.json)
contains all 480 integer numerators.

| Quantity | Exact value |
| --- | ---: |
| Minimum numerator | 24 |
| Maximum numerator | 851 |
| Common denominator | 1,836 |
| Minimum coordinate | 2/153 |
| Maximum coordinate | 851/1836 |
| Minimum motif slack numerator | 1,505 |
| Maximum motif slack numerator | 1,711 |

The counts sum to 60 times 1,836.
A separate calculation from the final 480 coordinates checks all 171 upper-triangular Gram equations.
Each motif inequality has the form x_a+x_b<=1 and has positive slack.

## Consequence

Suppose the Gram equations are Cx=b.
A combination y^T C>=0 with y^T b=0 satisfies

```text
0 = y^T b = sum_a (y^T C)_a x_a.
```

Every x_a is positive, so every coefficient in y^T C must vanish.
Such a combination cannot force a selector absent.

The binary incidences give a stronger direct check on fixed selectors.
Every selector occurs in at least 24 incidences and is absent from at least 985.
Thus neither value is forced by the base binary constraints.

## Recovery and reproduction

The local Python certificate became inaccessible before publication.
This replacement was rebuilt from the two already published gzip inputs.
Their SHA-256 digests were checked during retrieval.
The pure JavaScript checker then recomputed every incidence and the exact average.

The CLI uses only standard Node modules and checks both input digests again:

```sh
node experiments/workspace/root_prism_free_f0_gram_interior_recovery.js
```

The pure checking function ran successfully in the available JavaScript runtime.
The Node filesystem wrapper could not be executed while the workspace was unavailable.

The [peer review](../experiments/logs/root-prism-free/f0-gram-interior-recovery-peer-review.json) read the complete source and checked all 480 certificate numerators independently.
It did not repeat the complete input retrieval or incidence execution.
