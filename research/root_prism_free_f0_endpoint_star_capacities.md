# Endpoint capacities in the fixed F0 orbit model

The complete endpoint-star census gives 518 valid count inequalities.
A separate implication audit accounts for 516 using previously retained
linear equalities and nonnegativity. Two rows remain outside those
specific arguments:

| Exterior-edge orbit | Reduced edge-count column | Selector orbit | Bound |
| ---: | ---: | ---: | --- |
| 2,975 | 2,917 | 29 | `Y2917 <= N29` |
| 2,993 | 2,935 | 23 | `Y2935 <= N23` |

This does not prove that the two rows are independent of every other
constraint in the full model. The census does not give a new zero,
an incidence, or a graph.

## Summing exact local capacities

For a retained selector-pair or exterior-edge orbit R, use its already
checked compatibility graph. An actual selection of objects from R is
a clique in that graph. Fix a literal selector v. The selected objects
incident to v are therefore a clique in the induced endpoint star.

Let d be the largest star clique number over all v in selector orbit
O_i. A selected incident object activates v. Its incident count is at
most `d*x_v`, including when `x_v=0`. Summing over O_i gives

`m*P_R <= d*N_i`,

where m is one for a cross-orbit object and two for an object internal
to O_i. For exterior edges, replace P_R by the edge count. This is a
literal binary implication followed by summation. It does not assume
that the completed graph has an automorphism.

Every endpoint star has at most four vertices. Each certificate gives
an attaining clique and a nonedge witness in every subset of the next
larger size. The latter proves the upper bound without another clique
search. The checker uses all endpoints, so it does not need to infer a
uniform clique number from transitivity.

## Complete finite scope

The inventory covers all 9,353 retained pair-orbit graphs and all 5,643
retained edge-orbit graphs. It skips 27,865 degree-one endpoint cases,
where the raw degree bound is already exact. The remaining 1,572 cases
contain 10,230 literal stars and at most 40,920 tiny subsets.

The single census finishes in 2.76 seconds. It improves 269 pair rows
and 249 edge rows from raw degree two to capacity one. All pair rows
are cross-orbit rows. The edge rows comprise 243 cross-orbit rows and
six internal rows. The separate 4.13-second replay checks all saved
star certificates and all summed count coefficients. Both stages have
their own sixty-second owner and make no optimizer call.

## Removing simple consequences

The 269 pair rows all follow from original quota-one Gram equations
multiplied by the endpoint selector. At every endpoint, the two other
selectors occur in the same quota-one support. The lifted equality and
nonnegative pair variables bound their two incident pair moments by
the endpoint variable. Summing the rows and averaging actual core
relabelings gives the count inequality. The audit records all original
and quotient lifted-row IDs.

Of the 249 edge rows, 156 follow from those pair capacities and the
existing edge-to-pair inequalities. Another ninety have stored mixed
quota-one witnesses. Their mixed equalities already bound the two
incident edge variables by the endpoint variable.

The first audit leaves three rows whose stored conflict witnesses are
two-edge prisms. The original graph chose witnesses in a fixed priority
order, so a prism witness does not establish the absence of a mixed
witness. A separate check examines every common core site of all eighteen
remaining stars. It finds mixed quota-one witnesses for `Y2855 <= N27`,
which removes one more row from the residual family.

The two rows in the table each use six literal centers. At every center,
the two eligible incident edges cannot both occur because they create
the previously checked two-edge prism. Their other endpoints share
exactly one core site, with mixed target quota two. The tested direct
mixed quota-one and common-core-pair arguments therefore do not cover
these stars. Selecting either edge activates its center; the prism
restriction then makes the two-edge sum at most that center's Boolean
variable. Summing over the six centers proves the displayed inequality.

The frozen count-query target is unchanged by this census. Any later
use of the two rows is a separate model update. Adding the other 516
rows would expose existing consequences for propagation; it would not
establish 516 new independent restrictions.

## Records

- [Census and certificate checker](../experiments/workspace/root_prism_free_f0_endpoint_star_capacities.py).
- [Complete census](../experiments/logs/root-prism-free/f0-endpoint-star-capacities-census01.json.gz) and [cold replay](../experiments/logs/root-prism-free/f0-endpoint-star-capacities-census01-cold.json).
- [Original implication audit](../experiments/logs/root-prism-free/f0-endpoint-star-capacities-implication-audit01.json.gz).
- [All remaining mixed-site checks](../experiments/logs/root-prism-free/f0-endpoint-star-capacities-additional-mixed-check01.json).
- [Independent implication review](../experiments/logs/root-prism-free/f0-endpoint-star-implications-literature-review.json).

The source review, all seventy-five labelled star-graph controls, the
complete certificate replay, and the separate implication review pass.
The fixed component and the unrestricted graph problem remain open.
