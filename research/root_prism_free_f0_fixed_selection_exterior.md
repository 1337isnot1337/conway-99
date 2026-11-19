# Shared exterior edges for a specified first incidence

The new adapter reuses the original fixed-incidence exterior builder and
inspector. Its input is a sorted list of 60 distinct signature IDs in the
complete F0 domain. It reconstructs the data from that list and checks all
172 original selector equations. It never calls the historical input
loader or fixes the historical incidence in a new query.

The [adapter source](../experiments/workspace/root_prism_free_f0_fixed_selection_exterior.py)
has SHA-256 `2c8a0f7f2bc2a219c994f42618585879e16a6d3a5809627b9aea25be40798160`.
Its preparation checks the complete historical data against the original
model and binds the unchanged function ASTs for `build`, `inspect`, and
`read_clauses`. It does not build a new CNF or construct a solver.

## Necessary edge conditions

Let H be the 18-by-60 first-component incidence matrix, A its fixed cubic
component adjacency, and D the unknown exterior adjacency. A completion
requires one symmetric Boolean D with

\[
D\mathbf1=8\mathbf1,\qquad HD=2J-H-AH.
\]

For every distinct exterior pair u,v, it also requires

\[
(D^2)_{uv}+(H^TH)_{uv}+D_{uv}\le2.
\]

The missing second component can only add common neighbors, which is why
this is a necessary upper bound. It is not an assertion that the second
component contributes zero.

The reused builder imposes all 60 degree equations, all 1,080 mixed
equations, and all 1,770 pair caps on one shared edge set. It retains the
original eligible edge domain. The later 162 zero edge orbits are not
silently substituted into this model.

If a degree or mixed row has too few possible selected neighbors, the
adapter records a direct capacity contradiction and its universal
selector inequality. Otherwise it prepares the full Boolean edge model.
A separately owned cold phase must reconstruct the complete data and CNF.
A solver query and any new DRAT proof remain later stages.

Even a satisfying exterior graph would leave the second component,
its incidence, and further motif conditions unresolved.

## Historical control and the limit of local matchings

The earlier
[60-signature incidence](../experiments/logs/root-prism-free/f0-incidence-case00-run01/result.json)
has SHA-256 `64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf`.
The new data factory reproduces every field of its original exterior
model. That model has 1,224 primary edge variables and 426,090 clauses.
Its existing
[complete CNF and DRAT replay](../experiments/logs/root-prism-free/f0-first-design-exterior-run01-cold-replay.json)
already excludes that particular incidence. The new preparation binds
those files; it does not repeat the old solver or proof check.

The separate eight-vertex matching oracle passes this historical incidence
at all 18 core sites. Its
[result](../experiments/logs/root-prism-free/f0-core-matching-old-incidence01/result.json)
and [cold replay](../experiments/logs/root-prism-free/f0-core-matching-old-incidence01/cold.json)
give an explicit example where all separate local matchings exist but no
shared exterior graph satisfies the stronger constraints.

This historical incidence is also rejected by the current literal cuts.
Direct Python integer evaluation and an independent JavaScript BigInt
evaluation check all 4,416 cuts. The violated row IDs and excesses are

| Row ID | Excess above its upper bound |
| --- | ---: |
| 0 | 1 |
| 24 | 3 |
| 590 | 1 |
| 599 | 1 |
| 650 | 1 |
| 4415 | 2 |

The complete scans are retained with the matching result. This control is
not a new accepted incidence for the current model and gives no new
whole-case exclusion.
