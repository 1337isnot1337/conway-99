# Computations and replay

## Main checks

From the repository root, use Python, GNU Make, and a C++20 compiler. The archived checks were replayed with Python 3.14 and GCC 16.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r experiments/requirements-verify.txt
make verify
```

`make verify` uses the repository's `.venv` when present. Set `PYTHON` to the absolute path of a different interpreter or set `CXX` to select the compiler.

| Check | Scope |
| --- | --- |
| [`grid_intersections.py`](workspace/grid_intersections.py) | Enumerates all 2,097,152 labeled seven-vertex graphs for the grid-count inequalities and equality case. |
| [`grid_support.cpp`](workspace/grid_support.cpp) | Computes disjoint-pair minima for the grid proof's incidence-support condition. [Log](logs/grids-and-triangles/grid-support.log) |
| [`root_cover_audit.py`](workspace/root_cover_audit.py) | Replays the parity and transport cases used to exclude a root contained in 21 grids. [Log](logs/grids-and-triangles/root-cover-audit.log) |
| [`level_seven_check.py`](workspace/level_seven_check.py) | Replays the rational rank certificates and checks the theta transform on five explicit lattice controls. [Log](logs/eigenlattices/level-seven-check.log) |

## Global-constraint certificates

The additional [global-constraints investigation](../research/session-ab2f.md)
uses the versions pinned in `requirements-global-constraints.txt`:

```sh
.venv/bin/python -m pip install -r experiments/requirements-global-constraints.txt
make verify-global-constraints
```

This target replays four integer Farkas certificates for size-twenty
transversal cocliques, seventeen elementary norm-16 counting certificates,
61 further integer Farkas branch certificates, eleven zero-class forest
witnesses, five exact scalar-theta witnesses, the incomplete-grid signature
and edge-completion certificates, and an integral grid-count witness. It
also checks the small covering enumeration for the all-red grid bound and
the exact minimum-Ramsey hemisphere witness. It does
not start a new SAT or mixed-integer search. These certificates prove the
stated local exclusions or feasibility of finite relaxations; none is a
solution of the existence problem.

The exact zero-grid count and moment witness has its own replay:

```sh
make verify-grid-free-relaxation
```

It checks all 23,189 original extension equations, all 6,535 nonnegative
integral induced counts, and integer positive-definiteness certificates
for all 584 selected cached moment blocks. It does not run an optimizer.
The result concerns this finite relaxation, not all possible order-nine
inequalities or a completed graph.

The same zero-grid point passes 832 additional root-conditioned spectral
and Schur blocks. Their exact kernel and positive-quotient certificates
have a separate replay:

```sh
make verify-grid-free-projectors
```

Each block has eight explicit exact kernel vectors. Integer congruences
certify the complementary principal matrix as positive definite. Together
with the preceding target, this checks 1,416 blocks at the same count point.

The three-base obstruction and the independent bounds of one all-red grid
and 119 total grids have a standard-library replay target:

```sh
make verify-current-grid-bounds
```

It exhausts all three interface classes, reconstructs the translation
incidence identity in two implementations, and checks the aggregate
integer inequality on all 2,097,152 labeled root graphs and all 1,596 grid
profiles. The parallel [root-grid branch](https://github.com/1337isnot1337/conway-99/pull/3)
proves stronger global bounds using a separate intersecting-triangle
exclusion. Those results are not premises of this replay.

The stronger bound of one rook-isomorphic partner per grid has a complete
replay, including the independently audited binary encoding and its checked
proof:

```sh
make verify-rook-partner-bound DRAT_TRIM=/absolute/path/to/drat-trim
```

The retained proof excludes the last of 59 three-grid interface classes.
It does not assume graph symmetry or fix an outside-incidence witness.
The earlier star and short-cycle obstructions, independent dense-matrix
audits, fixed-incidence certificate, and exact rational relaxation witnesses
have a separate replay:

```sh
make verify-general-rook-interfaces
```

The unresolved single-pair completion has an exact transcript replay:

```sh
make verify-rook-pair-completion
```

This checks the baseline and duplicate-label runs, every local Hall
certificate, the rational tip Gram identities, and all points and necessary
cap clauses in the Hall-strengthened run. The Hall transcript is compressed;
the verifier reads it directly. It uses no timed solver. All three search
outcomes are UNKNOWN. The saved points satisfy the fixed core equations
but fail equations among the exterior vertices. They are not graph solutions.
The same target checks an explicit near-edge tip graph against all 3,394
local clauses and an exact positive-definiteness certificate. That small
projection refutes a proposed local implication; it does not complete the
exterior graph.
The target also reconstructs all 5,040 labelled rook tip graphs, replays
the eighteen-edge boundary propagation, and checks both exported complete
incidence domains. The separate complete-cap search is documented in
[its model note](../research/grids-and-triangles/two_rook_iso_pair_full_caps.md);
the replay target does not start its timed solve.

The two later binary boundary exclusions have a proof-replay target:

```sh
make verify-rook-tip-boundary DRAT_TRIM=/absolute/path/to/drat-trim
```

It rebuilds the complete 188-signature model and verifies its retained
DRAT proof, reconstructs the high-edge nine-vertex catalogue, and replays
the complete complementary-rook `a=0` census and its final binary proof.
Both wrappers check source and input hashes, full formula hashes, and
membership of every retained input clause. The coordinating worker ran
both full rebuilds and proof replays successfully. The unrestricted
two-grid case remains open. The next incidence proof excludes `a=1`,
and the complete `a=2` census gives four orbits containing 576 designs:

```sh
make verify-complement-rook-incidence DRAT_TRIM=/absolute/path/to/drat-trim
```

This reconstructs both incidence formulas, checks the `a=2` witness,
regenerates all orbit blocks, and replays both retained DRAT proofs.
It does not solve any exterior edge-completion problem.

All four `a=2` edge-completion models are now excluded. Their complete
formula reconstruction and retained-proof replay are separate:

```sh
make verify-complement-rook-a2-completion DRAT_TRIM=/absolute/path/to/drat-trim
```

Each case retains all 1,764 eligible edge variables and all 2,556
exterior pair caps. Together with the `a=0` and `a=1` exclusions, these
four proofs give `a>=3` in the complementary-rook boundary case.

The unrestricted rooted model has a separate small coverage replay:

```sh
make verify-root-matching-coverage
```

It covers all 10,395 perfect matchings by explicit relabelings and an
independent orbit traversal, then checks the closed-form counts and all
64 local cell assignments. It does not start the eleven-case SAT batch.
The [model note](../research/root_full_caps.md) gives the complete formula,
positive controls, build command, and separate outcome records.

The single-source and duplicate-pair binary projections have direct
partial-witness replays, without loading their SAT builders:

```sh
.venv/bin/python experiments/workspace/complement_rook_row_projection_replay.py \
  --output /tmp/complement-rook-row-replay.json
