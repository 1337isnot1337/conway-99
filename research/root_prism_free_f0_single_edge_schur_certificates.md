# Targeted certificates for the 252 supplied one-edge patterns

This package prepares an independent certificate checker for exactly the 252 records in the frozen diagnostic projection f392154f9e6d56e088163d32451fc4b27cba5164, SHA256 3fcd2dafb3d585ac09dc8e5639ce90cb5d5b58f642cabcd0087b36fde525c2b6. It does not resume the canceled complete eight-pattern replay.

The supplied pattern counts are 112 for bit 001, 90 for 010, and 50 for 100. These are counts within the provided list, not a completeness statement about any graph, pair or triple universe. The stored minor strings, PSD masks and compatible-pattern masks are not used for acceptance.

## Exact proof for each supplied record

The checker rebuilds the complete eligible-edge order from the accepted literal domain and checks every saved neighbor list. It checks the primitive coefficient hashes of the accepted full-core kernels. Each target's selector IDs, signature sites, original parent-triangle identity, three edge IDs and one-edge mask are then bound directly to those inputs.

For the actual one-edge matrix M, the checker first tries the fixed 49 primitive vectors in [-2,2]^3, keeping the sign with first nonzero component positive and ordering by L1 norm then lexicographically. If necessary it tries three positive-pivot cofactor vectors. For M=[[A,D,E],[D,B,F],[E,F,C]] and p=AB-D^2>0, the cofactor vector is (DF-BE,DE-AF,p), up to the tested coordinate permutation. It satisfies v^T M v=p det(M).

The acceptance gate does not rely on that identity or on any saved determinant. It contracts the actual matrix and proposed integer vector afresh with BigInt and requires v^T M v<0. A failed witness search is unaccepted, not evidence that the pattern is feasible.

The kernel is a necessary PSD matrix when the three selectors are present. Therefore a verified negative vector at the sole-edge-ab pattern proves
\[
 x_c+Y_{ab}-Y_{ac}-Y_{bc}\le1.
\]
Y_ab already activates a and b. The isolated selector x_c remains in the row. The complete guarded implication is proved in research/root_prism_free_f0_one_edge_schur_implications.md, SHA256 17adfc156dbabefbb223025abac10da935c95f2d5bd65af18f1744f122245606.

## Native row identity and known zeros

Every certificate retains the original selector IDs, edge IDs, mask, actual primitive matrix, integer vector and exact negative quadratic value. It also stores a complete sorted native row key:
\[
[-2,\ 1,\ [[\text{variable index},\text{coefficient}],\ldots]].
\]
Selector indices remain 0..479. The edge variable for original edge ID e is 540+e. The lower bound -2 is the requested conservative box bound. No variable alias or symmetry assumption is introduced.

The known 1,884 literal edge-zero rows are checked against the reconstructed edge order. Every certificate records whether its present edge is already zero and lists the exact premise when applicable. Such records are retained, not pruned. Other redundancy tests are outside this package.

A report-level row_keys array is sorted and deduplicated while retaining every certificate origin. The number of provided certificates and number of distinct row keys are reported separately.

## Frozen preparation and controls

Source:
experiments/workspace/root_prism_free_f0_single_edge_schur_certificates_v8.js
SHA256 db1d0956b261e2dd10b69f70f104bdbb8cd055ad49c039583fdec67aeda9bca3.

Configuration:
experiments/logs/root-prism-free/f0-single-edge-schur-certificates-configuration01.json
SHA256 a42abc4489fcc8738539ffa05a24eeb4eb0d1f8fd5d9ab7b31716ea52678f4d4.

The actual preparation passed in 10.426 seconds. It verified all input bytes and the supplied target metadata, then ran:

- 3,375 synthetic symmetric matrices;
- 6,975 cofactor identities checked against an independently expanded determinant;
- 2,050 negative-determinant cases with a positive pivot, all producing a checked negative vector;
- a 102-bit scaled matrix;
- 54 valid endpoint assignments across the three guarded row orientations;
- four deliberate certificate/row corruption rejections.

These are control counts, not case-pattern results. No supplied case matrix or negative vector has been evaluated.

The proposed main has a cooperative 60-second budget and 16 MiB report cap. It will preserve a failed or partial prefix without retry. Peer and root source gates are required before that single main call. No native model, optimizer, full pattern census, graph construction or ref mutation is part of this package.
