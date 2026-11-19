# Integer linear certificates for ten norm-16 templates

This note gives independent linear proofs for ten of the fourteen additional
template exclusions in [the coupled-shell census](coupled_shells.md). It does
not exclude another class. The remaining census is still 447 classes and
4,720 labeled templates, conditional on the existence of a norm-16 negative
eigenvector.

The new relaxation counts high-neighborhood masks of low and zero vertices.
It does not choose edges within `Z`, from `Z` to `L`, or within `L`. The
integer Farkas certificates can be replayed without an optimization or SAT
solver. Their input templates are explicit in the certificate file.

## Results

Core and orbit indices use the archived complete-incidence census. An
H-edge case is either the empty graph on `H` or one specified edge.

| Core | Orbit | Exhaustive H-edge cases | Nonzero terms per certificate |
| --- | ---: | ---: | ---: |
| 2 | 31 | 12 | 6–119 |
| 3 | 75 | 7 | 25–81 |
| 4 | 33 | 2 | 57–58 |
| 4 | 35 | 2 | 51–57 |
| 4 | 159 | 3 | 59–141 |
| 4 | 166 | 3 | 59–147 |
| 4 | 187 | 6 | 13–100 |
| 4 | 204 | 6 | 9–128 |
| 4 | 214 | 5 | 45–122 |
| 4 | 225 | 5 | 91–159 |
| Total | | 51 | |

These ten templates are excluded in every H-edge case. For core 4, orbits
64, 136, 165, and 186, the search encountered an aggregate branch reported
feasible by floating-point LP. The linear method does not replace their
existing DRAT proofs. Before reaching those branches, it certified another
ten individual H-edge exclusions. The saved file therefore has 61 exact
branch certificates, of which 51 prove the ten complete template
exclusions. It also records the four floating-feasible branches; no exact
feasibility claim depends on them. The search stopped on the first branch
without an exact exclusion for each of those four templates.

All 447 saved partial SAT witnesses project into this linear model by
integer substitution. Each projection satisfies every equation and every
inequality exactly. Thus searching this relaxation on those witnesses'
templates cannot give another exclusion.

## Input and exhaustive high graphs

Use the partition `P ∪ N ∪ H ∪ L ∪ Z` of sizes `8,8,8,64,11` from the
coupled-shell note. Let `C` be the adjacency matrix on the sixteen support
vertices `P ∪ N`, and let `D` be the 8-by-16 incidence matrix from `H` to
that support. The template fixes both matrices. It also fixes the number

\[
r_{pn}=2-C_{pn}-\sum_{h\in H}D_{hp}D_{hn}
\]

of low vertices whose support neighbors are exactly `p ∈ P` and `n ∈ N`.
Each `r` is zero, one, or two, and their sum is 64.

The coupled-shell degree and pair-count argument proves `e(H) ≤ 1` without
assuming symmetry. Thus the high graph has adjacency matrix `E=0`, or has
one of the 28 possible edges. For each proposed graph, every high row must
admit its remaining low incidences. For high vertex `h`, their required
support incidence vector is

\[
u_h=2\mathbf1-D_h-D_hC-(ED)_h.
\]

A necessary test is a bipartite capacity matching between `P` and `N`,
with row and column demands given by `u_h`. The capacity of `(p,n)` is
`r_{pn}`, except that it is zero when `h` is adjacent to both `p` and `n`.
Such a low vertex cannot also be adjacent to `h`: that adjacent pair would
already have two common support neighbors. A proposed high edge is also
forbidden if its endpoints already share two support neighbors.

The replay enumerates all 29 high graphs and applies these necessary
tests. Its matching implementation is an integral augmenting-path
max-flow calculation. It is separate from the recursive matching routine
used by the SAT model. No graph automorphism or unproved restriction on
the high graph is used.

## Mask variables and admissibility

For each low signature `(p,n)` with positive multiplicity, and each
eight-bit mask `m`, let `x[p,n,m]` count low vertices with exactly that
high-neighborhood mask. For each zero mask `m`, let `y[m]` count zero
vertices with that high neighborhood. The relaxation makes these variables
nonnegative reals. Every graph completion would give nonnegative integers.

Write `d[p,n]` for the support indicator of the two low neighbors, and
interpret `m` as a zero-one column indexed by `H`. A low mask is retained
only when all these necessary inequalities hold:

\[
m_h+(Em)_h+(D d[p,n])_h\le2\quad(h\in H),
\]

\[
(D^T m)_t+(C d[p,n])_t+d[p,n]_t\le2
\quad(t\in P\cup N).
\]

The first counts already determined common neighbors of a high/low pair,
plus its adjacency bit. The second does the same for a support/low pair.
Furthermore, a mask cannot contain both `h,k` when
`(DDᵀ)[h,k]+E[h,k] ≥ 2`: the low vertex would exceed that high pair's
common-neighbor budget.

