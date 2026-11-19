# Independent literal replay of the triangle support tables

The completed forward support check and indicator inventory are not sufficient by themselves for model use. This separate checker reconstructs the literal support universe before comparing the saved ledger. Its source author also wrote the forward check; a separate complete peer review and root execution gate remain required.

## Accepted premises

The checker binds the original 480-signature domain, the 1,884 literal edge-zero certificates, the accepted spectral cold and root acceptance, and the 10,830 accepted triangle-cover records with their independent cold/root acceptance. It also binds the exact forward ledger, successful finalization, execution gate and configuration.

The spectral cold supplies 132 must-triangle edges and 132 edge-zero deductions. Sixty spectral zeros overlap the literal zeros, so the initial union has 1,956 edges. Forty-eight must-triangle targets are already zero; 84 remain. The old forward result reports no new zero. These quantities are checked from the original premise lists, not taken from its summary.

The checker does not import or call the forward support source, re-run either Schur census, use the unverified eight-pattern diagnostic, or read a three-path inventory.

## Different literal reconstruction

Signatures and core neighbor rows are represented as sets. Every mixed quota is computed by literal intersection counts:

\[
q_{a,i}=2-\mathbf1_{\{i\in h_a\}}-|N_{C_0}(i)\cap h_a|.
\]

Candidate pairs are visited with the larger endpoint outermost, and both endpoints descend. A pair is eligible exactly when its first-signature intersection has size at most one and each signature lies on positive quotas of the other. The complete edge list is then sorted to recover the original native edge IDs. All 480 saved neighbor lists and the complete edge-order hash must agree.

Supports are enumerated with the third vertex outermost, in descending order. For a third vertex v, form its eligible neighbors whose first signatures are disjoint from h_v. Visit each live target ab anchored at its smaller endpoint a. It contributes a support exactly when both a and b are in this set and h_a and h_b are disjoint.

Every valid structural support appears: its two side edges put a and b in the third vertex's eligible-neighbor set, and pairwise signature disjointness keeps both there. It appears once because the target is anchored only at its smaller endpoint.

This differs from the forward constructor, which visited each target and scanned all third signatures using signature bit masks.

## Complete comparisons and conclusion

The new checker reconstructs every initial zero authority, including both origins for overlapping literal/spectral zeros, every target's spectral premise index, and all already-zero target references.

For every live target it compares every structural record

    [third_selector, edge_ac, edge_bc, accepted_cover_index_or_minus_one]

with the saved table. It independently removes records whose accepted triangle cover is present or whose side edge belongs to the reconstructed zero set, and compares the complete surviving-index list. It requires all 84 remaining targets to have at least one surviving support.

A successful main must check all 1,956 initial zeros, 132 targets, 48 already-zero targets, 6,540 structural support records and 5,364 surviving records. It must also confirm the empty new-zero certificate list and unchanged final zero set. This proves the recorded one-pass fixed point for the stated rule. It proves neither joint realizability of surviving supports nor a graph construction.

The report saves a hash of the complete normalized independent tables and live-index lists. The original full ledger remains the explicit table artifact; no reduced sample is substituted.

## Actual tiny controls and proposed main

The new source's controls passed 6,144 small graph/signature/cover/zero systems. The third-vertex enumeration was compared with a direct scalar triple oracle, checking 6,144 structural records and 1,880 surviving records. Three separate quota controls check disjoint eligibility, rejection from two shared sites, and rejection from a zero mixed quota.

Five changed ledgers are rejected: an omitted support, an altered side-edge ID, an altered cover index, an omitted live-support index and an omitted target table. The controls took 201 milliseconds. No actual-case replay has run.

The proposed single pure-V8 main has a 30-second bound through input validation and report serialization, and a 16 MiB report bound. Partial, failed or over-budget results are unaccepted. There is no native model build, optimizer or automatic retry.

Source SHA-256: 456da9b26b97e71b574003230682dc0cff099ed10c6f394b8d0bef602d59d7c1.
