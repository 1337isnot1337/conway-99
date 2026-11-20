# IPM preparation for the reduced second-moment model

This package prepares one numerical-method change on the unchanged reduced
linear model. It has not run a production optimizer. The preceding simplex
queries remain UNKNOWN.

The full and reduced simplex calls reached their limits after 10,023 and
10,479 iterations respectively, without a valid primal, dual or basis. The
next prepared call uses HiGHS IPM with crossover enabled. This tests a
different numerical method; it makes no mathematical strengthening and no
prediction about speed.

## Frozen model and exact acceptance

The matrix has 15,200 variables, 5,973 equalities, 15,719 inequalities and
183,702 nonzeros. Its SHA-256 remains
`5e417221ed814a5a0dcb03e31820871113bcc0eb8af2856dd2ac493958d16f39`.
The source, exact zero substitutions and row-dependency certificates from
`root_prism_free_f0_second_moments_reduction.md` are unchanged.

The exact helper is unchanged. A proposed point must pass the reduced matrix,
then all 650,350 original literal rows and 183,834 original variable bounds.
A proposed finite-box Farkas certificate must pass integer arithmetic against
the exact reduced matrix. The independently replayed equivalence transfers
such an exclusion to the original linear model. Numerical status alone is
never accepted.

No selector is fixed. The complete 480-selector domain, all 4,416 proved
selector inequalities and full linear moment lift remain present. PSD
constraints are not included. The conditional component-zero scope remains
unchanged; this is not an unrestricted graph-construction model.

## One-call budget

There is exactly one `Highs.run()` call. Its solver options are IPM, crossover
on, presolve on, one thread and seed zero. The owned numerical child has a
hard 180-second limit, including loading and matrix setup. The backend time
limit is the actual remaining allowance minus a three-second output reserve.
If setup consumes that allowance, no optimizer is called. A cooperative
overrun is recorded, and the owned process is stopped at its hard limit.

The exact arithmetic child has its separate unchanged 60-second hard limit.
The active-face reconstruction bounds are also unchanged. The preparation
and replay calls are optimizer-free preflight work, outside these production
phase allowances.

The numerical record preserves returned primal values, row values and basis
statuses, including when their validity flags are false. It separately
records IPM, crossover and simplex iteration counts. These data are proposals
until exact acceptance. Ray extraction is permitted only if an already
existing ray is reported by `getDualRayExist`; no call is made to generate a
missing ray. There is no automatic retry, IIS calculation, repair objective,
or hidden follow-up optimization.

## Preparation checks

The preparation verifies pinned dependency versions, the unchanged exact
point/ray and Dixon controls, and the installed option API without calling an
optimizer. The independent preflight cold-rebuilds the reduced model and its
literal domain. The source-diff report identifies every changed function;
the exact helper and literal point checker remain unchanged.

The publication manifest binds the driver, replay, preparation, preflight,
source-diff record and this note. A production call requires a separate
coordinator gate. Its prospective command is:

```bash
.venv/bin/python experiments/workspace/root_prism_free_f0_second_moments_ipm_query.py query \
  --preparation experiments/logs/root-prism-free/f0-second-moments-ipm-query-preparation.json \
  --model experiments/logs/root-prism-free/f0-second-moments-reduced-model.json.gz \
  --directory experiments/logs/root-prism-free/f0-second-moments-ipm-query-run01 \
  --lp-seconds 180 --exact-seconds 60
```

The directory must be fresh. The paired independent replay must run before
any exact feasibility or exclusion claim is recorded.
