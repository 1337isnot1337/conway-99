# Combined exterior formulation for component zero

The completed strengthened-model query returned UNKNOWN with no vector. The next native preparation combines one exact reformulation with two additional necessary graph conditions. The accepted 68,934-variable, 257,594-row model remains unchanged until a separate build and complete independent replay pass.

## Accepted inputs and remaining check

The [complete star inventory](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-inventory01.json) has 2,448 distinct channels for all 23,010 retained four-exterior rows. Its [root terminal review](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-root-terminal-review01.json) checks every reported channel identity, all 46,020 origin links and all mixed-row support inclusions. The source has complete independent review.

The [triangle indicator inventory](../experiments/logs/root-prism-free/f0-spectral-triangle-support-indicator-inventory01.json) has 5,364 distinct triangles for 84 live targets. Every target incidence is unique to its triangle. The [separate literal replay acceptance](../experiments/logs/root-prism-free/f0-spectral-triangle-support-independent-literal-root-acceptance01.json) confirms the complete original edge namespace, all 1,956 initial zeros, 132 targets, 48 already-zero targets, all 6,540 structural supports and all 5,364 surviving supports. Root also recomputes the normalized full-table hash and compares every indicator identity.

The [forest inventory](../experiments/logs/root-prism-free/f0-cap-one-forest-support-inventory01.json) covers all 48 accepted cap-one pairs and all 23,040 candidate dispositions. All pairs retain 80 through 84 common-neighbor candidates, totaling 3,936 wedges; no small-support skip occurs. The [root artifact review](../experiments/logs/root-prism-free/f0-cap-one-forest-support-root-artifact-review01.json) reconstructs all 3,984 proposed variables and 15,888 native row keys from the saved supports. Separate reconstruction of the complete original literal support universe is still pending at this publication. The final actual-input configuration must bind its successful replay.

## Three constraint families

For each exact old live-star support, introduce a Boolean residual p and the definition

    p + sum(y_e for e in the star) - x_center = 0.

A checked quota-one mixed equation bounds the star sum between zero and its center selector. Each old four-exterior row then becomes

    -2 <= y_central - p_left - p_right <= 0.

This has a unique auxiliary extension and preserves the old integer projection. Relaxing the auxiliary domains also preserves the old real projection. No later spectral zero is substituted into an old star.

For each surviving triangle, a Boolean indicator t equals the AND of its three original edge bits. The rows are the three bounds 0 <= y_e - t <= 1 and the lower bound -2 <= t - y_1 - y_2 - y_3 <= 1. Each live target receives the equality sum(t for its complete supports) = y_target. The central edge belongs to the AND, so an inactive target may still have a two-edge path. These are additional necessary conditions; they are not claimed to be consequences of the previous relaxation.

For each cap-one pair a,b and each complete live candidate c, introduce the Boolean wedge indicator z_c with z_c >= y_ac + y_bc - x_c and z_c <= y_ac,y_bc. Introduce Boolean Z = sum(z_c), enforce Z <= x_a,x_b, and add

    y_ac + y_bc + Z - z_c <= x_a + x_b.

The [forest theorem](root_prism_free_f0_common_neighbor_forest_extension.md) proves these rows represent every root-omitted subset forest inequality. Its real projection statement uses relaxed auxiliary bounds; its integer statement uses the original Boolean activations. The pair's central edge has no assumed value.

## Fixed combined indices

All indices below are zero-based. Original variable messages remain unchanged.

| Family | New variables | Variable indices | New appended rows | Appended row indices |
|---|---:|---|---:|---|
| Star definitions | 2,448 | 68,934 through 71,381 | 2,448 | 257,594 through 260,041 |
| Triangle ANDs and target equalities | 5,364 | 71,382 through 76,745 | 21,540 | 260,042 through 281,581 |
| Cap-one forest extension | 3,984 | 76,746 through 80,729 | 15,888 | 281,582 through 297,469 |

Exactly the 23,010 original rows at indices 227,270 through 250,279 are replaced in place by their three-term counterparts. Every other original row remains byte-identical. The new total is 80,730 variables and 297,470 rows.

The standalone star inventory proposes a different row order, with definitions immediately before the replacement block. This combined plan instead preserves every original row index and appends the definitions. The equations and channel identities are the same. Triangle and forest inventories likewise use standalone auxiliary offsets; the combined builder must rebase them to the disjoint ranges above.

The old four block has 401,874 coefficient occurrences. Star definitions and replacements have 91,410, a reduction of 310,464. Triangles add 59,088 and forest rows add 59,280. The net change from the accepted model is therefore a reduction of 192,096 coefficient occurrences.

## Native preparation contract

The producer and checker are separate sources. Preparation has zero optimizer calls. It exports the complete native model, a patch containing the new variable messages and replacement rows, and the true appended-row suffix. The edited prefix plus suffix must reproduce every new native byte. Removing new variables and appended rows and restoring the original four block must reproduce every accepted parent byte. The old complete raw model is not claimed to be an unchanged prefix.

The independent checker uses protobuf only and reconstructs every new and replaced literal row with the combined offsets. It also checks all unchanged variables and rows, exact archive/raw identities, and complete parent restoration. Source review, tiny controls, separately owned preparation and complete replay precede any new query. A later query needs its own frozen source, configuration and execution bounds.

The model still treats one first-component type under the stated globally prism-free split hypothesis. It does not encode all exterior common-neighbor caps or a complete compatible second component. No graph, whole-component exclusion or unrestricted solution is established by these inventories.
