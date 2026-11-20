# Injective embedding bounds through order ten

The sequential ordinary-count bounds can subtract vertices already used
by an embedding. This improves all 549 saved core bounds. The repaired
prism-zero count point satisfies every improved bound, so these bounds
do not separate that point.

## Bound for one extension

Let `F` be a fixed pattern, let `S` be its already embedded vertices,
and let `v` be the next vertex. Write `N` for the neighbors of `v` in
`S`. In a hypothetical SRG(99,14,1,2), the number of available images
for `v` is at most the minimum of the following quantities:

- `99 - |S|`;
- `14 - |N_F(u) intersect S|`, for each `u` in `N`;
- `2 - 1_{uw in E(F)} - |N_F(u) intersect N_F(w) intersect S|`,
  for each pair `u,w` in `N`.

The second expression subtracts already used required neighbors of `u`.
The third subtracts already used required common neighbors. An edge
`uw` forces its images to be adjacent, so their common-neighbor quota
is one. A pattern nonedge can map to a host edge; two remains a valid
upper bound in either host case. No host nonadjacency is assumed.

If a quantity is negative, the partial embedding cannot occur. We use
zero as its extension bound. Multiplying the factors along a vertex
order bounds the number of labelled injective embeddings. Dividing by
the pattern's automorphism order and taking the floor bounds ordinary
copies. Subset dynamic programming finds the minimum product over all
vertex orders, because each factor depends only on `S` and `v`.

## Exact computation

`order10_embedding_bounds.py` checks all 76 labelled patterns on at
most four vertices against direct embeddings in the nine-vertex rook
graph. It also checks every vertex order for each control pattern.

The prism bound illustrates the improvement. An optimal order has
factors `99,14,1,12,1,1`, giving

\[
\#\text{prisms}\le\frac{99\cdot14\cdot12}{12}=1386.
\]

The earlier independent-factor bound was 3234. This agrees with the
separate elementary triangle-partner upper bound. It is an upper bound
and gives no positive prism minimum.

All 549 bounds improve strictly. The new-to-old ratios range from about
0.0124 to 0.7391. Every coordinate of the repaired prism-zero point
lies below its new bound; the largest count-to-bound ratio is below
0.44. The computation takes about five seconds and calls no optimizer.

The source, complete bounds, optimal orders, factors, input hashes, and
outcome are saved as:

- `experiments/workspace/order10_embedding_bounds.py`
- `experiments/logs/moments-and-counts/order10-injective-bounds.json`
- `experiments/logs/moments-and-counts/order10-injective-bounds.log`

Reproduction:

```sh
.venv/bin/python experiments/workspace/order10_embedding_bounds.py \
  --preparation experiments/logs/moments-and-counts/grid-free-order10-scaled-preparation.json \
  --witness experiments/logs/moments-and-counts/prism-zero-repair-witness.json \
  --output /tmp/order10-injective-bounds.json
```
