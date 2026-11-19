# Completed blossom overlay on the full Fourier count model

The append-only overlay and its separate cold replay pass. The full target has 32,296 variables and 65,811 constraints; the initial model has 65,694 constraints. The 16,280 products, 44 allowed tables and 117 external pool rows are unchanged.

Exactly 6,854 core-matching blossom inequalities were appended to both models. They contribute 20,542 terms. The other 2,040 inequalities in the complete 8,894-row family follow from the saved domains. The preparation checks all 6,120 upper-bound uses in those omission certificates against the actual native02 domains.

## Preserved failed attempt

Attempt01 used system Python and failed with ModuleNotFoundError for ortools before any protobuf was loaded. Its child exited and was reaped. The owner took 1.283 seconds. No model archive or solver result was created.

The failed record remains unchanged:

- Report SHA256: 7af550ad580a5ac5095b255b0723bd2c45d495d5ac2cac4d3c75e7f1010e3df9.
- Owner SHA256: 6dec2e04b7371f3d306e421b4cf93c397462983c07d86dcd7c96572d1c9b69ab.

A separately authorized environment correction used the established native interpreter with OR-Tools 9.15.6755 and optimization level zero. The source and preparation were unchanged. The environment record has SHA256 93035d565d7a33e78d1b07eadd8af3a29411be7e95978dc2322a2fe5b8c8f8fc.

## Successful build02 and cold replay

| Stage | Owner seconds | Child seconds | Result |
|---|---:|---:|---|
| Build02 | 26.988 | 24.798 | PASS |
| Separate cold | 15.634 | 15.190 | PASS |

Both stages used separate 60-second owned deadlines. All children were reaped. Neither stage constructed a solver or queried a candidate.

The build report has SHA256 ddd0eac97aac5741a60778276ac1798240089a547ffb43a77629fb8736114d4e. The cold report has SHA256 268a2d4f97f4436823f4d36271425c856ad770f5877667941b13e403f5b9166f.

| Artifact | Compressed SHA256 | Raw SHA256 |
|---|---|---|
| Target | fe349215460dcf8e609d1381e357e14c6f5b7fb21ea896f59bddc91b707133a9 | 60de781b2b324c270bac9cec30c1adbc769631dc959c1a2e2414fbc5eef96ab6 |
| Initial | 1f633c70a669badb8d151a7696d744c194b8ed649b4a6f90a0ea7b8142efb7ee | 940e34316ed30532aee8c192947a7d69e54ccd7e9ebf8d85a3c4ada912a7331a |
| Plan | 0aeb8cd5a53362f68dff836a9792c1ccea17bef349bf4389f92ed90479032502 | 1065773bf8c6e5bf213f700a6232f2e86b39c91335d3617b9b9ca753ccf8050d |

The audits check every one of the 13,708 appended row instances against the immutable compact certificates. Deleting the suffix restores both complete native02 protobuf hashes exactly. This includes every old variable, domain, table, product and linear coefficient, rather than only a row-count comparison. Every initial constraint is compared to its mapped target constraint, and all 117 pool hashes and IDs are checked.

The initial model has 819,134 linear terms. Its maximum absolute box activity remains 783,727,900,923; the maximum for an added blossom row is 36.

## Interpretation

This is a stronger prepared necessary count model, with no new query outcome. A future proposed integer vector still requires the independent restored-parent check and literal decoder. These averaged edge rows do not produce one shared symmetric Boolean exterior adjacency matrix.

The 6,854-row selection is justified by a complete comparison with explicit domain boxes. No claim is made that all selected rows are independent of every old inequality.
