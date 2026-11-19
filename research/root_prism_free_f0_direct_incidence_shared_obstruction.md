# A four-row obstruction and twelve universal cuts

The new literal incidence is impossible already in the real shared-edge
relaxation. Its exact dual certificate uses four nonzero mixed-row
potentials. Their combined demand is 60 and their total positive edge
capacity is 51. The strict gap is 9.

This gives a second proof of the [fixed-incidence exclusion](root_prism_free_f0_fixed_selection_exterior_query_run01.md).
It also gives twelve necessary selector inequalities for other incidences.
It does not exclude the whole first component.

## A short arithmetic form

Write y_ab for the shared exterior edge between signatures a and b.
Every such variable lies in [0,1]. For this selected incidence, put

\[
e=y_{106,240},\qquad f=y_{106,318},\qquad
g=y_{392,240},\qquad h=y_{392,318}.
\]

The four integer combinations of mixed equations give the following bounds:

\[
54\le60e+6f+21,\qquad
72\le60g+12h+24,\qquad
e+g\le1,\qquad f+2h\le2.
\]

Adding the first two bounds and using the last two would require

\[
126\le60(e+g)+6(f+2h)+45\le117.
\]

All omitted contributions have the signs needed for these bounds. In the
first row, the only other positive coefficient is 21 at neighbor 447.
In the second, the only other positive coefficients are 12 at each of
neighbors 152 and 443. Each corresponding edge is at most one.
The third potential has coefficient -60 at exactly four selected eligible
neighbors, including 106 and 392, and has demand -60.
The fourth has demand -6, coefficients -6 at neighbor 106 and -12 at
neighbor 392, one positive coefficient 6 at neighbor 136, and otherwise
nonpositive coefficients. This gives f+2h <= 1+y_318,136 <= 2.

The complete eighteen-coordinate integer potentials and every coefficient
are retained in the certificate. No exterior pair cap, integrality of the
edge variables, or choice of the second component is needed for this proof.

The standalone standard-library verifier
`experiments/workspace/root_prism_free_f0_direct_incidence_short_obstruction.py`
reconstructs the mixed demands and all 1,219 selected eligible edges directly
from the original core and signatures. It checks each sign assertion above
and all four remaining positive shared-edge weights. Its report is
`experiments/logs/root-prism-free/f0-direct-incidence-short-obstruction01.json`,
SHA-256 `0a7cb92716012e7e1ff5155aaa68ba09f40d0af4b21735b2c2a061d79bb52641`.
It imports no optimizer and does not call the separation or cut-lift code.

## Universal selector inequalities

The [separation adapter](root_prism_free_f0_direct_incidence_shared_separation.md)
extends those four potentials by zero to all 480 signatures. It evaluates
every one of the 68,394 original eligible edges. Each positive edge weight
is allocated to one of its endpoint selectors, using the valid bounds
y_ab <= x_a and y_ab <= x_b. The resulting signed selector inequality
holds for every incidence in the same component-zero setting.

There are 216 positive edge weights in the complete domain: four internal
to the saved selection and 212 across its boundary. Allocating the boundary
weights outside the saved selection preserves the strict violation at that
selection. Division by the coefficient gcd, three, gives a violation of
three. The selection chooses this allocation and is not a hypothesis of
the resulting inequality.

Twelve checked core automorphisms give twelve transported inequalities.
Each has 140 nonzero terms and maximum absolute coefficient 51. The first
cut rejects the new selection, which satisfies all 4,416 earlier cuts;
therefore the earlier selector system does not imply this new cut.

## Execution and replay

The reserved sequence makes one ordinary shared-feasibility call. It finds
an exact integer Farkas obstruction, so no bounded fallback call is made.
The entire numerical phase and its exact arithmetic take 3.613 seconds;
the complete owner finishes and reaps its child in 6.141 seconds.
No numerical or owner budget is exceeded.

A separate cold owner finishes in 2.922 seconds. It reconstructs the whole
selected shared-row domain, replays the integer obstruction, recomputes
every full-domain coefficient and checks all twelve transports. Its
accepted report has SHA-256
`c48ebcae55fc253bbeeb5186049734933b32ae63824c8ac5188bcea1f7b0eb0b`.
The universal-cut file has SHA-256
`22afff749b73ecc41cde7c8afac2ad67d262524f08b0607901a3967aa3484294`.

The forward and cold records are in
`experiments/logs/root-prism-free/f0-direct-incidence-shared-separation-run01/`
and `f0-direct-incidence-shared-separation-run01-cold/`.
All twelve cuts are certified. Their integration into another native
selector query is separate work.
