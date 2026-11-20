# Independent reconstruction and cross-quota certificates

The compact reconstruction reproduced the complete original four-exterior family: **73,404 cases, 936 central-zero cases, no empty-side cases, 72,468 distinct rows, and 1,250,496 terms**. Its ordered row-key SHA256 is exactly the previously accepted value:

`2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c`

The census took 10.694 seconds. Input checks, reconstruction, classification and complete serialization took 14.876 seconds. The preserved report is 10,809,436 bytes, within the declared 30-second census, 60-second total and 16 MiB limits. No retry occurred.

## Complete original family

The source independently reconstructs the original 68,394 eligible edges from signatures and mixed quotas. It then enumerates the 48 relevant core pairs and the two separated signature supports. Orienting each central pair with b<c and sorting all case tuples by (edge ID, i, j) recovers the accepted original order.

The report preserves every original row key as `[b,c,positive_edge_ids]`. The corresponding inequality is:

\[
\sum_{e\in E_+}y_e-x_b-x_c\leq 0.
\]

Its lower bound is -2, which follows from the selector bounds and nonnegative edge variables. Every original case, including the 936 central-zero cases, remains in the compact case array. A row's origins are exactly the case-array indices that refer to its row ID.

This is a reconstruction of the exact row family. It does not recover or rewrite the unavailable original compressed inventory or the old metadata-resolution records.

## Sufficient mixed certificates

For a core site k and exterior signature v, the existing mixed equation is:

\[
\sum_{w:\,vw\text{ eligible},\,k\in h_w}y_{vw}=q_{vk}x_v.
\]

For an original row with sites i,j and central endpoints b,c, the original premises give $q_{bi}=q_{cj}=1$.

When $q_{bj}=1$, the sum of the equations at (b,j) and (c,j) has selector coefficients $-x_b-x_c$ and includes every positive term of the target row. When $q_{ci}=1$, the equations at (b,i) and (c,i) provide the corresponding second recipe. Subtracting all surplus nonnegative edge terms gives the target upper inequality.

The program checks these actual coefficient identities. It constructs the complete mixed supports, requires exact agreement of both selector coefficients, and checks every target edge coefficient against their sum. Overlapping source supports retain coefficient multiplicity. A quota test alone cannot produce an accepted certificate.

| Cross quotas $(q_{bj},q_{ci})$ | Original rows |
|---|---:|
| (1,1) | 13,878 |
| (1,2) | 17,860 |
| (2,1) | 17,720 |
| (2,2) | 23,010 |

The output contains **63,336 saved certificates covering 49,458 rows**. It inspected 956,916 target edge coefficients and 126,672 selector coefficients.

The 23,010 rows without either sufficient recipe have 401,874 terms. Their ascending IDs are preserved as `retained_row_ids`, with canonical JSON SHA256:

`b53cff225273f025bc9b6d8e2cd6a654291993df8da4d0345a0dc2312b0dafac`

No original row is deleted from this report. The retained IDs are provisional until the separate artifact-only certificate check succeeds. Failure of these two sufficient recipes does not prove that a retained row is independent of all existing constraints.

## Verification boundary

The independent source review read the complete source, configuration and actual small controls. The root main gate authorized exactly one bounded run.

Root subsequently prepared a distinct artifact-only verifier. It rebuilds each star using center-neighbor traversal, accumulates full sparse native coefficient vectors, subtracts the target, and checks every selector residual and edge residual. It also checks every saved origin, promised side, row mask and retained ID. That verifier's full 116-line source passed a separate review by this agent; its main execution is outside this producer package.

Any row removal must bind the separately accepted artifact-check receipt. The present package preserves the producer result and all certificate data needed for that check.

## Durable artifacts

The complete report is available directly at:

`experiments/logs/root-prism-free/f0-four-exterior-cross-quota-independent01.json`

Its SHA256 is `7e9df6f8798483bbe4be386f857b8997dffd08dd409080c258fde2b9bcbbfb22`, and its Git blob is `b41abfd71d80c163a6180f6ab5276bfbed1a9e2e`.

Three exact contiguous chunks were uploaded before the full report. Their offsets and hashes are in [the chunk map](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-independent01-publication/chunks.json). They provide an alternative when a connector cannot return the complete blob in one response. The direct full-file upload succeeded and can be used by a fresh clone or CI without restoration.

The [finalization receipt](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-independent01-finalization.json) records the actual bounded run and successful serialization. The [summary](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-independent01-summary.json) records the counts and provisional retained-family digest.

The prior failed root-owned verbose attempt remains separate. This run used independent pair-support enumeration, compact arrays, explicit coefficient checks, and publication hashing after the complete output was safely stored. The small preparation-control failure and publication logging error are also preserved.

No native model was built or solved in this lane. No graph was constructed, and no F0 exclusion or global solution is claimed.
