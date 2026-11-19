# Complete fractional model for the F0 component-zero stratum

## Status and scope

This is a preparation plan, not an executed model or an infeasibility result. Workspace access failed after the allocated-lazy run's exact cold replay passed. The terminal run remains UNKNOWN. Its captured record is in `experiments/logs/session-ab2f/f0-allocated-recovery-status.json`.

The conditional setting is a globally prism-free, F-free SRG(99,14,1,2) whose triangle shell splits into two 18-vertex components. Fix the first component to the already classified component zero. The model leaves the second component and its fiber alignment free. It also leaves all first-component incidence selectors free.

The frozen domain `f0-exterior-row-domains02.json.gz` contains 480 admissible triples and 68,394 possible undirected exterior edges. The latest allocated-lazy transcript contains 3,948 individual row cuts and 456 signed shared-edge cuts. Those 4,404 cuts remain necessary conditions; no terminal candidate is fixed or excluded by an unproved visitation clause.

## Variables and equations

Index the triples by \(a\). Let \(h_a\in\{0,1\}^{18}\) be a triple's incidence column, \(A_1\) the first component's adjacency matrix, and

\[
q_a=2\mathbf 1-h_a-A_1h_a.
\]

Every domain column has weight three, every \(q_a\) is nonnegative, and \(\mathbf 1^Tq_a=24\). These identities must be rechecked from the frozen core rather than copied into the implementation as assumptions.

Introduce one selector \(x_a\in[0,1]\) for every triple and one variable \(y_{ab}=y_{ba}\) for every eligible unordered pair. Impose

\[
0\le y_{ab}\le x_a,\qquad y_{ab}\le x_b.
\]

There are 68,874 full variables before taking orbits. No edge variable is introduced for an ineligible pair or a loop.

The full first-component Gram equations are

\[
\sum_a h_{ai}h_{aj}x_a=G_{ij}\qquad(1\le i\le j\le18),
\]

where \(G\) is reconstructed from the fixed 21-vertex core. Include the population equation \(\sum_a x_a=60\), even though the diagonal Gram sum already implies it.

For every signature \(a\) and core point \(i\), impose

\[
\sum_{b:\{a,b\}\ {\rm eligible}}h_{bi}y_{ab}=q_{ai}x_a.
\]

This gives 8,640 mixed equations. The equation remains correct when a signature is absent because activation then forces every incident edge to zero.

Summing its 18 entries gives

\[
3\sum_b y_{ab}=24x_a,\qquad
\sum_b y_{ab}=8x_a.
\]

Thus degree eight follows exactly; adding degree rows would be redundant.

Retain all 90 component motif inequalities \(x_a+x_b\le1\). Add all 4,404 exact terminal selector inequalities. Also inspect the twelve earlier weighted row inequalities represented by the unchanged base's 444 primary clauses; they are not to be silently dropped or assumed to be part of the later registry.

Before deduplication, the listed rows give 150,094 rows, plus the twelve earlier weighted rows if they are distinct: 171 Gram, one population, 8,640 mixed, 136,788 activation, 90 motif, and 4,404 terminal selector rows. Bounds are separate. These are combinatorial input counts, not final quotient counts.

## What the joint model adds

Each previous row-box test selected a different possible neighborhood independently. The new variables make an undirected edge appear with the same value in both endpoint equations. Every selector remains free, so a fixed-incidence obstruction cannot remove an unrelated incidence by accident.

For raw potential inequalities, this model already gives the algebra behind the existing cuts. If \(v_a\) is an integer row potential, then

\[
(v_a\cdot q_a)x_a
=\sum_b(v_a\cdot h_b)y_{ab}
\le\sum_b\max(v_a\cdot h_b,0)x_b.
\]

Likewise, summing endpoint potentials and allocating each positive edge weight to a chosen endpoint gives every raw signed shared-edge inequality. Their explicit inclusion preserves the certified registry and can help a numerical solver.

The implementation must distinguish those raw linear rows from any coefficient capping, threshold rounding, or predicate normalization that used Boolean selectors. Such a normalized inequality may still be a valid additional linear relaxation of actual graph incidences, but its continuous row must not be identified with the raw potential inequality without proof.

