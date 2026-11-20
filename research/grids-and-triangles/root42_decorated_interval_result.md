# The decorated root 42 test passes

## Exact result

At the immutable 48-cut count point, the complete decorated root 42 model has the following exact feasible parameter set:

\[
u_0\in 2\mathbb Z,\quad 0\le u_0\le8764,
\qquad
u_1\in 2\mathbb Z,\quad 0\le u_1\le966.
\]

Here \(u_0\) is the weight of one labelled edge-absent fifth state, and \(u_1\) is the corresponding edge-present weight. Each orbit has 12 labelled states. The rectangle contains 2,121,372 even integer pairs.

The saved certificate chooses \(u_0=u_1=0\). Its 343 atom weights consist of 319 positive weights and 24 zero fifth-state weights. Their sum is 55,883,520, the labelled root count. After probability normalization, their common reduced denominator is 27,941,760.

The single exact point query took 29 milliseconds. A separate direct certificate replay took 170 milliseconds. No optimizer was used.

## Why only three intervals are needed

Every fifth state contains exactly one possible complementary-\(A\) edge. For a lower decorated state, either that edge is outside the specified state, in which case both fifth orbits can extend it, or the edge status has already been specified.

Consequently each affine coefficient pair is of the form \((t,t)\), \((t,0)\), or \((0,t)\). After setting \(u_0=2x\) and \(u_1=2y\), nonnegativity reduces to integer intervals for \(x\), \(y\), and \(x+y\). The exact query obtains

\[
0\le x\le4382,\qquad
0\le y\le483,\qquad
-35117\le x+y\le6669.
\]

The last interval contains every sum permitted by the first two. Thus the full feasible set is the rectangle stated above.

The two upper bounds have explicit atomic witnesses. State 79 has masks \(\{21,22,26,49\}\) with no high edge. Its weight is

\[
N_{37894}-u_0=8764-u_0.
\]

State 142 has masks \(\{22,25,49,50\}\), with the complementary pair \(22,25\) adjacent. Its weight is

\[
2N_{35571}-u_1=966-u_1.
\]

The fifth-state weights themselves give \(u_0,u_1\ge0\). Their root stabilizers give evenness.

The independent replay checks these necessary bounds and every atom mass at all four rectangle corners. Since all masses are affine in the two parameters, corner nonnegativity proves sufficiency throughout the rectangle. The coefficientwise stabilizer checks show that every even integer pair gives integral state masses with all required divisibilities.

## Direct verification

The separate replay imports no query code and does not recompute the Möbius inversion. It checks the saved masses against the original moment equations by literal induced-edge restriction.

It verifies:

- all 343 literal state caps and 8,232 root-action images;
- all 319 known literal graph identities and the 31 exact automorphism factors;
- all 343 original decorated moment equations and all 31 quotient equations;
- all 343 stabilizer divisibilities;
- all 253 presence coarsenings and all 241 known presence moments;
- all 1,372 moment equations and divisibilities at the four rectangle corners.

The induced-edge restrictions are checked directly on the literal adjacency rows, independently of the query's three-edge bit-code shortcut.

## Scope

The decorated model constrains the fifth-state split more tightly than the earlier presence model, which only used \(u=u_0+u_1\). At this count point, the decorated model still has complete integral local distributions.

This is a finite local moment certificate. It does not construct an SRG(99,14,1,2), establish joint consistency with other roots, or prove feasibility of every order-ten inequality.
