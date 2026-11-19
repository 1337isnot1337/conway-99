# A two-parameter decorated model for root 42

## Scope

This preparation retains the induced graph on the complete high set of root 42. It has 343 labelled states and 33 orbits under the actual root automorphism group. Of these, 319 states and 31 orbits have at most four high vertices, so all their moments are known from the order-ten count catalogue. The remaining 24 states form two orbits of size 12.

All exact state masses are affine functions of two unknown fifth moments, denoted \(u_0,u_1\). Both must be even in an actual graph. The source checks the full symbolic moment equations and stabilizer divisibilities without loading a count point.

No optimizer, tensor generation, new catalogue lookup, or point query was used.

## Complete states and edge choices

The root consists of a four-leaf star with center 5 and an isolated vertex 4. Write

\[
A_{ij}=\{i,j,4\}\quad(0\le i<j<4),\qquad
B_i=\{i,4,5\}.
\]

These ten masks are the complete classes with at least three root neighbors. Each class is Boolean because two different vertices in it would have at least three common neighbors.

A presence set is admissible for the visible common-neighbor caps exactly when

\[
\deg_A(i)+\mathbf1[B_i\text{ selected}]\le2\quad(0\le i<4),
\qquad
\#\{B_i\text{ selected}\}\le2.
\]

If it contains \(a\) masks of type \(A\) and \(b\) of type \(B\), then \(2a+b\le8\) and \(b\le2\), so \(a+b\le5\). At population five, equality holds: the three selected \(A\)-pairs form a Hamiltonian path on the four leaves, and the two \(B\)-masks are its endpoints. There are 12 such presence sets.

Only a complementary pair \(A_{ij},A_{k\ell}\) can be adjacent among the high vertices. The three possible pairs are disjoint. A pair involving a \(B\)-mask either has two common root neighbors or would give the star center a third common neighbor with an \(A\)-vertex. Every subset of the available complementary-pair edges satisfies all visible caps.

The source independently tests all 1,024 presence sets, all 45 possible pairs, and all 18,629 internal graph choices over admissible presence sets. The resulting state counts by high population are:

| Population | Presence sets | Decorated states |
|---:|---:|---:|
| 0 | 1 | 1 |
| 1 | 10 | 10 |
| 2 | 45 | 48 |
| 3 | 100 | 124 |
| 4 | 85 | 136 |
| 5 | 12 | 24 |

Each five-set contains exactly one possible complementary edge. Its absence and presence give the two fifth-state orbits. The source enumerates all 24 root automorphisms and checks their action on every mask, possible edge, and state.

## Known moments and labelled normalization

For a decorated pattern \((A,E)\) with at most four high vertices, distinct high masks make its rooted indicator sum equal to

\[
m(A,E)=|\operatorname{Aut}(F_{A,E})|\,N_{F_{A,E}}.
\]

The source matches every one of the 319 literal graphs against the frozen 31 induced types from the presence preparation. It independently counts the automorphism order of each literal representative. No orbit-stabilizer divisor is inserted in this labelled embedding moment.

This refinement uses existing data. The previous presence moments sum over these induced edge patterns; the new model keeps them separate.

## Exact inversion

Order decorated states by induced restriction: \((A,E)\le(T,D)\) when \(A\subseteq T\) and \(D\) restricts exactly to \(E\) on \(A\). Below a fixed upper state, the interval is a Boolean lattice on the added high vertices. Its Möbius coefficient is \((-1)^{|T|-|A|}\).

Every exact-state mass is therefore

\[
w(A,E)=
\sum_{\substack{(T,D)\ge(A,E)\\|T|\le4}}
(-1)^{|T|-|A|}m(T,D)
+
(-1)^{5-|A|}
\sum_{\substack{(T,D)\ge(A,E)\\|T|=5}}u_{\operatorname{orbit}(T,D)}.
\]

The frozen output retains all 343 affine forms, every root orbit, and all stabilizers. It checks all 343 symbolic zeta equations and all 253 coarsenings to the previous presence model. Under coarsening, the old fifth moment is exactly \(u=u_0+u_1\).

The 31 known invariant equations contain a population-triangular minor with diagonal 1. Thus they have rank 31 on the 33 orbit-state variables, leaving exactly two affine parameters.

## Integer units

The stabilizer of a decorated state acts freely on the injective ordered root embeddings realizing that exact state. Its order divides the exact-state mass. Each fifth-state stabilizer has order 2, so \(u_0\) and \(u_1\) are even.

For every state, the source also checks that each known-count coefficient is divisible by its stabilizer order and that twice each unknown coefficient has the same divisibility. Therefore even \(u_0,u_1\) satisfy all 343 state stabilizer congruences. This is checked coefficientwise, before substituting any count values.

## Next test and limits

An exact query would substitute the immutable count point into the affine constants, require all 343 masses to be nonnegative, and decide whether the resulting rational polygon contains an even integer pair. This needs no linear-programming optimizer.

The previous presence test constrains only the sum \(u_0+u_1\). The decorated test also constrains how that mass splits between the edge-absent and edge-present fifth states. It can detect negative edge-specific exact-state masses that presence coarsening hides.

This package is a complete point-independent preparation for that finite test. It does not yet report feasibility or separation at the count point, and a feasible local distribution would not construct a graph.
