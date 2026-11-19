# Independent F0 triangle-Schur census replay

## Frozen scope

This replay uses the committed complete 480-signature domain, the two accepted full-core Schur kernels, the accepted direct kernel audit, and the committed 1,884 literal edge-zero premises. It checks the complete forward record with SHA256 7027feb1a77cb8131371bb10823ec7e5e8b6a33f5281a0b27881ee2f6b088155. It does not reconstruct the Schur inverses or rerun the prism-zero proof.

The source is experiments/workspace/root_prism_free_f0_triangle_schur_independent_cold.js, SHA256 cc15c3022af605c47c3ad6830066b26faa1ecb8adb07ad57d2b849f44a9f6db3. Its configuration is f0-triangle-schur-independent-cold-configuration01.json, SHA256 c363820f64f487ea7beb03f6b939fb8e855f0e6153dcba3b2e522784d275eae3. Every input has archive and uncompressed hashes, byte lengths and Git blob bindings in that configuration.

Only the codec is reused. The parent census and classifier sources were read to understand their scope and output schema; neither mathematical implementation is executed by this replay.

## Independent enumeration

For signature h_a and fixed-core vertex i, the replay reconstructs
q_a(i) = 2 - 1[i in h_a] - |N_core(i) intersect h_a|.
An unordered pair a,b is eligible precisely when their signatures intersect in at most one vertex and each signature lies in the positive-quota positions of the other. The source reconstructs all eligible pairs and compares all 480 saved neighbor arrays exactly. It also reconstructs the lexicographic eligible-edge order used by the literal-zero archive.

The triangle graph retains only eligible pairs with disjoint signatures. An actual graph triangle must have this property: a shared fixed-core neighbor of two adjacent exterior vertices would be a second common neighbor in addition to the third triangle vertex, contrary to lambda=1.

The independent enumeration uses c as the largest vertex, b as a lower neighbor of c, and a in the intersection of the lower-neighbor sets of b and c. Every emitted triple has a<b<c and all three disjoint eligible edges. Every unordered triangle has a unique largest and middle vertex, so it appears exactly once. This differs from the producer's smallest-vertex loop.

The lower-neighbor sets use 32-bit words. Complete four-vertex graph controls compare the enumerator with literal triple loops. A separate 65-vertex control exercises indices on both sides of the 31/32 and 63/64 word boundaries.

## Exact arithmetic and comparison

Each accepted kernel is divided by its positive common integer divisor. The source verifies exact divisibility, all positive diagonals, and the complete primitive coefficient hash against the direct audit. For a selected triangle, each off-diagonal entry is the primitive Z coefficient plus the primitive Y coefficient.

Every determinant in both families is evaluated by the six signed permutation products using BigInt. The controls compare this implementation against fraction-free Bareiss elimination with row swaps on all 15,625 symmetric matrices whose six independent entries lie in {-2,-1,0,1,2}; three additional matrices have entries up to 104 bits. Named controls include a singular positive semidefinite matrix and a matrix with positive proper minors but negative determinant.

All eligible-pair two-dimensional minors are computed once with BigInt. Every triangle checks its three proper minors and determinant. The independent nonpositive records are sorted into lexicographic a,b,c order and compared field by field with the forward records, including the determinant and all three two-dimensional minors. Counts, extrema, primitive hashes and negative eligible-pair lists must also agree. The output additionally hashes JSON.stringify(records) without a newline for each family.

## Literal-zero disposition

No known zero edge is removed before the census. After the independent negative list is accepted, the replay checks all 1,884 committed edge-zero rows against the reconstructed edge order, including their variable and native-row indices. Each negative triple receives an explicit list of any zero-edge premises among its three edges. The expected 3,840 versus 6,990 split is an equality check on this reconstructed ledger.

This disposition tests only the 1,884 literal edge zeros. Passing that test does not establish independence from other native rows, prism constraints or earlier cuts.

## Runtime and acceptance contract

Preparation is optimizer-free and does not reconstruct the full case edge domain or evaluate any case minor. The completed preparation took 8.449 seconds; its small controls took 0.094 seconds. The main census is a separate, still-unrun step requiring the root source gate.

One main call is permitted after that gate, with a cooperative 60-second budget, at most 50,000 retained nonpositive records and a 64 MiB report limit. Deadline or comparison failure returns an unaccepted partial record. A complete pass requires the whole enumeration, every forward comparison and the complete literal-zero disposition.

No local process, Pyroam, native optimizer, graph construction, component exclusion or novelty claim is part of this replay.
