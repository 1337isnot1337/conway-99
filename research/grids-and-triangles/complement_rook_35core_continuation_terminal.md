# Three more original-incidence exclusions

The fixed twenty-case continuation excluded matching cases **6, 7, and
14**. Each exclusion has direct and cold DRAT verification. All retained
inputs belong to the corresponding original incidence formula; no added
Gram-downdate clause is needed by these retained proofs.

The other seventeen cases returned UNKNOWN. There was no SAT incidence
witness, failed proof check, retry, or query outside the specified set.
The first local eight-set remains unresolved.

Together with the earlier checked cases, the excluded matching indices
are now

\[
\{0,1,2,3,6,7,8,9,10,14,21\}.
\]

The remaining indices are

\[
\{4,5,11,12,13,15,16,17,18,19,20,22,23,24,25,26,27\}.
\]

This is 11 exclusions among the 28 matchings of one local eight-set. It
does not exclude the whole local set, another local-set orbit, the
complementary-rook core, or a Conway99 graph.

## What was run

The preparation and model are described in
[`complement_rook_35core_continuation_preparation.md`](complement_rook_35core_continuation_preparation.md).
All twenty formulas preserved their complete frozen original clauses and
appended only their previously certified binary Gram conflicts. The
coordinator reviewed both new sources and independently ran the direct
domain/vector/byte audits for cases 4 and 5 before authorizing the batch.
Every prepared case had its own complete direct audit and exact bindings.

The runner made one fresh proof-enabled query per case, in index order.
Each requested solver limit was 60 seconds including bootstrap. Timer
interrupts were not hard process deadlines; observed return times are
reported below, including the 70.723-second return for case 5. Each direct
and cold proof check had a separate 60-second limit.

| Case | Result | Observed solver time including bootstrap |
| --- | --- | ---: |
| 4 | UNKNOWN | 60.333 s |
| 5 | UNKNOWN | 70.723 s |
| 6 | Checked UNSAT | 40.798 s |
| 7 | Checked UNSAT | 19.388 s |
| 11 | UNKNOWN | 63.218 s |
| 12 | UNKNOWN | 63.700 s |
| 13 | UNKNOWN | 60.157 s |
| 14 | Checked UNSAT | 19.672 s |
| 15 | UNKNOWN | 60.186 s |
| 16 | UNKNOWN | 60.025 s |
| 17 | UNKNOWN | 60.363 s |
| 18 | UNKNOWN | 60.050 s |
| 19 | UNKNOWN | 60.041 s |
| 20 | UNKNOWN | 60.066 s |
| 22 | UNKNOWN | 60.016 s |
| 23 | UNKNOWN | 60.278 s |
| 24 | UNKNOWN | 60.355 s |
| 25 | UNKNOWN | 60.038 s |
| 26 | UNKNOWN | 60.046 s |
| 27 | UNKNOWN | 60.119 s |

The complete run took 1,179.399 seconds, including checks and bookkeeping.
Every terminal outcome was saved before the next query. Earlier
ten-second UNKNOWN outcomes and the separate case-2/9/10 runs remain
unchanged.

The terminal record is
[`continuation01-run/terminal.json`](../../experiments/logs/grids-and-triangles/complement-rook-35core-first-local-continuation01-run/terminal.json),
SHA256 `eaa961f4efc79184c16ac6ec2e74695be333f98dda563a960530c083829edae7`.

## The three exact exclusions

Use the ordered local signature list
\(L=(0,1,9,10,18,20,26,27)\). Matching endpoints in the following table
are positions in that list.

| Case | Matching | Retained input clauses | Retained inputs outside original formula |
| --- | --- | ---: | ---: |
| 6 | \((0,4),(1,7),(2,5),(3,6)\) | 27,075 | 0 |
| 7 | \((0,4),(1,7),(2,6),(3,5)\) | 26,306 | 0 |
| 14 | \((0,5),(1,7),(2,6),(3,4)\) | 26,030 | 0 |

For each case, the cold replay reconstructed the entire attachment
domain and original formula. It checked the original CNF hash and
verified that every retained input occurs in that formula. The original
hashes are:

| Case | Original CNF SHA256 |
| --- | --- |
| 6 | `feb11347eb462a59caad68caec016ce9c1de4bd8a6cdf9bbc50e4d9ac3dd4cd0` |
| 7 | `7a305be5da7ff5cbe8a37866723d76866b5c4ac01abea3e8d2e9b164ee1bad3b` |
| 14 | `aa75765d105442e566e877115fe5bb46a6b5ce8e4a1c46b61bd8d5494504af2e` |

The appended conflicts may have affected solver propagation. Their
absence from the retained input sets means that the published proof
packages can be verified without the downdate inverses, pair census, or
overlay sources. The incidence model is still a necessary model of a
completion, so UNSAT excludes the indexed 35-core and its valid
relabelings only.

## Compressed original-only replay

The retained CNFs and proofs total 29,118,479 bytes uncompressed. Their
deterministic gzip copies total 5,253,818 bytes. Each archive binds both
its compressed SHA256 and the exact decompressed byte hash. The immutable
discovery records and raw files are unchanged.

The standalone source
[`complement_rook_35core_continuation_original_certificate.py`](../../experiments/workspace/complement_rook_35core_continuation_original_certificate.py)
imports only the original incidence builder. Its certificate is
[`continuation01-original-certificates/certificate.json`](../../experiments/logs/grids-and-triangles/complement-rook-35core-first-local-continuation01-original-certificates/certificate.json),
SHA256 `77ae26ff5484dbe71eb781521f803c7c2720075ffa171fd5d6c47462a127eabb`.

Replay checks each gzip/raw binding, reconstructs the original full
formula, checks retained-input inclusion in that original formula, and
runs DRAT. It does not query a SAT solver. Use a new output directory:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_continuation_original_certificate.py replay \
  --certificate experiments/logs/grids-and-triangles/complement-rook-35core-first-local-continuation01-original-certificates/certificate.json \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-first-local-continuation01-original-replay-new \
  --seconds 60
```

The terminal publication manifest includes all twenty result records,
the three direct and cold checks, the standalone archive certificate and
replays, the preparation and coordinator gates, and this note. It omits
the uncompressed proof copies while retaining their hashes and sizes.

The separate
[`case-4 LP diagnostic`](complement_rook_35core_case0004_lp.md)
found only numerical feasibility in two real relaxations. It adds no
exclusion to this list. No wider local-set sweep or further query is part
of this checkpoint.
