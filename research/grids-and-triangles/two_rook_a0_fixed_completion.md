# Complete edge model for the remaining a=0 incidence

This test concerns the complementary-rook tip case
`Z=J-I-R` for one pair of rook grids with an isomorphic matching.
The parameter `a` counts exterior signatures `(p,q,t)` for which both
`p,t` and `q,t` are adjacent in the original rook graph `R`.

The exact census in
[two_rook_pair_structural.md](two_rook_pair_structural.md) gives 16
incidence designs when `a=0`. Fourteen have exact integer Farkas
exclusions. The remaining two are equivalent under coordinate
relabeling and exchange of the first two grids. This model uses one
representative of that last orbit and imposes all binary edge and
common-neighbor constraints. It imposes no graph symmetry.

The complete model is **UNSAT**, with a directly verified DRAT proof.
Combining this two-design exclusion with the fourteen exact Farkas
exclusions proves

\[
\boxed{a\ge1\quad\text{when } Z=J-I-R.}
\]

This is a restriction on the complementary-rook case. It does not
exclude that case for `a>=1`, the general eighteen-edge boundary, or
an unrestricted isomorphic rook pair.

## Exact fixed incidence

The input is `cases[2]['signatures']` in
`experiments/logs/grids-and-triangles/two-rook-pair-structural-certificate.json`.
Each stored triple `(p,q,t)` gives core neighbors `(p,9+q,18+t)`.
The 72 triples are distinct and sorted. All nine tip permutations
have cycle type `(1,8)`; at tip zero the permutation is

\[
(0,5,7,8,2,6,4,3,1).
\]

The builder first replays the complete 16-design census, its orbit
transports, both exact Farkas certificates, and the surviving rational
linear-relaxation witness. That witness is a control only. None of
its edge weights or orbit equalities enter the binary model.

The structural certificate SHA256 is
`2842d990148ed3968804d8355bcc0284e81ad66c298e02dfbedf373deff9d0ec`.
The compact JSON of the converted 72 core signatures has SHA256
`7d66efd0001a6debfae045fe4cce71c6f9af7ca875167123b7188defa95890f0`.

The 27-core matrix is

\[
B=\begin{pmatrix}R&I&I\\I&R&I\\I&I&J-I-R\end{pmatrix}.
\]

The exact incidence check verifies

\[
XX^T=12I+2J-B^2-B.
\]

Every core vertex has six core neighbors and eight exterior neighbors.
Every exterior vertex has three core neighbors and requires eleven
exterior neighbors.

## Complete binary model

There is one independent Boolean variable per eligible exterior edge,
with 1,764 variables in total. Eligibility uses only the visible core
common-neighbor and mixed-equation requirements. The builder compares
its bitset mixed demands with a separate dense-matrix calculation.

It imposes every mixed equation and exterior degree:

\[
XC=2J-(B+I)X,\qquad C\mathbf1=11\mathbf1.
\]

Identical cardinality requests are deduplicated, leaving 1,873 counts.
There are no selector variables because all 72 columns are fixed by
this incidence subcase.

For each distinct exterior pair `u,v`, let `c_uv` be its number of
common core neighbors. The model imposes

\[
C_{uv}+\sum_w C_{uw}C_{vw}\le2-c_{uv}.
\]

All 2,556 unordered exterior pairs are present. Their overlaps are:

| Core overlap | Pairs | Exterior cap |
| --- | ---: | ---: |
| 0 | 1,836 | 2 |
| 1 | 684 | 1 |
| 2 | 36 | 0 |

For the 36 overlap-two pairs, direct adjacency is ineligible and 1,296
binary packing clauses prohibit every possible exterior common
neighbor. Every remaining possible two-edge path has a fresh variable
`p` with clause `not e_uw or not e_vw or p`. An at-most counter bounds
the path variables and optional direct edge. These forward clauses
are existentially equivalent to the stated cap: true paths force
their variables true, and every cap-valid edge assignment extends by
setting path variables to the exact conjunctions.

The model contains no lazy cuts, orbit equalities, or symmetry clauses.
All exterior pair constraints are included before solving.

## Sufficiency and verification

