# An order-ten obstruction to the published order-nine point

The published 58-coordinate integer point cannot extend to the order-ten
count reduction. An exact positive integer combination of 52 induced
ten-vertex counts and 21 ordinary ten-vertex core counts gives a linear
inequality on the old coordinates. It evaluates to **-2,564,720** at that
point.

The inequality is necessary for every hypothetical `SRG(99,14,1,2)`.
It does not exclude all grid-free count assignments. The previously
checked order-nine point remains a valid witness for the finite model
stated in [`grid_free_order_nine.md`](grid_free_order_nine.md); the new
inequality uses order ten.

## The reusable cut

Let `x=(1,x_1,...,x_57)` use the existing ordinary-core coordinate order
from `moments-order9.pickle`. The compact certificate includes each
coordinate's catalogue type and graph, so the indexing is explicit.
Every graph count vector must satisfy `q·x >= 0`, where

```text
q = [4573800, 3384, 1520, 0, 366, -4, -896, 0, -12, 96,
     0, 102, 34, 0, 0, 0, 15, 0, 3, 56,
     41, 44, 22, -26, 224, 108, 30, 0, 0, 38,
     -2, 16, 0, 0, -4, 0, 0, 68, 0, 0,
     0, -4, 0, 12, -132, -38, 106, -504, -162, 112,
     0, 0, 6, 28, -156, 96, -138, 540].
```

The exact certificate is the identity

\[
q\cdot x
=\sum_{H\in\mathcal H}a_Hc_H
 +\sum_{j\in\mathcal J}b_jx_j,
\]

where `|H|=10` for all 52 types in `\mathcal H`, `c_H` is the induced
unlabelled count of `H`, and the second sum uses 21 new ordinary core
coordinates `j>=58`. Every coefficient `a_H,b_j` is a positive integer.
The induced-count coefficients lie between 1 and 36. The remaining
ordinary-count coefficients are:

```text
[(111,22), (199,3), (211,2), (213,2), (229,12), (255,2),
 (287,4), (337,2), (347,2), (364,3), (371,34), (384,5),
 (389,2), (395,11), (396,2), (412,13), (423,12), (455,2),
 (466,4), (518,24), (536,5)].
```

Thus ordinary and induced count nonnegativity proves the cut. No upper
bound, numerical tolerance, graph symmetry, or positive grid count is
used in this final identity.

Substitution of `INTEGER_POINT` from `grid_free_core9_certificate.py`
gives `q·INTEGER_POINT=-2564720`. The full positive combination and all
52 original sparse count forms are saved in
[`grid-free-order10-scaled-fixed-cut.json`](../../experiments/logs/moments-and-counts/grid-free-order10-scaled-fixed-cut.json).

## How the exact identity was obtained

The unchanged original probe maximized a normalized strict margin and
timed out in both its fixed-prefix and free-prefix runs. The separate
scaled finder instead used a zero objective, nonnegative count
inequalities, and rigorous upper bounds on ordinary core counts.

For a graph pattern `H` and a vertex order, the first image has at most
99 choices. A later vertex with no earlier required neighbor has at most
99 choices; with one, at most 14. With at least two earlier required
neighbors, it has at most one choice if some pair of them is adjacent in
`H`, and at most two otherwise. A nonedge in `H` need not remain a
nonedge in an ordinary embedding, so the latter bound is two in both
possible host cases.

The product of these factors bounds labelled injective embeddings.
Dividing by `|Aut(H)|` and taking the floor gives an ordinary-count upper
bound. A complete subset dynamic program minimizes the product over all
vertex orders. The preparation record includes every graph, automorphism
order, optimum, attaining order, and factor list. It also records exact
checks against all 76 labelled patterns of order at most four in the
nine-vertex rook graph.

These bounds range from 539 to 30,425,472 for the 549 core coordinates.
The fixed prefix satisfies each individual bound. Variables were scaled
to `[0,1]`, and each inequality was divided by the largest absolute
scaled coefficient or substituted constant. The smallest nonzero
normalized coefficient was about `6.55e-7`.

The fixed-prefix feasibility model was numerically infeasible. A separate
bounded highspy run returned a dual ray. Rounding its normalized weights
first gave an exact certificate using 52 induced inequalities, 15 upper
bounds, and 31 lower bounds, with negative constant `-67377959`.
That original certificate is retained unchanged.

Rounding those 52 integer weights by `w -> round(36w/1000)` then removed
every positive new-coordinate coefficient exactly. The simplified
identity needs only the 21 nonnegativity terms listed above. It requires
no denominator clearing or final gcd division. The upper bounds were
useful to find the certificate; they are absent from its simplified proof.

## Bounded run outcomes

| Run | Variables | Inequality rows | Nonzeros | Solver outcome |
| --- | ---: | ---: | ---: | --- |
| Fixed order-nine prefix | 492 | 38,070 | 4,182,740 | Numerical infeasible in 3.20 s; later exact certificate |
| Free old coordinates; rook and broken-rook zero | 547 | 47,620 | 5,427,663 | Numerical feasible in 25.11 s |
| One fixed-prefix highspy dual extraction | 492 | 38,070 | 4,182,740 | Ray obtained in 7.30 s, including retrieval |

Each run had a 30-second limit and requested one thread. There were no
additional optimization solves. The original catalogue and dense count
reduction were not regenerated.

The free-prefix real proposal is preserved in
[`grid-free-order10-scaled-free-result.json`](../../experiments/logs/moments-and-counts/grid-free-order10-scaled-free-result.json).
Rounding produces 114 negative induced counts and no divisibility
failures. It is not an exact count witness. The real proposal has not
received an exact rational feasibility replay, and its changed old
coordinates do not inherit the earlier moment certificates.

## Sources and replay

The new files are:

- [`grid_free_order10_scaled.py`](../../experiments/workspace/grid_free_order10_scaled.py):
  complete bound dynamic programs, model preparation, and the two
  feasibility probes.
- [`grid_free_order10_scaled_dual.py`](../../experiments/workspace/grid_free_order10_scaled_dual.py):
  the one bounded ray extraction and the original integer box certificate.
- [`grid_free_order10_scaled_cut.py`](../../experiments/workspace/grid_free_order10_scaled_cut.py):
  exact export of the original forms, denominator-36 simplification, and
  the universal cut.
- [`grid-free-order10-scaled-preparation.json`](../../experiments/logs/moments-and-counts/grid-free-order10-scaled-preparation.json):
  all bound records, model statistics, and source/cache bindings.
- [`grid-free-order10-scaled-fixed-dual.json`](../../experiments/logs/moments-and-counts/grid-free-order10-scaled-fixed-dual.json):
  the numerical ray and the unchanged original exact certificate.
- [`grid-free-order10-scaled-fixed-cut.json`](../../experiments/logs/moments-and-counts/grid-free-order10-scaled-fixed-cut.json):
  the compact original and simplified identities.

The saved-form algebra replay uses only the standard library:

```sh
python experiments/workspace/grid_free_order10_scaled_cut.py replay experiments/logs/moments-and-counts/grid-free-order10-scaled-fixed-cut.json
```

It checks the positive combination, the elimination of new coordinates,
the integer cut, and its negative value. The export binds all source forms
to the exact reduced cache. A separate root-owned audit checks their
provenance directly against that cache, independently of these finder and
dual functions. The original 52-row box certificate also passed a root
replay with independently computed graph automorphism orders.
