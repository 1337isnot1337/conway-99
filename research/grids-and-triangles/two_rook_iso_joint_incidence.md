# Joint incidence and edge relaxation for the surviving two-arm core

The 27-point core with two rook-isomorphic root interfaces has one
surviving class in the separate interface census. Its full joint
incidence and edge linear relaxation is feasible. Two saved rational
points verify this exactly, including a strengthened version with
core-pair neighbor-packing inequalities.

These points are fractional relaxation witnesses. They are not
integer incidence matrices or graphs. The earlier
[fixed-assignment certificate](two_rook_iso_completion.md) excludes
one particular 72-column assignment and remains valid.

## Variables and necessary equations

The root matchings are identities and the remaining matching is

\[
p=(0,5,7,8,6,1,4,2,3).
\]

Let `B` be the resulting 27-point adjacency matrix. Enumerating all
`9^3` possible one-per-grid signatures, applying positive pair quotas
and `(B+I)h <= 2`, leaves 168 indicators `h_s`.

Introduce a selection variable `0 <= z_s <= 1` for each signature.
A signature cannot occur twice, since its two vertices would have
three common neighbors. Every completion therefore satisfies

\[
\sum_s z_s h_sh_s^{\mathsf T}=12I+2J-B^2-B,
\qquad \sum_s z_s=72.
\]

There are 9,846 potential edges between distinct signatures. An edge
is omitted when its signatures share two core points, or when one
endpoint's signature exceeds the other's remaining mixed quota.
For each retained pair use a nonnegative symmetric variable `a_st`,
with

\[
a_{st}\le z_s,\qquad a_{st}\le z_t.
\]

For each signature `t` and core vertex `i`, impose

\[
\sum_{s:\,i\in h_s}a_{st}
=\bigl(2-((B+I)h_t)_i\bigr)z_t.
\]

Also impose `sum_s a_st = 11 z_t`. When `z_t=1`, these are the usual
mixed codegree and exterior-degree equations. When `z_t=0`, its
incident edges vanish. Thus every actual completion gives a feasible
point, without any symmetry assumption about that graph.

## Additional neighbor-packing inequalities

Fix a potential outside vertex `t` and a pair of core points `i,j`.
Two neighbors of `t` cannot both have signatures containing `i,j`:
they would have `i`, `j`, and `t` as three common neighbors. Therefore

\[
\sum_{s:\,i,j\in h_s}a_{st}\le z_t.
\]

These constraints remain necessary whether `t` is selected or not.
The strengthened model includes every such inequality.

## Averaging is used only for the real relaxation

The builder lists eight explicit automorphisms of the 27-point core.
It verifies each one on every core pair, on the entire signature
domain, and on the candidate edge set. They come from rook
automorphisms commuting with `p` and the exchange of the two arms.

If the real linear model has a feasible point, averaging that point
over this finite group preserves every equality and inequality.
Consequently variables can be identified along its orbits for this
feasibility test. This argument does not permit the same
identification in an integer graph search.

There are 25 signature orbits and 1,298 edge orbits. The averaged
model has 1,323 variables, 613 equalities, and 2,544 inequalities.
Adding the neighbor-packing constraints increases the inequality
count to 4,958.

Both models have exact rational feasible points. The solver supplied
an approximate active set; rational elimination recovered its point.
The replay verifies nonnegativity and every model row with exact
`Fraction` arithmetic. No floating-point tolerance is used to accept
the saved witness.

## The remaining incidence freedom

The full Gram incidence matrix has 168 columns and exact rank 134.
Its augmented matrix has the same rank. Thus its affine solution
space has dimension 34 before the interval constraints. The script
also measures the smaller averaged incidence space.

These ranks are computed by integer row elimination. A separate
calculation with rational FLINT elimination agreed on rank 134.
The incidence constraints therefore leave substantial freedom; a
single excluded 72-column point cannot represent the whole class.

## Reproduction

The two witnesses and dimension report are in
`experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence*.json`.
The builder is `experiments/workspace/two_rook_iso_joint_incidence.py`.
All replay commands below use only Python's standard library.

```bash
python experiments/workspace/two_rook_iso_joint_incidence.py \
  --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence.json
python experiments/workspace/two_rook_iso_joint_incidence.py \
  --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence-packing.json
python experiments/workspace/two_rook_iso_joint_incidence.py --space-only \
  --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence-space.json
```

The mixed equations and the added packing constraints do not include
all common-neighbor equations between outside vertices. Further
progress requires integrality or additional necessary conditions.
