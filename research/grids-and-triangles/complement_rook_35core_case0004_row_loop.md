# Bounded LP and exterior-row continuation for case 4

The continuation uses the complete original case 4 real incidence model,
including all Gram margins, original-signature capacities, triple
capacities, and bounds \(0\le x\le1\). It also retains the 30 checked
binary Gram no-goods and the two checked exterior-row inequalities from
`complement_rook_35core_case0004_row_separation_run01.md`.

Initially there are 397 equality rows and 1,444 inequality rows. Writing
each inequality with its own nonnegative slack gives 1,841 rows and
2,658 columns, with 19,337 nonzero entries. The 1,214 primary selectors
remain real during this experiment.

## The bounded loop

Each round first reoptimizes the full current real model. A numerical
point is a discovery proposal, not an exact feasible witness. Values
below \(10^{-9}\) are set to zero and values above \(1-10^{-9}\) to one
for row separation. The number and sum of discarded tiny positive
values are recorded.

Every positive column of that sanitized proposal is tested, in increasing
index order, using its complete exterior-neighbor domain. This searches
the full 1,214-column universe rather than the earlier 32-row sample.
Zero-valued targets cannot violate a row inequality at the sanitized
proposal, since its left side is nonnegative and its right side is zero.

The frozen bounded-dual separator supplies a candidate integer potential.
All coefficients and the positive demand are then recomputed exactly.
Each new inequality has the form

\[
d x_a-\sum_b c_bx_b\le0,
\qquad d\in\mathbb Z_{>0},\quad c_b\in\mathbb Z_{\ge0}.
\]

The cut pool retains the full coefficients; no binary coefficient
truncation is applied in this continuation. Equivalent positive scalar
rows are deduplicated. The next global LP includes every accepted cut.

The authorized limits are five rounds and 60 seconds overall, with one
thread, at most ten seconds for each global LP, and at most two seconds
for each row LP. There are no retries or SAT calls. Every visited row and
every accepted cut is checkpointed. An unfinished round records its
entire expected positive support and its exact visited prefix.

## Exact infeasibility gate

Let \(Eu=b\) be the full current standard-form system, with all primary
and slack variables nonnegative. A numerical infeasibility status is
not an exclusion. The verifier requires an integer vector \(r\) with

\[
E^Tr\ge0,\qquad b^Tr<0.
\]

It checks every primary coefficient. Each inequality row has a distinct
unit slack column, so it also checks \(r_i\ge0\) on every inequality
row. The exact cut pool used by each global LP is recorded by its prefix
length and complete row-inventory hash. This binds any Farkas proof to
the actual model solved in that round.

The verifier has an exact positive control for the inconsistent system
\(x=2,\ x+s=1,\ x,s\ge0\), and rejects four incorrect ray controls.
Failure to reconstruct an exact ray leaves the case unresolved.

## Reproduction and scope

The source is
`experiments/workspace/complement_rook_35core_case0004_row_loop.py`.
The frozen preparation is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-preparation.json.gz`.

The separate replay command reconstructs every exact input, verifies
every retained integer inequality, checks cut-prefix coverage, and
checks any integer Farkas ray. It calls no optimizer:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_row_loop.py replay \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-preparation.json.gz \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-run01.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-replay-new.json
```

Use a fresh output path. Even an exact infeasibility certificate would
exclude only this indexed 35-core. It would not exclude the whole local
eight-set, another matching, or the Conway graph problem.
