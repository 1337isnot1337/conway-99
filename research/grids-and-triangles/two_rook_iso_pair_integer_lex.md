# Duplicate-label ordering in the two-grid completion search

A separate continuation of the
[two-grid integer run](two_rook_iso_pair_integer.md) added only a
justified ordering of the 36 duplicate-signature pairs. It inherited
the first run's 1,939 necessary cap clauses. The continuation returned
`UNKNOWN`, with no new binary point and no new clause.

## The ordering and why it is allowed

The nine diagonal vertices are fixed tips, numbered `0,...,8`.
For a duplicate-signature pair `a,b`, compare its two adjacency
vectors to these nine vertices. Either ordering of `a,b` gives the
same fixed core incidence, so choose labels with the first vector
lexicographically at least the second.

The two vectors have disjoint supports. Otherwise the duplicate
vertices would share a tip in addition to their two core neighbors.
With this packing condition, the order has the simple Boolean form

\[
\neg C_{b,z_j}\ \lor\ \bigvee_{k<j}C_{a,z_k}
\quad(j=0,\ldots,8).
\]

Ineligible coordinates are zero for both vertices and can be
omitted. There are seven eligible coordinates per duplicate pair,
giving 252 clauses over all 36 pairs.

Every pair can be relabeled independently. Swapping one pair does
not change any other pair's adjacency vector to the fixed tips.
Therefore every possible completed graph has a labeling satisfying
all 36 orders. This is not an assumption that the graph has an
automorphism. No order is imposed on full 81-coordinate neighborhood
rows.

An exhaustive control checks all 29,524 pairs of disjoint binary
vectors of lengths zero through nine. A separate reviewer checked
the argument and reran that control. Starting phases came from the
last partial point after these relabelings; phase preferences add
no constraints.

## Frozen formula and bounded outcome

The initial formula consists of the original 297,684 clauses, the
252 ordering clauses, and the 1,939 verified cap clauses. It has
299,875 clauses and 147,060 variables including cardinality
auxiliaries. Its SHA-256 is

```text
afbc39da672337f729d09492bb3a2ff236a7c95f65c38e21b7e3f82dc459e717
```

The run requested 180 seconds and at most 100 refinement rounds.
It returned `UNKNOWN` without finding an additional binary point.
The reported elapsed time was 192.11 seconds. Since no new clause
was added, the initial and final CNF hashes are identical.

The separately proved tip-neighborhood Hall clauses were not used
in this model version. No infeasibility or graph-existence claim
follows from the timeout.

## Replay

The continuation source is
`experiments/workspace/two_rook_iso_pair_integer_lex.py`. Its output is
`experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-lex.json`,
with the execution log beside it. The record binds its source and
seed transcript by SHA-256 and records both CNF hashes.

```bash
python experiments/workspace/two_rook_iso_pair_integer_lex_replay.py \
  experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-lex.json
```

This uses only the standard library. It verifies the source and
seed hashes, the tip-vector orders for any new points, and the
complete inherited point/cap-clause transcript.
