# Local conflict clique scan at the F0 Schur/path point

The fixed scan produced no new retained restriction. All 128 retained
rows are exact copies of existing equality orientations after the 162
proved edge-zero substitutions. A separate checker verifies every one
of their 1,945,600 coefficients. They are not added to the next model.

## Scope and row proof

This calculation uses the complete 42-representative local conflict
inventory, covering all 480 exterior signature centers. A literal center
has eight exterior neighbors. If a set C is a clique in its proved
neighbor-conflict graph, at most one member of C can be selected as a
neighbor when the center is present. Therefore

\[
\sum_{a\in C}Y_{ba}\le x_b.
\]

The averaged row adds coefficients when distinct literal edges share an
edge-orbit variable. It does not identify their Boolean assignments or
assume that a hypothetical graph has the core symmetry.

The input numerical point is retained as exact dyadic numbers. Its
common denominator is 147573952589676412928. Exact evaluation at that
point measures a candidate gap; it does not certify point feasibility.

## Fixed search and replay

For each of the 42 centers, the scan starts a greedy clique from every
literal neighbor under three fixed orderings: edge weight, weight times
degree plus one, and degree followed by weight. This gives 34,974 trials.
The cap is 128 retained rows and the cooperative wall limit is 30 seconds.
The scan completed in 15.4507 seconds.

There were 187 positive-gap coefficient rows absent as literal existing
inequalities. The saved 128 rows have 5,924 nonzero coefficients, maximum
coefficient two, and clique sizes 23 through 65. They involve 39 center
representatives. Their gaps range from about 7.59e-18 to 8.17e-16.

A separate replay takes 3.0881 seconds and checks all 128 saved row witnesses
and 126 saved best-clique witnesses. It does not repeat the greedy search or
claim that these cliques are maximum.

The first preparation failed before any clique search because the saved
conflict bitsets use literal signature IDs, not positions within each
neighbor list. The failed source and diagnostic are preserved. The
corrected source explicitly transports between these index sets and
checks adjacency symmetry and every edge-variable mapping.

## Exact redundancy

The redundancy checker considers both orientations of every parent
equality, as well as the parent inequalities. It substitutes the 162
proved zero edge variables and normalizes positive integer factors.
All 128 retained candidates equal an existing parent equality
orientation after these substitutions. No nonnegative box residual is
needed.

An independent checker imports none of the scan or redundancy code. It
reconstructs each saved identity over all 15,200 coordinates, verifies
the original singleton zero premises, and checks 128 times 15,200
coefficients. The result is PASS in 2.8475 seconds.

The other 59 positive candidates were not retained or audited by this
redundancy check. No conclusion is claimed for them, for unsearched
cliques, or for the entire local stable-set polytope. The tiny retained
gaps are numerical violations of already imposed equalities.

## Reproducible records

- Source: `experiments/workspace/root_prism_free_f0_local_clique_scan.py`,
  SHA256 `6971e3631461929355eb565cbfa002bd14ea33dc64bcfccdfde659688fb03dd8`.
- Scan: `experiments/logs/root-prism-free/f0-local-clique-scan01.json`,
  SHA256 `f19b34f16e23f3cef0ec764935c5d43fb0fda638fb80e1c074b15ef3207cc9c5`.
- Redundancy proof:
  `experiments/logs/root-prism-free/f0-local-clique-scan01-redundancy.json`,
  SHA256 `909fcb07b6c161c0f13feaa49c3a9eeb2051ac2fddae90dbbdf4f2f50f508af5`.
- Independent checker:
  `experiments/workspace/root_prism_free_f0_local_clique_implication_check.py`,
  SHA256 `0d210a3eade44faf8b4419eca6349e23c79ad60884b14e5cf6ff60e29c023fbe`.
- Independent report:
  `experiments/logs/root-prism-free/f0-local-clique-scan01-independent-implication-check.json`.

The conditional F0 branch and the unrestricted Conway 99 problem remain
unresolved.
