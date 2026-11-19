# F0 selector PSD-cut query, run 01

## Outcome

The single prepared query is **UNKNOWN**. HiGHS returned numerical optimality, with valid numerical primal, dual, and basis records. Exact reconstruction did not produce a point or an infeasibility certificate. The component is not excluded.

The queried model has 15,200 variables, 5,973 equality rows, 15,751 inequality rows, and 380,052 nonzero coefficients. It retains the original complete linear system and all 4,416 selector inequalities, and adds the 32 certified selector PSD directions described in [the preparation note](root_prism_free_f0_selector_psd_model.md). The full PSD cone is not enforced.

The conditional scope is still one occurrence of component zero in the split \(18+18\) shell under global prism-freeness and \(F=0\). All 480 selectors remain free. The other component and its fiber alignment remain free.

## Recorded run

| Item | Observed result |
|---|---|
| Production optimizer calls | 1 |
| Numerical method | IPM with crossover, one thread |
| Numerical status | `HighsModelStatus.kOptimal` |
| IPM iterations | 29 |
| Crossover iterations | 9,823 |
| Simplex iterations | 0 |
| Numerical owned-process time | 176.394355 seconds |
| Exact owned-process time | 3.908876 seconds |
| Total query time | 180.409646 seconds |
| Numerical hard limit including setup | 180 seconds |
| Separate exact hard limit | 60 seconds |
| Exact reconstruction stop | Active-face column resource bound |
| Exact point or Farkas certificate | None |

Both owned processes exited normally. The numerical process stayed within its 180-second limit. The total includes the separate exact stage.

The denominator-1,000 rational proposal passed the unit bounds and inequality rows but failed 5,952 exact equality rows. The denominator-\(10^6\) and denominator-\(10^9\) proposals exceeded the fixed common-denominator resource bound. Active-face reconstruction then stopped at the unchanged 1,600-column limit. No exact feasibility inference follows from the inequality checks or the numerical optimum.

The lossless numerical record preserves all 15,200 column values, 21,724 row values, and both complete basis-status arrays. Row values are explicitly in the numerically scaled row units. The numerical model included the stored positive power-of-two scales; exact acceptance used the unscaled integer matrix.

## Replay and archive

The independent replay rebuilt the earlier equivalent reduction and all 32 new coefficient rows directly from their integer vectors. It checked the source, model, numerical-scale and preparation bindings and confirmed the terminal UNKNOWN scope.

A deterministic gzip archive preserves all seven original run files byte-for-byte, including the numerical proposal and basis. It contains 1,982,786 raw bytes in 174,846 compressed bytes. Archive SHA256:

`41ec1e625290a71150f3f31238e681a79293de6123912eb36da26fe49f7b8968`

The archive was unpacked into a fresh directory and passed the same independent cold replay. The two replay reports are byte-identical. No optimizer or eigendecomposition was repeated.

Raw result SHA256:

`c766de716a7c0f4c372894d9dd68811e90b2570304c6f687d01362f4d72595d0`

Raw numerical record SHA256:

`ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf`

Raw exact-stage record SHA256:

`183d8640fcea05cfb7f480a611341e224b5de15f45be6c5d62b022277020ca73`

The terminal publication manifest lists the archive, lossless pack/unpack helper, summary, both cold replays, and the independent source review. The frozen preparation sources and model are unchanged.

