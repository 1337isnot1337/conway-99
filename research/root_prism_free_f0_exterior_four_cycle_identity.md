# Exterior four-cycles and the omitted component

In the existing globally prism-free, F-free split18+18 branch, let C0 and C2 be the two connected cubic shell components and D the simple eight-regular exterior graph on sixty vertices. Write c4(G) for the number of unoriented four-cycles in G. Then
\[
c_4(D)=171+c_4(C0)+c_4(C2).
\tag{1}
\]
For the fixed component zero, c4(C0)=6, so
\[
c_4(D)=177+c_4(C2),\qquad177\le c_4(D)\le190.
\tag{2}
\]
These are necessary conditions on a complete exterior graph. No exterior graph is evaluated or excluded here, and no native row is installed.

## Derivation from the accepted spectral decomposition

The [spectral-gap theorem](root_prism_free_f0_spectral_gap_pair_minor.md) gives the full-core plus Schur matrix S. It is zero on the eighteen-dimensional image of H^T, and on ker(H) it is 9(3I-D). Its spectrum is
\[
0^{(36)},\quad63^{(9)},\quad36+9\lambda_i(C2|W_2)\ (1\le i\le15),
\]
where W_2 is orthogonal to the three fiber indicators.

The mixed equation
\[
HD=2J-(I+C0)H
\]
and the column weight three imply
\[
HD=\bigl(\tfrac23J_{18}-I-C0\bigr)H.
\]
The first incidence has row rank eighteen. Hence the spectrum of D on im(H^T) consists of 8, two copies of -1, and -1-lambda_i(C0|W_0) for i=1,...,15.

Combining the two invariant subspaces gives the complete sixty-dimensional spectrum
\[
8,\quad(-1)^{(2)},\quad3^{(18)},\quad(-4)^{(9)},
\quad-1-\lambda_i(C0|W_0),\quad-1-\lambda_i(C2|W_2).
\tag{3}
\]
No isomorphism or fixed relative fiber alignment between the two components is used.

For either triangle-free cubic component C of order eighteen, the fiber-constant spectrum is 3,0,0. On its fifteen-dimensional orthogonal complement W,
\[
\operatorname{tr}(C|_W)=-3,\quad
\operatorname{tr}((C|_W)^2)=45,\quad
\operatorname{tr}((C|_W)^3)=-27.
\]
The standard closed-walk count gives
\[
\operatorname{tr}C^4=18\cdot3\cdot5+8c_4(C)=270+8c_4(C),
\]
so the fourth moment on W is 189+8c4(C). Expanding (1+lambda)^4 therefore yields
\[
\sum_{i=1}^{15}(1+\lambda_i)^4
=15+4(-3)+6(45)+4(-27)+189+8c_4(C)
=354+8c_4(C).
\]
Substituting into (3),
\[
\operatorname{tr}D^4
=8^4+2+18\cdot3^4+9\cdot4^4+708+8(c_4(C0)+c_4(C2))
=8568+8(c_4(C0)+c_4(C2)).
\]
The same closed-walk count for the eight-regular graph D is
\[
\operatorname{tr}D^4=60\cdot8\cdot15+8c_4(D)=7200+8c_4(D).
\]
Comparison proves (1).

## The finite numerical bounds

In a cubic component, the three pairs of neighbors of a vertex can each lie in at most one four-cycle through that vertex. A second opposite vertex for the same pair would give those two neighbors at least three common neighbors in the full graph, contradicting its codegree bound of two. Thus every component vertex belongs to at most three four-cycles, and
\[
4c_4(C2)\le18\cdot3,\qquad c_4(C2)\le13.
\]
The lower bound is zero.

For fixed C0, direct arithmetic on the already accepted eighteen adjacency bit rows finds exactly twelve unordered pairs with two component common neighbors:
(0,7), (0,13), (1,6), (1,12), (2,9), (2,15), (3,8), (3,14), (4,11), (4,17), (5,10), (5,16).
Each four-cycle has two opposite pairs, so c4(C0)=12/2=6. This is a small check of fixed core metadata, not a catalogue sweep.

## Interpretation and limits

For an actual D, the full common-neighbor cap makes every unordered exterior pair have at most two D-common neighbors. Equation (1) is therefore equivalently
\[
\#\{\{a,b\}:|N_D(a)\cap N_D(b)|=2\}
=342+2(c_4(C0)+c_4(C2)).
\]
For fixed component zero this count is 354+2c4(C2).

The missing component's four-cycle count remains unknown. This note does not assert that every integer from zero through thirteen occurs among the accepted component catalogue. It does not assert independence from every existing polynomial, residual, or spectral condition. Equation (1) is itself a consequence of the accepted complete spectral decomposition; its use is as an exact complete-candidate check and a restriction on the omitted component's possible type.

No linear expression in the current edge variables alone is supplied. Counting four-cycles or exterior common-neighbor pairs introduces products. It would be incorrect to apply this equality to an averaged adjacency matrix as though it described a single graph.

## Immutable sources

- research/root_prism_free_f0_spectral_gap_pair_minor.md, Git 168ca05d66609a2ac7027d3958a4f22c63385e1c, SHA-256 169a4b0c8ba1381302d0eeacb449599a5e4913cd6a55a24bb711e5d4126829ce.
- research/root_prism_free_f0_components.md, Git e9ba184ee254130652c252b981487266ad078c15.
- research/root_prism_free_f0_exterior_triangle_counts.md, Git 83580252626b2951069ac5f618c0462ac8a42e9e.
- Accepted fixed-domain archive f0-exterior-row-domains02.json.gz, SHA-256 665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4; raw SHA-256 fa3bd2e5bb541d58cb647aa1d3df95a9d3c17e394836a657ad4f4bf6eb5f6bfe.

There was no assignment search, new component census, native construction, optimizer call, or full-model feasibility claim in this derivation.
