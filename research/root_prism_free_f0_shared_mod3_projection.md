# Modulo-three projection with explicit exterior degrees

The complete shared degree and mixed system gives no new selector
congruence modulo three. Its edge-free selector consequences all follow
from the original Gram equations and population 60. The calculation uses
the same conditional F0 domain as the
[modulo-two projection](root_prism_free_f0_shared_mod2_projection.md).

The 480 degree equations are included explicitly:

\[
\sum_{b:\{a,b\}\in E}y_{ab}=8x_a.
\]

The 8,640 mixed equations are

\[
\sum_{b:\{a,b\}\in E}h_{bi}y_{ab}=q_{ai}x_a.
\]

Each target sums to 24 and each signature has three core neighbors.
Over the integers, summing the mixed equations and dividing by three
recovers the degree equation. Division by three is unavailable in the
field used here. Keeping the degree equation avoids weakening this
modular projection by that division.

All 480 selectors and all 68,394 original eligible edge variables remain
separate. No graph symmetry, selected incidence, or later edge-zero
restriction is imposed. The source reuses only the exact domain
reconstruction from the frozen modulo-two source.

Two disjoint integer bit planes encode the coordinates with coefficients
one and two. Addition and subtraction act independently at each bit.
All 6,561 pairs of four-coordinate vectors are checked against ordinary
integer arithmetic for each operation. A separate dependent-row control
checks the basis multipliers. The elimination then carries an exact
original-row witness and selector vector through every operation.

| Quantity | Result |
| --- | ---: |
| Degree and mixed rows processed | 9,120 |
| Initially nonempty edge rows | 8,364 |
| Edge-column rank found modulo three | 7,731 |
| Edge-free dependencies | 1,389 |
| Dependencies with zero selector vector | 1,213 |
| Dependencies with nonzero selector vector | 176 |
| Original Gram/population rank modulo three | 132 |
| New independent selector congruences | 0 |
| Field row additions | 167,990 |

The run finished in 12.445 seconds. Its 70-second outer owner completed
and reaped the child in 12.639 seconds. No optimizer or native arithmetic
library was used.

Together, the two finite calculations close the search for additional
selector congruences obtained by linear elimination of this shared system
over these two fields. They do not prove integer realizability of the
edge system and do not address other moduli, edge bounds, Boolean pair
caps, or the unrestricted graph problem.

The [source](../experiments/workspace/root_prism_free_f0_shared_mod3_projection.py)
has SHA256
`1911a2b75fd22f5eda3dad0303d26663bc03819b14bdeae945ef89ba3833b5f7`.
The [terminal report](../experiments/logs/root-prism-free/f0-shared-mod3-projection01/report.json)
has SHA256
`5f0ea9fa1e83856e24637eaa736625ccd0a38b56f70c7a3cce9403d255e96512`.
The [certificate archive](../experiments/logs/root-prism-free/f0-shared-mod3-projection01/certificates.json.gz)
contains the original Gram rows and an empty new-congruence list.
The [owner receipt](../experiments/logs/root-prism-free/f0-shared-mod3-projection01-owner/supervisor.json)
retains the completed command and source/report bindings. Independent
review is recorded separately. Reproduction requires a fresh output
directory; completed records must not be overwritten.

## Independent complete rank check

A separate verifier imports neither producer. It inserts all original Gram
rows first, processes the shared rows in reverse order, and uses the opposite
pivot direction on the combined edge, selector and constant matrix. The
augmented rank is 7,863, equal to edge rank 7,731 plus Gram rank 132.
No new selector pivot appears. The complete replay takes 5.762 seconds.

The [independent report](../experiments/logs/root-prism-free/f0-shared-mod3-projection-independent01.json) has SHA256
`c9708a77fa7aa80e5fa31d4b9d4929766bf5656b7b7c901aa29a74c975035124`. Its standalone
[source](../experiments/workspace/root_prism_free_f0_shared_prime_projection_independent.py)
has SHA256
`8a02c4ffcf473df48bbd0f55001f5d8ccc4cda0ec9b9ded62e650708095f5696`.
Root read the complete verifier and checked the rank-projection argument.
