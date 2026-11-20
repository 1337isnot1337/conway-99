# Two-unit branches of the full complementary-rook joint model

The [two-row projection](complement_rook_duplicate_row_projection.md)
admits partial witnesses for all 21 possible tip pairs. This experiment
instead branches the existing
[full joint incidence/edge model](two_rook_tip_boundary_joint_integer.md).
All 252 incidence selectors and all 20,934 eligible exterior-edge
variables remain independent.

## The unchanged necessary model

For each potential exterior signature `h_s`, let `z_s` be its binary
selector. The core matrix is

\[
B=\begin{pmatrix}R&I&I\\ I&R&I\\ I&I&J-I-R\end{pmatrix}.
\]

The unchanged base formula imposes the full Gram margins

\[
\sum_s z_s h_s h_s^T=12I+2J-B^2-B,
\qquad \sum_s z_s=72.
\]

Each eligible exterior pair has a binary edge variable `c_st`, activated
only when both selectors are one. Its conditional mixed and degree
equations are

\[
\sum_{s:i\in h_s}c_{st}
=\bigl(2-((B+I)h_t)_i\bigr)z_t,
\qquad \sum_s c_{st}=11z_t.
\]

The base also forbids two neighbors of one vertex from sharing two core
points. It does not impose every exterior common-neighbor cap. Therefore
a SAT point requires a complete 99-vertex defect check; satisfiability of
this formula alone does not settle the graph problem.

## Exhaustive branches

The core pair `(R0,S4)` has Gram quota two. Its seven possible exterior
signatures are `(0,4,t)` for `t=1,2,3,5,6,7,8`, occupying selector variables
one through seven in that order. Exactly two must be selected.

The previously audited four-element core stabilizer gives eight cases
covering all 21 unordered tip pairs. Each case appends exactly the two
positive selector units shown here:

| Case | Selected tips | Added unit literals | Covered tip pairs |
| --- | --- | --- | ---: |
| 0 | `(1,2)` | `1`, `2` | 4 |
| 1 | `(1,3)` | `1`, `3` | 1 |
| 2 | `(1,5)` | `1`, `4` | 4 |
| 3 | `(1,8)` | `1`, `7` | 2 |
| 4 | `(2,5)` | `2`, `4` | 2 |
| 5 | `(2,6)` | `2`, `5` | 2 |
| 6 | `(2,7)` | `2`, `6` | 2 |
| 7 | `(2,8)` | `2`, `7` | 4 |

No bound on `a`, local matching system, exterior cap, or graph symmetry
condition is added. The original 1,156,482 variables remain unchanged.
The clause count increases from 2,575,728 to 2,575,730.

## Exact assembly and review

`experiments/workspace/complement_rook_joint_split.py` checks the frozen
base manifest, its source dependencies, the full boundary/domain/Hall
certificate hashes, and the original CNF SHA256. It independently compares
the complete ordered signature domain with the incidence module and
reconstructs all edge-variable IDs. The domain hash must match the one
saved when the base formula was built.

Each split hash is computed from the original CNF body, a header with two
additional clauses, and the two singleton clauses in their saved order.
The solver parses that same base formula and appends those same clauses.
The eight large CNFs need not be duplicated on disk.

The independent audit reconstructs the full 252-selector/20,934-edge
domain and checks every split hash directly from the unchanged base
bytes. It also reviews the 21-pair coverage, selector indexing, and proof
wrapper. Its report is
`experiments/logs/grids-and-triangles/complement-rook-joint-split-independent-audit.json`.

## Outcome verification

Each run uses a proof-enabled solver with a 30-second budget, including
CNF parsing and solver bootstrap. A SAT result is reconstructed on all
99 vertices. The checker verifies every degree and core-related common
count, then records every exterior common-neighbor defect. A point with
no defects is held for separate graph validation.

An UNSAT result remains provisional until its proof is independently
checked. The wrapper
`experiments/workspace/complement_rook_joint_split_certificate.py`
retains the proof's input clauses and lemmas. Replay rebuilds the original
full base formula from its frozen source and domain certificates, appends
the exact two units, compares the split hash, checks retained-clause
inclusion, and verifies the retained DRAT proof.

The result and manifest prefix for case `i` is
`experiments/logs/grids-and-triangles/complement-rook-joint-split-i`.

## Bounded outcomes

All eight runs returned UNKNOWN. None produced a SAT point or an UNSAT
proof, so no tip-pair case is excluded.

| Case | Actual return time, seconds | Peak process memory, KiB |
| --- | ---: | ---: |
| 0 | 30.006 | 677,968 |
| 1 | 30.024 | 677,832 |
| 2 | 30.488 | 677,960 |
| 3 | 30.081 | 678,004 |
| 4 | 30.301 | 676,808 |
| 5 | 30.352 | 676,944 |
| 6 | 30.024 | 677,828 |
| 7 | 30.016 | 677,956 |

The largest process peak was about 662 MiB. The elapsed times record the
actual interrupt return, including small overruns beyond the requested
30 seconds. The saved manifests and independent audit establish which
formulas were tested; these bounded UNKNOWN outcomes leave every case
unresolved. The prepared proof wrapper was not invoked because no UNSAT
proof was obtained.
