# Bounded query for the equivalent reduced second-moment model

This package prepares one query on the exact equivalent reduction documented in root_prism_free_f0_second_moments_reduction.md. No production optimizer was called during preparation.

The model has 15,200 variables, 5,973 equalities, 15,719 inequalities and 183,702 nonzeros. Its real feasible set is equivalent to the original second-moment LP after inserting the 389 explicitly zero coordinates. It adds no selector condition or graph hypothesis. All 4,416 selector cuts remain enforced. PSD constraints remain outside this query.

## Reused driver and exact acceptance

The frozen reduced driver uses the same one-call schedule as the published original query: at most 60 seconds for setup and optimization, a 65-second owned-process hard limit, and one separate 60-second exact process. It preserves numerical primal and row values, both basis-status lists and validity flags. Ray extraction still requires an already-existing ray; no hidden ray-generating solve or optimizer retry is permitted.

The complete driver AST matches the original after the explicit helper binding, nonzero-count and scope changes. The exact reconstruction functions recover_point and exact_phase are AST-identical to the originals. Active-face and denominator limits remain unchanged.

The new exact adapter checks the reduced matrix, inserts zero at every removed coordinate, and calls the unchanged original full inspector. A rational point is accepted only after all 650,350 original literal rows and 183,834 bounds pass. This gate includes all original moment bounds, activation equations and the complete selector-cut family, even where the numerical reduced matrix omits their redundant rows.

For an exact ray, the finite unit-box support calculation is unchanged. Its validity for the original model uses the separately checked equivalence certificate. No solver status alone produces an exclusion.

## Independent cold replay

The standalone reduced replay imports neither production driver nor production helper. It rebuilds the entire exact reduction from the original model and the rank certificate. It then restores any point into the original 15,589 coordinates and uses the frozen independent literal checker.

The native preparation passed all original exact controls plus zero-insertion controls. It called no optimizer. The final independent cold preflight is f0-second-moments-reduced-query-cold-preflight02.json.

The first unpublished replay wrapper accidentally contained two identical command-line entry blocks. Its first full preflight passed; the second invocation refused to overwrite the first report and exited with an assertion. The old source, report and failure record are retained. The correction removes only the duplicate entry block; every mathematical function is unchanged. The corrected preflight completed normally.

## Commands after the coordinator gate

Use a fresh output directory and the pinned native environment:

    .venv/bin/python experiments/workspace/root_prism_free_f0_second_moments_reduced_query.py query \
      --preparation experiments/logs/root-prism-free/f0-second-moments-reduced-query-preparation.json \
      --model experiments/logs/root-prism-free/f0-second-moments-reduced-model.json.gz \
      --directory experiments/logs/root-prism-free/f0-second-moments-reduced-query-run01 \
      --lp-seconds 60 --exact-seconds 60

Then run the optimizer-free cold replay:

    python experiments/workspace/root_prism_free_f0_second_moments_reduced_replay.py replay \
      --preparation experiments/logs/root-prism-free/f0-second-moments-reduced-query-preparation.json \
      --model experiments/logs/root-prism-free/f0-second-moments-reduced-model.json.gz \
      --directory experiments/logs/root-prism-free/f0-second-moments-reduced-query-run01 \
      --output experiments/logs/root-prism-free/f0-second-moments-reduced-query-run01-replay.json

The original query remains UNKNOWN. This preparation neither resolves that outcome nor predicts the reduced query's runtime or status.

