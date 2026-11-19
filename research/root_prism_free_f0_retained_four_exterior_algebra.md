# What the retained four-exterior rows still require

The retained cross-quota case has a precise unresolved condition. The original two-site mixed equations rewrite the four-exterior inequality as
\[
                 y_{bc}\leq A_b+D_c,
\tag{1}
\]
where \(A_b\) counts b's neighbors containing i but not j, and \(D_c\) counts c's neighbors containing j but not i. When both cross quotas are 2, the same equations and endpoint bounds allow both sums to be zero while \(y_{bc}=1\).

This note gives an explicit obstruction to deriving the row from that reduced system, an exact alternative encoding, and a separate consequence of the spectral pair theorem. It does not prove that the retained rows are nonredundant in the complete literal model. No new census, optimization, or graph-completion search was performed.

## 1. Exact quota identities

Fix an original four-exterior case. The core vertices i,j are nonadjacent and have no common neighbor in the fixed 21-core. Let
\[
 T=\{a:i,j\in h_a\}.
\]
The central signatures satisfy \(i\in h_b\), \(j\notin h_b\), \(j\in h_c\), \(i\notin h_c\), and
\[
 q_{bi}=q_{cj}=1,\qquad q_{bj}=q_{ci}=2.
\]
Write \(y=y_{bc}\). All sums below are over original eligible exterior edges. Previously proved zero edges contribute zero, so the all-T sums agree with the live-star sums in the original row.

Partition the neighbors at each center by membership in the two incidence columns:

| Neighbor class | At b | At c |
|---|---|---|
| Contains both i,j | \(L\) | \(R\) |
| Contains i, not j | \(A\) | \(y+C\) |
| Contains j, not i | \(y+B\) | \(D\) |
| Contains neither | \(W\) | \(Z\) |

The four original mixed equations are
\[
 L+A=x_b,\qquad L+y+B=2x_b,
\]
\[
 R+y+C=2x_c,\qquad R+D=x_c.
\tag{2}
\]
The original exterior-degree equations give
\[
 W=5x_b+L,\qquad Z=5x_c+R.
\tag{3}
\]
Consequently the exact target slack is
\[
 \Delta=y+L+R-x_b-x_c=y-A-D.
\tag{4}
\]
The remaining two class sums are
\[
 B=x_b-y+A,\qquad C=x_c-y+D.
\tag{5}
\]

Endpoint activation gives \(0\leq y\leq\min(x_b,x_c)\). Therefore, once the own-site equations and nonnegativity are satisfied, (5) does not impose a positive lower bound on either A or D.

More precisely, in this aggregate system, for any fixed
\[
 0\leq x_b,x_c\leq1,\qquad 0\leq y\leq\min(x_b,x_c),
\]
the maximum target slack is exactly y. The upper bound follows from (4). Equality is attained by
\[
 L=x_b,\ R=x_c,\ A=D=0,\ B=x_b-y,\ C=x_c-y,
\]
\[
 W=6x_b,\qquad Z=6x_c.
\tag{6}
\]
All these quantities are nonnegative and satisfy (2)-(3).

Thus reweighting these four mixed equations and the two degree equations cannot supply the missing inequality (1). This conclusion allows arbitrary signed multipliers on the displayed equalities; it is stronger than failure of just the two previously tried sums. Extra information must couple the central edge to the unused i-only and j-only neighbor sums.

The same calculation explains why the cross-quota-one cases were removable. Replacing the second equation of (2) by \(L+y+B=x_b\), or the third by \(R+y+C=x_c\), supplies exactly the missing unit of central-edge coverage.

## 2. An explicit binary obstruction for the reduced system

The following construction also satisfies every exterior triangle-cover upper inequality. It shows that such upper inequalities and the indicated Gram counts do not repair the aggregate gap by themselves.

