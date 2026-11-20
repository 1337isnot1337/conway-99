# Exact triangle inequalities for binary flags

Both saved prism-zero count points pass 170,183,860 exact inequalities
from three binary flags. The scan uses every root in the complete
916-root, order-ten cache. It finds no new cut at either point.

The first point is the repaired count witness with `x549=6`. The second
is the rounded witness from the zero-closure IPM loop, with `x521=116`.
The result concerns this specified quadratic family. It does not certify
all moment matrices or construct a graph.

## The four inequalities

Fix a labeled induced root on eight vertices. A one-vertex flag records
the exact neighbors of an outside vertex in that root. If its mask has
at least three neighbors, at most one outside vertex can have that mask:
two such vertices would share at least three neighbors. Therefore each
flag variable `X_i` takes values zero or one at each rooted embedding.

For three distinct flags, the following polynomials are nonnegative:

\[
\begin{aligned}
1-X_i-X_j-X_k+X_iX_j+X_iX_k+X_jX_k&\ge0,\\
X_i-X_iX_j-X_iX_k+X_jX_k&\ge0.
\end{aligned}
\]

The second expression has three versions, one for each choice of the
distinguished flag. The first expression equals `q(q-1)/2` for
`q=X_i+X_j+X_k-1`. The version distinguished by `i` has
`q=-X_i+X_j+X_k`. These are integer-valued expressions, so their products
with the preceding integer are nonnegative. An exhaustive eight-row
truth table checks all four formulas.

Sum each polynomial over the labeled embeddings of its root. With `M`
the induced moment matrix and its constant feature indexed by zero,
the inequalities become

\[
\begin{aligned}
M_{00}-M_{0i}-M_{0j}-M_{0k}+M_{ij}+M_{ik}+M_{jk}&\ge0,\\
M_{0i}-M_{ij}-M_{ik}+M_{jk}&\ge0.
\end{aligned}
\]

Each product contains at most two outside vertices, so its expansion
uses only induced counts through order ten. The justification uses
binary values; it does not require a positive-semidefinite test.

## Domain and exact calculation

The source reads the complete point-independent `r=8,s=1` cache. It
checks the root list and the complete mask list at each root. It removes
no roots or flags using the count point. For every unordered triple of
flags it evaluates all four expressions with integers. The total is

\[
4\sum_{\text{916 roots }H}\binom{f_H}{3}=170{,}183{,}860,
\]

where `f_H` is the number of nonconstant flags at root `H`.

Every matrix entry is a sum of at most two labeled induced-embedding
counts. A checked magnitude bound proves that all matrix products and
seven-term expressions fit signed 64-bit arithmetic. Counts are read
from exact integer witnesses. No numerical eigensystem or optimization
is called, and the large reduced matrix is not loaded.

| Count point | Negative expressions | New cuts | Seconds |
| --- | ---: | ---: | ---: |
| Repaired earlier prism-zero point | 0 | 0 | 29.190 |
| Zero-closure loop's rounded point | 0 | 0 | 26.457 |

The earlier repaired point still fails the eleven separately proved
order-ten PSD inequalities. Passing the binary triangle inequalities
does not remove those failures. The newer point satisfies all 25 held
linear cuts and every original count equation; its exact PSD status is
not established by this scan.

The source can export a negative instance as an induced-count row and
rebuild its products by direct graph lookup. No negative instance was
found in either run, so there is no exported-cut reconstruction to check
in these two results.

## Files and reproduction

Source: `experiments/workspace/root_binary_flag_triangles.py`.

The logs and certificates in `experiments/logs/moments-and-counts/` use
the prefixes `prism-zero-binary-flag-triangles` and
`prism-zero-binary-flag-triangles-round0`. Their manifest records the
source, input, note, and output hashes.

```sh
.venv/bin/python experiments/workspace/root_binary_flag_triangles.py \
  --catalogue /tmp/conway99-order10-catalogue.pickle \
  --cache experiments/logs/moments-and-counts/order10-r8s1-full-blocks.pickle.gz \
  --witness experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure-round0-rounded-counts.json \
  --output /tmp/prism-zero-binary-flag-triangles-replay.json
```

The source requires the exact catalogue hash already bound by the
order-ten preparation. Timing fields may differ in a repeated run.
