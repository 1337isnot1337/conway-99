# An exact aggregate certificate for at most 119 grids

Let `g` count all induced three-by-three rook grids in a hypothetical
`srg(99,14,1,2)`. Let `b` count all-red grids, whose six lines each belong
to six grids. Then

\[
29g-4b\le3465.
\]

This inequality does not assume an upper bound on `b`. Combining it with
the [three-base boundary obstruction and closure](three_red_boundary.md),
which give `b<=1`, yields

\[
29g\le3469<29\cdot120,
\qquad g\le119.
\]

The earlier [four-base obstruction](red_grid_three_bound.md), giving
`b<=3`, also suffices for the same integer bound. The present note supplies
the aggregate inequality and its independent integer replay. The
[percolation identity](grid_intersections.md) then gives at least
`4158-18*119=2016` percolating unordered nonedges.

This independent bound is weaker than the bound of 114 reported and
proved on the parallel [root-grid branch](https://github.com/1337isnot1337/conway-99/pull/3).
That proof uses the separate exclusion of intersecting red triangles.
The present certificate does not use that exclusion or assert
nonexistence of the strongly regular graph.

## Root and grid flags

At a vertex `p`, let `D_p` be the graph on its seven incident triangles:
an edge means that the two triangles lie in a common grid. Write `e(D)`
for its number of edges and `m(D)` for its number of unordered disjoint
edge pairs. A vertex degree of `D_p` is the total grid multiplicity of
the corresponding triangle.

For an unordered degree pair `a,b` with `1<=a<=b<=6`, define:

- `P_ab(D)`: the number of edges whose endpoint degrees are `a,b`;
- `K_ab(D)`: the number of those edges whose endpoints cover every edge
  of `D`.

The second condition is equivalent to `e(D)-a-b+1=0`.

A grid has three row-line multiplicities `r_1,r_2,r_3` and three column-line
multiplicities `c_1,c_2,c_3`. Let `P_ab(Q)` count its corners with line
degrees `a,b`. Let `L_ab(Q)` count the same corners for which the other two
rows contain a red line and the other two columns contain a red line.

Such a corner must use a covered root edge. Otherwise a second grid
meeting the first only at that corner would produce a nongrid crossing
square using a red edge. The opposite four-cycle matching preserves either
all four edges or two opposite edges; the assumed red line in both
directions guarantees that one of these preserved edges is red. A red
edge has all its twelve squares in grids, giving a contradiction. This is
the covered-corner implication used in
[`grid_flag_relaxation.md`](grid_flag_relaxation.md).

Summing the flags over all roots and all grids therefore gives

\[
\begin{aligned}
\sum_D n_D &=99,\\
\sum_D P_{ab}(D)n_D-\sum_Q P_{ab}(Q)z_Q&=0,\\
\sum_Q L_{ab}(Q)z_Q-\sum_D K_{ab}(D)n_D&\le0.
\end{aligned}
\]

Here `n_D` and `z_Q` are the nonnegative numbers of roots and grids of each
type. In particular `g=sum_Q z_Q`, and `b` is the variable for the profile
`r=c=(6,6,6)`.

The [crossing-square count](grid_intersections.md) gives the remaining
inequality

\[
\sum_D m(D)n_D+18g\le4158.
\]

It counts pairs of grids meeting only at a point against nongrid squares.

## The exact weighted sum

All coefficients below are integers; the final inequality is divided by
180. Give the root-count equality weight 3696 and the crossing-square
inequality weight 62. Give each degree-pair equality weight `u_ab`, and
each covered-corner inequality weight `v_ab`, as follows:

| Degree pair | Equality weight `u_ab` | Covered-corner weight `v_ab` |
| --- | ---: | ---: |
| `(2,2)` | -487 | 0 |
| `(6,6)` | -332 | 44 |
| `(a,6)`, `a<6` | -456 | 160 |
| Every other pair | -456 | 31 |

All inequality weights are nonnegative. Equality weights may have either
sign. Triangle-population equalities have weight zero, and no all-red
upper-bound row is used.

For a root type `D`, its coefficient in this weighted sum is

\[
s(D)=3696+62m(D)+\sum_{a,b}u_{ab}P_{ab}(D)
                         -\sum_{a,b}v_{ab}K_{ab}(D).
\]

For every necessary root type, `s(D)>=0`. The exact finite verification
below establishes this with weaker restrictions than the original flag
model uses.

For a grid type `Q`, its coefficient is at least

\[
180\bigl(29-4\mathbf1_{Q\text{ all-red}}\bigr).
\]

To check this directly, let `r,c` count red rows and columns, interchanging
the directions so that `r<=c`. Let `N_22` count corners whose two lines both
have multiplicity two. The excess over the displayed target is:

| Red row and column counts | Scaled excess |
| --- | ---: |
| `(0,c)` | `31 N_22` |
| `(1,1)` | 0 |
| `(1,2)` | 454 |
| `(1,3)` | 588 |
| `(2,2)` | 351 |
| `(2,3)` | 0 |
| `(3,3)` | 0 |

Every entry is nonnegative. The finite verifier also checks all 1,596
unordered pairs of sorted line triples, independently confirming this
table.

Since every type count is nonnegative, the weighted left side is at least
`180(29g-4b)`. Its right side is exactly

\[
3696\cdot99+62\cdot4158=623700=180\cdot3465.
\]

This proves `29g-4b<=3465`.

## Necessary root restrictions used by the verifier

The original model enumerates 509 isomorphism classes using the full
incidence-support criterion and the excluded six-cycle support. This
certificate works on a larger class. It only needs the following three
restrictions on `D`.

First, `e(D)<=15`, the proved pointwise grid bound in
[`grid_intersections.md`](grid_intersections.md).

Second, `D` has no vertex of degree five. Its complement `F` carries a
nonzero vector on each edge, with the incident vectors summing to zero at
every vertex. This is the incidence-support identity proved in the same
note. A degree-one vertex of `F` would force its unique edge vector to
vanish.

Third, `D` is not either of the following graphs:

\[
K_1\vee(K_4\sqcup2K_1),\qquad
K_2\vee(K_3\sqcup2K_1).
\]

The complement consists of isolated vertices and a book of four or three
triangles sharing an edge `ab`. At every other nonisolated vertex `w`,
the incidence identity gives `z_aw+z_bw=0`. Adding the identities at `a`
and `b` then gives `2z_ab=0`, contrary to the requirement that every
support edge have a nonzero vector.

These two forbidden graphs are uniquely specified by degree multisets
`1^2,4^4,6` and `2^2,4^3,6^2`. Removing their universal vertices leaves a
complete graph and two isolated vertices, so excluding these multisets
does not discard any other graph.

## Complete integer verification

`experiments/workspace/global_grid_flag_certificate.py` uses only the
Python standard library. It visits all `2^21=2097152` labeled graphs on
seven vertices by Gray code and updates their degrees and adjacency
exactly. The root coefficient is evaluated by

\[
s(D)=3696-456e(D)+62m(D)-31P_{22}(D)+124P_{66}(D)
                         -\sum_{a,b}v_{ab}K_{ab}(D),
\]

with

\[
m(D)=\binom{e(D)}2-\sum_v\binom{d(v)}2.
\]

The complete counts are:

| Labeled graphs | Count |
| --- | ---: |
| More than fifteen edges | 27,896 |
| At most fifteen edges, with a degree-five vertex | 926,891 |
| One of the two remaining forbidden forms | 315 |
| Root columns checked | 1,142,050 |
| Total | 2,097,152 |

The minimum checked root coefficient is zero. The minimum excess among
the 1,596 grid columns is also zero. Thus every coefficient is checked by
integer arithmetic, with no floating-point sign decision, optimizer,
isomorphism package, or atlas-completeness assumption.

The saved certificate contains the weights, exact right side, filter
counts, and coefficient histograms. Generate or replay it with:

```sh
python experiments/workspace/global_grid_flag_certificate.py \
  --write experiments/logs/grids-and-triangles/global-grid-flag-certificate.json

python experiments/workspace/global_grid_flag_certificate.py \
  --verify experiments/logs/grids-and-triangles/global-grid-flag-certificate.json
```

As an additional check against the older model, direct evaluation of these
same weights on its 509 root columns and 1,596 grid columns gives minimum
slack zero, with four root equality types and 1,281 grid equality types.
The old all-red cap is absent from this certificate.
