# Exact Gram downdates for complementary-rook 35-core case 2

The complete 1,287-column attachment domain for indexed case 2 has **886
additional explicit binary conflicts** from two-column Gram downdates.
Each exported conflict has an integer negative vector checked against the
full 35-by-35 remainder. No column fails the single-column test.

These are consequences of the existing complete Gram equations. This
calculation does not exclude case 2, establish feasibility of the remaining
columns, or concern any other matching case. It makes no claim that the 886
clauses are semantically independent of one another.

## Fixed core and domain

Use the indexing of `complement_rook_35core_domains.py`. The first local
eight-set has original signature indices

\[
L=(0,1,9,10,18,20,26,27).
\]

Case 2 selects the matching

\[
(0,4),\ (1,5),\ (2,6),\ (3,7)
\]

on the eight local positions. Its complete attachment domain was included
in the frozen 32-case prefix. The verifier reconstructs the complete
2,521-case index, the selected case, and all its attachment columns, then
compares them with the hash-bound prefix. A column consists of one original
three-point signature and its zero, one, or two local attachments.

Let \(B\) be this induced 35-core adjacency matrix. If it occurs in the
desired graph, its remaining 64 vertices have incidence columns \(h_v\)
with

\[
G=12I+2J-B^2-B=\sum_v h_vh_v^T.
\]

Consequently, selection of a column \(h\) requires \(G-hh^T\succeq0\).
Selection of two distinct columns \(h,k\) requires
\(G-hh^T-kk^T\succeq0\). This implication uses the complete Gram equality
and the nonnegative contributions of every other selected column.

## Exact quotient

Four integral kernel vectors are

\[
e_{R_0},\qquad
1_R-1_S,\qquad
1_R-1_T,\qquad
1_{N_B(R_0)}-2\,1_R.
\]

Their restriction to coordinates \(P=(0,9,18,27)\) is

\[
\begin{pmatrix}
1&0&0&0\\
1&-1&0&0\\
1&0&-1&0\\
-2&1&1&1
\end{pmatrix},
\]

which has determinant 1. Let \(I\) be the other 31 coordinates. The kernel
equations give an integral embedding \(E\) whose rows indexed by \(I\)
form the identity. With \(K=G[I,I]\), the certificate checks

\[
G=EKE^T,\qquad K=L_0\Delta L_0^T,
\]

where \(L_0\) is unit lower triangular and every entry of \(\Delta\) is
positive. The complete rational factors are saved. Thus \(K\succ0\) and
\(\operatorname{rank}G=31\). Its determinant is

\[
\det K=111657624486642845810688.
\]

Every candidate column is checked to have the form \(h=Ex\), with
\(x=h[I]\). The certificate supplies a symmetric integral matrix \(Q\)
and the identity

\[
KQ=DI,\qquad
D=54520324456368577056.
\]

The denominator exceeds signed 64-bit range. All products, sums, and
comparisons use Python integers or exact rational numbers.

## Schur tests and direct witnesses

For a candidate column define \(n_h=x^TQx\). The one-column condition is
\(n_h\le D\). All 1,287 columns satisfy it strictly. The least and greatest
numerators are respectively

\[
21649580726721404260,
\qquad 46420091595619324453.
\]

For a pair \(h=Ex\), \(k=Ey\), put \(p=x^TQy\). Since \(K\succ0\),
the two-column condition is equivalent to positive semidefiniteness of

\[
\begin{pmatrix}
D-n_h&-p\\
-p&D-n_k
\end{pmatrix}.
\]

Both diagonal entries are positive in this case. The pair fails precisely
when

\[
(D-n_h)(D-n_k)-p^2<0.
\]

The verifier checks all \(\binom{1287}{2}=827541\) pairs. It does not use
floating-point eigenvalues or tolerances.

For each exported failure, choose
\(c=(p,D-n_h)^T\). This gives a negative value for the displayed two-by-two
form. Set the coordinates indexed by \(I\) of a 35-vector to

\[
Qx\,c_1+Qy\,c_2
\]

and set its other coordinates to zero. The program divides by the common
divisor and fixes the sign. It then directly evaluates, using the original
35-by-35 integer matrix,

\[
v^TGv-(v^Th)^2-(v^Tk)^2<0.
\]

The primitive vector \(v\) and the negative integer value are saved for
every exported pair. This last check is sufficient to certify each binary
clause independently of the inverse or Schur calculation.

## Pair counts and scope

The three elementary conflict tests below refer to sharing an original
signature, sharing at least three core points, and sharing a core pair
whose Gram quota is one. A pair can meet more than one test.

| Same original signature | Shared core triple | Shared quota-one pair | All pairs | Negative downdates |
|---|---|---|---:|---:|
| No | No | No | 750,873 | 886 |
| No | No | Yes | 51,738 | 548 |
| No | Yes | No | 1,693 | 2 |
| No | Yes | Yes | 18,477 | 2,545 |
| Yes | Yes | Yes | 4,760 | 1,564 |
| Total | | | 827,541 | 5,545 |

There are 1,434 negative pairs beyond original-signature multiplicity and
triple packing. Of these, 548 already violate one quota-one Gram equation.
The exported fragment consists of precisely the other 886 clauses
\(\neg z_h\lor\neg z_k\). The primary column ordering is identical to the
frozen case 2 incidence formula. No other restrictions are added.

This distinction concerns immediate pair tests, not logical independence:
all the downdate clauses already follow from the complete exact Gram
equalities and binary selection. Their purpose is to expose those
consequences directly to a later solver.

## Artifacts and replay

- Source: `experiments/workspace/complement_rook_35core_gram_downdate.py`.
- Certificate: `experiments/logs/grids-and-triangles/complement-rook-35core-case0002-gram-downdate.json.gz`.
- Binary fragment: `experiments/logs/grids-and-triangles/complement-rook-35core-case0002-gram-downdate-clauses.cnf`.
- Generation and replay logs use the same prefix with `-generation.log`
  and `-replay.log`.

The gzip stream has a fixed zero timestamp. Its certificate records the
complete quotient, all column leverage numerators, all negative pairs,
their elementary classifications, and the 886 direct negative vectors.
The small positive control is a Gram matrix formed by three explicit
incidence columns; every actual pair passes. An impossible repeated
column pair has the directly verified negative vector \((1,1)\).

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_gram_downdate.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-35core-case0002-gram-downdate.json.gz \
  --clauses experiments/logs/grids-and-triangles/complement-rook-35core-case0002-gram-downdate-clauses.cnf \
  --replay
```

Replay rebuilds the domain, checks the integer congruence and inverse
identities, recomputes every single and pair test, directly checks all
exported vectors, and compares the exact clause bytes. It calls no solver.
