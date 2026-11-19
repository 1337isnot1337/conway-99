# Joint incidence and edge checks at the eighteen-edge tip boundary

The finite census in `two_rook_tip_rook_boundary.md` reduces the
eighteen-edge tip boundary to two labelled-core orbits. This note tests
their complete incidence domains. It does not fix a 72-column incidence
witness or impose an automorphism of a completion.

The 188-signature orbit, represented by `3679836361`, has a directly
verified UNSAT certificate. The wrapper below reconstructs its model
and checks the retained proof. The complement-rook orbit, `3943553752`,
returned **UNKNOWN** after 205.562 seconds on a requested 200-second
budget. It remains open. Excluding the first orbit does not exclude
the complement-rook case.

The coordinator independently rebuilt the full first-case CNF, matched
its hash, checked all 3,667 retained clauses against that formula, and
verified the trimmed DRAT proof. That replay is archived beside the
direct checker log.

## Core and full incidence domain

The 27-point adjacency matrix is

\[
B=\begin{pmatrix}R&I&I\\I&R&I\\I&I&Z\end{pmatrix},
\qquad G=12I+2J-B^2-B.
\]

Here `R` is the fixed rook graph and `Z` is a labelled rook graph from
the boundary census. The identity matchings into `Z` are not assumed
to preserve rook adjacency. Each core vertex has degree six within the
core and needs eight exterior neighbors.

Every remaining vertex has a three-point signature, one point in each
rook grid. Signatures cannot repeat, since a repeated signature would
give two vertices three common neighbors. For every complete-domain
signature `s`, introduce a Boolean selector `z_s`. Exactly 72 selectors
must be true, and the Gram equalities are

\[
\sum_s h_s h_s^T z_s=G,
\]

where `h_s` is the signature indicator. All diagonal and off-diagonal
entries are imposed. Identical cardinality requests are deduplicated.

The builder reconstructs and checks the entire finite census and the
exported domains before encoding either case. It retains all 188 or
252 selectors. In the 188-signature case, the archived binary margin
propagation adds 16 positive and 32 negative unit clauses. These are
deductions from the Gram equations, not choices of incidence.

## Joint exterior adjacency

For each signature, define

\[
d_{is}=2-((B+I)h_s)_i.
\]

An edge between distinct signatures `s,t` is eligible only when they
share at most one core neighbor and every point of either signature
has positive mixed demand for the other. Both directions are checked.
All eligible edges are retained, including edges incident to selectors
later forced to zero.

Each eligible edge has a Boolean variable `a_st`, with activation
clauses `a_st => z_s` and `a_st => z_t`. For every signature `t`, impose

\[
\sum_{s:i\in s}a_{st}=d_{it}z_t,
\qquad \sum_s a_{st}=11z_t.
\]

The second equality is the exterior degree, since a selected vertex
already has three core neighbors. An unselected signature has no
incident edges.

The conditional counter uses an unconditional upper bound and a
selector-guarded lower bound. Activation makes this exactly equivalent
to the displayed equality. If a quota exceeds the number of available
edges, the selector is forced false. The builder exhaustively checks
14,840 assignments of this helper, including quotas zero and eleven.

Finally, for each core pair `i,j` and each exterior candidate `t`, at
most one neighbor of `t` may have a signature containing both `i,j`.
Otherwise the two such neighbors would have three common neighbors:
`i`, `j`, and `t`. These pair-packing clauses are necessary regardless
of whether the two neighbors are adjacent.

This is an integer relaxation of full graph completion. A satisfying
point must still pass all 99-vertex common-neighbor equations. The
wrapper performs that check and reports a defective point as partial.
No cap clauses are added lazily in these initial runs.

## Deterministic model sizes

| Core representative | 3679836361 | 3943553752 |
| --- | ---: | ---: |
| Labelled core orbit | 18 | 1 |
| Signature selectors | 188 | 252 |
| Eligible exterior edges | 12,010 | 20,934 |
| Total Boolean variables | 649,302 | 1,156,482 |
| Clauses | 1,424,532 | 2,575,728 |
| Pair-packing clauses | 81,904 | 186,372 |
| Forced positive selectors | 16 | 0 |
| Forced negative selectors | 32 | 0 |

