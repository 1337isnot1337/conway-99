# A selector cut from incompatible symmetric exterior rows

The 60-triple incidence that passed every separate row-box test has no
symmetric real edge completion satisfying its degree and mixed equations.
One LP call found infeasibility; an exact integer Farkas certificate and
optimizer-free replay establish the contradiction. The certificate also
gives a necessary linear inequality on all 480 incidence selectors.

The new inequality rejects this incidence without fixing it in future
models. It does not exclude component zero or the entire split case.

## Exact symmetric-row contradiction

The shared-edge relaxation has 1,220 undirected variables with bounds
from zero to one, 1,080 mixed equations, and 60 degree equations.
Introducing 1,220 nonnegative upper-bound slacks gives 2,440 nonnegative
variables and 2,360 equations.

The single authorized LP call returned infeasible. Its integer ray has
58 nonzero multipliers, with maximum absolute value five. Direct replay
checks every coefficient of all 2,440 nonnegative variables and gives

$$
E^Tr\geq0,\qquad b^Tr=-2.
$$

This is a contradiction for the fixed first incidence, independent of
the missing second component and its alignment. The total run took
4.101 seconds within its 60-second limit. No SAT query was needed.

The result is
`experiments/logs/root-prism-free/f0-row-box-design-linear-run01.json`,
SHA256
`96486063f18150392852eeddd55e7e023b4987e0b2233d3fd133c88168de29f9`.
The optimizer-free replay is
`f0-row-box-design-linear-run01-replay.json`, SHA256
`b73b97d938ec9cbc5754d09361eccd7967f68da063d199eb183c2462953ad393`.

## Extending the certificate to all selectors

The complete domain has 480 distinct possible triple signatures and
68,394 universally eligible undirected edges. For every actual
completion, the activated mixed equations are

$$
\sum_{b:\{a,b\}\in E} h_b y_{ab}=q_a z_a,
\qquad 0\leq y_{ab}\leq z_a,\quad y_{ab}\leq z_b.
$$

Absorbing the Farkas degree multipliers produces integer vectors $v_a$
supported at nine signature indices:

$$
35,\ 93,\ 136,\ 232,\ 261,\ 335,\ 397,\ 410,\ 476.
$$

All other targets receive zero potential. Define

$$
\delta_a=v_a^Tq_a,\qquad
\omega_{ab}=v_a^Th_b+v_b^Th_a.
$$

Summing the activated equations gives
$\sum_a\delta_a z_a=\sum_{\{a,b\}\in E}\omega_{ab}y_{ab}$.
Discard each nonpositive edge contribution. For every positive edge,
allocate its weight to one endpoint selector, using $y_{ab}\leq z_a$
or $y_{ab}\leq z_b$ at that endpoint. This gives the universal inequality

$$
\sum_a c_a z_a\leq0,
\qquad
c_a=\delta_a-\sum_{\substack{\omega_{ij}>0\\\text{allocated to }a}}\omega_{ij}.
$$

For the present certificate, a positive edge inside the saved selected
set is allocated to its smaller signature index. A positive edge that
crosses its boundary is allocated to the outside endpoint. The saved
set chooses this allocation; it is not a hypothesis of the inequality.
The validity follows from the activated equations and endpoint bounds
for every selector assignment arising from a completion.

The complete global domain has 265 positive-weight edges for these
potentials. Two lie inside the saved selection and 263 cross its
boundary. The two internal contributions are weight six on edge
$\{85,476\}$ and weight three on edge $\{136,179\}$.
The total target demand is 15 and the internal positive capacity is
nine, giving an integer gap of six.

All resulting coefficients have gcd three. After division, the cut is

$$
2z_{35}+z_{93}+z_{136}+z_{261}+3z_{476}
\leq\sum_{b\in B}w_bz_b,
$$

where the certificate lists all 163 indices in $B$ and their positive
integer weights. The weights are at most eight. The saved incidence
has left side eight and right side six. Thus the normalized gap is two.

## Complete replay and transports

The standard-library verifier independently reconstructs the complete
480-signature domain, all 68,394 eligible edges, all 1,140 fixed LP
equations, and every coefficient of the integer Farkas ray. It then
recomputes the potentials, all positive edge weights, endpoint
allocations, and selector coefficients. No optimizer, SAT solver, or
subject model builder is imported.

Each of the 12 verified core relabelings transports the inequality.
The verifier checks the full global edge set under each relabeling,
recomputes every transported coefficient, and verifies that it is the
corresponding coordinate permutation of the original cut. The chosen
internal endpoint is transported with the edge; it is not replaced by
a new unrelated ordering rule. All 12 coefficient vectors are distinct.

These relabelings generate necessary cuts. They do not impose graph
automorphisms or equalities between selectors. The frozen certificate
contains the nine supported potentials, all 265 positive edge
allocations, the full signed inequality, and all 12 transports.

The source is
`experiments/workspace/root_prism_free_f0_symmetric_selector_cut.py`,
SHA256
`15ec937609b7de44b808e9de7053bb9ee080ddf732a3defd2b23577c026fe274`.
The certificate is
`experiments/logs/root-prism-free/f0-symmetric-selector-cut-certificate.json.gz`,
SHA256
`3aea5e48c4a35eb7e023708231f3dbf585634c25de25484f364276041260f846`.
Its generation and replay logs are saved beside it. The allocation
routine also passes 448 exhaustive small activated-edge controls,
including the three-vertex path example in
`research/symmetric_exterior_row_cuts.md`.

## Consequence and limits

This is a concrete obstruction that separate row-box cuts miss. The
same saved incidence has exact witnesses for every separate row, so
it satisfies every single-row potential inequality. It violates the
new shared-row inequality because adjacent rows must use the same
undirected edge variable.

The cut applies to every first-incidence selection for component zero
under the globally prism-free and $F$-free split $18+18$ hypothesis.
No incidence formula has yet been changed by this certificate package.
The complete Boolean exterior formula prepared for the rejected fixed
incidence remains unqueried; its LP relaxation already supplies the
exact contradiction.
