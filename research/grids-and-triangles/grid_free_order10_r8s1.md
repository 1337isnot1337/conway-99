# New order-ten induced moment cuts from eight-vertex roots

## Result and scope

The repaired prism-zero count witness violates eleven new order-ten
induced moment inequalities. Each violation has an integer-vector
certificate and a primitive integer linear form in the 550-coordinate
order-ten vector. A separate replay reconstructs the eleven matrices
directly from graphs and verifies every negative value and reduced form.

These blocks differ from the previously certified 1,416 blocks: their
products can involve ten vertices and their inequalities have nonzero
coefficients on new order-ten coordinates. They reject the saved witness
in this larger relaxation. They do not exclude every prism-zero count
point or settle graph existence.

All eleven inequalities are necessary for any SRG(99,14,1,2). The
particular prism-zero point selected the directions to test; the validity
of the resulting Gram inequalities does not depend on that point.

## Rooted binary flags

Fix an induced labelled eight-vertex root graph `H`. Include a constant
flag and one flag for each admissible outside-neighbor mask `m` with at
least three root neighbors. For a fixed embedding of `H` in a candidate
graph, the variable `f_m` counts outside vertices whose root-neighbor set
is exactly `m`.

Each `f_m` is zero or one. Two distinct vertices with that same mask would
have at least three common neighbors, contrary to the common-neighbor
bound. The moment matrix is the sum of the outer products of
`(1, f_m, ...)` over all labelled induced root embeddings, so it is PSD.

If `E(F)=Aut(F)c_F` is the number of labelled induced embeddings of a
catalogue graph `F`, its entries are:

\[
M_{00}=E(H),\qquad
M_{0m}=M_{mm}=E(H+m).
\]

For distinct masks `m,n`, the outside vertices must be distinct. Their
only unspecified edge is the edge between those two vertices. Therefore

\[
M_{mn}=\sum_{e\in\{0,1\}\text{ admissible}}E(H+m+n+e).
\]

The catalogue contains exactly the graph types needed for these products.
The chosen flag family omits masks with fewer than three neighbors; the
cache is complete for the stated family, not for every conceivable
rooted moment construction.

## Efficient exact construction

The initial builder identifies each one-vertex flag through the existing
catalogue child table. It constructs and verifies an explicit graph
isomorphism to that child's stored representative. The second neighbor
mask is transported through that isomorphism and looked up in the child's
extension table, with and without the outside edge.

Thus the builder avoids canonicalizing every ten-vertex graph separately.
Every transport is checked on the full adjacency relation. It also
checks directly that two distinct outside vertices cannot realize the
same high-neighbor mask.

Every entry is an exact sum of at most two labelled induced counts. The
generation verifies an absolute product bound before using signed 64-bit
matrix storage. Approximate eigensystems only propose integer vectors.
All accepted quadratic values and all contractions to linear count forms
use integer arithmetic.

Only after an integer negative direction is found does the source load
the reduced order-ten forms. It contracts that single quadratic form
through sparse catalogue weights. It does not multiply an entire dense
matrix of moment entries by all 550 reduced coordinates.

## Direct positive controls and exact replay

Two controls use the nine-vertex rook graph. Their seven-vertex roots
omit either an adjacent pair or a nonadjacent pair. The code enumerates
root embeddings directly, forms each binary flag vector, and sums its
outer product. These matrices exactly equal the extension formula.

| Omitted rook vertices | Root catalogue type | Root embeddings | Flags |
| --- | ---: | ---: | ---: |
| 0, 1 | 306 | 72 | 3 |
| 0, 4 | 304 | 72 | 11 |

The separate negative-certificate replay does not use the transport
builder. For each of the eleven matrices it explicitly constructs the
one- and two-extension graphs, checks every pair quota, identifies their
catalogue types by graph canonicalization, and reconstructs the complete
tensor and integer matrix. It then checks the saved vector, induced-count
form, 550-coordinate form, and strict negative value. The replay took
33.358 seconds and used no eigensystem or optimizer.

## Eleven certified cuts

The values below are those of the primitive integer forms in the full
550-coordinate core vector at the repaired witness.

| Root type | Matrix order | New-coordinate support | Exact cut value |
| --- | ---: | ---: | ---: |
| 779 | 21 | 127 | -324,647,805 |
| 851 | 20 | 195 | -400,814,210 |
| 854 | 17 | 104 | -72,270,192 |
| 888 | 18 | 196 | -549,919,198 |
| 993 | 17 | 164 | -136,580,637 |
| 1015 | 20 | 105 | -89,503,617 |
| 1018 | 26 | 139 | -128,681,699 |
| 1026 | 59 | 317 | -1,605,384,489 |
| 1033 | 8 | 24 | -1,367,978 |
| 1060 | 29 | 323 | -707,459,885 |
| 1146 | 24 | 186 | -359,067,209 |

The original scan finished in 50.337 seconds, within its 180-second
bound. It processed all 897 positive-count eight-vertex roots and
recorded the 19 zero-count roots separately. There were no unresolved
numerical negative directions. Its point-specific cache omits zero flag
rows after checking that all corresponding child counts are zero.
Passing this scan would not by itself certify PSD, and this pruned cache
must not be treated as the complete family at a different point.

## Complete cache for later proposals

A separate generation supplies a point-independent cache. It disables
all zero-root and zero-flag pruning and includes every admissible
high-neighbor mask for all 916 root types.

| Property | Complete cache |
| --- | ---: |
| Root blocks | 916 |
| Nontrivial blocks | 911 |
| Largest flag set | 220 |
| Lower-triangle entries | 1,383,645 |
| Tensor nonzeros | 1,151,532 |
| Verified label transports, including controls | 39,105 |
| Generation time | 7.011 s |
| Compressed bytes | 3,127,487 |

This cache has no count-witness dependency. Any later numerical point
must be evaluated on this full cache, or explicitly described as testing
only a smaller fixed family. Exact zero rows may be removed dynamically
after checking their entries at the new point.

## Files and hashes

Sources in `experiments/workspace/`:

- `grid_free_order10_r8s1.py`: initial exact construction and separation.
- `grid_free_order10_r8s1_replay.py`: direct graph reconstruction and exact
  cut replay.
- `grid_free_order10_r8s1_full_cache.py`: complete point-independent cache.

The generator SHA-256 is

```text
77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469
```

The replay source SHA-256 is

```text
c58b437172a85386f5b10da6d16a7609c9ae547cd7eddd6e9cd0ab3fedb2c44e
```

The full-cache source SHA-256 is

```text
25e9cebb9593311e0a852e84bd9e0f2798eb9eba0e0b4811a3c85561af03aa83
```

Artifacts are under `experiments/logs/moments-and-counts/`. The initial
result, pruned cache, log, and direct replay use prefix
`prism-zero-order10-r8s1`. The point-independent cache is
`order10-r8s1-full-blocks.pickle.gz`, with metadata and log named
`order10-r8s1-full-cache`. A package manifest binds all files.

The full-cache SHA-256 is

```text
aecf7411230f718c8c3879c38ad39dcdb041ed07c58a799f8b044ebd0ab5028d
```

Replay the eleven exact cuts with:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_r8s1_replay.py \
  --certificate experiments/logs/moments-and-counts/prism-zero-order10-r8s1-result.json \
  --output /tmp/prism-zero-order10-r8s1-replay.json
```
