# Shared indicators for the remaining required triangles

The accepted support closure processed all 132 spectral must-triangle edges. Forty-eight were already zero. The remaining 84 retained possible supports, and the closure derived no new edge zero. This preparation represents their remaining support obligations jointly.

## Necessary extension of every actual graph

For each distinct surviving support triple {a,b,c}, introduce one Boolean t_abc with

\[
t_{abc}=y_{ab}\,y_{ac}\,y_{bc}.
\]

The indicator is shared by every target edge for which the triple is a surviving support. For every live target e, impose

\[
\sum_{\{a,b,c\}\in \mathcal T_e}t_{abc}=y_e.
\]

If y_e=1, its accepted spectral premise requires exactly one exterior common neighbor. Every actual triangle belongs to the complete original eligible, pairwise-disjoint signature support domain. Supports omitted from the final list have an accepted triangle-cover or edge-zero reason. Exactly one surviving indicator is therefore one.

If y_e=0, every incident indicator is zero because its AND includes y_e itself. Two-edge paths through an exterior common neighbor remain allowed when the central target edge is absent. Replacing the three-edge AND by the AND of only the two side edges would incorrectly forbid such paths.

Existing edge endpoint activations imply all three selector activations when t_abc=1. No additional selector guard, variable identification or symmetry assumption is needed. Every actual completion extends uniquely to these indicators. This is a new necessary graph obligation represented in the relaxation; equivalence to the old relaxation is not claimed.

## Exact Boolean linear encoding

For each of the three edges d of a support triple, use

\[
0\le y_d-t_{abc}\le1.
\]

Also use

\[
-2\le t_{abc}-y_{ab}-y_{ac}-y_{bc}\le1.
\]

Together with Boolean domains these four rows are exactly the three-edge AND. The target equality has lower and upper bound zero for sum(t)-y_e.

The frozen base has 68,934 variables and 257,594 rows. New proposed indicator IDs start at 68,934. Every old variable and row remains in the proposal.

Let T be the number of distinct surviving support triples and I the number of target-to-triple incidences. The inventory will give both values exactly. Its proposed additions are:

- T Boolean variables;
- 4T AND rows and 84 target equalities;
- 10T AND terms and I+84 target-equality terms.

Sharing is recorded by complete origins: target edge ID, accepted support-table index and accepted support index. A triple can serve at most its three edges. Deduplication never drops an incidence.

## Artifact-only inventory scope

The new source reads the exact accepted 429,105-byte support ledger, its successful finalization, the original execution gate/configuration, and the accepted base-model receipt. It checks each saved final live-support index list against the saved support table and final zero set, then deduplicates sorted triples while checking consistent original edge IDs.

It does not reenumerate the 480-signature support domain, rerun the zero closure, build a native model, change the current model, or query a solver. The proposed one-call size inventory has a ten-second measured bound through serialization and a 16 MiB output bound. Its actual main remains unrun pending a separate gate and arithmetic slot.

## Actual tiny controls

The frozen source passed all 16 assignments of a three-edge AND and 128 assignments of a shared two-triangle/two-target fixture. Thirteen fixture assignments satisfy the complete logical obligations. The inactive-central-edge two-edge path is explicitly retained. A conflicting original edge identity for a shared triangle is rejected. The controls took three milliseconds and used no actual case inventory.

Source SHA-256: 5e7e2419d51fdc51e0a204a4df5ac422358189bc68f2e0d28b8e27db753f2d6a.
