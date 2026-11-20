# Complete incidence census at a=2

The complementary-rook core has exactly **576 labelled incidence designs
with a=2**, in **four orbits of size 144** under simultaneous rook-coordinate
relabeling and exchange of the first two grids.

This is a complete census of the selector-only Gram equations. It does
not assert an exterior edge completion for any design.

## Domain and equivalences

The 252 possible signatures and the 180 positive Gram margins are the
same unrestricted incidence model as in
[`complement_rook_a_incidence.md`](complement_rook_a_incidence.md).
The only extra equation sets `a=2`. Every solution selects 72 distinct
columns, and each saved representative is checked against all 729
entries of the core Gram matrix.

The coordinate group has 144 elements: 72 automorphisms of the fixed
rook graph, applied simultaneously to all three coordinates, followed
optionally by exchange of the first two coordinates. The implementation
checks every induced permutation of all 252 signatures and every
corresponding permutation of the 27-core adjacency and Gram matrices.
These are equivalences of labelled incidence designs. No design is
required to possess an automorphism.

## Why the enumeration is complete

For each solver point, the program constructs its entire coordinate
orbit and checks a canonical representative exactly. It then blocks
each labelled design in that orbit with the clause

\[
\bigvee_{s\in D}\neg z_s.
\]

Every solution selects exactly 72 signatures and `|D|=72`. Thus this
clause removes precisely the design `D`, independently of assignments
to counter auxiliaries.

The four saved orbits are pairwise disjoint and each contains 144
designs. After blocking all 576, the remaining formula is UNSAT.
The final CNF and DRAT proof are saved. Independent `drat-trim` checking
verifies that no additional incidence design remains.

The run was bounded by 60 seconds and 50,000 labelled designs. It
exhausted the model well before either cap; the fourth representative
was found at approximately 0.427 seconds. The completeness claim rests
on the checked final proof, not on the absence of further points before
a timeout.

## Artifacts and replay

- Source: `experiments/workspace/complement_rook_a_incidence_census.py`.
- Final formula and proof:
  `experiments/workspace/complement-rook-a2-incidence-census.cnf` and
  `complement-rook-a2-incidence-census.drat`.
- Representatives and orbit sizes:
  `experiments/logs/grids-and-triangles/complement-rook-a2-incidence-census.json`.
- Run, replay, and DRAT logs use the same stem.

Representatives are stored as sorted indices into the complete
lexicographically ordered signature domain from
`complement_rook_a_incidence.domain()`. Replay reconstructs this domain,
checks every representative's full Gram matrix, reconstructs all 144
coordinate actions, checks orbit sizes and disjointness, regenerates
every blocking clause, compares the exact final CNF, and rechecks DRAT.

```sh
python experiments/workspace/complement_rook_a_incidence_census.py --replay \
  --output experiments/logs/grids-and-triangles/complement-rook-a2-incidence-census.json \
  --cnf experiments/workspace/complement-rook-a2-incidence-census.cnf \
  --proof experiments/workspace/complement-rook-a2-incidence-census.drat \
  --drat-log experiments/logs/grids-and-triangles/complement-rook-a2-incidence-census-drat-replay.log \
  --drat-trim /path/to/drat-trim
```

No exterior adjacency variable occurs in this census. A separate
completion argument is required to exclude any of the four orbits.
