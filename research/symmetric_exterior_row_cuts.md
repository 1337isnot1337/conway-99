# Selector cuts from shared exterior rows

A failed symmetric real edge completion can give a linear inequality
for every incidence selection. The inequality need not fix the failed
selection. This extends the separate row-capacity cuts by requiring both
endpoint equations to use the same edge variable.

This note proves the implication. It does not report an infeasible
joint model or exclude any new component or matching case.

## Activated row equations

Use a complete finite domain of distinct possible exterior signatures.
Each signature labels at most one exterior vertex. In the F0 component
domain every column has three core neighbors. In the indexed rook
35-core domain every column has at least three. The two-common-neighbor
bound therefore prevents repeated columns in both applications.

Write z_a for the selector of column a and y_ab for an undirected edge.
The eligible edge set must include every edge possible in a completion.
For an actual graph, the activated mixed and degree equations have the
form

\[
\sum_{b:\{a,b\}\in E} w_b y_{ab}=t_a z_a,
\qquad 0\leq y_{ab}\leq z_a,\quad y_{ab}\leq z_b.
\]

Here w_b can be the incidence column h_b with an appended one, and t_a
can be the mixed quota q_a with an appended exterior degree d_a. For
the split-shell component, the degree equation already follows by
summing the eighteen mixed equations, so the appended coordinate is
optional. The respective frozen model preparations justify the complete
signature and eligible-edge domains.

Choose any integer vector v_a for each target a. Put

\[
\delta_a=v_a^Tt_a,
\qquad
\omega_{ab}=v_a^Tw_b+v_b^Tw_a.
\]

Summing the scalar products of all activated row equations gives

\[
\sum_a\delta_a z_a=\sum_{\{a,b\}\in E}\omega_{ab}y_{ab}.
\]

Every edge appears once on the right with contributions from both
endpoint equations. This is where shared edge variables enter the proof.

For each edge with positive omega, choose one endpoint sigma(ab). Since
y_ab is at most either endpoint selector, every actual incidence obeys

\[
\sum_a\delta_a z_a
\leq
\sum_{\{a,b\}\in E:\ \omega_{ab}>0}
\omega_{ab}z_{\sigma(ab)}.
\]

Negative edge terms are discarded using y_ab>=0. The resulting inequality
is linear in the selectors. In particular, with

\[
c_a=\delta_a-
\sum_{\substack{\{i,j\}\in E:\ \omega_{ij}>0\\\sigma(ij)=a}}
\omega_{ij},
\]

the universal necessary cut is sum_a c_a z_a<=0. Coefficients may have
either sign. No assumption about which selectors are one enters its
validity.

## Turning a fixed-incidence failure into a violated cut

Let S be a candidate selected set. Give vertices outside S zero potential.
For a positive edge with both endpoints in S, choose either endpoint.
For a positive edge with exactly one endpoint in S, choose the endpoint
outside S. An edge with both endpoints outside S has weight zero.

At the candidate z=1_S, the cut's exact left side is

\[
\sum_{a\in S}v_a^Tt_a-
\sum_{\{a,b\}\in E(S)}\max(\omega_{ab},0).
\]

A strictly positive integer value rejects that incidence. The cut stays
valid for every other incidence, including selections that omit some
members of S or add columns outside S. The saved set only determines
the potential support and endpoint choices.

The fixed-incidence symmetric row relaxation is

\[
\sum_{b:\{a,b\}\in E(S)}w_b y_{ab}=t_a
\quad(a\in S),\qquad 0\leq y_{ab}\leq1.
\]

The image of the edge box is a compact polytope. Its support function
in direction (v_a) is the sum of positive omega values. Therefore this
relaxation is feasible exactly when the displayed gap is nonpositive
for every real potential. If it is infeasible, strict separation gives
a positive gap. Since the data are rational and the gap is strict,
rational potentials can be chosen and scaled to integers.

Thus every infeasible fixed-incidence symmetric row box has a violated
integer selector inequality of this form. A numerical dual can propose
the potentials. Acceptance requires direct integer recomputation over
the complete global eligible-edge domain, including all edges from S
to columns absent from the candidate.

## Why separate row boxes can miss the obstruction

Consider a path 0--1--2, with unit degree required at each selected
vertex. All three independent row boxes are feasible when all vertices
are selected. The endpoint rows choose their sole edges. The middle
row can choose either edge.

For shared edge variables, the endpoint rows require y_01=y_12=1,
while the middle row requires their sum to equal one. Give the three
degree equations potentials (1,-1,1). Both edge weights are zero.
The universal selector inequality is

\[
z_0-z_1+z_2\leq0.
\]

The all-selected candidate has value one. This is an algebraic control
for the method, not a Conway core or an exclusion in the research ledger.

## Limits

The cut family detects failure of the shared real row relaxation.
Passing it does not produce binary edges, outside-pair common-neighbor
counts, a missing shell component, or a full strongly regular graph.
A SAT exclusion of one fixed incidence can use integrality or pair caps
that this real dual does not capture. Such an exclusion cannot be lifted
by this argument unless an appropriate exact potential is also supplied.
