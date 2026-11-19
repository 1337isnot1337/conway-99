# Completion checks beyond the eleven zero forests

This note records further tests of the norm-16 partition after
[the eleven-forest restriction](coupled_zero_structure.md). It separates
certified exclusions of particular partial choices from unresolved
incidence templates. No new whole-template exclusion is claimed here.

## A necessary Gram matrix on thirty-five vertices

Let `B` be the adjacency matrix induced on `P∪N∪H∪Z`, of order
thirty-five. Let `N_L` be its incidence matrix to the sixty-four
vertices of `L`. The strongly regular graph equation

\[
A^2+A=12I+2J
\]

implies

\[
G(B):=12I_{35}+2J_{35}-B-B^2=N_LN_L^T.
\]

Thus `G(B)` must be positive semidefinite. The saved high/low witnesses
already determine `B`, although they have not chosen the zero-to-low
entries of `N_L`.

Among the 447 saved high/low witnesses, 265 have a recorded integer
vector `v` with

\[
v^TG(B)v<0.
\]

The counts by support-core index are `1,11,75,41,137`. These are exact
integer certificates against the particular `H/Z` cores. They are
independent of the high/low choices. They do not exclude the underlying
incidence templates, since another `H/Z` graph may work.

Floating point eigenvectors were used only to propose integer vectors.
The replay evaluates all quadratic forms with Python integers and
requires a strictly negative value. For the other 182 saved points,
no negative certificate is recorded; this note makes no exact PSD
claim about them.

The vectors are saved in
`experiments/logs/eigenlattices/coupled-zero-gram-certificates.json`.
Replay with:

```bash
.venv/bin/python experiments/workspace/coupled_zero_gram.py --verify
```

## Exact linear cuts from a negative quadratic witness

Each such certificate also yields a linear inequality in the unknown
`H/Z` edge bits. For a fixed integer vector `v` and any integer vector
`q`, positivity of `G(B)` implies

\[
\boxed{v^TBv+2q^TBv
\le12\|v\|^2+2\Bigl(\sum_i v_i\Bigr)^2+\|q\|^2.}
\]

Indeed, `||Bv||²≥2qᵀBv-||q||²`. Substituting this lower bound into
`vᵀG(B)v≥0` proves the inequality. Set `q=B0v`, where `B0` is the
rejected point. The inequality then fails at `B0` by exactly
`-vᵀG(B0)v` before normalization.

For an undirected edge `ij`, the coefficient on its adjacency bit is

\[
2(v_iv_j+q_iv_j+q_jv_i).
\]

The entries involving the sixteen support vertices are fixed by the
incidence template, so they can be subtracted from the right-hand
side. This leaves a sound inequality on the 171 possible `H/Z` edges.
`coupled_zero_gram.linear_cut` regenerates the coefficients, checks
that the recorded point violates the inequality, and divides out a
common coefficient factor. The saved file contains compact summaries
of these inequalities; it does not need to repeat every coefficient.

## A neighborhood obstruction beyond the quadratic test

Fix a high/low partial witness, and let `D` be the first twenty-four
rows of its incidence matrix to `L`. These rows correspond to
`P∪N∪H`. For a zero vertex `z`, its remaining neighborhood row `y`
would satisfy

\[
Dy=2\mathbf1-B_{R,z}-(B^2)_{R,z},
\qquad \mathbf1^Ty=14-\deg_B(z),
\qquad y\ge0,
\]

where `R=P∪N∪H`. The actual row is binary, but nonnegativity already
gives a useful necessary condition.

For support core zero, incidence class one, and the first zero vertex
in the saved witness, these twenty-five equations are inconsistent
with nonnegativity. An exact integer dual vector `u` has

\[
u^TM\ge0,\qquad u^Tb=-1,
\]

where `M` is `D` with a bottom row of ones. Any feasible nonnegative
row would therefore imply `0≤uᵀMy=uᵀb=-1`.

The dual vector is saved in
`experiments/logs/eigenlattices/coupled-zero-row-certificate.json`.
The replay uses integer arithmetic and does not invoke a linear
programming solver:

```bash
.venv/bin/python experiments/workspace/coupled_zero_row_certificate.py --verify
```

This certificate fixes the chosen high/low edges as well as the
`H/Z` graph. It does not reject every high/low choice for that graph.

## A certified conditional full-incidence obstruction

