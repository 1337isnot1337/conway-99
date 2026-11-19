# Exact lifts for three clique-absence conditions

The preparation constructs the 23 representative matrices from the frozen
five-root scope census. It verifies every selected zero row on the complete
integer coefficient support. It does not evaluate a count point or test
positive semidefiniteness.

The source is
`experiments/workspace/grid_free_order10_triple_clique_lifts.py`.
Its certificate and cold replay are
`experiments/logs/moments-and-counts/order10-triple-clique-lifts.json.gz` and
`experiments/logs/moments-and-counts/order10-triple-clique-lifts-replay.json`.
The separate scope proof is in
`research/grids-and-triangles/grid_free_order10_triple_clique_scope.md`.

## Matrix and normalization

Fix a labelled induced five-vertex root $H$. For each allowed neighborhood
mask $a$ of size at least three, let $X_a$ count the outside vertices with
that neighborhood in $H$. The common-neighbor bound gives $X_a\in\{0,1\}$.
Write $X=(1,(X_a)_a)^T$.

For three maximal cliques $C_1,C_2,C_3$ of the visible incompatibility
graph, put $Z_i=\sum_{a\in C_i}X_a$. Each $Z_i$ is binary. Therefore

\[
L=\sum_{e:H\hookrightarrow G}
  (1-Z_1)(1-Z_2)(1-Z_3)XX^T\succeq0.
\]

The sum is over labelled induced embeddings. The scope certificate expands
the product as

\[
L=M+\sum_{\substack{\varnothing\ne S\subseteq C_1\cup C_2\cup C_3\\
                         S\text{ compatible}}}
       (-1)^{|S|}C_S,
\qquad
C_S=\sum_e\left(\prod_{a\in S}X_a\right)XX^T.
\]

A compatible set has at most three members. When the selected product is
nonzero, every selected high class contains a unique vertex, and its mask
identifies its label. Thus $C_S$ is a sum of congruences of scalar moment
matrices rooted at $5+|S|$ vertices. The congruences use no factorial or
automorphism divisor.

For each selected set, the source checks every internal edge pattern.
Patterns that violate $A^2+A\leq2$ have an explicit offending vertex
pair in the certificate. Every remaining pattern contributes its child
matrix, including patterns that share the same unlabelled child type.
This retains their distinct labelled embeddings.

Four pairwise compatible selected triples have no admissible internal
edge pattern. Their registry entries remain present with zero contribution.
No feasible child is discarded because another child is isomorphic to it.

## Parent extraction and tensor support

The five-root parent matrix is an exact principal submatrix of the frozen
`induced-moments-5-2-512.pickle` cache. For each of its 21 roots, the source
selects the constant flag and every one-free-vertex high-mask flag.
It verifies their order against the complete scope domain.

The certificate stores the original flag positions, original lower-product
row indices, extracted coefficient rows, and their SHA-256 digest.
All 895 extracted entries use graph types of order at most seven. The
source cache has 6,535 columns because it is padded; the extracted entries
have nonzero indices below 308. Every binary diagonal agrees coefficientwise
with its first-row entry.

The six-, seven-, and eight-root scalar child caches have true product
support through orders eight, nine, and ten, respectively. The six-root
cache also has padded columns. The source checks nonzero support separately
from array width. Missing constant-only six- or seven-root blocks are
represented by their exact single root-count entry.

## Complete finite checks

The full scope ledger remains unchanged and is bound by its digest. It has
236 candidate triples of cliques after the stated quota-one reduction.
Explicit root automorphisms transport these candidates to 23 representatives.
This uses relabelings of the root, with no symmetry assumption on the
hypothetical graph.

| Root type | Representatives | Candidates covered | Quotient lower entries |
| --- | ---: | ---: | ---: |
| 17 | 6 | 165 | 271 |
| 18 | 10 | 56 | 451 |
| 19 | 3 | 4 | 100 |
| 22 | 3 | 10 | 135 |
| 26 | 1 | 1 | 1 |
| Total | 23 | 236 | 958 |

The largest quotient has order ten. All other five-root domains remain in
the certificate, including constant-only domains and roots with no surviving
candidate triple.

| Selected set size | Registry entries | Admissible child patterns |
| --- | ---: | ---: |
| One | 45 | 45 |
| Two | 83 | 93 |
| Three | 38 | 49 |
| Total | 166 | 187 |

The source classifies all 515 internal edge patterns. It rejects 328 by an
explicit visible cap. It checks 3,394 literal lift controls: each selected
child root alone, and that root with each allowed high-mask extra vertex.
For each control, direct old-class counts equal the sparse lifted vector.

All 171 representative union rows vanish coefficientwise. The replay checks
2,804 entries and 13,782 signed coefficient occurrences before deleting any
row. These are unrestricted identities, independent of the prism-zero
count face or a chosen count vector.

The preparation took 0.821 seconds and used 203,016 KiB peak RSS. A cold
replay took 1.635 seconds and used 202,888 KiB. The saved sparse lifts need
at most 12,677 lower-entry scalar products to form all conditional matrices.
The largest per-root registry, child matrices, and two working matrices
occupy 32,482 scalar cells. These are workload counts, not a point-scan result.

## Reproduction and scope

Run from the repository root with the existing frozen caches:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_triple_clique_lifts.py \
  --replay experiments/logs/moments-and-counts/order10-triple-clique-lifts.json.gz \
  --output /tmp/conway99-triple-clique-lifts-replay.json \
  --seconds 60
```

The output path must not already exist. Replay rebuilds the parent
extractions, every internal edge classification, every transport and sparse
lift, the literal controls, and every representative union-row identity.
It compares the complete regenerated certificate after removing timing and
memory fields.

The frozen source SHA-256 is
`d70999d19f1a49284a211edcbeb7d68e03025935523fed78c7a798ad6060ea66`.
The certificate SHA-256 is
`a6f5315d82c74fb3432fb357f247ef11c1aabbdae85df3ca22f0d86ed74db8b8`.
No new product tensors, numerical optimizer, dense reduction, or count-point
scan were used. This package prepares necessary matrices; it proves no
new exclusion of a count point or graph.
