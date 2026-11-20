# Independent literal verification of triangle-capacity rows

The separate literal verifier accepted all 3,324 proposed capacity rows. Its complete input binding, reconstruction, report serialization and hash took 10.679 seconds under the declared 30-second bound. Its outer owner took 10.709 seconds under 45 seconds. The [root acceptance](../experiments/logs/root-prism-free/f0-recorded-triangle-capacity-literal-root-acceptance01.json) binds the exact source, configuration, peer review, original proposal, actual report, finalization and owner.

The source was written independently of the proposal extractor and received complete source/configuration review before one execution. It reconstructs all 480 saved neighbor lists and the full 68,394-edge original order from previously accepted metadata. It checks all 5,364 accepted triangles, the complete 6,300 edge-incidence records, all 84 target-equality origins and 3,312 existing singleton AND origins. It then derives and compares every 2,904 side row, every 420 local row and all 60 empty local dispositions.

The side rows contribute 10,320 terms; local rows contribute 16,512. No new variables are proposed. Root independently recomputes all seven full row/origin/table digests from the preserved proposal and matches the separate verifier. The combined ordered row-key SHA-256 is `9e7d7387a389e31232799697b7228976dfb4ae22980bf0a6ecc3885456e93b43`.

The [capacity proof](root_prism_free_f0_recorded_triangle_capacities.md) proves at most one recorded triangle per edge from lambda=1. The local bound follows from these capacities and the original mixed/degree equations by an explicit integer rounding step. It is not asserted to be a continuous implication of the unrounded inequality.

## The original timing failure remains recorded

The original extractor finished its table in 8.374 seconds, but complete serialization/hash took 12.196 seconds under a 10-second declaration; its outer receipt took 17.209 seconds. Its finalization and owner remain UNACCEPTED. The complete original bytes, source/configuration and timing records are retained. The producer was not rerun and its budget was not waived.

The new acceptance concerns this independently derived row family. It does not turn the old execution into an accepted run. The separate verifier does not rerun or accept the proposal's sufficient-redundancy audit; every one of the 3,324 rows is retained regardless of that audit's classifications.

## Native use remains a separate step

The accepted parent has 80,730 variables and 297,470 rows. These two capacity families would produce 300,794 rows, with the complete original raw bytes preserved as a prefix. A separately proved 84-term target-total row may follow as a third family; that addition has its own certificate and acceptance. A future producer and a separate checker must compare every complete appended protobuf message and all original messages before a new model can be accepted or queried.

No native model, optimizer call, graph, component exclusion or unrestricted contradiction was produced by this literal verification.
