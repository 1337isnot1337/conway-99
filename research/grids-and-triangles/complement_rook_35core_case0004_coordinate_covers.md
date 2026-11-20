# Complete coordinate covers for case4

## Scope and result

For the fixed 35-core case4, every ordered difference of its 36 exterior-row
coordinates gives a necessary Boolean cover when the target difference is
positive. The complete census gives 476,766 such differences. Exact duplicate
removal and same-target subset implications reduce this family to 178,533
clauses, containing 12,887,146 literal occurrences.

Fourteen clauses are units. They reproduce the complete intrinsic dominance
exclusions. Twelve of those targets were not explicit units in the earlier
60-cut Boolean model. This is a comparison of recorded unit conclusions; it
does not assert that those twelve units are independent of the earlier full
formula.

The preparation appends all retained clauses to the frozen 60-cut model.
It leaves all 1,214 optional columns available as primary variables, subject
to the new units. It fixes no incidence design and imposes no graph
automorphism. No new solver query is part of this checkpoint. Case4 and the
first local set remain unresolved.

## Derivation from an actual exterior row

Let B be the fixed 35-core adjacency matrix. For an admitted attachment
column h_a, set

\[
q_a=2\mathbf1-h_a-Bh_a,\qquad d_a=14-|h_a|,
\qquad t_a=(q_a,d_a).
\]

For each possible exterior neighbor b, put w_b=(h_b,1). There are 35 mixed
coordinates and one exterior-degree coordinate. Let x_a be the indicator
that attachment column a occurs, and let y_ab indicate the actual exterior
edge. Every graph completion satisfies

\[
\sum_{b\in E(a)}w_b y_{ab}=t_a x_a,
\qquad 0\le y_{ab}\le x_b.
\tag{1}
\]

The complete candidate set E(a) includes every possible actual neighbor.
Its two endpoints share at most one core neighbor, and each endpoint passes
the other endpoint's zero-quota support test. The frozen domain has 275,578
eligible unordered edges, checked from all 736,291 pairs of attachment
columns. It is used without fixing any numerical or integer incidence point.

Choose ordered coordinates i,j with positive difference
delta=t_a(i)-t_a(j). Subtract their equations in (1). Since every coordinate
of w_b is zero or one,

\[
\begin{aligned}
\delta x_a
 &=\sum_{b\in E(a)}(w_b(i)-w_b(j))y_{ab}\\
 &\le \sum_{\substack{b\in E(a)\\w_b(i)>w_b(j)}}y_{ab}
 \le \sum_{\substack{b\in E(a)\\w_b(i)>w_b(j)}}x_b.
\end{aligned}
\tag{2}
\]

For Boolean x_a and positive integer delta, (2) implies the clause

\[
\neg x_a\ \lor\!
\bigvee_{\substack{b\in E(a)\\w_b(i)>w_b(j)}}x_b.
\tag{3}
\]

When delta exceeds one, (3) deliberately weakens the original demand to one.
The certificate records the original demand and this weakening for every
origin. There are 111,586 such weakened origins. This checkpoint does not
encode their stronger cardinality demands.

An empty positive support gives the unit negation of x_a. Its conclusion
already follows from nonnegative row feasibility, independently of Boolean
neighbor choices.

## Complete coverage and exact reductions

For each of the 1,214 targets, the census considers all 36 squared ordered
coordinate pairs, including the vacuous diagonal pairs. Every positive
difference stores its two coordinates, original demand, unique support ID,
and weakening flag. The certificate stores each support as an exact integer
bitmap on the complete 1,214-column domain.

Identical supports with the same target give identical clauses. If retained
support C is a strict subset of support D for the same target, the clause
with C implies the clause with D. Every removed support stores the ID of a
retained subset. An empty retained support implies all other clauses for its
target. No cross-target subsumption is used.

