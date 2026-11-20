# Modulo-two projection of the complete shared mixed equations

The complete unreduced shared mixed system gives no new selector congruence
modulo two. Every selector congruence obtained by eliminating its edge
variables follows from the original 171 Gram equations and population 60.
This calculation concerns the frozen globally prism-free, F-free split
18+18 shell with first component type zero. It does not exclude that case.

## Equations and scope

Let `x_a` be the selector for one of the 480 admissible core triples `h_a`.
For each of the 68,394 original eligible unordered pairs `{a,b}`, keep a
separate edge variable `y_ab`. The 8,640 mixed equations are

\[
\sum_{b:\{a,b\}\in E}h_{bi}y_{ab}=q_{ai}x_a,
\qquad a=0,\ldots,479,\quad i=0,\ldots,17.
\]

The targets are reconstructed as
`q_a = 2*1 - h_a - D*h_a` from the literal core. All target coordinates
are nonnegative and each target sums to 24. No selected incidence is
fixed. No edge is removed using a candidate or a later zero-edge result.
No averaging or graph automorphism is assumed.

Reduction modulo two is necessary for every integer solution. The degree
equation is already implied in this field: summing the eighteen mixed
rows gives `3*sum(y_ab)=24*x_a`, hence `sum(y_ab)=0 (mod 2)`.

## Exact elimination

The source represents each edge-coefficient row as a Python integer bit
vector. It eliminates the edge columns, carrying both the original mixed
row multipliers and the 480 selector coefficients through each XOR.
An edge-free row is a necessary selector congruence. A separate 481-bit
elimination, including the constant coordinate, compares that congruence
with the original Gram and population equations.

The Gram equations are reconstructed directly from the 21-vertex core.
For component sites `i,j`, their right side is

\[
12\mathbf1_{i=j}+2-A_{i+3,j+3}
-|N_{\mathrm{core}}(i+3)\cap N_{\mathrm{core}}(j+3)|.
\]

The left side sums selectors whose triple contains both sites. The
formula agrees with the frozen direct literal model. All arithmetic in
the elimination is exact.

| Quantity | Result |
| --- | ---: |
| Selector coordinates | 480 |
| Original eligible edge coordinates | 68,394 |
| Mixed rows processed | 8,640 |
| Initially nonempty edge rows | 7,884 |
| Edge-column rank found over the field of two elements | 7,713 |
| Edge-free dependencies | 927 |
| Dependencies with zero selector coefficient vector | 757 |
| Dependencies with a nonzero selector vector | 170 |
| Rank of original Gram/population congruences | 132 |
| New independent selector congruences | 0 |
| XOR row additions | 141,455 |

The complete calculation took 2.921 seconds. Its outer owner completed
and reaped the child in 3.101 seconds, within the 70-second bound.
No optimizer or native arithmetic library was imported.

This eliminates one possible source of additional linear parity cuts.
It says nothing about edge bounds, Boolean feasibility, pair caps, odd
moduli, or a completed graph. In particular, modulo-two compatibility
does not establish an integer edge realization.

## Reproduction and records

The immutable producer is
[`root_prism_free_f0_shared_mod2_projection.py`](../experiments/workspace/root_prism_free_f0_shared_mod2_projection.py),
SHA256 `a548fe26b54a559909bece50df984e0755d9321adc7e8a41d0b6e836c8b34fd5`.
Its input domain has SHA256
`665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4`.

The [terminal report](../experiments/logs/root-prism-free/f0-shared-mod2-projection01/report.json),
[certificate archive](../experiments/logs/root-prism-free/f0-shared-mod2-projection01/certificates.json.gz),
and [owner receipt](../experiments/logs/root-prism-free/f0-shared-mod2-projection01-owner/supervisor.json)
are retained. The certificate archive contains the complete original Gram
rows and an empty new-congruence list. The terminal report has SHA256
`e794dfc28b83296833d158e0732e9b786f430f7c682f294d171a74dc2cb7eebc`.

Run the source with `--directory` set to a fresh output directory under
the repository. Completed records must not be overwritten. Independent
rank review is recorded separately; no numerical rank test is used.

## Independent complete rank check

A separate verifier imports neither producer. It inserts all original Gram
rows first, processes the shared rows in reverse order, and uses the opposite
pivot direction on the combined edge, selector and constant matrix. The
augmented rank is 7,845, equal to edge rank 7,713 plus Gram rank 132.
No new selector pivot appears. The complete replay takes 1.470 seconds.

The [independent report](../experiments/logs/root-prism-free/f0-shared-mod2-projection-independent01.json) has SHA256
`b9681565811ee38866303a482811675704064a5d0745708d30586e83916b702d`. Its standalone
[source](../experiments/workspace/root_prism_free_f0_shared_prime_projection_independent.py)
has SHA256
`8a02c4ffcf473df48bbd0f55001f5d8ccc4cda0ec9b9ded62e650708095f5696`.
Root read the complete verifier and checked the rank-projection argument.
