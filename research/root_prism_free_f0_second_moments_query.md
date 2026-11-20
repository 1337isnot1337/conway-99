# Bounded linear query for the complete F0 second-moment model

## Scope

This query concerns component zero in the split \(18+18\) shell of a hypothetical globally prism-free graph with \(F=0\). It leaves the second component, its alignment, and all 480 incidence selectors free. A point of this relaxation is not a graph.

The model retains the complete fractional incidence and edge system, all 4,416 proved Boolean-normalized selector inequalities, and the second-moment constraints prepared in `root_prism_free_f0_second_moments.py`. Its 15,589 variables consist of 42 selector orbits, 5,805 eligible-edge orbits, and 9,742 distinct-pair moment orbits. There are 7,165 equalities, 46,122 inequalities, and 279,627 nonzero coefficients.

The linear model includes all original Gram and population equations multiplied by every selector, the Fréchet bounds, edge-to-moment bounds, and the 4,410 certified zero products. It does not enforce the PSD conditions recorded in the model preparation. All numerical matrix coefficients and right sides are integers represented exactly in binary64.

## One-call budget

The frozen driver is `root_prism_free_f0_second_moments_query.py`. Preparation verifies pinned versions of NumPy, SciPy, HiGHS, and python-flint; exact small controls; and the existing-ray API guard. Preparation calls no optimizer.

After the coordinator gate, the driver may make one `Highs.run()` call. The numerical phase has 60 seconds including setup, one thread, and a 65-second owned-process hard limit. It saves the numerical primal values, row values, row and column basis statuses, solver status, and elapsed time. A numerical infeasibility status permits ray extraction only if `getDualRayExist()` already reports a ray. No ray-generation solve, retry, feasibility relaxation, or IIS request is allowed.

A separate owned process has at most 60 seconds for exact reconstruction. Both phase limits are explicit. A killed process, resource refusal, or failed reconstruction remains unresolved.

## Exact acceptance

The exact helper first tries three direct rational proposals. It may then propose aliases from numerically active unit-difference inequalities and fixed box bounds. These aliases affect only the reconstruction attempt; they are not added to the optimization model.

The active-face attempt uses a modular nonsingular minor followed by an exact Dixon solve. It allows at most 1,600 reduced coordinates, 64 proposed free coordinates, and 8,000,000 dense matrix cells. A common-denominator point may use at most 8,192 bits. Modular rank is not asserted to equal rational rank. Every reconstructed value must pass the full original model, regardless of the selected face or proposed free coordinates.

Point acceptance checks every quotient row and independently expands the orbit variables. The full validation has 650,350 rows and 183,834 unit-box bounds:

| Family | Full row count |
|---|---:|
| Core Gram and population | 172 |
| Mixed adjacency equations | 8,640 |
| Edge activation | 136,788 |
| Component motif inequalities | 90 |
| Boolean-normalized selector inequalities | 4,416 |
| Selector-multiplied Gram and population | 82,560 |
| Distinct-pair moment bounds | 344,880 |
| Edge-to-moment bounds | 68,394 |
| Certified zero moments | 4,410 |

For an integer finite-box infeasibility certificate, let the equality multipliers be unrestricted and the upper-inequality multipliers nonnegative. Their combined row is \(c^{\mathsf T}v\le b\). The unit box gives the lower bound \(\sum_j\min(c_j,0)\). Thus the exact strict inequality

\[
b-\sum_j\min(c_j,0)<0
\]

certifies infeasibility. Numerical rays only propose integer multipliers; this integer gap decides acceptance.

## Independent replay

The standalone `root_prism_free_f0_second_moments_replay.py` imports neither the production driver nor its exact helper and uses only the Python standard library. It checks source and model hashes, reconstructs the 171 Gram rows and all 480 mixed targets from the literal core, enumerates all 68,394 eligible edges, and derives the complete 4,410 zero-product set.

For a point it separately checks all 4,416 selector rows and every original lifted row. For a ray it computes the finite-box lower bound directly. Terminal UNKNOWN and error records produce no feasibility or infeasibility claim. A successful ray replay excludes this complete component-zero stratum under its stated hypotheses; it does not solve the unrestricted 99-vertex problem.

The existing mathematical-model cold replay remains a separate dependency. The native preflight and the standalone replay preflight are not optimizer runs.

## Commands

Run only after the coordinator gate:

```bash
.venv/bin/python experiments/workspace/root_prism_free_f0_second_moments_query.py query \
  --preparation experiments/logs/root-prism-free/f0-second-moments-query-preparation.json \
  --model experiments/logs/root-prism-free/f0-second-moments-preparation02.json.gz \
  --directory experiments/logs/root-prism-free/f0-second-moments-query-run01 \
  --lp-seconds 60 --exact-seconds 60
```

Then run the optimizer-free replay:

```bash
python experiments/workspace/root_prism_free_f0_second_moments_replay.py replay \
  --preparation experiments/logs/root-prism-free/f0-second-moments-query-preparation.json \
  --model experiments/logs/root-prism-free/f0-second-moments-preparation02.json.gz \
  --directory experiments/logs/root-prism-free/f0-second-moments-query-run01 \
  --output experiments/logs/root-prism-free/f0-second-moments-query-run01-replay.json
```

No production query was made while preparing this package.

