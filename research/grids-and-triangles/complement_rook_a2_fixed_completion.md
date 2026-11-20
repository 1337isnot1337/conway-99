# Complete edge models for the four a=2 incidence orbits

This note concerns the complementary-rook boundary of an isomorphic pair of
induced rook grids. It does not assume that such a pair exists in every
putative graph.

Let `R` be the adjacency matrix of the nine-point rook graph, and put
`Z = J - I - R`. The 27-point induced core has matrix

\[
B=\begin{pmatrix}R&I&I\\ I&R&I\\ I&I&Z\end{pmatrix}.
\]

Each of its vertices has six core neighbors and needs eight exterior
neighbors. Each of the remaining 72 vertices has one neighbor in each of the
three core grids, so it needs eleven exterior neighbors.

The parameter `a` counts exterior signatures `(p,q,t)` with
`R[p,t] = R[q,t] = 1`. The
[complete incidence census](complement_rook_a2_incidence_census.md) proves
that `a=2` has exactly 576 labeled incidence designs. The 144 simultaneous
rook automorphisms and swaps of the first two grids divide these designs
into four orbits of size 144. Testing one representative per orbit relabels
the fixed incidence matrix. It imposes no automorphism on a completion.

## The exact graph model

For one representative, let `X` be its fixed 27-by-72 incidence matrix and
let `h_t` be column `t`. The census verifies the complete identity

\[
XX^T=12I+2J-B^2-B.
\]

All 72 columns are distinct. Their ordering is the increasing order of their
indices in the complete 252-signature domain. Every model manifest records
these indices, their coordinate triples, and their SHA256 digest.

Define the 27 mixed demands for vertex `t` by

\[
d_t=2\mathbf 1-(B+I)h_t.
\]

The code checks this vector both with the inherited incidence checker and
with a direct entrywise calculation. All demands are nonnegative, and each
vector sums to 33.

An exterior pair `{s,t}` is eligible precisely when

\[
|h_s\cap h_t|\leq1,
\quad d_t(i)>0\text{ for every }i\in h_s,
\quad d_s(i)>0\text{ for every }i\in h_t.
\]

These are necessary edge conditions. An adjacent pair cannot already share
two core neighbors. An edge `s--t` contributes one to each mixed demand
`d_t(i)` with `i` in `h_s`, and conversely. Every eligible pair receives its
own Boolean variable; no edge orbits are identified.

The mixed and degree equations are

\[
\sum_{s:i\in h_s}c_{st}=d_t(i)
\quad(0\leq i<27),\qquad
\sum_s c_{st}=11.
\]

Repeated identical equations are encoded once. For every exterior pair,
including ineligible edges, the model imposes

\[
|h_s\cap h_t|+c_{st}
+\sum_{w\ne s,t}c_{sw}c_{tw}\leq2.
\]

Here an ineligible edge is identically zero. If the core overlap is two,
each candidate common-neighbor path is forbidden by a binary clause. For
the other pairs, a fresh path variable `u` receives the forward implication
`c_sw AND c_tw -> u`; the path variables and the direct edge enter an
at-most constraint. A true path must therefore count toward the cap.
Conversely, setting each auxiliary variable to the actual conjunction
extends every cap-compatible graph assignment. The encoding does not add a
restriction by omitting reverse implications.

These conditions are also sufficient for a fixed-incidence completion.
Every vertex has degree 14, the core and mixed blocks of `A^2+A` are exact,
and all exterior entries are at most two. For each vertex the 98 off-diagonal
entries of `A^2+A` sum to `14^2=196`. Hence every cap is an equality, and a
Boolean solution is an `srg(99,14,1,2)`.

## Independent controls

The separate read-only audit rebuilt all four domains without constructing
their CNFs. It verified every Gram entry, every mixed demand, all eligible
edges, and every common-neighbor path domain. Every case has 1,764 eligible
edges, 1,873 distinct mixed/degree equations, and 2,556 exterior-pair caps.
The pair-overlap counts are 1,836 with overlap zero, 684 with overlap one,
and 36 with overlap two. None of the equations has a demand larger than
its available literals.

| Census orbit | Path variables | Binary packing clauses |
| --- | ---: | ---: |
| 0 | 83,279 | 1,395 |
| 1 | 83,286 | 1,388 |
| 2 | 83,291 | 1,383 |
| 3 | 83,292 | 1,382 |

The inherited forward-path control exhausts 3,069 small Boolean cases.
The independent audit is saved in
`experiments/logs/grids-and-triangles/complement-rook-a2-fixed-completion-independent-audit.json`.

## Proof binding

The source is `experiments/workspace/complement_rook_a2_fixed_completion.py`.
It replays the complete incidence census before each model build. Each
manifest binds the census, the census CNF and proof, the source modules,
the complete graph-variable domain, and the generated CNF by SHA256.

The wrapper `experiments/workspace/complement_rook_a2_fixed_certificate.py`
checks a saved UNSAT proof with `drat-trim` and retains its used input
clauses and lemmas. A separate replay rebuilds the complete formula from
the census, compares its exact hash and structural counts, checks that
every retained clause is present, and verifies the retained DRAT proof.
The full large CNF and raw solver proof are therefore reproducible inputs;
the retained certificate does not depend on trusting a solver status.

## Checked outcomes

All four formulas are UNSAT. The recorded wall budget was 120 seconds per
case, including CNF parsing and solver bootstrap. Each run finished well
inside that budget.

| Orbit | CNF variables | CNF clauses | Return time, seconds | Retained input clauses | Retained proof lines |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 298,617 | 593,759 | 5.793 | 289 | 271 |
| 1 | 298,618 | 593,758 | 1.328 | 499 | 538 |
| 2 | 298,601 | 593,723 | 0.864 | 655 | 779 |
| 3 | 298,618 | 593,750 | 1.155 | 1,833 | 2,028 |

For each row, a fresh reconstruction matched the full CNF SHA256, every
retained input clause was found in that formula, and `drat-trim` verified
the retained proof. Thus all 576 incidence designs with `a=2` are excluded.
Together with the existing
[a=0 completion exclusion](two_rook_a0_fixed_completion.md) and
[a=1 incidence exclusion](complement_rook_a_incidence.md), this proves

\[
\boxed{a\geq3}
\]

for any completion in the complementary-rook boundary. Larger values of
`a` remain unresolved by these four certificates.

The summary is
`experiments/logs/grids-and-triangles/complement-rook-a2-fixed-completion-summary.json`.
For each `i` from zero through three, the `complement-rook-a2-fixed-casei`
prefix identifies the model manifest, solver result, retained certificate,
and generation/replay logs in the same directory. The retained `.cnf` and
`.drat` files are in `experiments/workspace/`.

From the repository root, replay all four certificates sequentially with:

```sh
for i in 0 1 2 3; do
  .venv/bin/python experiments/workspace/complement_rook_a2_fixed_certificate.py replay \
    --certificate experiments/logs/grids-and-triangles/complement-rook-a2-fixed-case${i}-certificate.json \
    --log experiments/logs/grids-and-triangles/complement-rook-a2-fixed-case${i}-coordinator-drat.log \
    --drat-trim /tmp/conway99-drat-trim/drat-trim || exit 1
done
```

The proof checker path can be replaced by a local `drat-trim` executable.
The replay needs the small incidence census inputs and the retained case
certificates. It reconstructs each full completion formula, so the saved
large full CNFs and raw completion proofs are not required for replay.
