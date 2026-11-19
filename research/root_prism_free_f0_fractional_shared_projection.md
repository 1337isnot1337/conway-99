# Fractional shared-edge projection for component zero

## Scope and current result

The prepared model concerns component zero in the globally prism-free, F-free split18+18 shell. All 480 admissible first-component triples remain available. The second component and its fiber alignment remain free.

The complete structural and motif baseline reduces from 68,874 variables to 5,847 variables by averaging over twelve verified core relabelings. The quotient has 686 equalities, 11,373 inequalities, and 57,801 nonzero coefficients. This is an exact model preparation. No optimizer has been called, no shared-edge feasible point has been found, and no component has been excluded.

The inaccessible terminal registry of 4,404 selector cuts and the twelve earlier weighted row cuts are not included in this baseline. The relationship to raw potential cuts is proved below. No equivalence to Boolean-normalized versions of those cuts is asserted.

## The full baseline

Write \(h_a\in\{0,1\}^{18}\) for admissible triple \(a\), \(A_1\) for the first shell component, and

\[
q_a=2\mathbf 1-h_a-A_1h_a.
\]

The frozen domain has 480 triples and 68,394 eligible unordered pairs \(E\). Every \(h_a\) has weight three. Every \(q_a\) is nonnegative and has coordinate sum 24.

The selectors and shared edges satisfy

\[
0\le x_a\le1,\qquad
0\le y_{ab}\le x_a,\qquad y_{ab}\le x_b
\quad(\{a,b\}\in E).
\]

Impose the 171 upper-triangular component Gram equations, population 60, and all 90 certified motif inequalities \(x_a+x_b\le1\). The shared mixed equations are

\[
\sum_{b:\{a,b\}\in E}h_{bi}y_{ab}=q_{ai}x_a
\qquad(a=1,\ldots,480;\ i=1,\ldots,18).
\]

The same variable occurs at both ends of an undirected edge. This is the coupling that independent row boxes omit.

Summing the eighteen equations for \(a\) gives

\[
3\sum_b y_{ab}=24x_a.
\]

Thus degree eight is already present. No additional degree assumption is used.

## Exact projection theorem

Fix any \(x\in[0,1]^{480}\), without assuming integrality or the Gram equations. For a family of real potentials \(v_a\in\mathbb R^{18}\), define

\[
d_a=v_a\cdot q_a,\qquad
w_{ab}=v_a\cdot h_b+v_b\cdot h_a,\qquad
w_{ab}^{+}=\max(w_{ab},0).
\]

There exists a symmetric shared-edge assignment satisfying the mixed equations and activation bounds if and only if every potential family satisfies

\[
\boxed{\quad
\sum_a d_ax_a
\le
\sum_{\{a,b\}\in E}w_{ab}^{+}\min(x_a,x_b).
\quad}
\]

### Necessity

Multiply the mixed equations at \(a\) by \(v_a\) and sum. Each undirected edge appears in exactly its two endpoint blocks, giving

\[
\sum_a d_ax_a=\sum_{\{a,b\}\in E}w_{ab}y_{ab}.
\]

The box bounds give

\[
w_{ab}y_{ab}\le
w_{ab}^{+}\min(x_a,x_b).
\]

Summing proves the inequality. Negative edge weights cause no sign issue because \(y_{ab}\ge0\).

### Sufficiency

Let \(B\) be the matrix whose column for \(\{a,b\}\) contains \(h_b\) in block \(a\), \(h_a\) in block \(b\), and zero elsewhere. Let \(b(x)\) have block \(q_ax_a\). The question is whether

\[
b(x)\in
B\prod_{\{a,b\}\in E}[0,\min(x_a,x_b)].
\]

The set on the right is a nonempty compact convex set. Its support function at \(v\) is

\[
\max_y v^TBy
=
\sum_{\{a,b\}\in E}
\max\bigl((B^Tv)_{ab},0\bigr)\min(x_a,x_b).
\]

Here \((B^Tv)_{ab}=w_{ab}\). If \(b(x)\) lies outside the set, strict finite-dimensional separation supplies a potential family violating the displayed inequality. Conversely, all support inequalities imply membership.

It suffices to test all integer potential families. A strict separating gap persists under a sufficiently small rational approximation to \(v\), because the support expression is continuous in the finitely many potential coordinates. A positive common scaling then gives an integer separator.

This equivalence concerns shared mixed equations and activation. The Gram, population, and motif restrictions can be intersected with the resulting selector projection afterward.

## Endpoint allocations and Boolean quadratic checks

