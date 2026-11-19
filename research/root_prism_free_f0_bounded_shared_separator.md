# Bounded potentials for the final shared-box UNKNOWN

This package prepares a new separation LP for the terminal incidence of
the first lazy continuation. The earlier feasibility query remains
UNKNOWN. It reported numerical infeasibility but returned no saved dual
ray. No rounding scale was attempted in that branch, and there is no
saved ray to recover by arithmetic alone.

The new LP searches directly for bounded row potentials. Preparation and
cold reconstruction use exact arithmetic and call no optimizer. A later
query is limited to one call, one thread and at most sixty seconds,
including setup. Every returned numerical potential is saved, including
on nonoptimal statuses. A numerical status never establishes a result.

## Fixed incidence and exact equations

The selected incidence has sixty distinct triples from the complete
480-signature component-zero domain. Its first-component Gram matrix,
all ninety visible motif conflicts, all 1,356 registered inequalities,
and all 2,448 actual explanation clauses were rechecked.

Write its triples as $h_a\in\{0,1\}^{18}$, and its mixed-row demands as
$q_a\in\mathbb Z^{18}$, for $0\leq a<60$. Each triple has weight three,
and each demand has coordinate sum twenty-four. There are 1,220
universally eligible unordered exterior pairs. A shared fractional
completion would assign one number $y_{ab}\in[0,1]$ to each such pair,
with

$$
\sum_{b:\,ab\text{ eligible}}h_b y_{ab}=q_a.
$$

Summing the eighteen equations for a fixed $a$ gives
$3\sum_b y_{ab}=24$, so the degree-eight equation is redundant.
Preparation also checks this identity on the actual supports of all
sixty degree rows. Thus removing degree potentials does not discard a
feasibility condition from the original mixed/degree box.

This is a fixed first-incidence question. It uses neither a chosen
second component nor a fiber alignment. A shared fractional completion
would still be only a relaxation of a graph completion.

## Bounded separating LP

For each $a$, introduce $v_a\in[-1,1]^{18}$. For every eligible pair
$ab$, introduce $t_{ab}\in[0,6]$ and impose

$$
t_{ab}\geq v_a\cdot h_b+v_b\cdot h_a.
$$

Maximize

$$
\Phi(v,t)=\sum_a v_a\cdot q_a-\sum_{ab}t_{ab}.
$$

The implementation minimizes $-\Phi$. The upper bound six is automatic
for the smallest admissible capacity: both triples have three entries,
and every potential entry lies between minus one and one. The zero
potential and zero capacities give an exact feasible point.

For any shared box solution,

$$
\sum_a v_a\cdot q_a
=\sum_{ab}(v_a\cdot h_b+v_b\cdot h_a)y_{ab}
\leq\sum_{ab}\max(0,v_a\cdot h_b+v_b\cdot h_a).
$$

Consequently, a strict positive support gap excludes that fixed
incidence. Conversely, if the target vector is outside the linear image
of the compact cube $[0,1]^{1220}$, finite-dimensional separation gives
such a potential. Scaling it puts every coordinate in $[-1,1]$ without
changing the sign of the gap. The bounded formulation therefore does
not lose a separating direction through normalization.

| Model item | Count |
|---|---:|
| Mixed-row potential variables | 1,080 |
| Positive-capacity variables | 1,220 |
| Total variables | 2,300 |
| Edge inequalities | 1,220 |
| Nonzero matrix coefficients | 8,540 |

The exact model hash is
`c433fa3d8dc960dfec9860efc11d919da6c7f9741d5b15f7d53edd6aac8087c6`.

## Exact acceptance and universal transport

The optimizer proposes only the 1,080 potential entries. The source
stores every returned column as a hexadecimal float before attempting
reconstruction. It does not request a dual ray.

Reconstruction rounds only the potential entries at declared scales,
removes a common positive integer divisor, and computes every edge
weight again using integers. The final scale also includes the exact
dyadic denominator of the returned potential. Acceptance requires

$$
\Delta=\sum_a v_a\cdot q_a
-\sum_{ab}\max(0,v_a\cdot h_b+v_b\cdot h_a)>0
$$

as a strict integer inequality. The reconstructed potential need not
retain the numerical normalization: the support-gap implication holds
for every integer potential. Every tested scale and exact gap is saved.

A cold replay reconstructs the full domain and LP, checks the saved
proposal and integer calculations, then uses the previously checked
full-domain lifting routine. Potentials extend by zero to the other
420 signatures. Positive internal-edge weights are allocated to a fixed
endpoint selector; positive boundary-edge weights are allocated to the
outside selector. This produces a necessary inequality on all 480 free
selectors. All twelve verified core relabelings are replayed separately.
The saved incidence is used to derive the inequality, not imposed on
future incidence searches.

If no strict exact gap is recovered, the result remains UNKNOWN. A zero
numerical optimum alone is not accepted as a shared-box feasibility
certificate. No component exclusion or graph construction follows from
this preparation.

## Controls and replay

The exact positive control is the earlier certified shared ray from
continuation iteration fifteen. Its integer demand is eighteen and its
positive edge capacity is twelve. Its maximum absolute potential is ten,
so normalization gives objective $6/10$ and satisfies every new LP bound
and edge row.

A separate exact feasible-box control uses the eight-regular graph
$K_{10}$ with a perfect matching deleted. Ten explicitly listed triples
define the mixed demands from its forty chosen edges. Twenty-four
deterministic integer potentials check the shared-edge identity, the
nonpositive support gap, the normalized bounds and the objective sign.
This small control is not claimed to be an SRG completion.

The preparation also checks the zero-potential point, every target sum,
and all actual degree-row support identities. The cold preflight
reproduces the entire exact specification and controls without an
optimizer.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_bounded_shared_separator.py replay \
  --preparation experiments/logs/root-prism-free/f0-bounded-shared-separator-preparation.json.gz \
  --output /tmp/f0-bounded-shared-separator-preflight.json
```

The original terminal result, transcript, cold replay and UNKNOWN status
remain unchanged. The source, preparation and preflight are bound by
the separate preparation manifest.
