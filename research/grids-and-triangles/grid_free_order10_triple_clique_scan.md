# Five-root triple-clique scan at the 48-cut count point

The single authorized scan completed all 23 representative matrices. These
representatives cover the 236 candidate triples from the frozen scope
certificate. It found no exact negative direction and no unconfirmed
numerical negative. This is a discovery-scan result, not an exact certificate
of positive semidefiniteness.

The unchanged input is
`experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json`,
SHA-256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
That file is an exact finite count witness. It is not a graph.

## Matrices and coverage

The source uses the point-independent domains and exact conditional lifts
described in `grid_free_order10_triple_clique_scope.md` and
`grid_free_order10_triple_clique_lifts.md`. For each representative, it forms

\[
L=\sum_{e:H\hookrightarrow G}
  (1-Z_{C_1})(1-Z_{C_2})(1-Z_{C_3})XX^T,
\]

where $H$ has five vertices, $X$ contains the constant and every allowed
high-mask one-free-vertex class, and $Z_C=\sum_{a\in C}X_a$.

The parent entries come from the saved principal extraction. Conditional
entries come from the existing complete six-, seven-, and eight-root scalar
tensors. Every count contraction uses Python integers. The scan retains
all 21 root domains and every flag. It removes selected union rows only
after checking their entries are exactly zero.

The scan checks all 171 representative union rows and all 958 quotient
lower entries. The largest quotient has order ten. The four selected
triples with no admissible internal edge pattern remain explicit zero
contributions.

The scope certificate gives explicit root relabelings from all 236
candidates to the 23 representatives. These relabelings act on labelled
root embeddings and do not assume a graph automorphism.

The other 155 triples from the maximal-clique census have a quota-one
reduction. They were not scanned directly. Their redundancy depends on
the corresponding child localizers and exact count identities. The present
result does not certify those child matrices or all 391 census matrices
as positive semidefinite at this point.

## Recorded outcome

| Check | Result |
| --- | ---: |
| Direct representatives completed | 23 |
| Candidates covered by root relabeling | 236 |
| Candidate roots completed | 5 |
| Selected union rows checked exactly zero | 171 |
| Exact negative directions | 0 |
| Unconfirmed numerical negatives | 0 |
| Minimum recorded normalized numerical eigenvalue | 0.10615809196457553 |
| Scan time | 0.059 seconds |
| Total runtime, including input checks | 0.897 seconds |
| Peak RSS | 203,340 KiB |

The run used one thread and a 60-second scan limit. It completed without
timeout or error. A numerical eigensystem only proposes negative directions;
the acceptance path requires an integer vector and exact negative quadratic
and induced-count forms. No such direction was proposed here.

No product tensor was generated. No dense count reduction or optimizer was
used. The input witness and all prior sources remain unchanged.

## Preparation failure retained

The first preparation stopped before any matrix contraction. Its equality
check compared two polynomial-term records with different bookkeeping
fields. The original scope record also stores an internal-edge upper bound.
The corrected source compares the masks and coefficients on both sides.

The earlier source and failure record are preserved as
`grid_free_order10_triple_clique_scan_preparation_v1.py` and
`order10-triple-clique-scan01-preparation-failure.json`.
This was a preparation failure, not a failed point scan.

## Frozen files and reproduction

The driver is
`experiments/workspace/grid_free_order10_triple_clique_scan.py`,
SHA-256
`180a6699e7b8a1e174737ea327b030f181369e981d75b337d766b995a7fe79bc`.

The reviewed preparation is
`experiments/logs/moments-and-counts/order10-triple-clique-scan02-preparation.json`,
SHA-256
`042196dc933deb828842af49e1cdc764d494a2aabf27ea4f8631e3b037b3c663`.

The terminal result is
`experiments/logs/moments-and-counts/order10-triple-clique-scan02.json`,
SHA-256
`fdf28db02e1272a75f7b9be62af7eb37ff69783fc941a8e7d412ed8594e72955`.

The coordinator review is
`experiments/logs/moments-and-counts/order10-triple-clique-coordinator-review.json`,
SHA-256
`bc7d417d803c71fb184bfc3e26ac0a7ed383681462db824be597c69d54e0a6b2`.

Run from the repository root with the frozen caches and a new output path:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_triple_clique_scan.py \
  --preparation experiments/logs/moments-and-counts/order10-triple-clique-scan02-preparation.json \
  --output /tmp/conway99-triple-clique-point-scan.json \
  --seconds 60
```

The timing and numerical eigenvalues are informational. Any future exact
negative form requires a separate literal supported-product reconstruction
before use in an optimizer.
