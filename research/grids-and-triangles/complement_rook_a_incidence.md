# The next complementary-rook incidence value is two

In the complementary-rook tip case `Z=J-I-R`, let `a` count selected
exterior signatures `(p,q,t)` with both `R[p,t]=1` and `R[q,t]=1`.
The complete selector-only incidence model has these exact outcomes:

| Prescribed a | Outcome | Evidence |
| ---: | --- | --- |
| 0 | Feasible incidence control | Explicit 72-column full-Gram witness |
| 1 | Impossible even at incidence level | Rebuilt CNF and independently checked DRAT proof |
| 2 | Feasible at incidence level | Explicit 72-column full-Gram witness |

The separate checked completion exclusion for `a=0` is in
[`two_rook_a0_fixed_completion.md`](two_rook_a0_fixed_completion.md).
Combining it with the new `a=1` exclusion proves

\[
\boxed{a\ge2}
\]

for every full completion of the complementary-rook core. The `a=2`
witness satisfies incidence equations only; no exterior adjacency
completion is asserted.

## Complete selector domain

The 27-point core consists of two copies of `R` and one copy of its
complement, with identity matchings between them. All 252 possible
signatures are retained:

\[
(p,q,t),\qquad p\ne q,\ R[p,q]=0,\ t\notin\{p,q\}.
\]

The source independently checks this domain against every positive
core-pair entry of `G=12I+2J-B^2-B`. There is one Boolean selector per
signature. There are no exterior edge variables, orbit equalities,
fixed incidence choices, or prescribed tip permutations.

The model imposes all 180 positive cross-grid Gram margins. The
first/second-grid margins are two; the first/third and second/third
off-diagonal margins are one. Their sums force 72 selected columns
and all diagonal entries of `G`. The remaining zero Gram entries hold
by the complete signature domain. A cardinality equation on the 72
both-near candidate signatures fixes `a`.

For each fixed `t`, these margins make the eight selected `(p,q)` pairs
a permutation of the other eight points. Four points are rook-near
to `t` and four are rook-far. Hence the selected near-to-near and
far-to-far counts at that tip are equal. Summing shows that `a` also
equals the number of selected triples where both `p,t` and `q,t` are
rook-far. Every saved witness checks this equality explicitly.

## Exact results and controls

The `a=0` control uses
`p0=(0,5,7,8,6,1,4,2,3)` and the signatures

\[
(p,\ t+p_0(p-t),\ t),\qquad p\ne t,
\]

with coordinate arithmetic in `F_3^2`. It has 72 distinct columns,
and direct integer multiplication verifies all 729 Gram entries. The
generated `a=0` CNF also admits this fixed selector assignment.

For `a=1`, the formula has 1,403 variables and 2,733 clauses. Glucose4
returned UNSAT in approximately 0.047 seconds; `drat-trim` independently
verified the saved proof. Replay regenerates the exact formula,
compares its clause list and hash, and rechecks the proof.

For `a=2`, the formula has 1,612 variables and 3,080 clauses. It was
SAT in approximately 0.006 seconds. The saved witness checks all 729
Gram entries and has exactly two both-near triples:

\[
(8,3,6),\qquad(8,4,7).
\]

Its counts by third coordinate are `(0,0,0,0,0,0,1,1,0)`. The full
72-column witness is saved in the result JSON. The sequence stopped
at this first positive feasible value; no larger value was tested.

## Files and replay

Source: `experiments/workspace/complement_rook_a_incidence.py`.
The two CNFs and the `a=1` DRAT proof have the stem
`experiments/workspace/complement-rook-a-incidence-`.
The result JSON, run/replay logs, and DRAT logs use the same stem in
`experiments/logs/grids-and-triangles/`.

```sh
python experiments/workspace/complement_rook_a_incidence.py --replay \
  --prefix experiments/workspace/complement-rook-a-incidence \
  --output experiments/logs/grids-and-triangles/complement-rook-a-incidence.json \
  --drat-trim /path/to/drat-trim
```

The source and each CNF/proof are hash-bound in the result. No graph-edge
solver is launched by this incidence audit.
