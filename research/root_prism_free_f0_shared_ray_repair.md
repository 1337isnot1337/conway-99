# Exact repair of upper-bound dual multipliers

The compact incidence continuation stopped when a shared-edge LP
reported numerical infeasibility but its original reconstruction
did not produce an exact ray. This separate calculation recovers
an integer certificate from the saved numerical equality multipliers.
It calls no optimizer and leaves the earlier result unchanged.

## General certificate

Write the fixed-incidence edge box as

$$
Ay=b,\qquad y+s=\mathbf1,\qquad y,s\geq0.
$$

For any integer vector of equality multipliers $\lambda$, define

$$
u_e=\max\{0,-(A^T\lambda)_e\}.
$$

Then $u\geq0$ and $A^T\lambda+u\geq0$ exactly. Multiplying the
equalities by $\lambda$ and $u$ gives

$$
(A^T\lambda+u)^Ty+u^Ts=b^T\lambda+\mathbf1^Tu.
$$

The left side is nonnegative for every feasible nonnegative point.
A strictly negative integer right side therefore proves infeasibility.
For the chosen $\lambda$, this $u$ minimizes the upper-multiplier
contribution among all nonnegative choices that make the primary
coefficients nonnegative.

The numerical vector only proposes $\lambda$. No assertion about
floating-point feasibility enters this proof. In particular, all
numerical upper-bound multipliers may be discarded. Rounding them
independently can violate a zero coefficient sign; recomputing their
exact deficits avoids that reconstruction failure.

## Recovered certificate

The saved point is iteration eight of
`f0-carry-row-loop-run01`. Its selected sixty triples passed the
complete incidence checks and all retained cuts. Every one of its
sixty individual neighborhood boxes also has an exact rational
witness. Its shared box has 1,228 undirected edge variables and
1,140 mixed or degree equations.

The reconstruction negates each saved numerical equality multiplier,
interprets its binary floating-point value as an exact dyadic
rational, and rounds to the nearest integer with ties to even.
It then constructs $u$ by the exact deficit formula and removes
the gcd of the whole vector.

The resulting 2,368-entry ray has 1,013 nonzero entries and maximum
absolute entry 7,618. All 2,456 primary/slack coefficients are
nonnegative, and the exact right side is $-26$. This proves that
the saved incidence cannot support its required symmetric exterior
row box. It does not exclude all incidences of the component.

The independent direct row equations yield integer per-vertex
potentials with total demand 21,843 and internal positive-edge
capacity 21,765. Their strict gap is 78. Extending the potentials
by zero and allocating positive weights over all 68,394 eligible
signature pairs gives a universal selector inequality. Its
coefficient gcd is three, so its gap at the saved point is 26.

There are 7,217 positive edge weights: 7,043 boundary edges and 174
internal edges. All twelve verified core transports are stored.
Each transported inequality has 480 nonzero coefficients. The
positive-literal threshold is 9,663; the largest absolute coefficient
is 8,493. These are necessary inequalities on the free incidence
domain. The saved design only chooses potential support and endpoint
allocation; it is not a hypothesis of the inequalities.

## Replay and scope

The source
`experiments/workspace/root_prism_free_f0_shared_ray_repair.py` has
SHA256
`4a214635d5ba1ec73477a3acdfd36c30cb65be3c4c4fb662ee19a615388c07d3`.
It checks the frozen result and input hashes, revalidates the complete
selected incidence against its retained cut prefix, reconstructs
the shared domain, and verifies the integer ray, potentials, and
all twelve full-domain transports.

Its deterministic certificate is
`experiments/logs/root-prism-free/f0-carry-row-loop-run01-shared-ray-repair.json.gz`,
SHA256
`96e945d1211147e2ad13ed3468f51d72bd3ef87319ca33153eda6248e0b5c7c5`.
A separate cold invocation reproduced it exactly. The controls
include a known infeasible one-variable box and 5,832 integer
multiplier cases for explicit feasible three-variable boxes.

The original compact loop remains recorded as UNKNOWN. This later
exact certificate excludes that particular incidence and supplies
twelve universal inequalities; it does not change any earlier
formula, solver status, or cut registry. The component, second
component completion, and unrestricted problem remain unresolved.
