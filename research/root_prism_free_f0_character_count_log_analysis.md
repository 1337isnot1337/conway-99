# First count query: timing and row census

The frozen first signed-character query remains `UNKNOWN`. This analysis reads its saved log and exact input rows. It performs no solve, model rebuild, or new separation.

## What the log measures

| Native-clock interval | Seconds |
|---|---:|
| Before presolve | 0.34 |
| Presolve to search setup | 88.65 |
| Search setup to main search | 16.65 |
| Main search to native return | approximately 57.04 |
| Total native time | 162.6773 |

The stage timestamps are rounded in the native log. The three named presolve probes took 14.3, 10.9, and 30.2 seconds, totaling 55.4 seconds. The later setup probe took 13.2353 seconds. These four reported probes account for about 68.64 seconds. The log also reports 13.662 seconds across the `PresolveToFixPoint` timers and 5.936 seconds across `DetectDominatedLinearConstraints`. Named timers are not an exhaustive, disjoint wall-clock profile.

All 84 tables were expanded. The `new_bool: table expansion` rule was applied 20,607 times; integer encoding added another 3,311 Boolean variables according to its rule counter. No separate table-expansion wall timer is available.

The LP statistics report four components, 10,588 iterations and 196 added cuts. The final linear relaxation initially contained 27,052 rows and 903 cut generators. The first component's final displayed size was 1,750 rows, 18,533 columns and 123,020 entries. The log has no LP-only wall duration or attribution to original mathematical families. Its literal debug counters include `Overflow=0`, `Bad=70`, and `BadScaling=0`; this analysis does not infer the meaning or cause of `Bad`.

The actual search reached 433 branches and five conflicts. There was no returned solution. These counts do not establish proximity to a proof or witness.

## Which rows carry the arithmetic

The source reconstructs the exact family partition from the frozen original count matrix, protected PSD row IDs, product specification, and character records.

| Linear family | Rows | Nonzero terms | Maximum width | Maximum coefficient magnitude |
|---|---:|---:|---:|---:|
| Retained PSD directions | 92 | 877,079 | 15,038 | 2,021,027,760 |
| Selector integer refinements | 25 | 189,283 | 9,395 | 3,531,368 |
| Other inherited count rows | 27,627 | 202,753 | 85 | 72 |
| Trivial-character product links | 903 | 10,298 | 13 | 2 |
| Signed-character product links | 2,385 | 28,698 | 13 | 2 |
| Character-Gram equations | 32 | 377 | 32 | 3 |
| Total | 31,064 | 1,308,488 | — | — |

The 117 PSD/refinement rows contain 1,066,362 of the 1,308,488 linear terms, about 81.5%. They also contain every coefficient above 72. Thus they dominate the input's arithmetic volume and coefficient range. That is a structural observation, not a measured per-family runtime result.

The strongest direct runtime observation is the 68.64 seconds spent in named probing phases. The current evidence does not show whether dense-row propagation, table-generated literals, LP work, or their interaction caused most of that cost. It also does not establish a numerical-conditioning failure from the large coefficients.

## Consequences for a later formulation

There is an exact redundant table family. The 42 refined character tables project onto the original 42 profile tables, including every old tuple and its multiplicity. A separate equivalent model can omit the old 42 native tables and retain their projection certificates and full acceptance checks. This removes 5,733 redundant table tuples. The current queried model and its records stay unchanged.

The same frozen tables give exact coordinate domains, including holes. Installing those domains explicitly can be prepared as an equivalent transformation. The first run already found 240 table-domain reductions, so this would move known propagation into construction rather than add a new assumption. No timing improvement has been demonstrated.

A smaller probing allowance is an explicit algorithmic option because the saved timers identify its current cost. It could also lose useful propagation. A future comparison must be separately gated and preserve the full exact acceptance rules.

The dense 117-row family is a possible candidate for an external exact acceptance pool: keep the smaller necessary native subsystem, check every returned integer candidate against all saved dense rows, and add only violated original rows. Such a search would require its own prefix, deadline, and completeness rules. It is not implemented or authorized by this analysis. All 117 obligations would remain mandatory for a full count witness.

The newly prepared two-orbit tables are separate mathematical constraints. This report does not import them or claim that they improve runtime.

Reproducible source: `experiments/workspace/root_prism_free_f0_character_query_log_analysis.py`. Exact report: `experiments/logs/root-prism-free/f0-character-query-run01-log-analysis.json`, SHA256 `739e3ea18cd53d23a3caebe49b4f8849bac40b5bada20a487a6ac2a4c1f5e027`.