A stronger test leaves every high/low and zero/low bit free. It fixes
only part of the `H/Z` adjacency for core zero, class one. Fifty-eight
specified adjacency bits, twenty present and thirty-eight absent,
already make the full thirty-five-point incidence conditions
inconsistent. The other 113 `H/Z` bits remain free.

The builder orders zero vertices by their eight-bit high neighborhoods.
The fifty-eight-bit statement includes this canonical ordering. It is
a forbidden pattern in the ordered model, not an unlabeled induced-
subgraph prohibition. The complete saved `H/Z` point already has the
required order, so its nonextendibility does not depend on a choice
of names for the zero vertices.

This is certified by the saved files
`coupled-zero-fixed-core-0-1-core.cnf`,
`coupled-zero-fixed-core-0-1.drat`, and
`coupled-zero-fixed-core-0-1-certificate.json` in
`experiments/workspace`. The retained CNF core is 171,896 bytes; the
trimmed proof is 945,999 bytes. The manifest records the exact
incidence template, the fifty-eight assumptions, and SHA-256 digests.

The replay rebuilds `coupled_shells_incidence.build`, adds the listed
unit assumptions, checks the full formula digest, checks that every
retained core clause belongs to that formula, and invokes drat-trim
at revision `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`.

```bash
.venv/bin/python experiments/workspace/coupled_zero_fixed_proof.py \
  --verify --drat-trim /absolute/path/to/drat-trim
```

This gives a necessary forbidden pattern within the canonically
labeled model. It is not a proof excluding the entire class.

## A stronger forest restriction for the doubled-edge support core

For support core zero, both deficit graphs consist of four doubled
edges. Each high signature selects an entire deficit pair on each
side. Distinct high signatures therefore have core overlap zero or
two. The bipartite graph recording these eight pair selections is
simple and two-regular on four positive and four negative pair labels.

The high-overlap graph must be connected, by the earlier counting
lemma. Thus the pair-selection graph is an eight-cycle, and its line
graph is also an eight-cycle. The high-overlap graph is consequently
a cycle with every edge carrying weight two. This applies to both
surviving incidence templates of support core zero.

Every high-neighbor set `S_z` of a zero vertex is independent in this
eight-cycle: two high vertices of core overlap two cannot have an
additional common zero neighbor. Its independence number is four,
and its only independent four-sets are the two parity classes.

There are therefore at most two degree-two vertices in `Z`; their
high sets, if both occur, are disjoint. A four-vertex path component
is impossible, since the high sets of its middle vertices must
intersect in one point. A three-leaf star is impossible because its
center would require an independent high set of size five.

If `H` had one edge, the eleven-type table would leave only
`2K2+2P3+K1` for `Z`. Its two path-middle high sets are the two parity
classes and cover `H`. Each endpoint of the high edge must use the
unique isolate and four degree-one zero vertices, so it must avoid
both path-middle vertices. No high vertex can do so. Hence `H` is
independent in these two templates, and the only possible zero
forests are

\[
5K_2+K_1,\qquad
3K_2+P_3+2K_1,\qquad
K_2+2P_3+3K_1.
\]

This reduces a structural subcase. It does not exclude either of the
two incidence templates.

## Exploratory searches and their limits

`coupled_zero_completion.py` fixes both `H/Z` and high/low edges and
chooses only zero/low bits. A run over the 447 saved high/low points
reported UNSAT for all 447 already with linear incidence equations
and visible mixed-pair upper bounds. This is a solver observation;
the run did not save 447 independent UNSAT certificates. The exact
certificates above cover only their stated points or patterns.

`coupled_zero_fixed_core.py` instead fixes `H/Z` and frees every low
incidence. Runs on saved points `(0,1)`, `(1,2)`, and `(4,32)` reported
UNSAT in approximately 1.60, 0.83, and 0.66 seconds of solving. The
conditional proof above provides a saved independent certificate for
the first case. No full thirty-five-point incidence witness was found.

`coupled_zero_incidence_cuts.py` couples a high/low model to the full
incidence model. It proposes a new `H/Z` graph, adds an exact linear
Gram cut when available, or tests that graph with all low incidences
free. An UNSAT assumption core gives another clause to the outer
search. A bounded run on `(0,1)` processed fourteen exact Gram cuts
and forty solver-reported assumption cores, then stopped at a
five-second unresolved inner call. This is not a completed search
and gives no whole-template exclusion.
