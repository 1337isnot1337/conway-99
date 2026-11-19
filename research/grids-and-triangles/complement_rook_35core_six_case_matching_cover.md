# Four conditional matching restrictions from six excluded cores

The six checked exclusions at indices \(0,1,2,3,8,21\) give three
single-edge restrictions and one two-edge restriction on the first local
eight-set. Their 144 explicit core relabelings give 576 distinct clauses:
432 have seven literals and 144 have six. None subsumes another as a
Boolean clause.

These clauses are necessary for an actual graph containing the normalized
complementary-rook core. This package does not claim they are entailed by
the older weak joint incidence/edge CNF, does not assume a graph
automorphism, and does not exclude the whole local eight-set. The earlier
four-case edge-cover certificate remains unchanged.

## Complete matching cover

The original signature indices of the local eight-set are

\[
L=(0,1,9,10,18,20,26,27).
\]

If all eight occur, they are the eight exterior neighbors of \(R_0\).
Its six known neighbors in the 27-core already form three disjoint
edges. Since every neighborhood is seven disjoint edges, the local eight
must form a perfect matching.

The source enumerates all 105 perfect matchings on these eight vertices
and retains exactly the 28 whose edges belong to the complete eligible
edge domain. This set equals the indexed first-local matching list.
The following covers are exhaustive within that list:

| Pattern in local positions | Edges in original signature indices | All matching cases containing it |
|---|---|---|
| \((0,2)\) | \((0,9)\) | 0, 1 |
| \((1,2)\) | \((1,9)\) | 8, 21 |
| \((4,6)\) | \((18,26)\) | 0, 1, 8, 21 |
| \((0,4)\) and \((1,5)\) | \((0,18)\) and \((1,20)\) | 2, 3 |

Each listed case has a retained DRAT proof checked against its original
35-core incidence formula. The new case 2 dependency is the original-only
proof certificate; its exclusion needs no Gram-downdate premise. The
proof dependencies, retained files and completed replay records are
bound by hashes. Generation checks those bindings; the optional proof
replay command rebuilds and rechecks all six dependencies.

## Removing selectors forced by active edges

Let \(z_s\) select original signature \(s\), and let \(e_{s,t}\) be its
eligible exterior edge variable. Actual edges satisfy
\(e_{s,t}\le z_s,z_t\). Thus the two-edge cover gives

\[
e_{0,18}+e_{1,20}+z_9+z_{10}+z_{26}+z_{27}\le5.
\]

The four omitted endpoint selectors are forced whenever both edges are
active. The analogous three single-edge inequalities are

\[
\begin{aligned}
e_{0,9}+z_1+z_{10}+z_{18}+z_{20}+z_{26}+z_{27}&\le6,\\
e_{1,9}+z_0+z_{10}+z_{18}+z_{20}+z_{26}+z_{27}&\le6,\\
e_{18,26}+z_0+z_1+z_9+z_{10}+z_{20}+z_{27}&\le6.
\end{aligned}
\]

The source exhausts all Boolean assignments to the eight selectors and
the pattern edges that respect endpoint activation: 320 assignments for
each single-edge pattern and 400 for the two-edge pattern. In each case
the full eight-selector antecedent and the reduced antecedent agree.

The original joint primary numbering uses selectors 1 through 252 and
eligible edges from 253 onward. The new two-edge clause is exactly

```text
-425 -260 -28 -27 -11 -10 0
```

All other exported clauses retain that same complete primary numbering.

## Explicit relabelings and clause reduction

The verifier reconstructs all 144 relabelings of the normalized 27-core.
For each it checks the core adjacency, all 252 signature images, the
complete 28-matching image, and every proposed pattern's exhaustive cover.
It also checks the full 35-vertex adjacency transport of all six excluded
cores. These are 1,058,400 direct adjacency comparisons.

Every action supplies four clauses. The resulting 576 raw clauses are
distinct. A complete subset test discards none by Boolean subsumption.
The exact length counts are 432 seven-literal clauses and 144 six-literal
clauses. Each of the eighteen R/S core points receives eight transported
local sets. No T-centered analogue is inferred.

Relabeling the normalized core does not require the ambient graph to have
an automorphism. It transports a forbidden labeled configuration to an
isomorphic description. Conversely, the source makes no claim that the
exported clauses are semantically independent under other graph
constraints.

## Artifacts and replay

Source:
`experiments/workspace/complement_rook_35core_six_case_matching_cover.py`.
Certificate and fragment:

- `experiments/logs/grids-and-triangles/complement-rook-35core-six-case-matching-cover.json`
- `experiments/logs/grids-and-triangles/complement-rook-35core-six-case-matching-cover-clauses.cnf`

The adjacent `-generation.log` and `-replay.log` record successful exact
generation and readback. Replay reconstructs the coverage, endpoint
controls, complete transports, and deduplication/subsumption test:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_six_case_matching_cover.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-35core-six-case-matching-cover.json \
  --clauses experiments/logs/grids-and-triangles/complement-rook-35core-six-case-matching-cover-clauses.cnf \
  --replay
```

Add `--verify-proofs` followed by a new directory inside the repository
to cold-rebuild the six original formulas, check retained-input inclusion,
and verify each retained DRAT proof. Each checker has a separate
60-second bound. No new SAT query is made.
