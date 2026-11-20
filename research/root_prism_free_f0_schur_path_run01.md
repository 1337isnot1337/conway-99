# First Schur/path-prism numerical query

The single authorized query returned a numerically optimal point. Its
mathematical status is UNKNOWN. There is no exact primal certificate or
infeasibility certificate from this run.

| Item | Observed result |
| --- | --- |
| Backend status | HighsModelStatus.kOptimal |
| Optimizer calls | 1 |
| IPM iterations | 33 |
| Simplex iterations | 0 |
| Crossover iterations | 0 |
| Numerical child elapsed time | 157.849386582 seconds |
| Supervisor elapsed time | 159.223194346 seconds |
| Numerical child limit, including setup | 180 seconds |
| Hard timeout | No |
| Existing dual ray requested | No; the numerical status was not infeasible |
| Exact reconstruction calls | 0 |

The run used the complete prepared overlay: 15,200 variables, 6,135
equalities, 21,629 inequalities, and 905,276 nonzero coefficients. It retained
all 480 component-zero signatures, all inherited selector and RLT conditions,
71 fixed PSD directions, 162 edge-zero equalities, 715 one-edge prism rows,
and 5,124 two-edge prism rows. The later 258 core-pair clique inequalities
were not included.

The conditional scope remains the globally prism-free and F-free split
18+18 shell with component zero. No first incidence was fixed, and the
second component and alignment were free. This run does not establish a
feasible graph or exclude the component.

## Preserved proposal

The numerical record stores all 15,200 column values and 27,764 row values
as hexadecimal binary floating-point strings. Its SHA256 is
`bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e`.
These values are proposals for later exact arithmetic. The backend's
`value_valid` and `dual_valid` fields are both true; neither field is an
exact certificate.

The query did not request a basis or run primal reconstruction. Its exact
phase was restricted to a dual ray that already existed after numerical
infeasibility. That condition did not occur, so the exact phase was skipped.
No second numerical call was made.

## Cold terminal replay

The standalone replay passed in 13.715607240 seconds. It verified the bound
parent certificates, reconstructed all 5,124 appended inequalities and
61,488 literal transports, checked the complete assembled matrix and scale
hashes, and preserved the UNKNOWN terminal status. It checked all stored
numerical strings for the required dimensions and finite values without
claiming exact point feasibility.

The replay record is
`f0-schur-path-query-run01-cold-replay.json`, SHA256
`e8dea0c594a982b729303f920ce49832441be4b7a8648f4ff54b89a0eaac8e83`.
The mathematical matrix remains
`24da97cfaf7bdb6e73efcdf9b248d70f30e04443dada5a2c923ab112f10bc812`.

Exact feasibility and exact infeasibility remain unresolved for this model.
