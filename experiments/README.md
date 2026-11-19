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

Two later exact count witnesses include all 25 retained inequalities.
One also fixes the edge-component coordinate `x521` to zero. Their
independent original-equation checks and the motif identity replay with:

```sh
make verify-prism-zero-followup-counts
make verify-root-edge-components
```

The first rebuilds the small catalogue, checks both full induced-count
vectors, all original equations, and the retained exact cuts. It does not
load the dense reduction or call an optimizer. The second uses only the
standard library to check the edge-shell census, motif automorphisms,
cap-forbidden chords, and exact coordinate identification.
The [follow-up audit note](../research/grids-and-triangles/prism_zero_followup_audits.md)
states the distinction from the separate full-model replay. The
[x521-zero moment scan](../research/root_prism_free_x521_moments.md)
tests the exact integer witness in 2,332 blocks and finds no separator.
That outcome is not an exact PSD certificate.

The smaller complementary-rook subsystem and its local case census are
documented in the [star-model note](../research/grids-and-triangles/complement_rook_core_star_oracle.md)
and [local-star note](../research/grids-and-triangles/complement_rook_local_star_census.md).
The latter has a direct exact replay:

```sh
make verify-complement-rook-local-stars
```

It reconstructs all 864 local signature sets, the 118 stabilizer orbits,
and all 2,521 matching choices on the representatives. Integer Schur
matrices and rational LDL pivots verify both principal projectors for
every case. It calls no SAT solver. The star-model note gives the separate
full-baseline/reduced-formula reconstruction and DRAT commands for its
two transported conditional proofs. The free reduced-star pilot remains
UNKNOWN.

The [35-core matching-cover note](../research/grids-and-triangles/complement_rook_35core_first_local_sweep.md)
gives the complete replay for the five checked exclusions and 144
conditional edge clauses. Its ordinary replay checks matching coverage
and transports. Adding `--verify-proofs` rebuilds every required domain
and CNF, checks retained-input membership, and runs DRAT verification.
The 23 UNKNOWN cases remain unresolved.

The [split-component package](../research/root_prism_free_f0_incidence.md)
contains a complete 66-component cover and a SAT witness for one
component's sixty exterior-neighbor triples. Its manifest records the
independent domain/motif audit and cold formula/witness replay. The
witness supplies neither the second component nor exterior adjacency.

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

The [six-root moment package](../research/grids-and-triangles/grid_free_order10_r6s2_results.md)
has eighteen exact quadratic cuts and a separate direct-graph reconstruction
of every product used in those cuts. Its saved-tensor replay checks exact
contractions against the bound cache; the fresh reconstruction does not
use those tensors to generate coefficients. With the preparation's bound
catalogue and input paths available, the two checks are:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_r6s2_scan.py replay \
  --certificate experiments/logs/moments-and-counts/prism-zero-order10-r6s2-scan.json \
  --output /tmp/conway99-r6s2-cache-replay-new.json
.venv/bin/python experiments/workspace/grid_free_order10_r6s2_fresh_replay.py run \
  --preparation experiments/logs/moments-and-counts/prism-zero-order10-r6s2-fresh-preparation.json \
  --output /tmp/conway99-r6s2-fresh-replay-new.json \
  --seconds 300