For a fixed potential family, choose one endpoint \(\sigma(\{a,b\})\in\{a,b\}\) of every positive-weight edge. Each choice gives a valid linear inequality

\[
\sum_a d_ax_a
\le
\sum_{\{a,b\}\in E}w_{ab}^{+}x_{\sigma(\{a,b\})}.
\]

At a fixed fractional point, minimizing the right side over all endpoint choices gives exactly

\[
\sum_{\{a,b\}\in E}w_{ab}^{+}\min(x_a,x_b).
\]

The choices are independent edge by edge. Therefore the full shared-edge model is the intersection of all raw potential inequalities with all endpoint allocations, together with selector bounds.

For Boolean selectors only,

\[
\min(x_a,x_b)=x_ax_b.
\]

This recovers the earlier quadratic potential check. For fractional selectors, replacing the minimum by the product is invalid in general. For example, two endpoint values \(1/2\) have minimum \(1/2\) but product \(1/4\).

Consequently the new LP captures an entire family of raw row and shared-potential cuts instead of only the finite stored choices. This statement does not cover coefficient truncations or threshold rounding justified only on Boolean selectors. Those inequalities require their own explicit rows and validity records.

## Verified quotient

The twelve maps are automorphisms of the complete 21-vertex core and preserve the complete triple and edge domains. Their composition table, inverses, target transport, and motif transport were checked exactly. They are relabelings used to average a necessary convex system. No completed graph is assumed to have these automorphisms.

The variable orbits are:

| Variable family | Full count | Orbit count | Orbit sizes |
|---|---:|---:|---|
| Selectors | 480 | 42 | Four of size 6; 38 of size 12 |
| Shared edges | 68,394 | 5,805 | Ten of size 3; 196 of size 6; 5,599 of size 12 |

Independent fixed-point counts reproduce both orbit counts by Burnside's formula. In particular, the edge calculation counts both pointwise-fixed edges and edges whose endpoints are exchanged.

Each original row is replaced by the sum of its integer coefficients on each variable orbit. No implicit division by orbit size occurs. All original rows retain explicit quotient maps; tautological zero rows are recorded.

| Constraint family | Full rows | Nonzero distinct quotient rows |
|---|---:|---:|
| Gram | 171 | 18 |
| Population | 1 | 1 |
| Mixed equations | 8,640 | 667 |
| Edge activation | 136,788 | 11,365 |
| Motif inequalities | 90 | 8 |

The 90 motif pairs form eight group orbits: seven of size twelve and one of size six. Their literal quotient has eight rows.

The structural checker performed 582,396 exact full-to-quotient row evaluations on deterministic rational test vectors. The motif extension performed 360 further evaluations and checked all 1,080 motif transports.

## Exact inspector and controls

The baseline module includes a BigInt rational-point inspector. Given a quotient numerator vector and a positive common denominator, it lifts the point and checks every full bound, all 171 Gram positions, population, all 8,640 mixed equations, all 136,788 activation inequalities, and all 90 motif inequalities. It also checks the quotient rows directly and compares the resulting feasibility status.

The previously recovered Gram-interior certificate supplies a positive control for the selector projection. Its 480 values are constant on the 42 selector orbits and satisfy the Gram, population, bounds, and motif conditions exactly. Extending that point by zero edges fails exactly 7,884 full mixed equations and all 667 nonzero quotient mixed rows. This is an intentional negative control for shared-edge feasibility. It is not a shared-edge feasible point.

The two pure JavaScript modules also have standard-library Node replay entry points. Their literal input blobs, source hashes, exact matrix hashes, and explicit scope limits are recorded in the preparation reports.

## Artifacts and remaining gate

- Structural source: experiments/workspace/root_prism_free_f0_fractional_structural_recovery.js.
- Structural report: experiments/logs/root-prism-free/f0-fractional-structural-recovery.json.
- Baseline source and exact primary inspector: experiments/workspace/root_prism_free_f0_fractional_baseline_recovery.js.
- Baseline report: experiments/logs/root-prism-free/f0-fractional-baseline-recovery.json.
- Baseline matrix SHA256: 30bd8808dcd0490fa9ae124abb2ef060cfc8bfcbc57b78eaac0a67fe89f0dd55.
- Baseline specification SHA256: 32172068b93386040b2c3ef0a351d44cfb57484f3ad335ad28f9760516efe1bf.

A production query still requires review of the numerical matrix construction, positive scaling, status preservation, and exact primal/Farkas acceptance. A feasible fractional point would resolve this relaxation only. An exact infeasibility certificate would exclude this conditional component-zero stratum, not the full Conway problem.
