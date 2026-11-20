# Exact feasible point for the joint F0 fractional baseline

The complete fractional baseline for the conditional F0 domain has an exact rational feasible point. The independent replay checks all 145,690 original rows and all 68,874 variable bounds. This rules out a linear contradiction from this baseline alone. It does not construct a graph.

## Model and result

The unreduced variables are 480 selector weights and 68,394 eligible shared-edge weights. Averaging over the twelve checked core automorphisms gives 5,847 quotient variables: 42 selectors and 5,805 edges. This averaging preserves feasibility and imposes no automorphism on a hypothetical graph.

The quotient contains 686 equations and 11,373 inequalities, with 57,801 nonzero coefficients. The original checks include every Gram equation, the population equation, every mixed exterior-incidence equation, all edge activation bounds, and ninety motif constraints. The baseline omits the terminal 4,404 Boolean selector cuts and the earlier twelve weighted rows. See the [complete model derivation](root_prism_free_f0_fractional_shared_projection.md).

One HiGHS invocation returned a feasible numerical proposal after 4,361 simplex iterations. The exact phase used one active-face rational solve with 532 columns and full rank 532. A proposed active face is used only to reconstruct a point. Every resulting coordinate is then tested against the original complete model.

The exact point has the common denominator
\[
1854019811676736303924899757370339420637514913704062386488.
]
It has 191 bits. All 5,847 numerators are retained in the exact record.

| Check | Result |
| --- | --- |
| Original rows | 145,690 checked; zero violations |
| Original variable bounds | 68,874 checked; zero violations |
| Quotient rows | 12,059 checked; zero violations |
| Quotient variable bounds | 5,847 checked; zero violations |
| Production optimizer invocations | One |
| Exact reconstruction | Passed |
| Independent JavaScript replay | Passed |
| Coordinator replay in the restored workspace | Passed |

## Reproducible evidence

The native run used NumPy 2.3.5, SciPy 1.17.0, highspy 1.16.0 and python-flint 0.9.0. The arithmetic controls passed before the production query. The numerical child took 2.471 seconds and the exact child took 0.666 seconds. The supervisor recorded 3.141 seconds in total.

The complete native model has canonical SHA-256
`a30179bd5b2b7c58bb5458a3371a947997da17288a355452469d47a59ab81413`.
The exact certificate file has SHA-256
`560487737d9569be679565a317acfca5425b28267014ec771f4e3440f9374837`.
The numerical proposal file has SHA-256
`6c8135fba62163995ae2f9fd3eb568034b66ac76042b262dc6b284f2d05d8c29`.

The native execution is [workflow run 44506159728](https://github.com/1337isnot1337/conway-99/actions/runs/44506159728), at commit `833ea92079158f7b9847146b8d8970c55ac4c8ea`. The retained repository records use the prefix `experiments/logs/root-prism-free/f0-fractional-native-run01-`. They include the proposal, exact point, arithmetic controls, model export, reconstruction progress and both independent replay reports.

The coordinator rebuilt the model from the frozen public input files in a separate directory, matched its hash, and ran the independent checker on the recovered exact certificate. No optimizer was repeated.

To replay in a fresh output directory:

~~~sh
node experiments/workspace/root_prism_free_f0_fractional_native_io.js export \
  experiments/logs/root-prism-free/f0-fractional-structural-recovery-input.json \
  experiments/logs/root-prism-free/f0-fractional-motif-recovery-input.json \
  experiments/logs/root-prism-free/f0-gram-interior-recovery-certificate.json \
  /tmp/conway99-f0-baseline-replay

node experiments/workspace/root_prism_free_f0_fractional_native_io.js replay \
  /tmp/conway99-f0-baseline-replay/model.json \
  experiments/logs/root-prism-free/f0-fractional-native-run01-exact.json \
  /tmp/conway99-f0-baseline-replay/replay.json
~~~

## Consequence for the search

Every valid linear combination of these baseline constraints is satisfied by this rational point. Repeating the baseline optimizer cannot remove the obstruction posed by this feasible point. Further progress requires added valid constraints or integrality.

The restored final registry contains 3,948 individual cuts and 456 shared cuts. Those cuts were derived for binary selectors. Their Boolean-equivalent capped and gcd-normalized forms can strengthen the fractional relaxation. That separate derivation and model preparation are the next step. The final registry was not silently added to this baseline.