Take vertices
\[
 U=\{u_0,\ldots,u_{29}\},\qquad V=\{v_0,\ldots,v_{29}\},
\]
with subscripts modulo 30. Join \(u_r\) to \(v_s\) exactly when
\[
             s-r\pmod{30}\in\{0,1,\ldots,7\}.
\tag{7}
\]
This is a simple 8-regular bipartite graph on 60 vertices. Set every vertex selector to one and each edge variable to its adjacency value. All endpoint bounds and all 60 degree-eight equations hold.

Define the two partial incidence columns by
\[
 I=\{u_{29},v_7,v_0,u_1,\ldots,u_7\},
\]
\[
 J=\{u_{29},v_7,u_0,v_8,\ldots,v_{14}\}.
\tag{8}
\]
They have
\[
 |I|=|J|=10,\qquad |I\cap J|=2.
\tag{9}
\]
These are the relevant diagonal and off-diagonal Gram counts for this core pair, together with the selected-vertex count 60. In the split branch, each fixed component vertex has one central neighbor and three component neighbors, leaving ten exterior neighbors; the present core pair has exterior common-neighbor count two.

Choose
\[
 a=u_{29},\quad b=v_0,\quad c=u_0,\quad d=v_7.
\]
Then \(I\cap J=\{a,d\}\). The edges ab,bc,cd are present, while ad is absent because its shift is 8. At b, the neighbors are \(u_0,u_{23},\ldots,u_{29}\). At c, they are \(v_0,\ldots,v_7\). Hence the class totals are

| Center | Both | i-only | j-only | Neither |
|---|---:|---:|---:|---:|
| b | 1 | 0 | 1 | 6 |
| c | 1 | 1 | 0 | 6 |

They realize
\[
 x_b=x_c=y=L=R=1,\qquad A=B=C=D=0,\qquad W=Z=6.
\]
All four equations in (2) hold, but \(\Delta=1\).

Because the graph is bipartite, every triple satisfies
\[
 y_{uv}+y_{uw}+y_{vw}\leq2.
\]
Thus it satisfies even the family of all triangle-cover upper inequalities, which contains the newly accepted subset. It also satisfies the common-core neighbor clique for the two T vertices: no vertex can be adjacent to both a and d, since they lie in opposite bipartition classes.

This is deliberately a countermodel only to the displayed reduced system. The 60 vertices have two specified incidence coordinates, not complete signatures in the accepted 480-signature domain. The remaining mixed coordinates, complete Gram equations, literal eligibility/zero families, full spectral conditions and SRG common-neighbor equations are not asserted. Therefore the construction does not rule out a certificate using those additional constraints and is not a proposed F0 completion.

## 3. Exact star-channel encoding

Although the retained row has not been eliminated, its long sums admit a short exact extended formulation.

For each star that occurs in the retained family, introduce
\[
 z_{b,\{i,j\}}=\sum_{a\in T:\,ab\ {\rm live}} y_{ab}.
\tag{10}
\]
The own-site mixed equation and nonnegative edge variables already imply
\[
                   0\leq z_{b,\{i,j\}}\leq x_b\leq1.
\]
For binary original edge variables, the sum is integral and hence Boolean. The analogous fact holds at c.

The four-exterior inequality becomes the five-term row
\[
 y_{bc}+z_{b,\{i,j\}}+z_{c,\{i,j\}}-x_b-x_c\leq0.
\tag{11}
\]
A star channel can be reused across every row with the same anchor and unordered core pair.

With equality (10), this is exact for both the integer model and its continuous relaxation: each original feasible point has a unique extension, and the channel bounds are already implied. It changes the representation, not the projected feasible region, and does not justify deleting (11).

Whether this helps construction or propagation depends on the number and reuse of distinct stars. No star census, implementation, or performance claim is made here. It should not delay the currently prepared native model.

## 4. What the spectral pair theorem adds

