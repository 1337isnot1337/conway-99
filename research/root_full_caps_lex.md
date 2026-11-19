# Lexicographic reduction of the rooted matching cases

This is a separate overlay for the complete rooted model in
`root_full_caps.md`. The original model, its eleven normalized cases, and
the running first batch are unchanged. The overlay has exact group and
Boolean controls. At this checkpoint no large overlay CNF has been built
and no 99-vertex overlay case has been solved.

## Coverage by coordinate relabeling

Fix the root, near vertex 0, and its mate 1. The other twelve near labels
are six fixed mate pairs. Write their local labels as `(a,s)`, where
`0 <= a < 6` and `s` is a bit. Every permutation

\[
(a,s)\longmapsto (\pi(a),s+\epsilon_a\pmod 2)
\]

preserves the mandatory rooted core. These permutations form a group of
order `2^6 6! = 46080`.

The first model fixes the perfect matching on the twelve exterior
vertices adjacent to near vertex 0. Its union with the reference mate
matching has alternating components whose half-lengths form a partition
of six. The eleven partitions cover every possible matching, as checked
in `root_full_caps_coverage.py` and both independent matching audits.

For each canonical matching, retain exactly the signed-axis permutations
that preserve it. Such a permutation preserves the core, exterior
incidence signatures, mixed demands, exterior degree equations, pair
caps, normalization units, and the 84 broken-rook clauses. This is a
symmetry of the **set of labeled graph completions**. A completed graph
need not have any corresponding automorphism.

Let `x` be the ordered vector of 3,486 exterior edge bits. Every finite
orbit under the matching stabilizer has a lexicographically least vector
`x_min`. For every stabilizer element `g`,

\[
x_{\min}\leq_{\rm lex} g x_{\min}.
\]

It is therefore safe to impose these inequalities for the selected
generators simultaneously. At least one labeling of every possible graph
survives. Inequalities for generators alone need not select the global
minimum or a unique representative; neither assertion is required.

## Complete stabilizers and generators

For a canonical component on `p` axes, use the rotation
`(j,s) -> (j+1,s)` and the reflection `(j,s) -> (-j,1-s)`, with arithmetic
on `j` modulo `p`. Omit the identity rotation when `p=1`. Also interchange
adjacent components of equal size without changing their internal
coordinates. Each map preserves both matchings.

The standard-library coverage program enumerates all 46,080 signed-axis
permutations and directly tests whether they preserve each canonical
matching. A separate breadth-first closure of the proposed generators
must equal that explicit stabilizer. The equality is checked in every
case. For a partition with `m_p` parts of size `p`, the resulting group
order also equals

\[
\prod_p (2p)^{m_p}m_p!.
\]

The certificate stores every generator, the complete stabilizer's hash,
the group order, and the equality check. Replay repeats the enumeration
and closure; it does not trust the stored counts.

| Case | Partition | Stabilizer order | Generators | Added variables | Added clauses | Total variables | Total clauses |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1+1+1+1+1+1 | 46,080 | 11 | 23,233 | 69,710 | 983,647 | 1,978,574 |
| 1 | 1+1+1+1+2 | 1,536 | 9 | 19,907 | 59,730 | 980,321 | 1,968,594 |
| 2 | 1+1+1+3 | 288 | 7 | 16,655 | 49,972 | 977,069 | 1,958,836 |
| 3 | 1+1+2+2 | 256 | 8 | 19,912 | 59,744 | 980,326 | 1,968,608 |
| 4 | 1+1+4 | 64 | 5 | 12,785 | 38,360 | 973,199 | 1,947,224 |
| 5 | 1+2+3 | 48 | 5 | 13,329 | 39,992 | 973,743 | 1,948,856 |
| 6 | 1+5 | 20 | 3 | 8,601 | 25,806 | 969,015 | 1,934,670 |
| 7 | 2+2+2 | 384 | 8 | 22,520 | 67,568 | 982,934 | 1,976,432 |
| 8 | 2+4 | 32 | 4 | 12,062 | 36,190 | 972,476 | 1,945,054 |
| 9 | 3+3 | 72 | 5 | 16,111 | 48,338 | 976,525 | 1,957,202 |
| 10 | 6 | 12 | 2 | 6,924 | 20,774 | 967,338 | 1,929,638 |

These are exact prospective formula sizes, computed without constructing
any large overlay CNF. The original normalized formula has 960,414
variables and 1,908,864 clauses in every case.

## Edge-coordinate lift and lex encoding

A near-label permutation sends the exterior vertex `{a,b}` to
`{g(a),g(b)}`, then sends each unordered exterior edge to the unordered
edge of its images. The primary variables are exactly the integers
1 through 3,486 in the original edge order. If `edge_image[e]` is the new
coordinate of old edge `e`, the relabeled vector at coordinate `j` uses
the old bit at `edge_image^{-1}[j]`. The code explicitly forms this
inverse. It checks that vertices and edges are permuted bijectively and
that every fixed constraint family is preserved.

Coordinates where the two compared literals are the same variable can
be deleted: they are equal for every assignment. For each remaining
coordinate pair `(x_i,y_i)`, let `p_i` mark equality of the preceding
active prefix. The first prefix is true. Add

\[
\neg p_i\lor\neg x_i\lor y_i.
\]

Except at the last active coordinate, introduce a fresh flag `p_(i+1)`
and add

\[
\begin{split}
\neg p_i\lor x_i\lor y_i\lor p_{i+1},\\
\neg p_i\lor\neg x_i\lor\neg y_i\lor p_{i+1}.
\end{split}
\]

Omit the first prefix literal because that prefix is true. Every actual
equal prefix forces its flag to be true, so the first unequal pair
cannot be `(1,0)`. Conversely, if `x <=lex y`, assigning each flag to
actual prefix equality satisfies the clauses. Reverse implications are
unnecessary. For `m>0` active coordinates, this uses exactly `m-1` new
variables and `3m-2` clauses. Each generator receives distinct flags from
one pool starting above the original largest variable.

## Controls and replay

The overlay control checks every assignment to two independent Boolean
vectors of lengths zero through six: 5,461 assignments. It also checks
every coordinate permutation and every Boolean vector at those lengths:
50,363 assignments. In every case, SAT with fixed primary variables is
equivalent to direct tuple comparison. Thus the controls include aliases,
fixed coordinates, the identity permutation, and the empty vector.

A separate nine-vertex rook graph is constructed from grid coordinates.
All six exterior edge bits are fixed to that graph in the normalized
degree-four base formula with its stabilizer overlay. SAT and every
degree and pair equation pass. A free normalized nine-point solve also
passes exact graph verification. These are controls only; the 99-point
model remains the target.

The code and complete analysis are in:

- `experiments/workspace/root_full_caps_lex_coverage.py`
- `experiments/workspace/root_full_caps_lex.py`
- `experiments/logs/root-full-caps-lex/coverage.json`
- `experiments/logs/root-full-caps-lex/analysis.json`
- `experiments/logs/root-full-caps-lex/analysis.log`

Replay the group coverage with the standard library:

```sh
python experiments/workspace/root_full_caps_lex_coverage.py \
  --certificate experiments/logs/root-full-caps-lex/coverage.json
```

Replay the lift, source bindings, counts, and small SAT controls:

```sh
.venv/bin/python experiments/workspace/root_full_caps_lex.py replay \
  experiments/logs/root-full-caps-lex/analysis.json
```

The latter command does not build or solve a 99-point formula. A separate
`build` command can append the checked clauses to a frozen normalized CNF
after the proposed experiment has been reviewed. It verifies the input
CNF hash, preserves the original file, and records the resulting hash.
