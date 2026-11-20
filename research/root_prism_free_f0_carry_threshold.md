# Exact binary-adder encoding of selector inequalities

The first shared-row continuation stopped at its encoding limit.
Its last inequality had 454 nonzero coefficients and a positive
literal threshold of 331. The necessary inequality was proved, but
the suffix decision graph used too many auxiliary variables.

This separate encoder computes weighted sums in binary. It changes
the Boolean representation of a proved inequality. It adds no graph
assumption, incidence normalization, or candidate-visitation clause.
The earlier source and terminal formula remain unchanged.

## Positive weighted literal form

For a signed selector inequality $\sum_i c_i z_i\leq0$, use

$$
\sum_{c_i<0}(-c_i)z_i+
\sum_{c_i>0}c_i(1-z_i)
\geq\sum_{c_i>0}c_i.
$$

Individual-row inequalities have the guarded form
$z_a\Rightarrow\sum_b w_bz_b\geq d$. The same binary-sum circuit
encodes their positive threshold, with the final comparator guarded
by $z_a$.

Equal input literals are combined. A weight larger than the positive
threshold can be capped at the threshold: if that literal is true,
both versions meet the threshold; if it is false, neither contributes.
Dividing all capped weights by their gcd and rounding the threshold
up is also exact. Complementary literals may remain in the sum;
the circuit preserves their common underlying primary variable.

## Arithmetic circuit

Each set bit of a literal's integer weight places one copy of that
literal in the corresponding power-of-two bucket. Three literals in
one bucket are replaced by their XOR sum bit in that bucket and
their majority carry bit in the next bucket. This identity is exact:

$$
x+y+z=(x\mathbin{\mathrm{xor}}y\mathbin{\mathrm{xor}}z)
       +2\operatorname{majority}(x,y,z).
$$

The reduction ends when each bucket has at most two bits. It
terminates because every full adder reduces the total number of
bits by one. The two resulting rows are added with a ripple carry.
A half adder uses XOR and AND; a full adder again uses XOR and
majority. The output bits give the complete normalized sum. No
high bit or overflow is discarded.

The comparator processes bits from low to high. Let $L_i$ state
that the lowest $i+1$ sum bits are at least the corresponding
threshold bits. Start with the empty comparison true. If threshold
bit $i$ is zero, $L_i=s_i\lor L_{i-1}$; if it is one,
$L_i=s_i\land L_{i-1}$. The final $L_i$ is the exact comparison.

Every logic gate has a full Tseitin equivalence, generated from its
truth table. A fixed primary assignment therefore gives a unique
value to every gate output. It extends to the final CNF exactly
when the guarded or unconditional threshold holds. Constants and
repeated or complementary input literals do not change this proof:
truth-table rows inconsistent with their inputs simplify to
tautological clauses.

## IDs, refusal, and controls

One monotone auxiliary pool starts strictly above the supplied
maximum variable ID. Gate outputs never overlap primary selectors
or earlier auxiliary variables. The encoder builds a private clause
list and refuses the operation if it exceeds 250,000 gate states.
It returns no partial formula on refusal. The enclosing continuation
retains its existing one-million-variable and two-million-clause
limits.

The frozen source is
`experiments/workspace/root_prism_free_f0_carry_threshold.py`, SHA256
`942efb35d35429d88d7cc9c3bc14aa7a116972186f60abeebe50db89214ec75f`.
Its exact controls are recorded in
`experiments/logs/root-prism-free/f0-carry-threshold-controls.json`.

The controls check 280 gate truth assignments, 45,306 complete
weighted primary assignments across 2,278 formulas, and 11,223
signed assignments across 786 formulas. They compare the actual
CNF with integer arithmetic, directly evaluate every gate definition,
and check the exact binary sum. They include constants, zero or
impossible thresholds, repeated and complementary literals, guard
aliases, large weights, unused ID gaps, and resource refusal. Only
tiny Boolean control solvers are used; no incidence or LP query is
part of these controls.
