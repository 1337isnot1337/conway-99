# A binary projection of one exterior neighborhood

Fix the complementary-rook 27-core

\[
B=\begin{pmatrix}R&I&I\\ I&R&I\\ I&I&J-I-R\end{pmatrix}.
\]

Every possible completion uses 72 distinct columns from its complete
252-signature domain. This model keeps all 252 binary incidence selectors
and the full Gram identity

\[
XX^T=12I+2J-B^2-B.
\]

It fixes one source signature as selected. The source representatives are
`(0,4,1)`, `(0,4,2)`, and `(0,4,8)`, the three orbits of sizes 72, 144,
and 36 under simultaneous rook relabelings and interchange of the first
two grids. A representative labels an occurrence of that signature type;
the model imposes no graph automorphism and fixes no incidence design.

## The source row

Write `h` for the source signature and
`d = 2*1 - (B+I)h` for its mixed demands. Each eligible other signature
`w` has an independent neighbor bit `y_w`, with `y_w <= z_w`, where `z_w`
is its incidence selector. The model imposes

\[
\sum_{w:i\in h_w}y_w=d_i\quad(0\leq i<27),
\qquad \sum_w y_w=11.
\]

Eligibility requires at most one common core neighbor and positive mixed
demand at every core point consumed by the proposed edge, in both
directions. Every pair of chosen neighbors already has the source as a
common neighbor. Therefore two chosen neighbors cannot also share two
core vertices. The corresponding pairs receive binary packing clauses.

## The necessary matching

The three core neighbors of the source are pairwise nonadjacent. Each
has mixed demand one at the source, so exactly three chosen exterior
neighbors share one source core neighbor. Each of these three exterior
vertices is already paired with that core neighbor in the source's
neighborhood.

The other eight chosen exterior neighbors are disjoint from the source
signature. Since a degree-14 neighborhood is seven disjoint edges, these
eight vertices must admit a perfect matching. A proposed matched pair
must have disjoint core signatures: its endpoints already have the
source as their unique common neighbor. Its edge must also meet the
ordinary eligibility test.

For each eligible pair, introduce a matching bit `m_vw`. At every candidate
with source overlap zero, impose

\[
\sum_{u:\{u,w\}\text{ eligible matching pair}}m_{uw}=y_w.
\]

The encoding uses `m_uw -> y_w`, `y_w -> OR(m_uw)`, and an at-most-one
constraint on incident matching bits. It therefore selects one partner
exactly when the candidate is a chosen source neighbor.

## Domains and controls

| Source triple | Neighbor bits | Overlap-zero candidates | Overlap-one candidates | Matching bits | Packing clauses | CNF variables | CNF clauses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(0,4,1)` | 163 | 110 | 53 | 2,226 | 737 | 48,811 | 102,699 |
| `(0,4,2)` | 166 | 118 | 48 | 2,583 | 735 | 50,083 | 105,942 |
| `(0,4,8)` | 173 | 122 | 51 | 2,712 | 763 | 50,769 | 107,597 |

The matching encoder was checked against direct recursive matching
enumeration for every graph and selected vertex set through order four:
1,099 cases, including 318 positive cases. All nine neighborhoods of the
nine-vertex rook graph supply additional matching controls.

A returned SAT point is checked on its full selected incidence matrix,
all source mixed demands, and its four matching edges. The checker then
constructs the 99-point partial graph consisting of the core, all fixed
incidences, the complete source row, and the four matching edges. It
checks all 4,851 partial common-neighbor caps and verifies that the
source neighborhood is exactly seven disjoint edges. Such a witness
leaves all other exterior rows incomplete.

The implementation is
`experiments/workspace/complement_rook_row_projection.py`.

## Checked outcomes

All three source types survive this projection. Each proof-enabled solver
run returned SAT within its 30-second budget, and every saved partial
witness passed the exact checks above.

| Source triple | SAT return time, seconds | Incidence parameter a |
| --- | ---: | ---: |
| `(0,4,1)` | 0.365 | 17 |
| `(0,4,2)` | 2.079 | 14 |
| `(0,4,8)` | 0.189 | 13 |

The times include CNF parsing and solver bootstrap. These values of `a`
describe three selected incidence designs with a completed source row.
Their other exterior rows remain unspecified. The results give no new
exclusion of the complementary-rook boundary.

A separate verifier imports no SAT construction helper. It rebuilds the
core and complete signature list, reconstructs each saved 99-point partial
matrix, and checks its degrees, all pair caps, and the source matching.
Run it with:

```sh
.venv/bin/python experiments/workspace/complement_rook_row_projection_replay.py \
  --output experiments/logs/grids-and-triangles/complement-rook-row-projection-independent-replay.json
```

The three manifests, results, build logs, and solve logs use the prefix
`experiments/logs/grids-and-triangles/complement-rook-row-projection-i`,
where `i` is zero, one, or two. The independent encoding/domain audit is
`complement-rook-row-projection-independent-audit.json` in that directory.
