# Independent triangle-Schur census: accepted terminal

The single independent replay passed in 19.421 seconds under the frozen 60-second budget. It reconstructed 68,394 eligible pairs, including 49,320 disjoint-signature edges, and enumerated all 1,179,048 pairwise-disjoint eligible triangles.

| Family | Negative eligible-pair minor | Negative triangle determinant | Zero triangle determinant | Positive triangle determinant | Triangle with a negative proper minor |
|---|---:|---:|---:|---:|---:|
| plus | 12 | 10,830 | 0 | 1,168,218 | 0 |
| minus | 0 | 0 | 0 | 1,179,048 | 0 |

Every saved negative record, determinant and proper minor agrees exactly with the forward census. The independent plus-record list, sorted by a,b,c and serialized with JSON.stringify without a newline, has SHA256 60dd838a427e23b5d3c773e7eb8ecb9852e77a88bd0d9e1ac647e51be7965ff8.

The replay used a different triangle enumeration and BigInt six-permutation expansion in both families. It reconstructed every eligible-neighbor row before enumerating triangles. The full-core Schur kernels and their direct inverse audit remain accepted premises; the replay does not reconstruct their inverses.

No old zero edge was removed before the determinant census. The subsequent complete disposition against the 1,884 committed literal zero edges gives 3,840 negative triples containing such an edge and 6,990 without one. The report contains all 10,830 disposition records and the specific zero-edge references when present. An empty zero_premises array denotes no such edge. This tests no other prism, path, native-row or earlier-cut redundancy.

The full terminal is experiments/logs/root-prism-free/f0-triangle-schur-independent-cold01.json, SHA256 5436baf4d22a0d6b929162176029a1defa13ecb4446f2436655b22aa1b2de9c1, Git blob 58d2facfff6e29f2d8d5b2e8232f072758a3cc1c. It binds the exact forward census, committed inputs, independent source and configuration. A compact summary gives the counts, extrema and record hashes without repeating the ledgers.

There was one preparation and one main replay. No local runtime, Pyroam, native optimizer, graph construction or component-exclusion claim was used. The preparation note remains unchanged as the record written before the main gate.
