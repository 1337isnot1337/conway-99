# Original-count audit of the repaired 47-cut witness

The repaired order-ten count witness passes an independent exact audit
of its original count equations, prism-zero conditions, ordinary-count
bounds, and 47 saved linear inequalities. This establishes the listed
finite arithmetic conditions. It does not certify positive
semidefiniteness or construct a graph.

The new source is
[audit_prism_zero_held_count_witness.py](../../experiments/workspace/audit_prism_zero_held_count_witness.py).
The earlier witness-audit sources remain unchanged. The new audit imports
only the original identity generator and the direct prism detector. It
loads the original graph catalogue, not a dense reduced count matrix.

## Exact checks

| Check | Result |
|---|---:|
| Saved nonnegative integer induced counts | 48,965 |
| Nonnegative integer core-coordinate values, including the constant | 550 |
| Original count equations | 180,445 |
| Nonzero equation coefficients evaluated | 2,893,280 |
| Totals for graph orders zero through ten | 11 |
| Prism-containing induced types checked directly to have count zero | 1,443 |
| Ordinary prism-containing coordinates checked to be zero | 58 |
| Ordinary-count upper bounds | 549 |
| Exact saved linear inequalities | 47 |

For every order $n=0,\ldots,10$, the induced counts sum to
$\binom{99}{n}$. Every original identity has residual zero.
The smallest value among the 47 inequalities is 3,193.
All arithmetic uses unbounded Python integers; the largest absolute
single term in a held inequality is 447,792,346,386.

The audit also compares the repaired vector with the preceding rounded
vector. The only changed core coordinate is

\[
x_{525}:119\longrightarrow118.
\]

The repaired point has $x_{521}=88$. This is the prism-zero count
witness; it is not on the additional $x_{521}=0$ face.

The audit completed in 5.13 seconds without an optimizer.

## Bindings and scope

The audited
[witness](../../experiments/logs/moments-and-counts/prism-zero-order10-r6s2-repair01-witness.json)
has SHA256
`190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d`.
The 47 coefficient rows are read from the bound
[loop record](../../experiments/logs/moments-and-counts/prism-zero-order10-r6s2-loop01.json),
whose SHA256 is
`08366598ad71e2942e1cd1ea877616bd85c636f87a2c607e991834016a61644b`.

The
[audit report](../../experiments/logs/moments-and-counts/prism-zero-order10-r6s2-repair01-original-count-independent-audit.json)
also records the original catalogue, bound preparation, identity-source,
prism-helper, and preceding-vector hashes. It stores every level total
and every held-inequality value.

The induced counts are checked directly against the original equations.
The ordinary coordinates are checked against their saved bounds, zeros,
and held rows. This audit does not rederive the coefficient map between
those two descriptions or the reduction producing the 47 coefficient
rows. Those are separate certificate dependencies. No PSD scanner or
repair routine is imported, and no PSD feasibility claim is made.

## Replay

The catalogue argument is the original order-ten catalogue produced by
the repository's existing `subgraph_counts.build(10)` routine. Its
expected hash is checked before use.

```sh
.venv/bin/python experiments/workspace/audit_prism_zero_held_count_witness.py \
  --witness experiments/logs/moments-and-counts/prism-zero-order10-r6s2-repair01-witness.json \
  --sha256 190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d \
  --cuts experiments/logs/moments-and-counts/prism-zero-order10-r6s2-loop01.json \
  --cuts-sha256 08366598ad71e2942e1cd1ea877616bd85c636f87a2c607e991834016a61644b \
  --expected-cut-count 47 \
  --catalogue /tmp/conway99-order10-catalogue.pickle \
  --initial experiments/logs/moments-and-counts/prism-zero-order10-r6s2-loop01-round1-rounded-counts.json \
  --initial-sha256 1e9c60d376b35a4b5bf41c06f7ae89036d431a9a05c1b498f08372154f236fa5 \
  --expect-change 525 119 118 \
  --output /tmp/prism-zero-47cut-original-count-replay.json
```
