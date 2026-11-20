# An integer-incidence obstruction for the ten-high core

## Result

The specified sixteen-vertex core cannot occur with zero or one edge among its ten high vertices.
This excludes 31 labelled cores above one fixed high-mask configuration.
It does not resolve the existence of an SRG(99,14,1,2).

The proof below is independent of an optimizer, a signature census, and the failed local workspace.
The [standalone checker](../../experiments/workspace/high_graph_core16_recovery_check.js)
and its [exact output](../../experiments/logs/moments-and-counts/order10-high-graph-core16-recovery-check.json)
are included in this checkpoint.

## The core

Let C be six independent vertices.
The ten other vertices have the following neighborhoods in C, written as six-bit masks:

```text
7, 11, 21, 26, 28, 38, 41, 44, 49, 50
```

Each mask has size three.
Each root occurs in five masks, and each pair of roots occurs in two masks.
Let H be the graph on these ten high vertices.
Write e for its edge count and w for the sum of binom(deg_H(a),2) over its vertices.

Every vertex outside the core has at most one neighbor in C.
Indeed, every pair in C already has its required two common neighbors among the ten high vertices.

## Counting proof

For an outside vertex x, let r_x count its neighbors in C and let t_x count its neighbors in H.
Since r_x is zero or one,

```text
r_x - r_x*t_x + t_x*(t_x-1)/2
  = (t_x-r_x)*(t_x-r_x-1)/2 >= 0.
```

The final inequality holds for every integer t_x-r_x, including negative values.

The residual degree and common-neighbor counts give:

| Sum over the 83 outside vertices | Exact value |
| --- | ---: |
| sum r_x | 54 |
| sum r_x*t_x | 90 - 6e |
| sum binom(t_x,2) | 30 - e - w |

For the first row, each root has nine remaining neighbors.
For the second, sum the mixed root/high common-neighbor quotas.
There are sixty such pairs, thirty core adjacencies, and 6e two-step walks within the core.
For the third, sum the high/high quotas.
The six roots contribute 6 binom(5,2)=60 internal two-step walks, and H contributes w more.

Adding these identities proves

```text
5e(H) - sum_a binom(deg_H(a),2) >= 6.
```

When e=0, the left side is zero.
When e=1, it is five.
Both cases are impossible.

## Equivalent Gram certificate

For the literal core adjacency matrix B, set G=12I-B-B^2+2J.
Any extension gives G=XX^T, where the columns of X are its outside attachments.
Let v be minus one on the six roots and plus one on the ten high vertices.
Then

```text
(v^T G v - v^T diag(G))/2
  = sum_outside (v^T h)*(v^T h-1)/2 >= 0.
```

For the empty high graph, the first and second moments are 56 and 44.
The certificate value is minus six.
For each eligible single edge, the moments are 54 and 52.
The certificate value is minus one.

Thirty high-mask pairs intersect in one root.
The other fifteen pairs intersect in two roots and cannot be adjacent.
The checker enumerates every eligible single edge and checks all visible common-neighbor caps.
It then checks the negative Gram value directly on each literal adjacency matrix.
A [separate evaluation](../../experiments/logs/moments-and-counts/order10-high-graph-core16-recovery-root-replay.json)
reproduces the saved output.

## Reproduction

```sh
node experiments/workspace/high_graph_core16_recovery_check.js
```

The pure checker function was executed twice in separate JavaScript evaluations before publication.
Its Node command uses no dependencies or input files.
