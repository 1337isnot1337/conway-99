# Combined F0 native preparation

The frozen formulation has 80,730 variables and 297,470 rows. It combines the exact star-channel replacement with the complete triangle-support and cap-one forest extensions. This is a necessary-condition model for the globally prism-free F0 split-18+18 case. It does not supply the other component or prove unrestricted existence or nonexistence.

## Completed native run

[Run 44639233433](https://github.com/1337isnot1337/conway-99/actions/runs/44639233433), source commit `2f074cdeb65731a1a638c29e46f980ebecb964b7`, completes one native build and one complete independent replay on its first attempt. The [root acceptance](../experiments/logs/root-prism-free/f0-combined-extensions-native-root-acceptance01.json) binds every actual report and owner. No solver was constructed or called.

| Phase | Owner seconds | Owner limit |
| --- | ---: | ---: |
| Producer controls | 0.118 | 15 |
| Native preparation | 12.697 | 135 |
| Independent controls | 0.115 | 15 |
| Full independent replay | 7.332 | 135 |

The complete driver takes 20.456 seconds within its 420-second bound. All four owners report successful child exit, child reaping, stopped process groups and zero overrun. The final model has 3,310,380 linear terms, compared with 3,502,476 in its parent.

The recovered compressed model has 5,632,144 bytes and SHA-256 `afeadb94ffa6fba0465a3dbe0094f4c7f7c156de8d7aa5f24a8fcfa38d275542`. Decompression produces 39,306,083 bytes with SHA-256 `2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6`, matching preparation and cold replay. The raw model is stored losslessly in that archive. All 39 small outputs are preserved in their original bytes, including the large integer controls; root verifies 178 cross-references.

The checker compares all 68,934 original variables, 234,584 unreplaced rows, 23,010 replacement rows and 39,876 appended rows. It reconstructs all original eligible edges and neighbor lists, every affected star/triangle/forest support and every new variable message. Removing additions and restoring the replaced rows reproduces all 38,374,405 parent bytes. This accepts the necessary-condition model; general exterior pair caps, a compatible second component and unrestricted existence remain unresolved.

## Exact changes

| Family | Variables | Rows | Linear terms |
| --- | ---: | ---: | ---: |
| Retained-four replacement | 0 | 23,010 replaced | 69,030 |
| Star definitions | 2,448 | 2,448 appended | 22,380 |
| Triangle AND definitions | 5,364 | 21,456 appended | 53,640 |
| Triangle target equalities | 0 | 84 appended | 5,448 |
| Cap-one forest extension | 3,984 | 15,888 appended | 59,280 |

The original model has 68,934 variables and 257,594 rows. All original variable messages are retained. Only rows 227,270 through 250,279 are replaced; the other 234,584 original constraint messages are preserved. A total of 39,876 constraints is appended. The replacement and extensions together reduce the number of coefficient occurrences by 192,096.

The star replacement has a unique Boolean extension and the same continuous projection under the original mixed equations. The triangle and forest blocks add proved necessary conditions. Both support inventories have completed separate literal reconstruction. The forest replay checks all 48 pairs, all 23,040 candidate dispositions and all 15,888 standalone row keys, with no candidate disjointness or triangle-cover filter and no assumed anchor-edge value.

## Native build and independent replay

The active producer is `root_prism_free_f0_combined_extensions_model_v2.py`. Its predecessor is preserved; the sole change restricts a new-name uniqueness assertion to the newly introduced variables. The active independent checker is `root_prism_free_f0_combined_extensions_replay_v2.py`. Its preserved predecessor has a metadata variable-shadowing defect; six local substitutions repair the reported forest disposition digest without changing the mathematical checks.

The independent checker imports the protobuf decoder, not the producer or native optimizer. It regenerates every affected literal support, variable and constraint, compares every preserved original message, verifies the complete patch and appended suffix, and restores all 38,374,405 original model bytes. The edited prefix is a prefix of the new model; the original raw model is not an unchanged prefix.

The one-run workflow has four separately owned phases. Producer controls and checker controls each have a 10-second worker bound and 15-second owner. Native preparation and complete independent replay each have a 120-second worker bound and 135-second owner. The driver allows 420 seconds; the workflow job allows 12 minutes, including runtime installation and artifact export. It authorizes one native build and zero solver calls, with no automatic retry. Every successful phase requires a reaped child, a stopped process group and matching exact terminal artifacts.

Reports, ownership records, logs, the patch and suffix are exported as exact original bytes. The full raw model and compressed model are retained in the workflow artifact; the compressed model is also exported in bounded chunks. Large control integers must not be rounded by republishing parsed JSON.

At checkpoint 89 publication, no new native build, checker main or solver call had run. The root must accept the actual build and independent replay before any separate query preflight or query authorization. The previous model's query remains UNKNOWN with no vector.
