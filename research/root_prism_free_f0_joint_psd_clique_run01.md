# Bounded joint PSD/clique query 01

The one authorized query ended **UNKNOWN**. HiGHS reached its time limit after 21 IPM iterations on the 15,200-variable, 28,043-row model. This result establishes neither feasibility nor infeasibility of the local stratum.

The model contains every preceding path-prism row and scale, plus the 21 replayed PSD inequalities and all 258 core-pair edge-clique inequalities. There was one optimizer call, with crossover disabled. The numerical phase took 177.163 seconds including its setup. Its owned process returned normally after 179.976 seconds, within the 180-second limit; the enclosing result bookkeeping finished after 180.031 seconds. No hard timeout killed the process.

The numerical status was `HighsModelStatus.kTimeLimit`. Both `value_valid` and `dual_valid` were false. The driver did not request a dual ray for this status, and the exact phase did not run. It did not request a basis, reconstruct a primal point, or retry the optimization.

The saved file still contains 15,200 finite column values and 28,043 finite row values. Of the columns, 15,004 are nonzero; their range is 0 through 0.545936766605802. These values can propose further valid exact inequalities, but their existence does not certify a feasible point. A separate complete row audit is required to describe their exact residuals.

The frozen standalone cold replay passed. It reconstructed the 21 PSD and 258 clique rows over the certified parent, checked every old row/scaling prefix, and verified the terminal file and proposal bindings. It preserved the UNKNOWN classification and found no exact Farkas certificate to replay.

| Artifact | SHA256 |
|---|---|
| `f0-joint-psd-clique-model01.json.gz` | `43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69` |
| Run `result.json` | `d0439012c0e44e05db6b84f0a4442b82c26a9b3bd8dfc0849f10bcdb545e575a` |
| Run `numerical.json` | `c55a4e3e65df053a05dca2530d152a1d35fa18c653cdd2523443834885b1d594` |
| `f0-joint-psd-clique-query-run01-cold-replay.json` | `3bdd7baa5aab64a52a8b30c32ad6048d3682b0531389d7962c098ffb8fcbeb00` |

The exact preparation is documented in `root_prism_free_f0_joint_psd_clique_model.md`. No new optimizer call or spectral scan is part of this terminal package.
