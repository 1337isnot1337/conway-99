# A rook-near tip edge survives all local tip tests

The nine-tip Hall constraints, all tip common-neighbor caps, and the
necessary matrix inequality `3I-R+J-2Z >= 0` do **not** force all tip
edges to join rook-nonadjacent labels.

An exact counterexample is the graph with edges

\[
\{0,1\},\quad\{0,4\},\quad\{1,3\},
\]

and no other edges. It is a three-edge path and five isolated vertices.
The edge `{0,1}` is rook-adjacent. The other two edges are rook-nonadjacent.
This is a feasible necessary nine-tip projection, not a completion of
the two-grid core or a graph on 99 vertices.

## Direct checks

The only nonzero canonical Hall masks occur at tips `0,1,3,4` and are
respectively `9,18,64,128`. Each is one of the 103 admitted masks with
an explicit integral flow in the frozen Hall certificate. The other
five masks are zero.

For every pair of tips, the number of common tip neighbors plus the
adjacency indicator is at most one. Thus every required upper bound
of two holds.

The matrix

\[
H=3I-R+J-2Z
\]

is positive definite. The saved exact rational congruence reduces it
to the positive diagonal

\[
4,\ 3,\ 4,\ \frac{41}{12},\ \frac{138}{41},\
\frac{17}{6},\ \frac{1220}{391},\ \frac{924}{305},\ \frac2{11}.
\]

Replay checks the full congruence and the invertibility of its rational
change of basis, rather than checking approximate eigenvalues.

## The small SAT model

The separate model has 36 edge variables and 3,394 clauses:

- 1,377 transported Hall-mask clauses.
- 756 clauses forbidding an edge and two common neighbors.
- 1,260 clauses forbidding three common neighbors.
- One unit clause requiring `Z_01=1`.

The last condition represents a rook-near edge without loss of
generality because the rook automorphism group is transitive on rook
edges. No PSD assumption was imposed in the SAT formula; PSD was
checked exactly on the resulting point.

Glucose4 returned the displayed point in approximately 0.005 seconds.
The point was then checked directly against every CNF clause, the
geometric Hall masks, all common-neighbor caps, and the rational PSD
certificate. The empty graph and the full rook-complement graph are
positive controls for the model with the unit clause removed. A
256-case Boolean control verifies the complete cap encoding.

Because the result is SAT, the checked assignment is the certificate;
no UNSAT claim or DRAT proof is produced.

## Files and replay

- Source: `experiments/workspace/two_rook_tip_near_edge.py`.
- Formula: `experiments/workspace/two-rook-tip-near-edge.cnf`.
- Point and exact PSD certificate:
  `experiments/logs/grids-and-triangles/two-rook-tip-near-edge.json`.
- Run and replay logs use the same stem.

```sh
python experiments/workspace/two_rook_tip_near_edge.py --replay \
  --hall experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json \
  --cnf experiments/workspace/two-rook-tip-near-edge.cnf \
  --proof experiments/workspace/two-rook-tip-near-edge.drat \
  --output experiments/logs/grids-and-triangles/two-rook-tip-near-edge.json
```

The reserved `--proof` path is not read for this SAT replay and no file
at that path is needed. Replay uses only the standard library and the
two frozen exact helper modules. Solving again requires PySAT.
