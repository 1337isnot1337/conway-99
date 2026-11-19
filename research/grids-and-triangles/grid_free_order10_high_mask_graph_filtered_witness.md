# The decorated-moment witness survives both principal projectors

The saved exact 200-mass witness remains feasible after the complete principal-projector filter. No new optimization is needed: every graph carrying positive mass in that witness survives.

The complete filter excludes 22,146 of the 157,711 saved graph decorations. It retains 135,565 full columns. Identical feature columns reduce those survivors to a 200 by 17,922 matrix with 757,947 nonzero entries. The 200 right sides are unchanged.

## Retained representatives and exact transfer

The transfer source first derives the surviving feature identifiers from the complete full-column map. It then chooses the first retained full graph for each feature identifier. It does not assume that an old representative survives merely because some graph with that feature vector survives.

All 200 positive masses of the earlier witness have surviving feature identifiers. They are transferred to the new column numbering and checked against every equation over exact rational arithmetic. Their common denominator remains

\[
1,841,072,799,597,249,500,967.
\]

Each positive mass has a concrete retained graph representative. Uniform averaging over the 720 root relabelings again gives all 73,263 individual rooted induced-pattern moments. No host-graph automorphism is assumed.

The complete retained-to-filtered inverse map, multiplicities, representatives, and restricted coefficient matrix are saved. The transfer binds the complete exclusion certificate and its cold replay.

## Independent positive checks on the support

The domain filter certifies exclusions using integer negative vectors. The transferred witness also has a separate positive check on all 200 graphs that carry mass.

For each support graph with literal adjacency matrix (B), the transfer constructs

\[
P=27I-9B+J,\qquad Q=44I+11B-2J.
\]

It saves every coefficient of (\det(tI+P)) and (\det(tI+Q)), computed over the integers. All coefficients are nonnegative and the leading coefficient is one. Each matrix is real symmetric. A negative eigenvalue would give a positive root of its displayed polynomial, which a monic polynomial with nonnegative coefficients cannot have. Thus both principal matrices are positive semidefinite on every support graph.

These 400 full-matrix characteristic-polynomial checks use a different criterion from the filter's fraction-free Schur elimination. They do not repeat the complete domain scan.

## Outcome and limits

The transfer and positive checks complete in 1.831 seconds at 124,796 KiB peak resident memory. A separate cold invocation reconstructs the restricted maps, all rational equations, the representative graphs, and all 400 characteristic polynomials. Neither invocation calls an optimizer.

The current count point therefore passes the complete stated empty-six-root decorated moment model even when each allowed local graph must satisfy both principal-projector conditions. This remains a real finite measure. It does not provide an integer embedding distribution, a compatible family over all root types, or a 99-vertex graph.

The [exterior-Gram identity](projector_exterior_gram_identity.md) shows that the centered exterior-incidence Gram PSD condition is already equivalent to these two principal conditions. It would not strengthen this filtered model.

## Files

- `experiments/workspace/grid_free_order10_high_mask_graph_filtered_witness.py`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-filtered-witness01.json`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-filtered-witness01-arrays.npz`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-filtered-witness01-replay.json`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-projectors-finish-independent-review.json`

The original unfiltered query, witness, and manifests remain unchanged.