A zero mask must have at least two bits, because `d_Z(z)=d_H(z)-2`.
It obeys the same high-pair restriction. Its remaining low neighbors must
admit a bipartite matching with capacities `r` and demands
`2·1-Dᵀm`. This is again a necessary matching test, not an assertion that
all low incidences can be chosen simultaneously.

These are finite mask checks over only 256 masks. They involve integer
arithmetic and max-flow. The matrix builder imports no SAT library.

## Linear equalities and upper bounds

The low populations and all high/support common-neighbor counts give

\[
\sum_m x[p,n,m]=r_{pn},
\]

\[
\sum_{p,n,m}d[p,n]_t m_h x[p,n,m]
=2-D_{ht}-(DC)_{ht}-(ED)_{ht}.
\]

The zero population and forced high/zero degrees give

\[
\sum_m y[m]=11,
\qquad
\sum_m m_h y[m]=4+d_H(h).
\]

For each unordered high pair `h,k`, the full common-neighbor identity is

\[
\sum_{p,n,m}m_hm_k x[p,n,m]
+\sum_m m_hm_k y[m]
=2-(DD^T)_{hk}-E_{hk}.
\]

No high vertex can be a common neighbor of distinct high vertices when
`E` has at most one edge, so there is no omitted high contribution here.
Support, low, and zero vertices exhaust the remaining possibilities.

Two copies of one low signature already share two support neighbors.
They therefore have no common high neighbor. For each signature of
multiplicity two, impose

\[
\sum_{m:m_h=1}x[p,n,m]\le1\quad(h\in H).
\]

Two distinct zero vertices cannot share a high mask of size at least
three. Hence `y[m] ≤ 1` for those masks. For masks of size two, the common
high pair has at most two common neighbors, giving `y[m] ≤ 2`.

The builder converts every upper bound to an equality by adding a
nonnegative slack variable. It obtains an integer system

\[
Aw=b,\qquad w\ge0.
\]

These equations discard many completion requirements, including all
unselected zero/low and low/low edges. Infeasibility is sufficient for an
exclusion; feasibility is only feasibility of a necessary relaxation.

## Exact certificate replay

A saved certificate is an integer row vector `q` satisfying

\[
q^TA\ge0\quad\hbox{entrywise},\qquad q^Tb<0.
\]

If `Aw=b` and `w≥0`, these inequalities would imply both
`qᵀAw≥0` and `qᵀAw=qᵀb<0`. The contradiction uses only integer
arithmetic.

The LP optimizer is used to find candidate rays. Before saving a
certificate, the code checks every column dot product and the right-hand
side with Python integers. Replay rebuilds the mask system, regenerates
the full list of admissible high graphs, verifies dimensions and labeled
ray terms, and checks the inequalities again. A complete template
exclusion requires coverage of every admissible high graph. Partial
branch exclusions are retained without claiming complete coverage.

Passing the orbit archive to replay also checks that each explicit
template is exactly the template at its claimed core/orbit index.
The 447 positive controls reconstruct mask counts directly from the
saved adjacency bits and verify `Aw=b` with nonnegative integral slacks.
They do not call an optimizer.

## Files and reproduction

The implementation is `experiments/workspace/coupled_shells_linear.py`.
The certificate file is
`experiments/workspace/coupled-shells-linear-certificates.json`.
Search, exact replay, and positive-control logs are in
`experiments/logs/eigenlattices/coupled-shells-linear-{search,replay,controls}.log`.

From the repository root, the following commands replay the saved
certificates and all 447 positive controls. NumPy and SciPy are needed for
integer matrix storage; no optimization or SAT solver is invoked.

```bash
python experiments/workspace/coupled_shells_linear.py \
  --replay experiments/workspace/coupled-shells-linear-certificates.json \
  --orbits experiments/logs/eigenlattices/coupled-shells-orbits.json

python experiments/workspace/coupled_shells_linear.py \
  --orbits experiments/logs/eigenlattices/coupled-shells-orbits.json \
  --witnesses experiments/logs/eigenlattices/coupled-shells-low-all.json
```

To repeat the bounded discovery calculation, use a separate output file:

```bash
python experiments/workspace/coupled_shells_linear.py \
  --manifest experiments/workspace/coupled-shells-low-*-certificate.json \
  --seconds 3 --out /tmp/coupled-shells-linear-new.json
```

The time bound applies to the initial feasibility LP for each high graph.
An infeasible status triggers the existing exact-Farkas extraction helper.
Only a ray that passes the integer checks counts as an exclusion.

The longest displayed certificates still use over one hundred constraint
rows. They are finite arithmetic proofs, not short conceptual
contradictions. None of these results proves the existence of a norm-16
eigenvector or settles Conway's 99-graph problem.
