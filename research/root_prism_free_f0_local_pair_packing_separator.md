# Local mixed equations with core-pair packing

This preparation concerns one local LP at signature178 of the accepted first-component incidence. It does not change the current native count model or the exterior SAT model. No production LP has run in this package.

## Prior work and the new constraint

The earlier `root_prism_free_f0_exterior_row_box_separation.py` explicitly records `neighbor_pair_packing_in_LP=False`. Its dual uses the18 mixed common-neighbor equations and individual neighbor upper bounds. The present preparation adds all153 unordered core-pair packing bounds to that local LP. Previously checked core-pair edge cliques justify the same packing geometry, but they were not multipliers in the earlier local separator.

The accepted exterior UNSAT proof explains the choice of anchor178. Its116 retained clauses use13 mixed rows at that anchor and five two-neighbor exclusions. The five neighbor pairs are (58,71), (87,124), (90,124), (225,230), and (230,392). Each pair has two common core sites. The preparation binds this attribution and the accepted DRAT cold record. It does not repeat a SAT query, a proof check, or completion's separate local-cover derivation. The arithmetic cut below does not use the fixed selection or its UNSAT proof as a universal premise.

## Universal inequality

Let `x_a` indicate that a particular allowed exterior signature is present. High signatures are Boolean in this fixed18-core setting. Let `y_ab` indicate the actual edge between signatures `a` and `b`. Write `h_b` for the three core neighbors of `b`, and let `N(a)` be the complete original eligible edge domain at `a`. This domain is not pruned using the candidate or proved zero Y-orbits.

The SRG mixed equations are

\[
\sum_{b\in N(a)} h_b y_{ab}=q_a x_a,
\qquad 0\le y_{ab}\le x_b.
\]

Here `h_b` is the binary18-vector of the signature, and

\[
(q_a)_i=2-\mathbf1[i\in h_a]-\sum_{j\in h_a}(A_D)_{ij}.
\]

Its entries are0,1,2 and its sum is24. Since every `h_b` has weight3, the mixed equations already imply exterior degree8 when `x_a=1`.

For every unordered core pair `p={i,j}`,

\[
\sum_{b\in N(a):p\subseteq h_b}y_{ab}\le x_a.
\]

Indeed, if two different neighbors `b,c` of `a` both contain `i,j`, then `b,c` have the three distinct common neighbors `a,i,j`. This exceeds the common-neighbor cap even for a nonadjacent pair. When `x_a=0`, all incident edges vanish. No symmetry of a hypothetical host graph is used.

Choose any integer vector `v` of length18 and nonnegative integer weights `mu_p`. Define

\[
t=v\cdot q_a-\sum_p\mu_p,
\qquad
w_b=\max\left(v\cdot h_b-\sum_{p\subseteq h_b}\mu_p,0\right).
\]

Multiplying the mixed equations by `v` and subtracting the weighted packing upper bounds gives

\[
t x_a\le
\sum_{b\in N(a)}
\left(v\cdot h_b-\sum_{p\subseteq h_b}\mu_p\right)y_{ab}
\le \sum_{b\in N(a)}w_b x_b.
\]

The second step discards nonpositive edge coefficients and applies `y_ab<=x_b` to positive coefficients. This is a universal selector inequality for the stated fixed-core problem. Its validity does not require `t>0`, although the strict-separation acceptance rule below implies `t>0`.

## One fixed bounded search

At anchor178, `h_a={2,8,13}`. The complete eligible neighborhood contains244 signatures;31 are in the frozen selected set. The LP has202 variables and31 upper-bound rows with217 nonzeros:

| Variables | Count | Bounds |
|---|---:|---|
| Site weights `v_i` |18|[-1,1]|
| Core-pair weights `mu_p` |153|[0,3]|
| Selected-neighbor positive parts `z_b` |31|[0,3]|

It minimizes

\[
-q_a\cdot v+\sum_p\mu_p+\sum_{b\in N(a)\cap S}z_b
\]

subject to

\[
v\cdot h_b-\sum_{p\subseteq h_b}\mu_p-z_b\le0
\quad(b\in N(a)\cap S).
\]

The zero vector is feasible. Because `h_b` has three entries and `v_i<=1`, its raw score is at most3. Hence positive parts need no upper bound larger than3. Any pair weight above3 can be reduced to3 without increasing a constrained positive part; that reduction improves the objective. Thus these finite search bounds do not rely on the candidate's observed zero coordinates. They are used for discovery only; the cut verifier accepts only directly checked integer arithmetic.

One HiGHS simplex invocation is planned, with one thread, seed0, and at most30 native seconds. Each preparation, production, or cold stage has one60-second owned deadline. The supervisor is the already reviewed exterior-query supervisor. There is no automatic retry, second LP, or additional anchor.

## Exact acceptance and transports

The native solution is saved as exact hexadecimal float strings before reconstruction. Site and pair potentials are clamped to their declared search boxes as exact binary fractions. A frozen finite list of scales, followed by the common binary denominator, proposes integer vectors. Pair weights remain nonnegative. A positive common gcd can be removed.

For each proposal, all244 original neighbors are restored. The verifier calculates `t`, every signed raw neighbor coefficient, and every `w_b` with Python integers. Acceptance requires

\[
t-\sum_{b\in N(a)\cap S}w_b>0.
\]

No native status, float residual, or numerical objective is an acceptance certificate. The integer proposal also yields an exact rational feasible point of the advertised bounded dual: divide by

\[
D=\max\left(1,\max_i|v_i|,\max_p\lceil\mu_p/3\rceil\right)
\]

and set each `z_b=w_b/D`. The source checks every bound, all31 rows, and the exact negative objective.

All12 actual core relabelings transport the site coordinates, unordered core pairs, anchor, and complete neighbor domain. The preparation verifies each action on the21-core and the480 signature/target/neighbor records. A transported row is re-contracted from its own full eligible neighbors; it is not inferred from a graph automorphism. Identical normalized rows are deduplicated only after all12 witnesses are retained.

The cold verifier reconstructs the full frozen inputs and contracts pair weights from literal unordered pairs, independently of the producer's precomputed pair-index lists. It also reproduces the exact float-to-integer proposal. Only a separate accepted cold owner can produce the final certified cut file. A timeout, a native overrun, an incomplete proposal, or failure to find a strict integer gap preserves an UNKNOWN result. It does not establish local feasibility, exterior feasibility, or a graph.

## Controls and limits

Preparation includes exhaustive small binary and half-integral feasible examples of the multiplier inequality, literal coordinate relabelings, the inactive-anchor case, and rejection of a negative pair multiplier. A separate synthetic example is box-feasible but violates a pair packing bound: the two columns `{0,1,2}` and `{0,1,3}` with demand `(2,2,1,1)` force both columns, although their shared pair permits at most one. The weights `v=(1,0,0,0)` and `mu_{01}=1` give strict gap1.

That example proves a difference between the two declared local relaxations. It is not a point of the full F0 model and does not establish independence from every already encoded global inequality. All current models remain frozen.
