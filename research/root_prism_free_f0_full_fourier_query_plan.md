# Full Fourier native query and candidate-check plan

Status: preparation design. The combined native preparation is still running when this note is written. No production query is authorized by this note. Actual model, query-preparation and candidate hashes must be taken from completed records before a source is frozen.

## Frozen mathematical target

The combined target has 32,296 variables and 58,957 constraints. Its initial search prefix has 58,840 constraints; the remaining 117 rows are the unchanged, explicitly indexed external pool. All 16,280 product constraints and all 44 allowed-assignment tables are present initially. The 42 extended local tables replace their old projections; the two joint tables are retained. The 4,416 literal selector inequalities are encoded by 4,404 direct rows and 36 radix equations, with 480 exact inverse links.

The mathematical specification is f0-full-fourier-specification-ci01/specification.json.gz, SHA256 929703b3a685f95fb28bc6553aef02d5c7f6c879628154c62b8ecfa7d69ba8d5. The literal layer is f0-literal-cut-native-layer01/layer.json.gz, SHA256 dcb44159712f9c9a4f61cc61950c23d62b804a0d57709ca43afb33e3711d2b33. Configuration 96e8544121f3d285db3d0d438afb059be3a10d0cd1230fa951eb1ce816e494db binds both layer sources, completed proof records and source gates. The native v2 adapter is ce21cabaa26e28e69f84380736adb28b7e193037a67a83d0ec79df84230b77ad. A successful native report and its independent owned cold replay remain prerequisites.

## Proposed search adapter

Start from the reviewed root_prism_free_f0_character_packing_no_lp_query.py (SHA256 f3f704371307da14ab035eed1b2a7345bb1725babf0f01cc8e06d5b7e26475e7) and its separate terminal replay. Preserve one 180-second owned budget, one worker, seed zero, probing zero, linearization level zero, at most 12 native calls and at most 16 appended pool rows per returned point. A later call requires a strictly larger certified row prefix. No new objective, hint, selector fixing or visitation clause is proposed.

The narrow changes are actual source/archive bindings, dimensions, descriptive status fields and complete prefix checks. The integer evaluation, pool scan, row selection and solver parameter functions should retain complete AST identity. All appended rows come from the same 117-row pool. Full protobuf and domain checks remain authoritative.

The owner should avoid the duplicate complete archive hashing that consumed uninstrumented time in the first native preparation. A separately reviewed ownership delta can bind the small preparation/source records in the owner and retain every complete configuration/archive check in the worker before construction. The total 180-second owner includes startup, imports, archive loading, public model construction, serialization, calls, scans and durable writes. This is a proposed implementation change, not an executed or accepted query.

Every returned vector must be saved atomically as a plain JSON root array of 32,296 exact integers before response-text conversion or expensive checks. A full-target passing vector remains PROVISIONAL until the separate restored-parent arithmetic receipt passes. An INFEASIBLE backend status has no exclusion force without an independently checked proof. A late or failed child yields no accepted search outcome.

## Exact candidate namespaces

| Native interval | Meaning |
| --- | --- |
| [0, 15038) | Retained orbit counts, with all original column maps preserved |
| [15038, 15941) | 903 deterministic population product auxiliaries |
| [15941, 16059) | 118 signed character populations |
| [16059, 18444) | 2,385 signed-character product auxiliaries |
| [18444, 18612) | 84 plus Fourier columns, two integer coordinates each |
| [18612, 18764) | 76 minus Fourier columns, two integer coordinates each |
| [18764, 31756) | 12,992 Fourier scalar-product auxiliaries |
| [31756, 32236) | 480 literal selector bits |
| [32236, 32296) | 60 signed-radix auxiliaries |

The coordinate_records in the frozen specification define representation, column_index and part for every Fourier coordinate. The production adapter must verify that ordering; it must not rely only on the interval lengths.

## Restored-parent arithmetic receipt

Adapt the reviewed root_prism_free_f0_character_parent_receipt_no_lp.py, SHA256 4f773f33929465220205c2c4cbba2228026b38321af7a3ec48451af9e1dbd1ce. The complete new target is evaluated on all 32,296 values using Python integers. The original 18,444-variable native parent is evaluated on the first 18,444 values, and the unchanged count/restored-row checks use their original exact maps. This preserves the distinction between the complete candidate-file hash and any projected vector hash.

The receipt must bind the candidate file SHA256, canonical complete integer-vector SHA256, vector field, actual target protobuf SHA256, model-preparation SHA256, query-preparation SHA256 and acceptance-source SHA256. It must separately state full_target_checks_passed and restored_original_parent_checks_passed. Only a successful owned exact check can set accepted and count_feasibility_claimed true. The target arithmetic includes all literal-bit inverse equations and every radix auxiliary equation.

## Independent Fourier-to-literal check

Reuse the frozen abstract decoder root_prism_free_f0_fourier_literal_decoder.py, SHA256 94a7246f1aaf1715fab1c05b98519570bc4ac7e370c77ad7a03353ec06aa0d3f, with preparation 073e074ce272a542d9ae6e20456523678f9c6496ac09193b5598ace27953bffc and cold 0015f4e0b7052eebf526a3601da1e15ebfb04b8cb7bed9a0ad19d54401acdde7. The narrow native intake first requires the accepted arithmetic receipt and compares its actual source/model/query/candidate bindings.

Restore N from the first 42 count coordinates, the 118 signed populations from [15941,16059), and all 9,742 original pair counts from the frozen old/new map, inserting precisely the 389 certified zero pair orbits. The abstract Fourier_ab fields are keyed central_plus and central_minus in the frozen column_index order. Each contains integer [a,b] pairs. No new mask census or CSP search is required: the complete local Fourier data have a unique saved literal-mask preimage.

The decoder independently checks Fourier inversion, all pair histograms, all 172 original selector equalities, the profile and fiber margins, the 90 motif exclusions, the 4,410 literal zero pairs and all 4,416 original literal inequalities. Its reconstructed 480 bits must equal the explicit native interval [31756,32236). Its internal scope flags remain unchanged: the abstract kernel does not itself verify the native model or count receipt. An outer report can bind both checks without changing either claim.

A successful literal incidence does not realize the exterior Y edges. Exterior graph completion and a global Conway99 result remain separate tasks.