The fixed incidence and mixed equations make every pair involving the
core exact. All vertices have degree 14. Since every remaining pair
has `(A^2+A)_ij <= 2` and each off-diagonal row sum is
`14^2=196=98*2`, all pair bounds must be equalities. A satisfying
assignment is therefore a complete `(99,14,1,2)` graph.

The solver wrapper still reconstructs the whole graph explicitly. It
checks all 99 degrees, symmetry, absence of loops, and all 4,851
unordered pair counts. Only a zero-defect result is saved as a graph
candidate, which then requires independent validation.

Before solving, the build passed:

- the exact structural certificate replay and all core Gram entries;
- agreement between dense and bitset mixed demands;
- independent path-domain enumeration for all 2,556 exterior pairs;
- 3,069 exhaustive small assignments for the forward-path/cardinality
  encoding.

The author of the incidence census independently reviewed the new
builder. That review reconstructed the exact signatures, all 1,764
eligible edges, all pair overlaps and path domains, and all 1,296
packing clauses. It found no fixed fractional weights or graph
symmetry constraint.

## Formula and reproduction

| Quantity | Count |
| --- | ---: |
| Primary edge variables | 1,764 |
| Variables before exterior caps | 77,940 |
| Clauses before exterior caps | 157,968 |
| New path variables | 83,376 |
| New counter auxiliaries | 137,376 |
| Total variables | 298,692 |
| Total clauses | 593,820 |

The frozen source is
`experiments/workspace/two_rook_a0_fixed_completion.py`, SHA256
`409b69e4449083a294746f5c1fafa38fd16b43d7adf7356769f283c59ffb72d7`.
The full CNF SHA256 is
`7aee21fe380453f3d961740e740b27ec4e2918a4884352043bb0413c18b0a3d4`.

Use temporary output paths when replaying, so the archived model
manifest and its run binding remain unchanged:

```sh
.venv/bin/python experiments/workspace/two_rook_a0_fixed_completion.py build \
  --structural-certificate experiments/logs/grids-and-triangles/two-rook-pair-structural-certificate.json \
  --cnf /tmp/conway-two-rook-a0-fixed.cnf \
  --manifest /tmp/conway-two-rook-a0-fixed-model.json

.venv/bin/python experiments/workspace/two_rook_a0_fixed_completion.py solve \
  /tmp/conway-two-rook-a0-fixed-model.json \
  --seconds 120 \
  --proof /tmp/conway-two-rook-a0-fixed.drat \
  --output /tmp/conway-two-rook-a0-fixed-result.json
```

The run includes initialization in its requested 120-second budget and
records actual elapsed time. A raw solver UNSAT result requires a
separate proof check. A timeout leaves the remaining incidence and
the condition `a=0` unresolved.

## Actual outcome and retained proof

Glucose4 initialized in 10.221 seconds and returned UNSAT at 10.412
seconds. Final recording completed at 10.647 seconds. It reported
728 conflicts, 1,823 decisions, and 885,386 propagations. No binary
point, added cut, or second solver continuation preceded the result.

Direct `drat-trim` verification against the frozen full CNF returned
`VERIFIED` in 0.726 seconds. The retained certificate uses 3,724 input
clauses and 293 lemmas, with 13,896 resolution steps and no RAT
lemmas. The trimmed proof has 4,261 lines, including deletions.

The certificate is
`experiments/workspace/two-rook-a0-fixed-certificate.json`, with the
adjacent `two-rook-a0-fixed-core.cnf` and
`two-rook-a0-fixed-proof.drat`. The separate replay wrapper first
reconstructs the complete structural census and exact Farkas checks,
then regenerates the fixed-incidence CNF, verifies its hash, checks
retained-clause inclusion, and verifies the trimmed proof:

```sh
.venv/bin/python experiments/workspace/two_rook_a0_fixed_certificate.py \
  experiments/workspace/two-rook-a0-fixed-certificate.json \
  --drat-trim /path/to/drat-trim
```

The two surviving incidence designs are related by the explicit
coordinate actions in the structural census. Transporting a putative
completion through that relabeling would give a completion of the
excluded representative. This extends the proof to both designs
without assuming any automorphism of the completed graph.

The run, model manifest, build audit, and direct proof-check log have
prefix `experiments/logs/grids-and-triangles/two-rook-a0-fixed`.
