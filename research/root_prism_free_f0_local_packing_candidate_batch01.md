# Packing obstructions at anchors 4 and 202

The last incidence from the eight-step direct master has two additional local
packing obstructions. The all-anchor batch checked all 60 selected anchors.
Anchors 4 and 202 produced exact integer inequalities. Each has 12 distinct
transports under the verified core relabelings, giving 24 distinct rows.
The separate cold replay accepted all 24 rows.

The remaining 58 anchors produced no exact cut from their one numerical
proposal. This is not a proof of local feasibility at those anchors.

## Input and formulation

The input is iteration 07 of `f0-direct-master-continuation-run01`.
Its selection file has SHA-256
`87359efdc4877036159aa70f6dfc0a11cdefff2409c996c38995996902bdc076`.
The configuration also binds the complete 540-vector, its exact original and
prefix checks, and the accepted master run and cold receipts.

For an anchor a, the mixed equations require

\[
\sum_{b\in N(a)} h_b y_{ab}=q_a x_a.
\]

For each unordered pair p of core sites, the packing inequality is

\[
\sum_{b\in N(a):p\subseteq h_b}y_{ab}\le x_a.
\]

If two neighbors of a contain the same core pair, they already have two
common core neighbors. The anchor would give a third common neighbor.
This proves the packing bound. It does not assume a graph automorphism.

For an integer site vector v and nonnegative integer pair multipliers mu,
define

\[
t=v\cdot q_a-\sum_p\mu_p,
\qquad
w_b=\max\left(v\cdot h_b-\sum_{p\subseteq h_b}\mu_p,0\right).
\]

Multiplying the mixed and packing rows gives the universal selector row

\[
t x_a\le\sum_{b\in N(a)}w_b x_b.
\]

All coefficients are contracted over the complete eligible neighbor domain.
No point-zero pruning or extra Y-zero filter enters this calculation.

The batch uses one bounded LP per selected anchor. Its variables are 18
signed site potentials, 153 nonnegative pair potentials, and one positive
part per selected eligible neighbor. There are 200 to 219 variables and 29
to 48 rows per model. Integer rounding proposes a certificate; direct exact
arithmetic decides whether a cut is retained. Numerical optimality is not
an acceptance requirement.

## Two short contradictions

At anchor 4 the site vector is

```
[-2,-2,-2,-1,0,1,-1,-2,-1,1,1,1,-2,0,-2,0,2,1]
```

Only two pair multipliers are nonzero:
`mu[{1,16}] = 1` and `mu[{6,9}] = 1`.
The site demand is 5 and the pair-multiplier sum is 2, so t = 3.
Every adjusted coefficient on the 31 selected eligible neighbors is
nonpositive. The mixed equations and two pair bounds therefore give

\[
5\le \sum_{b:\{1,16\}\subseteq h_b}y_{4b}
      +\sum_{b:\{6,9\}\subseteq h_b}y_{4b}\le2.
\]

Among all 253 eligible neighbors, 76 have positive weight: 39 have weight 1,
25 have weight 2, seven have weight 3, and five have weight 4. The universal
row has 77 terms and a strict gap of 3 at the saved incidence.

At anchor 202 the site vector is

```
[2,3,-3,-3,-2,-3,1,1,0,-3,-1,-2,1,2,-1,0,-1,-1]
```

The nonzero pair multipliers are
`mu[{1,8}] = 2` and `mu[{6,13}] = 2`.
The site demand is 5 and the multiplier sum is 4, so t = 1.
Every adjusted coefficient on the 37 selected eligible neighbors is
nonpositive. Thus

\[
5\le2\sum_{b:\{1,8\}\subseteq h_b}y_{202,b}
      +2\sum_{b:\{6,13\}\subseteq h_b}y_{202,b}\le4.
\]

Among all 295 eligible neighbors, 85 have positive weight: 40 have weight 1,
26 have weight 2, 13 have weight 3, five have weight 4, and one has weight 5.
The universal row has 86 terms and a strict gap of 1.

The 24 exported weighted rows have at most 86 terms, maximum absolute
coefficient 5, and maximum absolute coefficient sum 157. The accepted
export preserves these weighted rows.

## Execution and acceptance

The source is `root_prism_free_f0_local_packing_candidate_batch.py`,
SHA-256 `d4b975f2a70b8a5ba4372c0cc226490e2ffb6962b8af25199d4686c5bd730472`.
The root gate is `f0-local-packing-candidate-batch-root-gate01.json`,
SHA-256 `99cca5de732212d63eb57eda591327b2f855d495de3e353408fa93091c498767`.

The no-optimizer preparation finished in 7.4395 owner seconds. All 60 LP
calls then used 0.222216 seconds of native solve time in total. The run
owner finished in 6.4094 seconds. The separate cold owner finished in
6.8417 seconds. All owners reaped their children with zero deadline overrun.
The limits were one second per LP, 30 cumulative native seconds, and 60
owner seconds per stage.

The cold path imports no native solver. It rebuilds all 60 small LP
definitions, reconstructs the integer proposals from the saved hexadecimal
floats, and checks all transported coefficients against literal core pairs.
It directly checked 7,124 full-neighbor weights across the two base forms
and their transports. Every one of the 60 proposal records is retained.

The accepted export is
`f0-local-packing-candidate-batch-run01-cold/certified-selector-cuts.json`,
SHA-256 `aa3f64e1bb463edc9449148729d3e53042e8665cf17cdc730975daedacc9a1a7`.
Its `rows_upper_zero` field contains the 24 exact rows, each with RHS 0.
The cold report has SHA-256
`8e0464c347dd87968fcbc528725a7e0124018691f9d1c65694d4ae4db37146d2`;
the cold owner has SHA-256
`5f8ad93f6dbde009ca1f88e63c966140d2783e71aea761b01e052d2e8e353687`.

These cuts are necessary throughout the stated F0 selector domain. They do
not exclude the whole F0 case or solve the unrestricted 99-vertex problem.
