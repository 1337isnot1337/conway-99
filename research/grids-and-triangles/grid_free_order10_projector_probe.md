# Four-root controls for the order-ten projector construction

The bounded control completed all sixteen specified projector blocks at
the integer witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
It found no exact negative direction and no unconfirmed numerical
negative direction. This is a four-root probe, not a complete scan or a
PSD certificate for the point.

## Scope and construction checks

| Root type | Selection reason | Outside classes | Unlabelled root count |
| --- | --- | ---: | ---: |
| 1223 | Smallest domain; rook graph with one vertex removed | 20 | 0 |
| 1200 | Smallest domain with positive count at this point | 22 | 243 |
| 308 | Largest domain; empty eight-vertex root | 256 | 1,707,772,382 |
| 610 | Largest inverse denominator | 176 | 635,747,720 |

Each root produces both spectral and per-embedding Schur blocks for
both Q projectors. All masks are retained in every saved tensor,
including the zero-count root and masks of degrees zero, one and two.
The sixteen blocks contain 203,612 lower entries and 208,673 nonzero
tensor coefficients. The CSR arrays occupy 3,318,588 bytes.

The producer obtains two-vertex extensions through the frozen
catalogue child maps and explicitly checked prefix transports. A
separate oracle constructs the full labelled adjacency prescription
directly, checks every common-neighbor cap, and identifies the graph
by its canonical certificate. It uses no child map or prefix transport.
The oracle agrees on 6,566 selected coefficient entries, including
every entry of the small blocks and diagonals plus sampled entries of
the large blocks.

The direct nine-vertex rook control enumerates all 72 labelled
embeddings of its eight-vertex root. It forms the full projector Gram
matrix from the actual vertex vectors and their outside classes. All
four matrices agree exactly with the count-tensor contraction. These
checks include the labelled count normalization and the Schur scale.

## Exact contraction and the limited numerical conclusion

Every tensor contraction uses Python integer multiplication and sums.
Every one of the sixteen resulting matrices satisfies all nine
universal kernel equations exactly. The zero-mask and singleton-mask
pivot matrix has determinant one. Only then does the probe delete the
nine pivot coordinates for separation.

The negative-direction routine removes only rows proved identically
zero at the integer point. It proposes other directions numerically
and would accept them only after exact quadratic evaluation. The
driver also contains an independent literal reconstruction of every
supported entry of an accepted direction. No separator occurred here,
so this latter branch was not exercised by the run.

The zero-count root contributes zero matrices. For the other roots,
the numerical quotient eigenvalues were positive after exactly zero
rows were removed. This observation does not certify exact PSD of
those matrices. No cut was added to any count model.

## Runtime and a bounded continuation estimate

The complete scoped run took 5.552 seconds, with peak RSS 206,188 KiB.
Product construction took 1.039 seconds; exact contraction, kernel
checks and quotient scans took 0.615 seconds. The remaining time
includes loading, the literal controls, the direct rook control, and
serialization. The complete selected cache compresses to 462,163 bytes.

The complete domains have 13,735,344 lower entries, about 67.46 times
the selected workload. Scaling the measured construction and scan
times gives roughly 110 to 130 seconds before any supported-entry
proof work. This is a runtime estimate, not a completion guarantee.

The domain preparation bounds the full construction by 26,586,624
coefficient placements. At the observed layout of eight-byte values
and four-byte indices, the CSR-array upper bound is 373,995,520 bytes.
Extrapolating the observed sparsity instead gives roughly 224 MB.
Catalogue objects, Python overhead and serialization require
additional memory. No dense reduced count matrix is needed.

A separate incremental run with a fixed 180-second budget is a
plausible next stage. It must preserve complete per-root domains and
mark partial root coverage explicitly if the budget expires. Any
resulting separator needs its own supported-entry reconstruction
before use in an optimizer. No full-family run is part of this package.

## Frozen artifacts

Producer:
`experiments/workspace/grid_free_order10_projector_probe.py`

Producer SHA256:
`0af37fafb7db4e68963fa602800e7aa3256b9cf56ef8ffd1ce4b06a48da16e7a`

Literal oracle:
`experiments/workspace/grid_free_order10_projector_literal.py`

Literal-oracle SHA256:
`ca302f44d051b4372e64b7c3a6353174c3b3880cff20b9c7055ad8343162d2b1`

Result:
`experiments/logs/moments-and-counts/order10-eight-root-projector-probe.json`

Result SHA256:
`3f896063f17be60d450df50095fd59e2244e554b11b7ac7182f4a3170098c075`

The matching manifest binds the preparation, cache, logs, note and
sources. To repeat the scoped run without replacing the saved result:

```sh
python experiments/workspace/grid_free_order10_projector_probe.py \
  --preparation experiments/logs/moments-and-counts/order10-eight-root-projector-probe-preparation.json \
  --output /tmp/order10-projector-probe-replay.json \
  --cache /tmp/order10-projector-probe-replay.pickle.gz \
  --seconds 60
```
