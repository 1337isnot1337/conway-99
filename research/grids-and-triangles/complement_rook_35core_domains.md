# Attachment domains for the 35-vertex complementary-rook cores

The complete local-core index has 2,521 entries. The bounded domain census
in this checkpoint processes the first 32 entries. It does not decide
incidence feasibility for any entry and does not exclude the complementary
rook core.

The source is
[`complement_rook_35core_domains.py`](../../experiments/workspace/complement_rook_35core_domains.py).
Its input is the exact
[`local-star census`](../../experiments/logs/grids-and-triangles/complement-rook-local-star-census.json),
which records 864 local eight-vertex sets, 118 stabilizer representatives,
and 2,521 eligible perfect matchings on those representatives. The
[`prefix certificate`](../../experiments/logs/grids-and-triangles/complement-rook-35core-domains-prefix01/certificate.json)
binds the source, full index, and compressed attachment records.

## The fixed core and complete attachment domain

Let $R$ be the nine-vertex rook adjacency matrix. The old 27-vertex core is

\[
B_{27}=\begin{pmatrix}R&I&I\\I&R&I\\I&I&J-I-R\end{pmatrix}.
\]

Use the established 252-signature domain. A signature $s=(p,q,t)$
specifies the three core neighbors $R_p,S_q,T_t$. Fix the old core vertex
$R_0$. Its eight neighbors outside the old core form a set $L$. Their
signatures have $p=0$, each of $q=4,5,7,8$ twice, and each tip
$t=1,\ldots,8$ once. The six neighbors of $R_0$ inside the old core
already form three independent edges. The graph on $L$ is therefore a
perfect matching. The local-star census enumerates every permitted choice.

For a selected local set and matching, let $B$ be the resulting 35-vertex
adjacency matrix. An actual graph completion would have 64 further
vertices and a binary attachment matrix $X$ satisfying

\[
XX^T=G:=12I+2J-B^2-B.
\]

Every remaining vertex has one of the 224 old signatures with $p\ne0$.
Write $h_s$ for its old 27-coordinate incidence column. Its number of
neighbors in $L$ is forced to be

\[
d_s=2-|N_{B_{27}}(R_0)\cap\operatorname{supp}(h_s)|\in\{0,1,2\}.
\]

This follows from the two common neighbors required for the nonadjacent
pair consisting of $R_0$ and the remaining vertex. The census considers
every $d_s$-subset of the eight local vertices. There are 16, 136, and 72
old signatures with $d_s=0,1,2$, respectively. Thus each indexed core has
exactly

\[
16+136\binom81+72\binom82=3120
\]

raw attachment columns before filtering.

For a proposed full column $h\in\{0,1\}^{35}$, the only filters are:

1. Every Gram entry on its support is positive. A selected column would
   contribute one to each of these entries.
2. $(B+I)h\le2\mathbf1$. For each core vertex this is the condition that
   its still unmodeled common-neighbor demand is nonnegative.

Both conditions are necessary. No spectral rounding, automorphism
assumption about the full graph, fixed remaining incidence design, or
constraint on edges among the 64 remaining vertices is used. Every actual
completion maps to a subset of the admitted columns.

## Forced population and attachment counts

The source checks the following sums for every processed core:

\[
\sum_{i<27}G_{ii}=192,\qquad
\sum_{27\le i<35}G_{ii}=80,\qquad
\sum_{27\le i<j<35}G_{ij}=20.
\]

Each attachment column has exactly three old-core entries. Consequently
the first sum forces 64 selected columns. If $n_d$ counts selected
columns with $d$ local attachments, the other sums give

\[
n_0+n_1+n_2=64,\qquad n_1+2n_2=80,\qquad n_2=20.
\]

Thus $(n_0,n_1,n_2)=(4,40,20)$. No separate population counter is needed
once all Gram rows hold.

More explicitly, among the 28 pairs in $L$, four are its matching edges
and four pairs share the same old $S_q$ neighbor. These eight pairs have
Gram quota zero. The other twenty pairs have quota one. Each of the twenty
two-attachment vertices uses exactly one of those pairs.

## Signature uniqueness and triple packing

Two remaining vertices cannot have the same original $R/S/T$ signature:
they would share three common neighbors in the old core. A binary model
must therefore select at most one attachment choice per old signature.

More generally, selected columns cannot share any three core coordinates.
For every core triple $U$,

\[
\sum_{h:U\subseteq\operatorname{supp}(h)}z_h\le1.
\]

If a pair inside $U$ has Gram quota one, this triple inequality follows
from that Gram equality. The census records all supported triple
families, their sizes, and the number requiring an additional inequality.
It does not construct all pairwise column conflicts.

## Exact rank and coverage checks

Every admitted column is orthogonal to four explicit vectors:

\[
e_{R_0},\quad \mathbf1_R-\mathbf1_S,\quad
\mathbf1_R-\mathbf1_T,\quad
\mathbf1_{N_B(R_0)}-2\mathbf1_R.
\]

These vectors are independent: their restriction to coordinates
$0,9,18,27$ has determinant one. The source also checks that $G$
annihilates them. Hence the rational span of the attachment columns has
dimension at most 31. In every processed core its rank over
$\mathbb F_2$ is 31, proving that its rational rank is exactly 31.
This statement concerns the attachment-column span, not the rank of the
outer-product equation system or an asserted rank of $G$.

Two further exact screens are applied. A positive Gram row must have
enough distinct quota-one $RT$ and $ST$ cells to supply its quota.
Also, the Gram target reduced modulo two must lie in the span of the
binary outer-product columns. A failure would have an explicit cover or
parity witness. Neither screen failed in the first 32 cores.

The residual stabilizer of each local set acts on its matching choices.
The full index records every matching, its orbit representative, and an
explicit core action transporting that representative. This reduces the
2,521 indexed choices to 2,379 matching orbits. It is a relabeling of
finite core descriptions, not a symmetry imposed on an unknown graph.

## Bounded prefix result

The 32-core prefix finished in 6.33 seconds under a 30-second wall budget
and a 32-core limit. It saved a progress record after every core.

| Quantity | Prefix result |
|---|---:|
| Indexed cores in the complete coverage file | 2,521 |
| Cores whose attachment domains were processed | 32 |
| Admitted columns per processed core | 1,130–1,399 |
| Exact rational attachment-column rank | 31 in all 32 |
| Outer-product equation rank modulo two | 285–293 |
| Cover-capacity or parity exclusions | 0 |

Case zero has 1,206 columns from 202 original signatures, including 186
signatures with multiple attachment choices. Its 1,347 nontrivial triple
families contain 1,335 inequalities already implied by Gram quota-one
pairs and twelve additional inequalities. All twelve additional triples
have one vertex in each of $R,S,L$.

Generation and exact readback both passed. The readback reconstructs the
complete index and every saved domain, Gram support count, rank check,
and triple-family count. It does not extrapolate the prefix to the other
2,489 cores.

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_domains.py \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-domains-prefix01 \
  --replay
```
