# Shared exterior edges for the row-box-feasible incidence

The saved 60-triple incidence passes every separate row-box test.
The next prepared models give each undirected exterior edge one shared
variable. The linear model keeps the degree and mixed equations with
edge bounds from zero to one. The Boolean model also keeps every
necessary exterior common-neighbor cap. Neither model has been queried
as part of this preparation package.

The first component and its saved incidence are fixed. The second
component, its alignment, and its incidence remain free. An exclusion
would reject only this fixed first incidence. A feasible linear or
partial Boolean point would not construct a Conway99 graph.

## Complete shared-edge domain

Let $A$ be the adjacency matrix of component zero and let $H$ be its
saved $18\times60$ incidence matrix. Each column of $H$ is a distinct
triple. For the exterior adjacency matrix $D$, an actual graph requires

$$
D=D^T,\qquad \operatorname{diag}D=0,\qquad
D\mathbf1=8\mathbf1,\qquad
HD=2J-H-AH.
$$

The missing second component contributes nothing to the displayed mixed
equations because the two shell components are anticomplete. Each
exterior vertex has three neighbors in each shell component and none
in the central triangle, so its exterior degree is eight.

Put $q_a=2\mathbf1-h_a-Ah_a$. A candidate edge $ab$ must satisfy

$$
|h_a\cap h_b|\leq1,\qquad
q_a(i)>0\ (i\in h_b),\qquad
q_b(i)>0\ (i\in h_a).
$$

The first condition is the adjacent-pair common-neighbor bound. Each
zero quota in the other two conditions forbids that edge directly.
Exhaustive inspection of the 1,770 exterior pairs leaves exactly
1,220 eligible undirected edges. This domain also matches the
restriction of the separately checked 68,394-edge universal signature
domain to the saved 60 signatures.

All 1,080 mixed positions and all 60 degree equations are retained,
including zero and dependent equations. The input incidence is rebuilt
from the complete component catalogue and checked against all its
Gram, profile, and motif constraints.

## Full necessary Boolean caps

For every exterior pair $a,b$, define $c_{ab}=|h_a\cap h_b|$.
The Boolean model imposes

$$
D_{ab}+\sum_w D_{aw}D_{bw}\leq2-c_{ab}.
$$

Unspecified common neighbors in the second component can only make
this necessary upper bound tighter. They are not assumed absent.
The 1,770 pair positions split into 1,008 with $c=0$, 714 with
$c=1$, and 48 with $c=2$.

The frozen earlier exterior encoder is called as a pure function on
the new domain. Its old incidence loader is not called. For positive
remaining capacity, each possible two-edge path receives an exact
conjunction variable and the full cardinality cap. Zero-capacity
pairs use the direct two-edge packing clauses. The encoder covers all
49,083 possible path centers across the exterior pairs; 47,437 use
conjunction variables and 1,646 occur in zero-capacity packing clauses.

| Boolean model item | Count |
| --- | ---: |
| Undirected primary edges | 1,220 |
| Degree equations | 60 |
| Mixed equations | 1,080 |
| Exterior pair caps | 1,770 |
| Total variables | 164,939 |
| Total clauses | 423,130 |
| Literal occurrences | 957,704 |
| DIMACS bytes | 6,936,223 |

The CNF SHA256 is
`9934d68eb3205bdc69c6e24b81fa98fbeefe4b180919fef85995a7341f66648a`.
A cold reconstruction reproduced the complete domain, all equation
supports, every cap domain, and the CNF hash without calling a solver.
The preparation also checks the mixed identities and pair caps directly
on the known nine-point rook graph.

## Linear relaxation and exact proof gates

The small LP uses the same 1,220 shared edges with bounds $0\leq x_e\leq1$.
It keeps only the 1,140 mixed and degree equations, which have 9,760
nonzero coefficients. The quadratic pair caps and integrality are not
part of this relaxation.

For an exact infeasibility check, each upper bound is written
$x_e+s_e=1$, with $s_e\geq0$. The standard form has 2,440 nonnegative
variables, 2,360 equality rows, and 12,200 nonzero coefficients.

The separate runner permits one bounded LP call. A numerical feasible
point is accepted only if rational reconstruction passes all 1,140
equations and every one of the 1,220 exact bounds. Such a point proves
linear feasibility only. Numerical infeasibility requires an integer
ray $r$ satisfying

$$
E^Tr\geq0,\qquad b^Tr<0
$$

for the complete standard form $Ex=b$, $x\geq0$. The replay checks
every primary coefficient and every upper-slack coefficient. Numerical
status or a failed reconstruction produces no exclusion.

If such a ray is found, its degree multipliers can be absorbed into
integer mixed-row potentials. If $\lambda_a$ multiplies the degree
equation and $\lambda_{ai}$ multiplies mixed position $ai$, put

$$
v_{ai}=-\lambda_a-3\lambda_{ai}.
$$

This uses $\sum_iq_a(i)=24$ and $|h_b|=3$. Direct integer replay then
checks a strict gap between $\sum_a v_a^Tq_a$ and the sum of positive
weights $v_a^Th_b+v_b^Th_a$ over the complete fixed shared-edge domain.
This is only a reformulation of a fixed-design contradiction here.
No universal selector cut is assembled by these preparation sources.

## Frozen inputs and artifacts

The candidate file is
`experiments/logs/root-prism-free/f0-incidence-row-loop-run01/iteration00/candidate.json`,
SHA256
`9e38e41273ad247021854236a56a4e9dd0cdc74b7156867904b7d19fe2d64e46`.
Its 60 separate row witnesses and complete incidence cold replay are
individually hash-bound inputs.

The model is
`experiments/logs/root-prism-free/f0-row-box-design-exterior-model.json.gz`,
SHA256
`1a75d60173991252b55892a911a5470e4e5074992916ead7ffc8d9df0c298b79`.
The linear preparation is
`experiments/logs/root-prism-free/f0-row-box-design-linear-preparation.json`,
SHA256
`68a325d1367db1b270fb311c614d99eaa147129a748b727fc40201f7573fd432`.

The new sources are `root_prism_free_f0_row_box_design_exterior.py`
and `root_prism_free_f0_row_box_design_linear.py` under
`experiments/workspace/`. They preserve every prior frozen formula,
point, and certificate. Their mathematical scope is the one saved
first incidence in component zero of the globally prism-free and
$F$-free split $18+18$ case.
