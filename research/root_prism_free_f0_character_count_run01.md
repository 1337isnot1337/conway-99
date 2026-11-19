# First signed-character count query

The single authorized query returned `UNKNOWN_NATIVE_LIMIT`. It produced no count assignment, feasibility witness, or exclusion. Its separate cold replay passed.

The queried model is the complete signed-character extension described in `root_prism_free_f0_character_cpsat.md`: 18,444 bounded integer variables, 31,064 linear constraints, 3,288 exact products, and 84 allowed-assignment tables. It retains all 92 previous PSD directions, all 25 integer refinements, all inherited count conditions, the 903 trivial-character population products, and the complete signed-character products and local tables. It assumes no completed-graph automorphism.

## Observed outcome

| Item | Recorded value |
|---|---:|
| Production solve calls | 1 |
| Workers | 1 |
| Random seed | 0 |
| Hard owner limit | 180 seconds |
| Total owner time | 175.702235249 seconds |
| Public model construction | 7.430285099 seconds |
| Assigned native time limit | 164.441979268 seconds |
| Native reported time | 162.677295846 seconds |
| Search branches | 433 |
| Conflicts | 5 |
| Native Boolean variables | 25,720 |
| Integer propagations | 3,238,230 |
| Returned solution values | 0 |
| Owner deadline overrun | 0 seconds |

The native log reports search setup starting at 88.99 seconds and the main search starting at 105.64 seconds. These are native-clock observations. They do not by themselves attribute the runtime to one mathematical constraint family. A separate log analysis may assess that question; this package does not claim that the PSD rows, tables, or products caused the limit.

The child exited with code zero before the owner deadline. The native status is `UNKNOWN`. No infeasible status or independently checkable infeasibility certificate was returned. No literal-incidence lift was attempted because there was no count candidate.

## Cold replay

One standalone replay ran under the reviewed supervisor with a separate 60-second limit. It completed in 14.520608662 seconds of owner time; the checker reported 13.043144928 seconds. It rebuilt no optimization model and called no solver.

The replay reads the archived protobuf, verifies its complete inherited prefix, checks every appended domain and constraint, verifies the one-call parameters, and binds the saved response and terminal status. The result remains `UNKNOWN`; replay does not convert it to a feasibility or exclusion claim.

Key SHA256 bindings:

| Artifact | SHA256 |
|---|---|
| Raw queried protobuf | `5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb` |
| Query preparation | `c480e2df6dbec03d95d3c8c1f387933b28c7e212c9e86a33d0b7f349451d4384` |
| Query preflight | `6622cb3f7783224f56d1b350664916b15155d8232b596445ddcbb8248bd50124` |
| Terminal result | `559caa13f84f458339fcd6357aa4c6ac7ddb83fbeee3400ce4e054c8f5caf837` |
| Cold terminal replay | `12655340cb422089fa406aea97487ee62b914f1295c9a16b60f8b0e4741e0df8` |

## Preservation and replay

The raw native protobufs are published as lossless gzip archives. `root_prism_free_f0_character_archives.py restore` restores only absent raw files and refuses to overwrite different content. It checks the raw byte count and SHA256 for the product parent, basic profile overlay, signed model, and the model constructed by the query child. The last target is byte-identical to the signed-model archive.

The frozen preparation note, original model sources, query sources, native response, logs, owner records, and cold records are unchanged. The publication manifest lists each file and its exact byte hash. The conditional scope remains the F0 split-shell component-zero count model. Neither the component nor the global graph problem is excluded.
