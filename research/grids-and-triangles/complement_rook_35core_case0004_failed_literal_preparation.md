# Case4 positive-assumption propagation preparation

The complete forward closure found no assignments beyond the 14 known
absent columns. This package prepares a bounded failed-literal test on
the same original constraints. It contains no production probe result.

## Complete automorphism check

The 35-core has exactly eight vertices of degree four and one vertex of
degree fourteen. Thus every core automorphism preserves the eight local
vertices, their 27-vertex complement, and the distinguished root R0.

Inside the 27-core, define a relation by pairs with exactly two common
neighbors in that core. Its relation degrees are eight at each vertex of
R or S, and four at each vertex of T. Therefore T is identifiable. Each
T vertex has exactly two neighbors outside T, namely its matched R and S
vertices. These nine pairs are also identifiable.

An automorphism of T preserves its complementary rook graph and hence
the rook graph itself. The six maximum rook cliques form two families of
three disjoint lines. Permuting the lines within both families and
optionally exchanging the families gives all 72 rook automorphisms.

After one of these point permutations is chosen, an automorphism of the
27-core can only swap the R/S endpoints independently at each point.
Preservation of the parallel edges between rook-adjacent points forces
these swaps to agree along every rook edge. The rook graph is connected,
so the swap is global. The full 27-core group consequently has exactly
144 elements.

Fixing R0 leaves eight possibilities. The preparation checks all eight
on the local triples and their matching. Seven fail already because a
local triple has no image among the eight local vertices. Only the
identity extends. The full 35-core group is therefore trivial, and all
1,214 attachment columns have singleton orbits. No symmetry reduction is
used in the proposed probes.

## Exact priority list

There are 1,200 initially free columns. For each column, the preparation
forms the union of all columns that would be forced absent by selecting
it in an original quota-one or at-most-one row. The union excludes the
14 already absent columns. There are 1,853 such rows, including the
original Gram quota-one rows, signature capacities, triple capacities
and Gram conflicts.

Candidates are ranked by descending size of this exact conflict union,
then by descending number of original-row occurrences, then by column
index. The conflict counts range from seven to 185. The first five
candidates are 556, 554, 1078, 972 and 443. This priority is a search order;
it asserts no new constraint or exclusion.

The prepared batch covers at most the first 32 candidates. The full
1,200-column priority list is saved. Untested candidates remain open.

## Failed-literal proof rule

For a selected candidate \(a\), the probe adds the explicit assumption
\(x_a=1\). It may also use negative units already proved by earlier
probes in this batch. It retains all original integer rows, all complete
registered covers and the 14 initial proved units.

The unchanged exact propagator then derives a sequence of assignments.
The separate reason checker replays the sequence against these explicit
premises. If it reaches a checked contradiction, the assumption is
impossible and \(x_a=0\) is a new necessary unit. Each use of a previous
unit refers inductively to an earlier checked contradiction.

If propagation ends without a contradiction, none of its conditional
assignments becomes a global unit. A completed conditional fixed point
is not a satisfying incidence witness. An incomplete trace gives no
failed-literal conclusion and stops the batch.

Tiny controls check this induction on a formula with a unique satisfying
point, including two successive learned units. A separate guarded-cover
control proves a failed positive literal using the complete clause
semantics. These controls run no solver.

## Resource and coverage limits

The proposed limits are 32 probes, five seconds per propagation pass and
a cooperative 60-second batch budget. The batch budget includes input
reconstruction, discovery, exact reason checking and durable checkpoints.
It stops at the first incomplete trace, exhausted budget or error.

The original one-sweep forward pass took 0.259 seconds; its full reason
and fixed-point check took 1.752 seconds. Thirty-two repetitions of those
measured stages would take about 64.35 seconds before other overhead.
Assumptions can change the work substantially. The preparation therefore
does not promise to finish all 32 probes under the batch budget.

Each completed probe saves its assumption, prior proved units, complete
trace, exact replay result and timing. The final record distinguishes a
completed 32-column prefix from partial coverage. Even a completed prefix
leaves 1,168 candidates outside this batch. There is no native presolve
premise, solver call or automatic retry.
