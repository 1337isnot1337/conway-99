# Case4 incidence with 60 exact exterior-row inequalities

## Prepared model

The complete Boolean preparation retains every original clause of indexed
35-core case4. It adds the 30 previously certified Gram conflicts and all 60
exact exterior-row inequalities from the bounded separation pass.

The formula has 1,214 primary selectors, 134,852 total variables, and 261,071
clauses. It does not fix an incidence design, impose graph automorphisms, or
model edges between the remaining 64 vertices. Preparation makes no feasibility
or exclusion claim. A SAT result would supply only a partial incidence witness.
A checked UNSAT proof would exclude this indexed core and its verified
relabelings.

| Part | Variables added | Clauses |
| --- | ---: | ---: |
| Complete original incidence formula | 107,207 | 218,863 |
| Certified binary Gram conflicts | 0 | 30 |
| All 60 guarded exterior-row inequalities | 27,645 | 42,178 |
| Complete formula | 134,852 | 261,071 |

The original full CNF has SHA-256
`e76d9cb74cc1b907c5af37fe224b278181d6e5d052de691f7d86cabb6b028b4d`.
The prepared complete formula has SHA-256
`b0ca3f15a6d2c9e27f82af783cb62c1ecc27376e53f5820105c49d6fd7b72738`
and occupies 4,564,801 bytes. The preparation cold-builds the original formula
and compares its full hash before appending anything. It also checks that the
original clause body remains unchanged afterward.

## Necessary integer inequalities

Let B be the fixed 35-core adjacency matrix. Each admitted attachment column
h_a is a zero-one vector on that core. If x_a indicates that this exterior
vertex occurs, its neighbors outside the core must satisfy

\[
\sum_b h_b y_{ab}=q_a x_a,\qquad
\sum_b y_{ab}=d_a x_a,
\]

where

\[
q_a=2\mathbf1-h_a-Bh_a,\qquad d_a=14-|h_a|.
\]

Only the complete eligible neighbor domain is used. A neighbor b must have
at most one core neighbor in common with a and must pass the zero-quota tests
at both endpoints. For an actual completion, every omitted candidate is
therefore a forced nonneighbor.

For an integer vector v on the 35 mixed coordinates and one degree coordinate,
write

\[
\delta=v\cdot(q_a,d_a)>0,\qquad
w_b=\max\{v\cdot(h_b,1),0\}.
\]

The exact activation bound y_ab at most x_b gives

\[
\sum_b w_b x_b\ \geq\ \delta x_a. \tag{1}
\]

Every cut is reconstructed from its saved integer potential. The preparation
recomputes the complete eligible domain, every integer product, the positive
right-hand side, and the positive coefficient list. The earlier floating
proposals are not used to establish validity. These are necessary conditions
for an actual graph completion; they are not asserted to follow from the
original incidence CNF alone.

The 30 separate binary conflicts retain their direct integer negative-vector
certificates for the Gram residual. Their necessity is checked independently
of (1).

## Exact Boolean encoding

Because the selectors are Boolean, (1) is equivalent to the guarded threshold

\[
x_a=1\ \Longrightarrow\ \sum_b w_bx_b\geq\delta.
\]

First replace each positive weight by min(w_b, delta). If a selected original
weight reaches the threshold, the capped weight still reaches it. Otherwise
the selected sum is unchanged. Capping therefore preserves the Boolean
inequality exactly. Divide the capped weights by their greatest common divisor
g and replace the demand by ceil(delta/g). Every attainable capped sum is a
multiple of g, so this step also preserves the threshold exactly.

The preparation uses the frozen encoder
`experiments/workspace/root_prism_free_f0_weighted_threshold.py`, with SHA-256
`a0c4b38d7787c8e6565ab122e0fdf41655ea40a9f0f218c0f860cd59d3f05144`.
Its suffix predicate s_(i,r) means that the remaining weighted variables reach
r. A predicate forced true follows the actual primary-variable branch to a
true terminal predicate. Conversely, any primary assignment satisfying the
threshold extends by assigning each auxiliary its actual suffix-predicate
value. Only forward implications are needed for this existential equivalence.
The target selector guards the root predicate.

Each cut receives new auxiliary IDs strictly above the current maximum. Every
cut can therefore choose its own auxiliary extension without imposing extra
relations on another cut or on the original counter variables.

Cuts 34 and 35, indexed from zero in the saved list, have positive demand 2 and
no positive supply terms. They encode the exact units forbidding columns 1080
and 1081. These are zero-based column indices, corresponding to DIMACS
variables 1081 and 1082.

## Controls and resource limits

The frozen encoder's exhaustive controls were rerun: 31,582 complete primary
and guard assignments across 1,149 small formulas passed. They check capping,
gcd normalization, existential auxiliary semantics, empty supply, impossible
thresholds, and resource refusal.

The preparation also checked 586 deterministic complete assignments for the
actual 60 weighted cuts. It constructs canonical auxiliary values using the
new clauses and checks the original uncapped integer threshold, the normalized
threshold, and the full clause block. These are actual-instance controls,
not an exhaustive enumeration of the 1,214 selectors.

The limits are 250,000 branch states per cut, 1,000,000 total variables, and
2,000,000 total clauses. Exceeding a limit refuses the entire preparation;
no incomplete cut list becomes a completed model. The observed total was
27,716 branch states. The largest cut used 13,352 states and 13,345 auxiliary
variables. All 60 cuts were completed.

Preparation took 44.132 seconds with peak RSS 117,524 KiB. These figures include
the exact input reconstruction and the small encoding controls. No incidence
solver query was made.

## Bindings and replay

The preparation source is
`experiments/workspace/complement_rook_35core_case0004_row_cut_boolean.py`,
with SHA-256
`2b231f418645d13c18fa4995277858e9b4fe5b770000e7ea742b5e5336fbfe45`.
The model is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-model.json`,
with SHA-256
`51268b36baee6ba62c7925ab85a18724d5e9b28006cb2a62f6bd3228f862346a`.
It records every cut's integer-certificate hash, normalized weights, variable
interval, clause interval, clause hash, and controls.

The cold preflight replay passed. It reconstructs the entire attachment domain, all original
clauses, every direct Gram conflict, every integer row inequality, and all
new threshold clauses. It compares the complete regenerated CNF hash. Use a
new output path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_row_cut_boolean.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-model.json \
  --output /tmp/conway99-case4-row-cut-boolean-replay.json
```

Any later SAT assignment must pass the original inspector for all 1,225 Gram
entries, 64 distinct original signatures, all triple capacities, and attachment
counts 4/40/20. It must also satisfy all 30 conflicts and all 60 original
uncapped integer inequalities directly.

Any later UNSAT claim requires a direct DRAT check, a cold complete formula
rebuild, inclusion of every retained input clause in that regenerated formula,
and a separate retained-proof replay. This preparation does not report such
an outcome.