```

Use a new output path for the fresh reconstruction.
The [full cache and scanner note](../research/grids-and-triangles/grid_free_order10_r6s2_full_cache.md)
records all 62 roots, the seven-block continuation, and controls for the
nonbinary flags. Its manifests bind the source and data files. A complete
scan with no detected separator does not certify positive semidefiniteness.

Run the individual research scripts from [`experiments/workspace/`](workspace/). The Python and C++ sources, certificate JSON, candidate arrays, and cached moment data share this directory because the scripts use sibling paths.

The archived logs cover [grids and triangles](logs/grids-and-triangles/), [independent sets](logs/independent-sets/), [eigenlattices](logs/eigenlattices/), [moments and counts](logs/moments-and-counts/), and [construction searches](logs/construction-searches/). The [research ledger](../STATE.md) explains which runs concern relaxations or particular construction families.

Some exploratory scripts refer to solver builds and generated inputs in the original `/tmp/conway99-tools` directory, which was unavailable when the archive was published. The four checks above use the archived files and the dependencies listed here. The [initial publication](https://github.com/1337isnot1337/conway-99/tree/270ae4f8c4cfb751f9c4b5b74949c41263b645ba) preserves the original paths.

## Replaying the 48-cut count face

The [47-to-48-cut record](../research/grids-and-triangles/grid_free_order10_higher_flags_loop.md)
gives exact commands for the three new six-root cuts, the four-cycle
cut, and the independent audit of the latest x521-zero count witness.
Its manifest is
`logs/moments-and-counts/order10-higher-flags-loop-artifacts.json`.
The face audit checks the original equations and all frozen reduction
rows using Python integers. It does not run an optimizer.

The [additional flag-family record](../research/grids-and-triangles/grid_free_order10_higher_flags_results.md)
and [four-cycle decomposition](../research/grids-and-triangles/grid_free_order10_higher_flags_c4_structure.md)
give their own replay commands. The complete 2,405-block discovery scan
uses the unrounded proposal. Only the C4 block has a separate exact PSD
certificate at the latest integer point.

## Later 35-core and split-shell proofs

The [case-two note](../research/grids-and-triangles/complement_rook_35core_case0002_exclusion.md)
gives the original-formula replay for the sixth excluded first-local
matching. This proof needs none of the discovery overlay's 886 additional
Gram-downdate clauses. Both the retained CNF and proof are archived.

The [split-shell coupling note](../research/root_prism_free_f0_coupling.md)
gives the full-formula and DRAT replay for one fixed pair of incidence
designs. Its broader fractional control has a different domain. Neither
certificate excludes the complete split-shell case.

The [two later local exclusions](../research/grids-and-triangles/complement_rook_35core_cases09_10_exclusion.md)
have compact replays that need only five additional integer Gram vectors
and the original incidence formulas. The
[six-case matching cover](../research/grids-and-triangles/complement_rook_35core_six_case_matching_cover.md)
separately checks all 576 conditional clause transports.

The [complete component-pair pilot](../research/root_prism_free_f0_pair_gram_run01.md)
records an UNKNOWN outcome. Its full DIMACS file is regenerated from the
streamed builder; the frozen record binds its exact hash and counts.

The [C4 integer distribution](../research/grids-and-triangles/grid_free_order10_c4_integer_distribution.md)
has an optimizer-free replay of all 120 literal products and all 225
symmetric moment entries. The positive rational mixture is a finite
moment certificate, with no graph-realization claim.

## Complete eight-root projector cache

The [full projector record](../research/grids-and-triangles/grid_free_order10_projector_full_scan.md)
binds all 916 roots, 3,664 blocks, and 29 compressed cache chunks. Its
publication manifest lists every chunk explicitly. The run contracts
the exact integer point and checks all universal kernels before numerical
separation. Finding no separator does not certify positive semidefiniteness.

The [class-size continuation](../research/grids-and-triangles/grid_free_order10_projector_integer_classes.md)
uses this cache to recover second moments coefficientwise. It checks
all 68,176 classes and every integer shift by the exact minimizing shift.
The saved table records every first moment, second moment, and result.

The [complement-domain package](../research/grids-and-triangles/grid_free_order10_complement_domains.md)
has its own complete regeneration and sparse-lift replay. It depends on
the scalar seven-root and eight-root caches, not on a numerical PSD claim.
Its 737 remaining cases are a prepared domain, not an exclusion.

The [single-complement scan](../research/grids-and-triangles/grid_free_order10_complement_scan.md)
now records its complete numerical separation outcome. The later
[clique package](../research/grids-and-triangles/grid_free_order10_complement_cliques.md)
has separate complete domain, coefficientwise lift and orbit replays.
Root relabelings give congruent matrices without imposing graph symmetry.
The [complete representative scan](../research/grids-and-triangles/grid_free_order10_complement_clique_scan.md)
records all 711 direct checks and their 3,939-case coverage. It finds no
separator and makes no exact PSD claim.

## The saved split-shell incidence

The [exterior exclusion](../research/root_prism_free_f0_first_design_exterior.md)
gives the full cold formula/proof command. The retained proof has 120
inputs, and an independently checked integer potential supplies a
shorter row contradiction. This excludes only the saved first incidence,
with the second component and incidence left free.

The [two-column Gram classification](../research/root_prism_free_f0_pair_downdate.md)
has a separate complete integer replay. Its empty set of new conflicts
is a finished finite result, not a timeout or a whole-core exclusion.

The [twenty-case rook continuation](../research/grids-and-triangles/complement_rook_35core_continuation_terminal.md)
has a standalone compressed original-only proof replay. It rebuilds each
original formula and checks decompressed retained inputs and proofs.
No downdate or overlay source is imported by that verifier.

## Exterior-row inequalities and absence products

The [complete replacement-incidence row check](../research/root_prism_free_f0_exterior_row_box_separation.md)
has an optimizer-free replay and a separate independent reconstruction.
Three exact integer gaps reject extension of that incidence. Fifty-seven
rational row boxes are separate controls; they do not form a joint graph.
Its manifest binds all 36 transported weighted inequalities.

The [case-four LP continuation](../research/grids-and-triangles/complement_rook_35core_case0004_row_loop_run01.md)
retains all sixty exact row cuts, every numerical proposal, and all
848 visited row outcomes. Its cold replay checks the full cut pool and
the precise prefix used by each LP. The final twenty cuts have not been
reoptimized, and the final support has nineteen unvisited rows.

The [visible-pair scan](../research/grids-and-triangles/grid_free_order10_complement_visible_scan.md)
and [double-complement scan](../research/grids-and-triangles/grid_free_order10_double_complements.md)
each finish their finite representative lists without a separator.
Neither result is an exact PSD certificate. The double-complement note
gives the separate cold replay wrapper for its JSON-key normalization.

The [prism-free clique preparation](../research/grids-and-triangles/grid_free_order10_complement_prism_domains.md)
keeps the full domains and records all nonzero terms in its new selected
zero rows. Each term lies in the proved prism-containing zero support.
The separate path-on-four-vertices replay reconstructs every genuine new
pair incompatibility without using the catalogue or child transports.