.venv/bin/python experiments/workspace/complement_rook_duplicate_row_replay.py \
  --output /tmp/complement-rook-duplicate-replay.json
python experiments/workspace/triangle_root_constraints.py \
  --replay experiments/logs/grids-and-triangles/triangle-root-constraints-exact.json
```

All source-row and duplicate-row cases have exact partial witnesses;
none is a completed 99-vertex graph. The last command checks exact
triangle-core identities and three controls, not a complete core census.
The [order-ten probe note](../research/grids-and-triangles/grid_free_order10_probe.md)
gives the separate large count-reduction recipe and its bounded UNKNOWN
outcomes. The [lex overlay note](../research/root_full_caps_lex.md) gives
its small coverage and Boolean replays without starting a large solve.

The subsequent [order-ten count cut](../research/grids-and-triangles/grid_free_order10_scaled.md)
excludes extension of the published order-nine point. Its saved integer
identity has a short replay:

```sh
make verify-order-ten-count-cut
make verify-root-anchor-max
```

The first command checks the 52 positive induced-count terms, 21
ordinary-count terms, and the negative value at the old point. The
separate root audit also checks every saved form against the large exact
reduction. The second command checks the new maximum-anchor coverage
and its cardinality clauses. Neither command starts a large solver.
The [run tables](../research/root_full_caps_runs_01.md) record eleven
original UNKNOWN cases and two UNKNOWN lex pilots.

The subsequent exact moment cuts and complementary-rook triangle
restrictions have separate replays:

```sh
make verify-order-ten-moment-cuts
make verify-complement-rook-schur
```

The first target reconstructs all thirteen moment inequalities from
their integer vectors and cached block forms. It starts no optimization.
The second regenerates the exact projector census, then independently
checks the nine full thirty-vertex negative quadratic witnesses and
all 1,296 forbidden-triangle clauses. These clauses do not exclude
the complementary-rook core.

The [prism-zero probe](../research/grids-and-triangles/grid_free_order10_prism_zero.md)
preserves its numerical proposal and exact rounding failures. Two induced
counts become minus one; no exact feasible point follows from the run.
The [maximum-anchor run table](../research/root_full_caps_anchor_max_runs_01.md)
records four further UNKNOWN cases under its separate coverage convention.

The [exact prism-zero repair](../research/grids-and-triangles/grid_free_order10_prism_zero_repair.md)
and its selected cached PSD blocks have independent replays:

```sh
make verify-prism-zero-counts
make verify-prism-zero-psd
make verify-incidence-master-cut-orbits
```

The first target rebuilds the small catalogue and checks all original
count equations without rebuilding the large reduced matrix. The
[count-audit note](../research/grids-and-triangles/prism_zero_count_independent_audit.md)
also gives the optional reduced-form replay. The second target verifies
all 1,416 exact PSD certificates without recomputing numerical
eigensystems. Neither target constructs a graph.

The third target replays the static closure of eight checked incidence
patterns under core relabeling. It binds the completed proof replays;
it does not itself call DRAT. The
[pilot result note](../research/grids-and-triangles/complement_rook_incidence_master_pilot_01_results.md)
gives the full-base rebuild and DRAT command for each of the eight cuts.

The repaired count point is rejected by the next
[order-ten flag family](../research/grids-and-triangles/grid_free_order10_r8s1.md).
Its eleven exact cuts have a direct graph-construction replay. That replay
requires the hash-bound order-ten catalogue and reduced cache. The complete
916-root cache is separate from the point-pruned discovery cache.

The newer incidence and prism-structure replays are:

```sh
make verify-incidence-core-simplification DRAT_TRIM=/absolute/path/to/drat-trim
make verify-refined-pattern-orbits
make verify-root-prism-free-structure
```

The first reconstructs exact quota implications, checks all 64 incidence
counterexamples, and verifies all 34 small DRAT proofs. The second checks
the refined relabeling export, including the eleven-positive-signature
pattern. The [positive-pattern note](../research/grids-and-triangles/complement_rook_positive_pattern.md)
gives its separate complete-base rebuild and decisive DRAT replay.
The third reconstructs all 34,440 prism clauses, partial controls, and
minimum-anchor matching census. It starts no complete graph search.
All four [prism-free overlay runs](../research/root_prism_free_runs_01.md)
remain UNKNOWN.

The earlier bound of three all-red grids retains its replay target:

```sh
make verify-rook-interfaces
```

It regenerates the local interface censuses, checks all saved integer
negative Gram vectors and explicit isomorphisms, and exhausts the boundary
signatures of the surviving four- and five-base cores. The four-base proof
uses no SAT result. A separate checked DRAT proof for the weaker six-base
obstruction can be replayed with:

```sh
make verify-rook-interfaces-drat DRAT_TRIM=/absolute/path/to/drat-trim
```

The earlier bound of seven retains its replay target, which also depends
on both interface replays above:

```sh
make verify-red-grid-bound
```

It regenerates both covering censuses, compares their full certificate
archives, enumerates the thirty residual-cycle partitions, and checks the
twelve surviving spectra by a second implementation using direct cycle
matrices. The [proof](../research/grids-and-triangles/eight_red_exclusion.md)
supplies the local and trace arguments excluding those twelve spectra.
The target also checks the [cubic trace identity](../research/grids-and-triangles/red_grid_cubic_trace.md),
which provides a shorter exclusion of all twelve without the three-cover
census.

The seven-grid follow-up has its own exact replay:

```sh
make verify-seven-red-residual
```

This rebuilds all 408 possible nine-vertex residual cores, reconstructs
their characteristic polynomials by a second method, and checks every
factor-multiplicity tuple against the quadratic and cubic trace conditions.
It excludes the nine-vertex case. The
[remainder note](../research/grids-and-triangles/seven_red_residual_reduction.md)
states the initial resulting counts 18, 27, and 36. The same target now
also regenerates all 331,776 normalized four-covers, verifies the three
surviving projection-graph colorings in two implementations, and checks
the negative rook-space polynomial contradiction. These checks exclude
the count 36. The counts 18 and 27 were unresolved by this remainder
argument; the later interface obstruction excludes the whole seven-grid
case. This historical replay is also part of `make verify-global-constraints`.

The fourteen additional norm-16 exclusions have saved CNF cores and DRAT
proofs. Build [drat-trim](https://github.com/marijnheule/drat-trim) at revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`, then run:

