# First lightweight search on the packed character-count target

## Result

The single authorized search returned `UNKNOWN_NATIVE_LIMIT`. It returned no integer candidate and appended no external row. The conditional F0 count model remains unresolved. There is no count-feasibility witness and no exclusion.

The owned process used 173.234155097 seconds, including imports, archive loading, native construction, search, and saved records. The native response records 167.568 seconds, 112,695 LP iterations, 4,531 branches, 68 conflicts, and no solution. The main search began at native time 5.01 seconds. These counters describe this run; they do not establish why it failed to find a candidate or predict another tactic's performance.

## Frozen model and search scope

The model has 18,444 integer variables. All 34,398 constraints remain in the full target; the initial native subset has 34,281 constraints and the external pool has 117 dense linear rows. The exact Z and Y packing bounds changed variable domains, while all constraints, variable IDs, products, tables, and pool IDs remained fixed.

The query used one worker, seed zero, probing level zero, one 180-second owned budget, at most twelve native calls, and at most sixteen exact violated pool rows per returned integer candidate. Only one call occurred. The driver saves a returned vector before any costly check. A full-target-passing vector would remain provisional until the separate original-parent arithmetic checker accepted it. This run produced no vector to check.

## Cold replay

The separate owned terminal replay passed in 4.254282227 seconds, with no optimizer call. It verified the exact 34,281-row saved native prefix, the complete 117-row target pool, all 18,444 domains, parameter serialization, native response, and the one-call chronology. It retained the terminal UNKNOWN and made no original-parent acceptance claim.

The full query result is `experiments/logs/root-prism-free/f0-character-packing-light-query-run01/result.json`. The cold report is the sibling `f0-character-packing-light-query-run01-cold/report.json`. The preparation and its source gates are in the separate `f0-character-packing-preparation-artifacts01.json` package. The raw saved call-zero model is byte-identical to the final initial-model archive and can be restored by gzip decompression; the terminal manifest records both hashes.
