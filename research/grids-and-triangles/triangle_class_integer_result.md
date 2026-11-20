# Exact integer triangle-count result

The frozen integer count point passes every prepared coordinate and signed-pair integer test for the 1,296 triangle classes over all 21 five-vertex roots.

The query checks all 127,296 vectors and 366,356 finite-interval shifts exactly. The interval bounds and exact minimizing-shift formula cover every integer shift for each vector. There are 14,234 zero evaluations, 352,122 positive evaluations and no negative evaluations. All 26,289 distinct primitive candidate forms also evaluate nonnegatively.

The query finished in 3.056 seconds. A separate cold replay reconstructed the scalar matrices and all tests in 4.572 seconds. Neither run used floating-point arithmetic, an eigensystem or an optimizer.

## Scope

For each labelled root embedding the tested integer variable is one triangle-class count, the sum of two distinct counts, or their difference. The complete preparation and its exact redundancy certificates are documented in [triangle_class_integer_preparation.md](triangle_class_integer_preparation.md).

All roots and classes remain in the ledger. Eleven of the vector functions are constant; their first and second moments are checked directly. The other functions have an exact finite shift interval containing a minimum over all integer shifts. Every first-moment bound and all first- and second-moment partition identities also pass at this point.

The result checks a finite support and coefficient family. It does not establish a joint integer distribution of all triangle-class counts, test arbitrary integer coefficient vectors, or construct a graph.

All underlying triangle products have at most nine vertices. Consequently these inequalities depend only on the original 58 count coordinates. No new order-ten core coordinates enter this completed family.

## Frozen certificate

The immutable count point has SHA256 0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.

The source is experiments/workspace/triangle_class_integer_query.py, SHA256 9e80735b2984049adcb0f851e246e481ed433de9e576d3803b108dbc8c4c0f38. Its interval controls cover 2,698 synthetic cases, including negative endpoints, zero mass and a negative inconsistent moment example.

The complete result is archived at experiments/logs/moments-and-counts/order10-triangle-class-integer-query01.json.gz. Its archive SHA256 is 9c940934bfbad7f3930a58b8e9658fd620eb020e437c130b64124b255d7b1f03. Decompression gives 11,600,516 bytes with SHA256 f9aa39b03fea725a6bc5d09fa2f7e196e51a6152bd4a6271554defebec321d0e. The result records every vector's minimizing shift, exact minimum and sign counts.

The cold replay is experiments/logs/moments-and-counts/order10-triangle-class-integer-query01-replay.json, SHA256 e435f9b601106a911edea63793787b1e806cb4fc655bfbb9c41911098348efa4.

To repeat the unchanged replay, decompress the result archive to its .json path, then run the source in replay mode with the frozen preparation directory, scalar model, count point, decompressed result and a new output path. The replay reconstructs the matrix entries and evaluations from frozen tensors. It does not repeat the product enumeration or the point-independent classification.