```sh
make verify-coupled-shells DRAT_TRIM=/absolute/path/to/drat-trim
```

This target regenerates the five template censuses in two ways, compares the
478 canonical representatives with the archive, and replays every outcome:
seventeen counting exclusions, fourteen DRAT exclusions, and 447 explicit
partial adjacency witnesses. Each DRAT replay rebuilds the full formula,
checks its SHA-256 digest, verifies that the saved core contains only input
clauses of that formula, and runs the separate checker. The 447 witnesses
still have unchosen edges and do not certify strongly regular graphs.

The [norm-16 note](../research/eigenlattices/coupled_shells.md),
[transversal note](../research/independent-sets/transversal_constraints.md),
and [completion note](../research/unrestricted-completion.md) state the
reductions and their limits. Independent replay output is in
[`logs/session-ab2f/`](logs/session-ab2f/).

The [linear-certificate note](../research/eigenlattices/coupled_shells_linear.md)
also gives a command to project all 447 saved partial witnesses into the
independent aggregate model. That exact control passed. The 61 branch
certificates include complete proofs for ten already excluded templates;
they do not add ten more exclusions to the census.

The global replay also checks 265 integer negative quadratic witnesses for
specified 35-vertex norm-16 cores and one exact neighborhood-row Farkas
certificate. The coupled-shell replay additionally checks the saved DRAT
proof for a 58-bit pattern in the canonically labeled full-incidence model.
These are exclusions of particular partial choices; the 447 unresolved
template classes remain unchanged. The
[completion note](../research/eigenlattices/coupled_zero_completion.md)
states the labeling restriction and the limits of the other solver runs.

## Explore the archive

Run the individual research scripts from [`experiments/workspace/`](workspace/). The Python and C++ sources, certificate JSON, candidate arrays, and cached moment data share this directory because the scripts use sibling paths.

The archived logs cover [grids and triangles](logs/grids-and-triangles/), [independent sets](logs/independent-sets/), [eigenlattices](logs/eigenlattices/), [moments and counts](logs/moments-and-counts/), and [construction searches](logs/construction-searches/). The [research ledger](../STATE.md) explains which runs concern relaxations or particular construction families.

Some exploratory scripts refer to solver builds and generated inputs in the original `/tmp/conway99-tools` directory, which was unavailable when the archive was published. The four checks above use the archived files and the dependencies listed here. The [initial publication](https://github.com/1337isnot1337/conway-99/tree/270ae4f8c4cfb751f9c4b5b74949c41263b645ba) preserves the original paths.