| Quantity | Count |
| --- | ---: |
| Optional targets | 1,214 |
| Ordered coordinate pairs covered | 1,573,344 |
| Positive target differences | 476,766 |
| Differences with demand weakened to one | 111,586 |
| Unique same-target covers | 239,299 |
| Duplicate origins merged | 237,467 |
| Strict supersets removed by a nonempty retained subset | 58,384 |
| Nonempty supports implied by a same-target unit | 2,382 |
| Retained clauses | 178,533 |
| Retained literal occurrences | 12,887,146 |
| Largest retained clause | 197 literals |
| Largest retained target family | 201 clauses |
| Unit clauses | 14 |

The zero-based unit targets are

\[
352,353,354,355,439,552,553,645,869,873,957,1080,1081,1167.
\]

Targets 1080 and 1081 were already explicit units. All fourteen cover units
remain in the new suffix, and the model metadata lists their exact DIMACS
clauses.

The independent ledger check does not rerun the greedy minimal-support
algorithm. It reconstructs every eligible coordinate support, checks every
positive origin against that support, verifies that the retained family is
an antichain, and verifies a retained subset for every omitted support.
Together these conditions certify the complete family of minimal
same-target covers.

## Controls and streamed formula

The census checks same-target implication on every assignment for every
subset pair of a four-variable Boolean universe. A genuine nine-vertex rook
graph supplies a separate positive control for the mixed equations,
eligible-neighbor test, and coordinate-difference demands. Neither control
calls a solver.

The streamed preparation cold-rebuilds the complete old formula and checks
its frozen full CNF hash before copying its clause body byte for byte. The
old formula has 134,852 variables and 261,071 clauses: the original case4
Gram, multiplicity and triple-packing model, thirty certified Gram pair
conflicts, and sixty exact exterior-row cuts with their threshold encodings.

The new source writes the adjusted header, copies that full body, and writes
one cover clause at a time. It never constructs a Python list containing the
12.9 million added literals. No auxiliary variables are added. The resulting
formula has 134,852 variables and 439,604 clauses. The original body, added
body, and complete CNF receive separate SHA-256 bindings.

The complete census certificate has SHA-256
`a255f8876d3d827ff94d7df2f2640be6963348987043665dcd6fc53bf41dff8f`.
Its canonical retained clause body has SHA-256
`6f4ccc4623e4a7b9a40236f84f05e1a3973dd8b1d6f95a82a5ff0b66e699a24a`.
The full formula occupies 57,873,863 bytes and has SHA-256
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.
The model has SHA-256
`727874f9f98f5e1fab2b85478dbf2ab347333329fceab938b0a2806ae1a86a4b`.
Preparation took 27.786 seconds with peak RSS 349,536 KiB. A separate cold
ledger and full-formula replay passed, with report SHA-256
`f9c9a3b0ead3b4e8d856b78790d7630fe89c355efebbd4e2c83329e2c284c9ec`.

## Replay

The census source is
`experiments/workspace/complement_rook_35core_case0004_coordinate_covers.py`.
Its SHA-256 is
`f4692deb00982e7f3a3153faafc2cc6084db0c5827ff12d11beaf5e3d493357a`.
The complete certificate and its cold replay are
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-covers.json.gz`
and the adjacent `-replay.json` report.

From the repository root, replay the complete census to a fresh output:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_covers.py \
  --replay experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-covers.json.gz \
  --output /tmp/conway99-case4-coordinate-covers-replay.json \
  --seconds 120
```

The separate overlay source is
`experiments/workspace/complement_rook_35core_case0004_coordinate_cover_overlay.py`.
Its SHA-256 is
`5597089c00a15f72927f31c8b05f5a6bed1198a0d7ebc16aacaeb6cd39cb1c4a`.
It exposes preparation and cold replay commands only. Replay the complete
ledger, the full old formula, and the streamed new formula to fresh paths:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_cover_overlay.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-overlay-model.json \
  --output /tmp/conway99-case4-coordinate-cover-overlay-replay.json
```

These replays certify necessary constraints and formula construction. They
do not decide whether the strengthened Boolean model is satisfiable, and
they do not exclude another matching, local set, or whole graph case.
