# Append-only core-matching blossom overlay

This preparation adds 6,854 proved linear inequalities to the completed native02 count model. The complete family has 8,894 rows. The other 2,040 rows follow from explicitly saved variable upper bounds.

The preparation is frozen without constructing a native model or running an optimizer. The source is root_prism_free_f0_core_matching_blossom_native_overlay.py, SHA256 45ec9069c1091f8c118a299f1806897fb52694f55814b01961f220443ff150b6. Its metadata record is f0-core-matching-blossom-native-overlay-preparation01.json, SHA256 cd6e7e3e56109ad09127d10f59d14b29b4704f316e22599abe094bb3d409b196.

## Exact scope

| Quantity | Native02 | Prepared overlay |
|---|---:|---:|
| Variables | 32,296 | 32,296 |
| Full target constraints | 58,957 | 65,811 |
| Initial constraints | 58,840 | 65,694 |
| Product constraints | 16,280 | 16,280 |
| Allowed tables | 44 | 44 |
| External pool constraints | 117 | 117 |
| Added linear rows | 0 | 6,854 |
| Added linear terms | 0 | 20,542 |

Every existing column ID and domain remains unchanged. The source appends the same sequence to target and initial. The new initial-to-target entries are target indices 58,957 through 65,810. All old pool IDs, target indices, coefficients and hashes remain unchanged.

The source loads the existing archived plan and protobufs through the frozen lightweight loader. It does not import the mathematical native builder or reconstruct any earlier subset, representation, motif or blossom census.

## Why all 8,894 rows remain enforced

The compact all-row, selected-row and omitted-row files are immutable and bound by SHA256. The preparation checks that the selected and omitted IDs form a disjoint partition of all IDs 0 through 8,893, and that their row coefficients and witness references agree exactly.

Every coefficient is positive. For each omitted row, the saved certificate supplies upper bounds u_j with sum(c_j u_j) at most the row's right side. All 6,120 used native02 upper bounds are checked to be no larger than those saved bounds. Thus the omitted inequality follows from the actual unchanged domains.

The 6,854 appended rows have nonnegative variables and coefficients. Their native domain is 0 <= sum(c_j Y_j) <= rhs. The lower bound is already implied by the old domains. The maximum absolute box activity of any added row is 36, well within the native integer range.

This comparison establishes only the stated box implication. It does not prove that every appended row is independent of the complete old model.

## Build and replay boundary

Build and cold replay are separate owned child processes with a fixed 60-second hard deadline each. A late, failed or killed child cannot produce an accepted result. Existing output directories are refused. There is no automatic retry and no solver construction.

After a future build, the source will check every appended protobuf row against the frozen compact inventory. Removing the complete suffix from each saved model must restore its exact native02 protobuf SHA256. It also compares all initial rows to their target positions and verifies all 117 external rows. The cold pass repeats these arithmetic and byte checks on saved output, without recreating the family.

The parent protobuf hashes are:

- Target: 4e0ec33cb363299a9e199ce33a30a937a85d2f96969965f54833ed38464a911b.
- Initial: cf4c7cf7cb21087f443f5bdd6f2781a02e13091b7329d7f05fe78820182e179d.

The metadata preparation completed in 0.369 seconds. No protobuf was parsed, no native package was imported and no model was constructed during that preparation. Build and cold output hashes remain unset until those separately gated stages run.

A future integer vector still requires restored-parent arithmetic acceptance and the literal decoder. These averaged edge inequalities do not construct one shared exterior adjacency matrix.