## Exact orbit reduction

The frozen component has twelve verified relabelings. They act on the 18 core points, the 480 triples, and the eligible unordered edges. The existing triple partition has 42 orbits: 38 of size twelve and four of size six.

For each action \(g\), independently check

\[
h_{g(a),g(i)}=h_{a,i},\qquad
q_{g(a),g(i)}=q_{a,i},
\]

as well as exact core adjacency, Gram, edge-domain, and motif preservation. Check identity, composition, inverses, and the complete twelve-element action set.

Averaging a feasible invariant linear system over these relabelings yields a point constant on each variable orbit. This is convex averaging of necessary conditions. It assumes no automorphism of a completed 99-vertex graph.

Use one variable for each selector orbit and one for each exactly enumerated edge orbit. In every original row, replace variables by their orbit IDs and add integer coefficients. Keep a map from every original row to its quotient row and its positive normalization factor. The population equation uses the selector orbit sizes as coefficients. Do not divide by orbit sizes implicitly.

The edge-orbit count is not yet computed. Check it independently by Burnside's formula. For an unordered pair, a fixed edge can have both endpoints fixed or have its endpoints exchanged; both possibilities must be counted.

There is a possible registry issue: earlier deduplication may use equivalent Boolean threshold predicates rather than identical continuous coefficient rows. Therefore test literal row transport closure. If a row's transported version is absent, explicitly take the verified group closure of the necessary rows. Every transported version has the same orbit-aggregated coefficients, so this does not enlarge the quotient matrix. In that event the quotient represents the invariant closure of the stated full model, rather than an unqualified equivalence to an unclosed fractional row list.

## Preparation and controls

The preparation should contain:

- Frozen domain, source, terminal-registry, and action hashes.
- Full variable and row counts, orbit counts, integer coefficient ranges, and sparse matrix sizes.
- Exact reconstruction of all 171 Gram positions, all mixed targets, every activation row, every motif row, and every selector cut.
- Complete row-to-quotient maps and checks that a quotient vector lifts literally to each full row.
- A separate equality between the original and quotient evaluations on deterministic integer and rational test vectors.
- Small feasible activated-edge controls for averaging and lifting, including an action that exchanges an edge's endpoints.
- An exact original-count/population check and finite-box certificate-sign controls.
- No optimizer call during preparation.

Any numerical scaling must be strictly positive and recorded. The exact integer matrix remains the authority for every certificate. Resource estimates should precede a proposal for one bounded, single-thread query.

## Exact acceptance gates

A feasible numerical proposal is accepted only after rational reconstruction and exact verification. Lift the quotient values to all 68,874 full variables and check every original equality, inequality, and bound, including the registry rows and any explicit group closure. An exact feasible fractional point is not a graph and does not settle completion.

For an infeasibility certificate, write the quotient system as

\[
Az=b,\qquad Cz\le d,\qquad 0\le z\le1.
\]

Take exact unrestricted equality multipliers \(\lambda\) and exact nonnegative inequality multipliers \(\mu\). Let

\[
w=A^T\lambda+C^T\mu.
\]

Every feasible point obeys

\[
\lambda^Tb+\mu^Td
\ge w^Tz
\ge\sum_j\min(w_j,0).
\]

Thus an exact strict inequality

\[
\lambda^Tb+\mu^Td-\sum_j\min(w_j,0)<0
\]

is a finite-box Farkas certificate. Equivalently, add exact upper-bound deficits \(u_j=\max(0,-w_j)\), require \(w+u\ge0\), and check a negative combined right-hand side. The multipliers and deficit sums must be evaluated as integers or rationals. A backend status or a floating negative value is insufficient.

An exact certificate for the quotient excludes the component-zero stratum only after the averaging/transport proof has passed. No conclusion about other shell components or the full Conway problem follows.

## Pending work

Workspace recovery is required to finish the allocated-run note and publication manifest, recover the terminal cold-replay hash, inspect the bundle restoration result, and build the complete fractional specification. The next production query is held until the coordinator reviews the source, complete domain, orbit reduction, controls, and exact certificate interface.
