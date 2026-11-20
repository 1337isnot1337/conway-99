# Six-cut LP: exact positive point

The single authorized LP continuation has an independently checked rational
point. Its common denominator is 2,594,289,631, and its max-min variable is
28,189,330 / 2,594,289,631. All 1,102 surviving selectors are positive. The
112 previously proved zero coordinates remain zero.

The accepted model has 1,103 variables, 167,121 rows, and 10,769,766 nonzero
coefficients. It preserves the complete five-cut prefix and appends only

\[
x_{23}+x_{260}+x_{399}+x_{403}+x_{406}+x_{761}+x_{762}
+x_{763}+x_{764}+x_{765}+x_{803}\le1.
\]

This row has a complete branch-box proof. The other five appended rows retain
their Gram-parity proofs. The distinct proof types remain explicit in the
registry and in exact acceptance.

## Numerical proposal and exact acceptance

The numerical stage made one native call, taking 1.1125 seconds. It found no
uninserted cover violation in the full pool. No cover was added to the
initial active system. This numerical outcome was only a proposal.

The exact stage reconstructed the saved basis through one 293-square
rational solve. It then checked all 167,121 extended rows, all 2,271 original
native rows, all 178,533 original coordinate covers, every fixed zero, and
all six appended cuts. The separate cold stage repeated the full exact
point checks and replayed the saved numerical prefix without an optimizer
or a second linear solve.

The numerical, exact, and cold children all exited successfully and were
reaped. The whole production owner took 29.2625 seconds. The subsequent
bindings-only verification passed. There was no retry.

The authoritative point is
`experiments/logs/grids-and-triangles/rook-case4-box-cut-lp-run01/exact/candidate.json`,
SHA256 `7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9`.
Its independent acceptance is the adjacent `cold.json`, SHA256
`b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317`.
The candidate's own historical status says that replay was pending; this
separate cold record supplies the completed acceptance.

## Frozen clique family

A separate integer-only contraction evaluated all 1,216 previously proved
maximal-clique capacities at the new exact point. Every inequality passes.
Four are tight, with stored indices 45, 80, 326, and 1001. Index 80 is the
11-term capacity appended in this continuation.

The clique family was already independently reconstructed from the 191
accepted final branch boxes. This evaluation reused that proof and did not
repeat branch propagation, clique enumeration, model construction, or an
optimizer. The evaluation record is
`experiments/logs/grids-and-triangles/rook-case4-box-cut-lp-clique-evaluation01.json`,
SHA256 `d5a3651a38f6cf68159dca6ef6485341eab9acfef8b85b112e414012e2774426`.

## Scope

The point proves feasibility of this strengthened real selector relaxation.
It supplies neither a Boolean incidence assignment nor a graph. It does not
establish membership in the convex hull of the 191 branch boxes. The complete
saved clique family supplies no additional violated row at this point.

The generic box-hull separator, a new parity search, and any further LP
continuation are outside this completed run. The case remains open.
