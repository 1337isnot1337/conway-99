# One local matching edge is forbidden after the bounded sweep

The 28 matching choices for the first complementary-rook local set have
five checked exclusions and 23 unresolved cases. The local set is not
excluded. Four of the checked exclusions do prove a smaller conditional
statement: if all eight specified local signatures occur, the vertices
with original signature indices 18 and 26 cannot be adjacent.

The full record is
[progress.json](../../experiments/logs/grids-and-triangles/complement-rook-35core-first-local-sweep01/progress.json).
The independently replayable
[matching-cover certificate](../../experiments/logs/grids-and-triangles/complement-rook-35core-matching-cover.json)
records every outcome, the complete matching cover, and 144 transported
versions of the conditional restriction.

## Scope and outcomes

The local signatures, in local vertex order, are

\[
L=(0,1,9,10,18,20,26,27).
\]

The old 27-core Gram equations alone admit this set. The separate
[Gram-only control](complement_rook_35core_local_incidence_control.md)
supplies an exact 72-column witness with $a=10$. It fixes no matching.

The [case-zero query](complement_rook_35core_case0000.md) returned UNSAT.
The remaining 27 cases then received fresh proof-enabled queries with
ten seconds requested per solver, including bootstrap. Direct and cold
DRAT checks had separate 60-second limits after an UNSAT result.
No new selector assumptions, learned constraints, or symmetry conditions
were added to those formulas.

The final verified cases are

\[
\{0,1,3,8,21\}.
\]

Each has a direct DRAT check and a cold reconstruction of the full domain
and CNF, retained-input inclusion, and retained DRAT replay. Every other
case returned UNKNOWN. No 35-core incidence witness was found in this
bounded run. UNKNOWN is not an exclusion or evidence of infeasibility.

The solver limits use cooperative interruption. Actual return times are
recorded per case and sometimes exceeded the requested ten seconds under
execution contention. No subsequent solver sweep is part of this
checkpoint.

## Matching structure

Let $Q$ pair the two local signatures with the same $S$-label. Its pairs
are $(0,1),(2,3),(4,5),(6,7)$. The chosen graph matching $M$ is disjoint
from $Q$, so $Q\cup M$ is either one eight-cycle or two four-cycles.

The following table covers all 28 cases. A projected edge records the
two $S$-labels of the endpoints of an edge of $M$. The four labels are
$4,5,7,8$ in the rook grid.

| Structure | Cases | Checked exclusions | UNKNOWN |
|---|---|---|---|
| One eight-cycle; all four projected edges rook-adjacent | 0, 8 | 0, 8 | None |
| One eight-cycle; its rook-adjacent projected pairs are $(4,5),(7,8)$ | 1, 21 | 1, 21 | None |
| One eight-cycle; its rook-adjacent projected pairs are $(4,7),(5,8)$ | 4–7, 11–18, 22–25 | None | All 16 |
| Two four-cycles with $Q$-pair labels $(4,7)$ and $(5,8)$, both rook-adjacent | 2, 3, 9, 10 | 3 | 2, 9, 10 |
| Two four-cycles with $Q$-pair labels $(4,8)$ and $(5,7)$, both rook-nonadjacent | 19, 20, 26, 27 | None | All four |

The certificate includes the individual cycle orders and all projected
edges. Cycle type alone does not separate the excluded and unresolved
cases. In particular, case 3 shares its coarse two-four-cycle type with
three UNKNOWN cases.

A separate exploratory canonicalization found 28 different uncolored
35-core certificates. It supplied no isomorphism transfer between these
matching cases. The conditional edge proof below does not depend on that
negative scout.

## Complete cover for a conditional forbidden edge

Local vertices 4 and 6 have original signatures

\[
18=(0,7,5),\qquad 26=(0,8,6).
\]

Among all 28 eligible matchings, the edge $\{4,6\}$ occurs in exactly
cases $0,1,8,21$. Their four matchings are:

| Case | Matching on local vertices |
|---|---|
| 0 | $(0,2),(1,5),(3,7),(4,6)$ |
| 1 | $(0,2),(1,7),(3,5),(4,6)$ |
| 8 | $(0,5),(1,2),(3,7),(4,6)$ |
| 21 | $(0,7),(1,2),(3,5),(4,6)$ |

All four are excluded by checked incidence proofs. The cover verifier
independently generates all 105 perfect matchings on eight vertices,
retains exactly the 28 using eligible source pairs, and verifies this
four-case edge cover.

In an actual strongly regular graph, the neighborhood of $R_0$ induces
seven disjoint edges. Its six known old-core neighbors already form three
of those edges. If the eight signatures in $L$ occur, they are all its
remaining neighbors and must form one of the enumerated matchings.
Therefore they cannot contain the edge between signatures 18 and 26.

Let $z_s$ denote an original signature selector and $e_{18,26}$ its
exterior adjacency variable. The implication is

\[
\left(\bigwedge_{s\in L}z_s\right)\Longrightarrow \neg e_{18,26}.
\]

Endpoint activation gives $e_{18,26}\le z_{18},z_{26}$. The two endpoint
selectors can therefore be removed from the antecedent:

\[
e_{18,26}+
\sum_{s\in\{0,1,9,10,20,27\}}z_s\le6.
\]

The verifier checks this reduction on all 320 Boolean assignments that
satisfy endpoint activation. In the frozen primary-variable ordering,
the clause is

```text
-3177 -28 -21 -11 -10 -2 -1 0
```

This is a necessary restriction for actual graph completions. The old
weak joint CNF omitted some exterior common-neighbor constraints. The
new clause is not asserted to be a logical consequence of that older
CNF alone.

## Explicit transported clauses

The 144 checked core relabelings give 144 distinct seven-literal clauses.
The local set has a trivial stabilizer within this group. There are eight
images at each of the eighteen $R$- or $S$-core points.

Every image records the full core-vertex and signature transport. The
verifier checks core adjacency, signature incidence, the complete
28-matching image cover, and the four excluded matchings containing the
transported edge. It does not impose any automorphism on the unknown
99-vertex graph.

The 144 clauses have equal length and are distinct, so none subsumes
another within this family. No claim of semantic irredundancy relative
to all other graph constraints is made. The
[CNF fragment](../../experiments/logs/grids-and-triangles/complement-rook-35core-matching-cover-clauses.cnf)
uses the frozen 252-selector/20,934-edge primary variable ordering.

The verifier source is
[complement_rook_35core_matching_cover.py](../../experiments/workspace/complement_rook_35core_matching_cover.py).
Ordinary replay reconstructs all coverage, input bindings, cycle types,
Boolean controls, and clause transports without a solver. The optional
proof mode cold-rebuilds and rechecks all five proof dependencies.

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_matching_cover.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-35core-matching-cover.json \
  --clauses experiments/logs/grids-and-triangles/complement-rook-35core-matching-cover-clauses.cnf \
  --replay \
  --verify-proofs experiments/logs/grids-and-triangles/complement-rook-35core-matching-cover-independent-proofs01 \
  --drat-trim /tmp/conway99-drat-trim/drat-trim
```
