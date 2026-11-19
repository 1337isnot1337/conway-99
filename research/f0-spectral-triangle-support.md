# Triangle support for edges with one required exterior common neighbor

This preparation checks a fixed list of 132 original eligible exterior edges. The accepted spectral-gap cold proves that presence of each listed edge forces exactly one exterior common neighbor. The check uses only the complete original 480-signature domain, 1,884 accepted literal edge zeros, 132 accepted spectral edge zeros, and 10,830 accepted triangle covers. The spectral zeros add 72 distinct initial zeros, giving 1,956 initial zero edges.

## Necessary support lemma

Let ab be a listed edge. If y_ab = 1, its required exterior common neighbor is a vertex c with y_ac = y_bc = 1. Every exterior vertex has one of the complete original signatures. Distinct exterior vertices cannot have the same weight-three signature, because that would give them three common fixed-core neighbors.

The first signatures of a, b and c are pairwise disjoint. If an adjacent pair in the triangle shared a fixed-core neighbor, that core neighbor and the third exterior vertex would give the adjacent pair two common neighbors, contradicting lambda = 1.

Consequently, the complete support set for ab consists of all other original signatures c such that:

1. The three first signatures are pairwise disjoint.
2. Both ac and bc belong to the original eligible edge domain.

No availability or symmetry restriction is added to this list. The checker reconstructs every original eligible edge and every saved neighbor list from the literal mixed quotas. It constructs support lists with bit masks and checks their completeness again by literal set unions.

A support is impossible if its triple is one of the accepted triangle covers, or either side edge is already certified zero. If every support is impossible, y_ab = 0. Failure to prove this emptiness gives no positive feasibility conclusion.

## Sequential closure and certificates

Targets are visited in increasing original edge-ID order. A zero is added only after every support has a complete checked reason. A later target in the same pass may use that new zero; it must cite the strictly earlier certificate index. Cyclic simultaneous elimination is not permitted.

Each support table row is:

    [third_selector, edge_ac, edge_bc, triangle_cover_record_index_or_minus_one]

Each new-zero certificate contains the target edge and endpoints, the index of its accepted must-triangle premise, the pass and certificate index, a reason for every support-table row, and the exact native row key:

    [0, 0, [[540 + target_edge_id, 1]]]

A triangle reason cites its record in the accepted 10,830-row ledger. A side-edge reason cites the edge ID and either an initial-zero authority index or a strictly earlier derived-zero certificate. Initial authorities retain their literal-overlay or spectral-cold record indices, including both origins when an edge occurs in both families. The checker verifies each complete certificate before committing it.

At most 132 targets can acquire a new zero. A pass with no changes ends the closure; 133 passes therefore suffice. The terminal check reconstructs each remaining target's complete support list and records every support whose triple has no accepted cover and whose side edges both remain outside the final zero set. This establishes a fixed point for this rule only.

## Accepted premise bindings

The configuration binds the archive and raw domain/overlay hashes, the complete accepted spectral cold and root acceptance, the original triangle ledger, and the independent triangle summary/root acceptance. The exact 10,830-record hash is compared with the accepted cold summary. Neither the diagnostic eight-pattern masks nor the unavailable three-path inventory is read. No other new row family is used.

The accepted n = 1 implication is an input theorem, not recomputed from floating point data. This check does not rerun a Schur determinant census or a spectral-pair census.

## Actual small controls

The frozen source's tiny controls completed in 0.238 seconds. They exhaustively checked 2,176 synthetic systems and 135,168 Boolean edge assignments, including disjoint and overlapping signatures and a sparse original edge graph. There were 20,105 admissible assignments and 17,368 checks that a derived zero is absent from every admissible assignment.

A mutually supporting three-edge cycle correctly produces no zero. A separate fixture checks an immediate sequential dependency chain. Five altered proofs are rejected: an omitted support, a future/self dependency index, a nonexistent triangle-cover witness, an altered native variable index, and an incomplete support table. No actual-case support has yet been enumerated.

## Proposed finite execution

One pure-V8 call, with a 30-second measured bound through report serialization and a 16 MiB report bound, is proposed. The source preserves a complete certificate prefix if an error or deadline interrupts the check. A partial or over-budget result has unaccepted terminal status and cannot establish a fixed point or completeness. Any later use of its complete certificates would require separate acceptance.

There is no optimizer, native model construction, case assumption, branch restriction, or automatic retry. The result does not assert a graph realization or exclusion of the whole component.

Source SHA-256: 030f5ebe67871ec7429ed3da223e8f9626cb7fd59aaaf2187f72cdd4bb98e091.
