# Scalar triangle-class recovery and dependencies

For each of the four-vertex roots 14 and 15, let T be its unique core
triangle, let M_Q be the complete triangle-class Q matrix, and let M_K be
the previously constructed per-embedding conditioned matrix. Write
d_C=Q(T,U) for a triangle U in class C. Every d_C lies in
{120, -20, -6, 1, 8, 15}, so none is zero.

The complete scalar class Gram matrix N has entries
N_CD=sum over labelled root embeddings of n_C n_D. The identity

```
M_K = 120 M_Q - diag(d) N diag(d)
```

therefore recovers every coefficient of N directly:

```
N_CD = (120 M_Q,CD - M_K,CD)/(d_C d_D).
```

The source `triangle_projector_scalar_recovery.py` checks all 11,650
divisions exactly. All resulting coefficients are nonnegative integers.
It also checks all 75 first-moment identities in the fixed-triangle row:
n_T=1 makes N_TC=p_C.

A separate direct Gram computation passes on 306 hosts: all 300 catalogue
graphs of orders 4 through 7, plus six ten-vertex hosts. On each labelled
root embedding, the control counts triangles in each class and adds the
outer product of that count vector. It agrees with contraction over the
host's induced-subgraph counts. The controls do not generate a new
pair-product tensor.

## Exact point result

At the immutable point with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`,
both complete scalar blocks are positive semidefinite.

| Root type | Order | Exact rank | Exact nullity |
| --- | ---: | ---: | ---: |
| 14 | 41 | 7 | 34 |
| 15 | 34 | 4 | 30 |

The query took 0.03275689399742987 seconds; cold replay took
0.017571452000993304 seconds. The replay recomputed all integer matrix
entries and all characteristic-polynomial coefficients.

The result is
`experiments/logs/moments-and-counts/order10-triangle-projector-scalar-query01.json`,
SHA256 `4a9b39ddec96f3418e30fa518c1301606c49c55e99443fd8e50841c0500db997`.
Its source SHA256 is
`1b7d65ab567a1e00f1e8871919273a154daeebc38a30c856f0969aa3d5f85f3b`.

## Relation to the existing scalar flag family

These are scalar Gram matrices, not a new independent projector family.
Any induced rooted flag with at most three free vertices can be reduced
linearly to flags whose free vertices have degree at least three.

To prove this, take a free vertex of degree t at most two and delete it,
leaving n specified vertices. For each embedding of the remaining graph,
the total number of reinsertion choices containing its prescribed
neighborhood is:

- 99-n if t=0;
- 14 minus the visible degree of the prescribed neighbor if t=1;
- 1 or 2, according as the two prescribed neighbors are adjacent or
  nonadjacent, minus their visible common-neighbor count if t=2.

Subtract every other exact neighborhood extension to isolate the desired
flag. Each same-size alternative has more edges; the parent has fewer
free vertices. Induction first on the number of free vertices and then
on the number of missing edges terminates. All counts here concern
labelled extensions. Dividing a triangle-class flag by its explicitly
known free-label stabilizer gives its unlabelled triangle-class count.

Thus, modulo the SRG extension identities, the class counts lie in the
span of the complete induced r=4,s=3 flag family already present in the
repository. N is a congruence of that full scalar flag Gram matrix.
This package does not construct a coefficientwise change-of-basis matrix;
it gives a separate exact certificate for N at the integer point.

There is also no need to treat the upper bound on the one-triangle
conditioned projector as an independent condition when N and the
complementary Q block are already positive semidefinite. Its matrix is

```
25200 diag(p) - M_K
  = 120(210 diag(p) - M_Q) + diag(d) N diag(d).
```

Both summands on the right are then positive semidefinite. The result
does not resolve graph existence.