The accepted [spectral-gap pair theorem](root_prism_free_f0_spectral_gap_pair_minor.md) supplies a condition on
\[
 n_{bc}=(D^2)_{bc},
\]
the number of common exterior neighbors. For an actual completion,
\[
 R_{bc}=2-|h_b\cap h_c|-y_{bc}-n_{bc}\geq0,
\]
and the new positive matrix has off-diagonal entry
\[
 B_{bc}=2z_{bc}-360+180|h_b\cap h_c|+180n_{bc}
         -900y_{bc}+30\,\eta(b)\cdot\eta(c).
\tag{12}
\]
Here \(z_{bc}\) is the accepted Schur-kernel coefficient, unrelated to the channel variable of (10).

The pair test depends on the full signatures, profiles and common-neighbor state. The two cross quotas do not determine these data. In particular, n counts a common-neighbor intersection, while A and D in (4) are one-sided neighbor-class sums. No identity from the two quotas replaces one by the other.

The gap theorem applies to an actual graph. Its polynomial matrix identity cannot be applied to an averaged fractional moment matrix. A pair-state consequence or another independently valid linear consequence must be established before using it in a linear redundancy argument.

## 5. A spectral-to-triangle zero rule

The following separate inference is exact.

**Lemma.** Suppose an accepted pair-state result implies that \(y_{bc}=1\) requires \(n_{bc}\geq1\). Let \(\mathcal W_{bc}\) be the signatures a distinct from b,c such that:

- \(h_a,h_b,h_c\) are pairwise disjoint;
- both side edges ab and ac belong to the original eligible-edge namespace.

If every member of \(\mathcal W_{bc}\) is ruled out as a common neighbor by an accepted side-edge zero or an accepted triangle cover on a,b,c, then \(y_{bc}=0\).

**Proof.** An actual exterior triangle has pairwise-disjoint first signatures. Otherwise an adjacent pair would have both a shared core neighbor and the triangle's third exterior vertex as common neighbors, contradicting lambda=1. Thus every actual exterior common neighbor of an active edge bc lies in \(\mathcal W_{bc}\). A side-edge zero prevents that signature from being a common neighbor. A triangle cover also prevents all three edges from being one. Under the stated exhaustive coverage, bc has no exterior common neighbor, contradicting \(n_{bc}\geq1\). Therefore bc is zero.

The rule may be iterated monotonically. Each new zero must use only immutable triangle covers and previously certified zeros, with every excluded third signature preserved. A simultaneous circular set of proposed zeros is not a proof unless it is justified independently.

A certified central zero immediately implies the corresponding four-exterior row from \(L\leq x_b\) and \(R\leq x_c\). A family of m new central-edge zeros can directly affect at most \(9m\) original case rows: a fixed central edge has at most three choices of i and three choices of j. This bound concerns central zeros only; side-edge zeros can have additional effects.

No support-elimination census or zero count is asserted in this note. Root assigned the finite method and its separate verification to another agent.

## 6. Current conclusion and sources

The 23,010 retained rows should remain until a stronger, source-bound certificate is accepted. The present analysis gives:

- the exact missing condition \(y_{bc}\leq A_b+D_c\);
- a binary obstruction to deriving it from the explicitly displayed reduced constraints, including all triangle-cover upper bounds;
- an exact shared-star representation of each retained inequality;
- a valid spectral-to-triangle zero inference requiring a complete support check.

It does not prove that any retained row is independent of the full model.

The accepted reconstruction, original ordered keys and provisional retained IDs are preserved in [the compact report](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-independent01.json), SHA256
`7e9df6f8798483bbe4be386f857b8997dffd08dd409080c258fde2b9bcbbfb22`.
The full original key digest is
`2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c`.
The retained-ID digest is
`b53cff225273f025bc9b6d8e2cd6a654291993df8da4d0345a0dc2312b0dafac`.

The spectral theorem note was read in full at Git blob
`168ca05d66609a2ac7027d3958a4f22c63385e1c`,
SHA256
`169a4b0c8ba1381302d0eeacb449599a5e4913cd6a55a24bb711e5d4126829ce`.
Its independent mathematical review was read at Git blob
`4358f7123e3459d78d0efc1670da8031c1fc989d`,
SHA256
`9132b5b87497a608e40ea07361257c963731a5dc758f41ba1d9605726af18099`.