The first full CNF SHA256 is
`f4a19557844bb29eb643791f818fb505263beac7c61ec570a01682e27e863cd4`.
The second is
`4beaccae679e2014ab0a3cf105ca1f65f326b6453ed6502d7e2d65cbede2a162`.

The source is
`experiments/workspace/two_rook_tip_boundary_joint_integer.py`, SHA256
`8fae0665de20ff2f99ab5aa78c47cfc6481c7abd4bc1a2b903c986a2a3b44f49`.
The source remains unchanged between construction and proof generation.
Each model manifest binds the source dependencies, exported domains,
boundary certificate, Hall certificate, and full CNF hash.

A separate worker independently counted both eligible edge domains and
reviewed the actual builder. The audit checked domain completeness,
Gram and population equations, certified units, activation, conditional
counters, and packing. It found no additional symmetry assumption or
fixed incidence restriction.

## Certificate for representative 3679836361

The proof-enabled Glucose4 solve returned UNSAT at 4.127 seconds,
including parsing and initialization. Its requested budget was 200
seconds. It reported 1,270 conflicts, 13,462 decisions, and 3,886,625
propagations. No binary point or lazy cut preceded the result.

Direct `drat-trim` checking of the frozen full CNF and raw proof returned
`VERIFIED` in 2.951 seconds. Trimming retained 3,667 input clauses and
467 lemmas, with 47,391 resolution steps and no RAT lemmas. The saved
trimmed proof has 4,462 lines, including deletion lines.

The retained core and proof are bound by
`experiments/workspace/two-rook-tip-boundary-joint-3679836361-certificate.json`.
The separate wrapper rebuilds the full domain and formula, checks that
every retained input clause occurs in the regenerated formula, and
then checks the trimmed proof. It therefore does not trust an isolated
UNSAT core without verifying its inclusion in the necessary model.

```sh
.venv/bin/python experiments/workspace/two_rook_tip_boundary_joint_certificate.py \
  experiments/workspace/two-rook-tip-boundary-joint-3679836361-certificate.json \
  --drat-trim /path/to/drat-trim
```

The exact coordinate transports in the boundary census extend this
representative's exclusion to its 18 labelled members. This statement
does not assume any automorphism of the hypothetical 99-vertex graph.

## Complement-rook outcome

The second formula initialized in 3.629 seconds. Glucose4 returned
`UNKNOWN` at 205.054 seconds, after the requested 200-second budget;
the recorded elapsed time includes the solver's interruption delay.
Final cleanup and recording completed at 205.562 seconds. The solver
reported 705 restarts, 107,685 conflicts, 358,561 decisions, and
913,610,201 propagations.

No binary point and no UNSAT proof were obtained for this case. There
is consequently no exclusion of the entire eighteen-edge boundary.
The finite census and checked first-core certificate leave only the
complement-rook labelled type at that boundary. This conditional
restriction does not apply to tip graphs with fewer than eighteen
edges.

## Rebuild either model

Replace the representative and temporary filenames for the other case.
Use temporary manifests when replaying, so archived run bindings remain
unchanged.

```sh
.venv/bin/python experiments/workspace/two_rook_tip_boundary_joint_integer.py build \
  --domains experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-domains.json \
  --boundary-certificate experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-certificate.json \
  --hall-certificate experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json \
  --representative 3679836361 \
  --cnf /tmp/conway-boundary.cnf \
  --manifest /tmp/conway-boundary-model.json

.venv/bin/python experiments/workspace/two_rook_tip_boundary_joint_integer.py solve \
  /tmp/conway-boundary-model.json \
  --seconds 200 \
  --proof /tmp/conway-boundary.drat \
  --output /tmp/conway-boundary-result.json
```

Both timed runs save their exact terminal status under
`experiments/logs/grids-and-triangles/two-rook-tip-boundary-joint-*`.
`UNKNOWN` is not an exclusion, and a partial binary point is not a
99-vertex strongly regular graph.
