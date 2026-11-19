# Four exact low-face branch exclusions

The single prepared 54-branch native-row pilot completed all branches. Four branches have exact contradiction certificates. Its separate cold replay accepted all four original-coordinate certificates and the complete numerical transcript. The other 50 branches remain unresolved.

The new Boolean consequences are:

| Guard excluded | Combined upper bound | Exact minimum over its whole box | Strict gap |
| --- | ---: | ---: | ---: |
| `x261 = x803 = 1` | 33,452 | 34,279 | 827 |
| `x262 = x803 = 1` | 53,423 | 54,489 | 1,066 |
| `x339 = x765 = 1` | 647 | 691 | 44 |
| `x761 = x1183 = 1` | 67,984 | 68,828 | 844 |

Thus each corresponding pair has sum at most one. The certificates are `forward/certificate-10.json`, `certificate-11.json`, `certificate-15.json`, and `certificate-53.json` under `experiments/logs/grids-and-triangles/rook-case4-low54-native-lp-run01/`.

## Why each pair inequality is unconditional

The three original Gram rows give `H27 + 2Q = 3`. Each excluded pair consists of one weight-one and one weight-two coordinate in this nonnegative identity. Selecting both exhausts the quota and forces all other positive-support coordinates to zero. The previously cold-checked complete branch propagation then supplies the entire saved box.

For each certificate, an integer signed combination of valid rows gives a linear form bounded above by the displayed upper bound. The minimum of that same form over the entire saved box is strictly larger. Every coefficient and box endpoint is replayed on all 1,214 original coordinates, including the 112 globally proved zeros. No numerical dual-feasibility premise enters this proof.

The excluded whole-cover box indices are 10, 11, 15, and 64. Removing them leaves 187 possible boxes: 50 low boxes and the unchanged 137 high boxes. This pilot proves no new global unit and no exclusion of the complete case.

## Numerical scope and timing

The pilot loaded one 1,102-variable, 2,288-row matrix with 26,266 nonzeros. It retained all 2,271 original native rows and 17 accepted additional rows. Every branch reset all 1,102 variable bounds. The large coordinate-cover matrix was not loaded.

There were exactly 54 native calls. Four returned infeasible and produced the accepted exact certificates. The remaining 50 returned numerically optimal; no exact primal feasibility claim was made for those boxes. Every call returned `kOk`; the longest measured native call was 1.309 seconds. Total native time was 18.662 seconds. The forward owner reaped after 20.440 seconds and the cold owner after 0.417 seconds, without a timeout. The complete wrapper finished in 20.862 seconds.

There was no retry or extra ray solve. The complete numerical records and bases are retained, including the 50 unresolved numerical points.

## Evaluation at the current global point

The separately accepted global selector point has denominator 2,594,289,631. It strictly satisfies all four new pair inequalities. Their slack numerators, in the table order, are 2,231,096,146; 2,231,096,146; 2,537,910,971; and 1,309,789,018. These four rows do not reject that point.

The artifact-only evaluation verifies the original-column byte hash, reconstructs all 1,214 coordinates from the saved extended point, and binds its independent point replay. It does not repeat branch propagation or optimize.

## Frozen records

- Terminal: `rook-case4-low54-native-lp-run01/result.json`, SHA-256 `63b8274dfdfd9cabe55155ab3fb2a8f1d9670dc2dd2c927d048bda1ed0ccce15`.
- Independent cold: `rook-case4-low54-native-lp-run01/cold.json`, SHA-256 `ea492ec530c512759b93d25afc6900a2468d1f221f75aac2eb39092bd8af73f3`.
- Terminal bindings and four-row evaluation: `rook-case4-low54-native-lp-run01-analysis.json`, SHA-256 `0e1cc245793cd1174699bd831355b92f72f7476570c083b1146515995dd6eaa6`.
- Production source gate: `rook-case4-low54-native-lp-root-gate01.json`, SHA-256 `5da4b8f59a0073c64775db4ebd0e4735fcd16ddb2e8c1ab024949854ed063a5d`.

The common log prefix is `experiments/logs/grids-and-triangles/`. The preparation package is separate and preserves the failed preflight and its narrow storage-format correction.

