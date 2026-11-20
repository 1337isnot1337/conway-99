# Full-span parity separation at one exact rook-case4 point

This preparation searches the entire affine parity row span of the original
630 Gram equations on the proved 112-zero face. It does not search for a graph
or a Boolean incidence. The input is the accepted exact point with denominator
67,336,409,858 from discovery cycle run02. Its 1,102 surviving coordinates are
positive and satisfy all 167,118 rows of the current relaxation.

The frozen preparation has 2,491 Boolean variables and 2,208 constraints. Its
protobuf has 166,814 bytes. No production optimizer has been called.

## Exact parity domain

Write the 286 saved independent parity equations as

\[
B_i x=b_i \pmod2.
\]

Each row carries an explicit XOR of the original Gram equations. The saved
triangular rank certificate proves independence. Each of the 630 original
equations has an explicit representation in these 286 rows after substituting
only the 112 previously proved zeros. Thus the row span is complete for this
Gram parity domain; it does not include unproved additional equations.

For choice bits \(u_i\), define

\[
h_j=\bigoplus_i B_{ij}u_i,\qquad
\beta=\bigoplus_i b_i u_i.
\]

The selected equation is \(\sum_{j:h_j=1}x_j=\beta\pmod2\).
The support bits refer to all 1,102 surviving original coordinates, separately.

## Distance to a forbidden vertex

At the fixed exact point \(x_j=n_j/D\), let

\[
f_j=\mathbf1[2n_j>D],\quad
w_j=\min(n_j,D-n_j),\quad
p_j=|D-2n_j|.
\]

The tie rule is \(f_j=0\) at a half. The vector \(f\) is a nearest Boolean
vertex on every selected support. If its parity is forbidden already, it is
a nearest forbidden vertex. Otherwise, one coordinate must change parity.
Flipping a support coordinate adds exactly \(p_j/D\) to the distance. Since
all penalties are nonnegative, an optimal forbidden vertex needs at most one
flip. This remains true for ties and coordinates at 0 or 1.

Introduce flip bits \(z_j\le h_j\) with \(\sum_j z_j\le1\). The constraints

\[
\beta\oplus\bigoplus_j f_jh_j\oplus\bigoplus_jz_j=1,
\qquad
\sum_j w_jh_j+\sum_j p_jz_j\le D-1
\]

are feasible exactly when some equation in this full span has a violated
parity-polytope inequality at this point. All arithmetic is integer. The
largest possible weighted activity over the full Boolean box is
69,998,985,719,486, below the declared signed 63-bit bound.

The model uses 286 choice bits, 1,102 support bits, 1,102 flip bits and one parity
bit. Its constraints are 1,102 support XORs, one right-hand-side XOR, one
forbidden-parity XOR, 1,102 flip-support inequalities, one at-most-one constraint
and one weighted bound. There is no objective, hint, assumption or symmetry
identification.

## Accepted output and its proof

A future native assignment is only a proposal. The exact inspector checks all
Boolean equations, the one-flip condition and the integer distance. It XORs
the selected basis witnesses to obtain original Gram row IDs, then adds those
original rows as nonnegative integer equations on all 1,214 original columns.
Only the 112 proved-zero coordinates are removed from the odd support.

Let \(H\) be that support and \(F\subseteq H\) the ones of the forbidden
vertex. Since \(|F|\not\equiv\beta\pmod2\), every Boolean solution of the
Gram equations has Hamming distance at least one from that vertex. Therefore

\[
\sum_{j\in F}x_j-\sum_{j\in H\setminus F}x_j\le |F|-1.
\]

The exact point deficit is \(D-\text{distance numerator}>0\). The certificate
stores the original row IDs, full 1,214-coordinate integer sum, original RHS,
removed proved-zero odd coordinates, signed cut and exact deficit. The
native basis choices and support bits cannot substitute for this replay.

Native INFEASIBLE or UNKNOWN is not an accepted no-cut certificate and cannot
exclude case4. A checked cut is a necessary inequality at this one local
incidence domain. It is not a solution or exclusion of the Conway99 problem.

## Preparation and limits

The model source only exposes preparation. A separate driver is prepared for
one 60-second, one-worker native call, with a 120-second owned-child bound and
no automatic retry. Its native transport reproduced the exact frozen protobuf
hash in 1.046 seconds without solving. The driver reuses the previously
reviewed owned-child function with an exact whole-function AST comparison.
Production awaits the separate driver/source/model/runtime gate.

The driver saves any complete Boolean vector before inspecting it. A successful
proposal must pass the original-Gram cut inspector. Its later artifact replay
checks every native Boolean constraint and derives the cut independently from
the saved original rows. Timeout, native INFEASIBLE, UNKNOWN and driver errors
remain unresolved. The complete response and child log are preserved.

Preparation passed 13,056 complete Boolean assignments against serialized tiny
protobufs, including signed forbidden vertices, half ties and boundary point
coordinates. Another 120 controls compared the zero-or-one-flip minimum with
literal enumeration of every forbidden vertex. No optimizer was used.

A separate audit reconstructs all 286 witnesses from the original integer
Gram rows, checks the triangular rank witness without repeating elimination,
checks all 630 span representations and all 315,172 transposed basis entries,
and reads every variable, XOR literal, linear coefficient and bound in the
saved protobuf. It does not import the subject, rebuild a native model or run
a parity search. The earlier zero proofs remain explicit source-bound
premises. This audit passed in 0.538 seconds. Two additional literal Gram
controls exercise the independent output checker for signed and unsigned
cuts; all 20 deliberately corrupted vectors/certificates were rejected.
These controls use no production point and no optimizer.
