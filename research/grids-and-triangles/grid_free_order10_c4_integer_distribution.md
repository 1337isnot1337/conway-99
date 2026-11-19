# An integer-valued distribution for the C4 moments

The latest 48-cut count point has an exact positive rational mixture
that reproduces every first and second moment of its fifteen C4 flags.
Each atom assigns integer values to the flags. This rules out a further
pointwise quadratic inequality that uses only those integer-value
restrictions. It does not realize the atoms as graph neighborhoods.

The count witness SHA256 is
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
The flag indices and normalization are those of the
[complete higher-flag cache](grid_free_order10_higher_flags_results.md).

## Exact integer cuts

Every flag counts labelled assignments and is therefore an integer.
For any integer linear combination L and integer k,

\[
(L-k)(L-k-1)\geq0.
\]

Write g for the labelled root count, p for the sum of L, and q for
the sum of L squared. The corresponding necessary inequality is

\[
q-(2k+1)p+k(k+1)g\geq0.
\]

Its minimum over integer shifts is attained at `k=floor(p/g)` when
g is positive. The difference between consecutive values is
`2*((k+1)*g-p)`. Replacing L by minus L gives the same minimum, so
the first nonzero coefficient can be normalized to plus one.

The bounded scan checks all 265,720 nonzero coefficient vectors in
`{-1,0,1}^12`, up to sign. It uses the twelve nonzero nonconstant
flags. Every exact inequality passes; the minimum is zero. The scan
takes 3.798 seconds and uses Python integers. This finite enumeration
alone would leave other coefficients and quadratic inequalities open.

## The eight binary flags

Flags `6,7,9,10,11,12,13,14` are binary. Independent direct products
give the coefficientwise identities `F_i^2=F_i`; both forms consist
of one labelled embedding of catalogue type 307. The product check
keeps all free-label factors and uses no reduced core matrix.

At this point, the first and second moments of these eight flags
have an exact representation on 29 Boolean patterns. Each pattern
has at most two ones. A pair has the prescribed cross-moment mass;
a singleton has its first moment minus the sum of incident pair
masses. The remaining mass belongs to the zero pattern. All masses
are nonnegative integers and sum to 16,632 labelled root embeddings.
A separate literal reconstruction checks all 45 distinct entries
of this nine-coordinate moment matrix.

## The full fifteen-flag representation

The four remaining nonconstant flags are `3,4,5,8`. A finite linear
search allows each to take values zero through three, combined with
the 29 Boolean patterns above. There are 7,424 candidate atoms and
75 exact moment/marginal equations. The numerical search only proposes
a support. Exact rational elimination then reconstructs its weights.

The saved support has 75 distinct atoms with strictly positive
rational weights. Every atom has constant coordinate one, zero
prism coordinates `1,2`, eight binary coordinates, and four integer
coordinates between zero and three. If v_a denotes its full
fifteen-coordinate vector and w_a its weight, the certificate gives

\[
M=\sum_{a=1}^{75}w_a v_a v_a^T,\qquad
w_a>0,\qquad \sum_a w_a=16632.
\]

All 225 entries are checked exactly. A separate replay imports no
finder or optimizer. It independently constructs all 120 distinct
flag products as literal graphs, evaluates their embedding counts,
and compares every entry with the weighted atoms. That replay passes
in 1.756 seconds. The discovery and reconstruction take 0.822 seconds.

Consequently, any quadratic polynomial nonnegative on all assignments
with these integer and binary value restrictions also has nonnegative
value under this moment matrix. Increasing the coefficient search in
the preceding shifted-integer test cannot reject this point.

The weights need not be integer root multiplicities. The atoms have
not been checked as realizable C4 neighborhoods, and the construction
does not impose every relation among actual graph flags. Such graph
relations, other rooted families, and higher moments remain separate.
This certificate does not construct an SRG(99,14,1,2).

## Files and replay

The full certificate is
`experiments/logs/moments-and-counts/order10-higher-flags-c4-integer-distribution01.json`,
with SHA256
`54c6e78cd57d7bdcf6086885cd6e97cf9276b9ecbf6be99bb053fd1e1c7c5ab4`.

Run the independent product and rational-weight replay from the
repository root, choosing a new output path:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_c4_integer_distribution_replay.py \
  --distribution experiments/logs/moments-and-counts/order10-higher-flags-c4-integer-distribution01.json \
  --sha256 54c6e78cd57d7bdcf6086885cd6e97cf9276b9ecbf6be99bb053fd1e1c7c5ab4 \
  --output /tmp/conway99-c4-integer-distribution-replay.json
```

The accompanying manifest binds the finite scan, its Boolean control,
the numerical support proposal, the exact atoms, and the independent
replay. It leaves all earlier C4 certificates unchanged.
