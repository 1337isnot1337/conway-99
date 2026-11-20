# Complete edge model for two rook-isomorphic grids

This model tests a graph with parameters `(99,14,1,2)` containing two
disjoint induced `3 by 3` rook grids whose unique matching is a rook
isomorphism. It does not assume an automorphism of the full graph.

The first proof-enabled run returned **UNKNOWN** after 180.392 seconds.
No complete graph or exclusion was obtained.

The source is
`experiments/workspace/two_rook_iso_pair_full_caps.py`. Its source and
input hashes are recorded in
`experiments/logs/grids-and-triangles/two-rook-iso-pair-full-caps-model.json`.
The timed result is recorded separately in
`experiments/logs/grids-and-triangles/two-rook-iso-pair-full-caps.json`.

## Fixed incidence

Label the two grids so their matching is the identity. Write their
18-point adjacency matrix as

\[
B=\begin{pmatrix}R&I\\I&R\end{pmatrix},
\]

where `R` is the nine-point rook adjacency matrix. Every exterior vertex
has exactly one neighbor in each grid. The core Gram equations force
the entire list of 81 exterior signatures:

- nine signatures `(i,i)`, each once;
- 36 ordered rook-nonadjacent pairs `(i,j)`, each twice.

The two coordinates refer to different grids. The nine unique signatures
are the tips. No adjacency pattern is prescribed on the tips.

Each core vertex has degree five within the core and nine exterior
neighbors. Each exterior vertex has two core neighbors and requires
12 exterior neighbors. The frozen base model imposes all degree and
mixed common-neighbor equations. It has 3,060 eligible exterior edge
variables. An excluded exterior edge already contradicts a core-pair
or mixed equation.

The model retains the previously checked duplicate-label ordering, the
1,377 certified Hall clauses, and the 1,939 necessary cap clauses from
the first partial search. These only remove impossible graphs or choose
labels between the two vertices with identical core signatures. No
positive-semidefinite cut or orbit equality is added.

## Complete exterior pair constraints

For distinct exterior vertices `a,b`, let `c` be the number of common
core neighbors. Let `e_ab` be the exterior edge indicator, with value
zero when that edge is ineligible. Every completion must satisfy

\[
 e_{ab}+\sum_{w\notin\{a,b\}}e_{aw}e_{bw}\leq 2-c.
\]

The 3,240 unordered exterior pairs split as follows.

| Core overlap `c` | Pairs | Allowed exterior contribution |
| --- | ---: | ---: |
| 0 | 2,628 | at most 2 |
| 1 | 576 | at most 1 |
| 2 | 36 | zero |

For each possible two-edge path through `w`, a fresh Boolean variable
`p_abw` has the clause

\[
\neg e_{aw}\lor\neg e_{bw}\lor p_{abw}.
\]

A sequential-counter encoding bounds the sum of these path variables
and the optional direct edge by `2-c`. These forward implications are
sufficient. Every true path forces its variable true; conversely, a
primary edge assignment satisfying the cap extends by setting each
path variable to the exact conjunction. Reverse implications would
not change the permitted primary assignments.

For overlap two, a direct edge is ineligible. The existing 2,772 checked
duplicate-packing clauses prohibit every possible common exterior
neighbor. The builder verifies that each required clause is present
before delegating these 36 zero caps to the base formula.

There are no lazily omitted pair constraints in this version.

## Why a satisfying assignment is a complete graph

All 99 degrees are 14, and every pair involving the core already has its
exact common-neighbor count. The full cap system gives
`(A^2+A)_ij <= 2` for every distinct pair. For every row,

\[
\sum_{j\ne i}(A^2+A)_{ij}=14^2=196=2\cdot98.
\]

Every off-diagonal entry must therefore equal two. Together with the
degree condition, this is precisely

\[
A^2+A=12I+2J.
\]

The solver wrapper nevertheless recomputes all pair counts directly
before saving a candidate graph. An independent 99-vertex validation is
still required before accepting such a candidate.

## Encoding checks and model size

The builder exhaustively checks 3,069 small primary assignments for the
forward-path/cardinality encoding. The controls include zero through
four paths, an optional direct edge, and bounds zero through two.

It then checks all 3,240 exterior pairs in each of the 31 archived Hall
partial graphs, using direct adjacency bitsets independently of the
planned conjunction list. All 100,440 comparisons agree. Each saved
partial graph violates at least one complete cap, with 951 through
1,024 violating exterior pairs. These points are excluded controls,
not graph solutions.

The complete deterministic formula has:

| Quantity | Count |
| --- | ---: |
| Primary exterior edges | 3,060 |
| Inherited variables, including auxiliaries | 147,060 |
| New path variables | 226,044 |
| New cardinality auxiliaries | 405,648 |
| Total variables | 778,752 |
| Total clauses | 1,556,032 |

The CNF SHA256 is
`804adb2b64ca2129005c6a40c3f3b177e69f8644375989d0bf3718bc8c315381`.
The frozen source SHA256 is
`9f3effed8dac24589d7cf80897240bda95414bfda0bea7e8cab63706bb24bdbd`.

The parent and a separate worker reviewed path completeness, overlap-two
packing, auxiliary allocation, existential equivalence of the encoding,
and the row-sum argument. Neither review assumes a rook graph on the
tips.

## Bounded outcome

Glucose4 parsed and initialized the formula in 2.826 seconds. The
requested 180-second budget included that initialization. The solver
returned `UNKNOWN` at 180.044 seconds; final cleanup and recording
completed at 180.392 seconds. Its reported statistics were 2,033
restarts, 317,782 conflicts, 821,322 decisions, and 975,331,547
propagations.

No primary assignment satisfying the full formula was found, and no
UNSAT proof was obtained. This run leaves the two-isomorphic-grid case
open. The durable result is the audited finite completion model and
its reproducible bounded outcome.

## Reproduction

From the repository root, rebuild into temporary output files so the
archived manifest and its timing fields remain unchanged:

```sh
.venv/bin/python experiments/workspace/two_rook_iso_pair_full_caps.py build \
  --seed experiments/logs/grids-and-triangles/two-rook-iso-pair-integer.json \
  --hall-certificate experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json \
  --points experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-hall.json.gz \
  --cnf /tmp/conway-two-rook-iso-pair-full-caps.cnf \
  --manifest /tmp/conway-two-rook-iso-pair-full-caps-model.json
```

The build performs all controls and prints the CNF hash. A separate
proof-enabled bounded solve is:

```sh
.venv/bin/python experiments/workspace/two_rook_iso_pair_full_caps.py solve \
  /tmp/conway-two-rook-iso-pair-full-caps-model.json \
  --seconds 180 \
  --proof /tmp/conway-two-rook-iso-pair-full-caps.drat \
  --output /tmp/conway-two-rook-iso-pair-full-caps-result.json
```

The requested wall budget includes CNF parsing and solver initialization.
Actual elapsed time is recorded. A solver `UNSAT` return requires a
separate proof check before it supplies an exclusion. `UNKNOWN` supplies
neither a graph nor an exclusion.
