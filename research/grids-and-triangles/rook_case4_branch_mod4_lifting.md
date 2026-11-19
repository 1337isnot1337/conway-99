# Exact mod-four lifting after branch substitution

Status: mathematical proof and tiny finite controls only. No Conway99 branch matrix was loaded by the controls. The all187-box GF(2) calculation and any case-specific mod-four calculation remain unrun.

## 1. Integer premises and exact branch substitution

Let the accepted integer equalities be
\[
C x=b,\qquad C\in\mathbb Z^{m\times N},\quad b\in\mathbb Z^m.
\]
For the prepared rook calculation, \(N=1214\) and \(m=633\): the630 original Gram equalities, the independently proved H1 and H2 unit sums, and the86-term equality obtained from the exact663 identity. These633 equations are necessary conditions for the scoped Boolean case. Their derivation must remain part of the proof ancestry.

The663 row is an integer premise only after the saved original-row combination is expanded on all1214 coordinates. After the already proved zeros, that combination gives
\[
6x_{663}+2\sum_{j\in S}x_j=4.
\]
Using the already proved \(x_{663}=0\), division in \(\mathbb Z\) gives
\[
\sum_{j\in S}x_j=2.
\]
No division by2 occurs inside \(\mathbb F_2\). The new mod-four layer described below is separate from this already proved premise.

Fix a branch box. Let \(F_0,F_1\) be the coordinates fixed to0 and1, and let \(U\) contain the unfixed coordinates. Substitute these values as exact integers:
\[
A=C[:,U],\qquad b'=b-\sum_{j\in F_1}C[:,j].
\]
Any Boolean solution in this box satisfies \(A x_U=b'\).

The fixed coordinates are not allowed to gain an additional \(2w_j\) in a modular lift. They were eliminated exactly. All lifting variables below correspond only to \(U\).

This statement permits the globally proved112 zeros and every conditional fixing in a cold-checked branch box. It does not promote a conditional fixing to a global premise.

## 2. The lifting theorem

Write \(\bar A,\bar b'\) for reduction modulo2 and let
\[
K=\ker(\bar A^{\mathsf T})\subseteq\mathbb F_2^m.
\]
Choose any basis \(v_1,\ldots,v_s\) of \(K\), represented initially by binary integer vectors. Since \(v_k\in K\), every coefficient of \(v_k^{\mathsf T}A\) is even.

First test the base system
\[
\bar A y=\bar b'.
\tag{1}
\]
If it is inconsistent, an exact left-kernel witness \(v\) with
\[
v^{\mathsf T}A\equiv0\pmod2,\qquad v^{\mathsf T}b'\equiv1\pmod2
\]
already excludes the branch.

Assume(1) is consistent. Then \(v_k^{\mathsf T}b'\) is even for every \(k\). Define integer rows and right-hand sides
\[
a_k=\frac{v_k^{\mathsf T}A}{2},\qquad d_k=\frac{v_k^{\mathsf T}b'}2.
\tag{2}
\]
The division in(2) is exact integer division.

**Theorem.** A vector \(y\in\mathbb F_2^{|U|}\) is the reduction modulo2 of a solution
\[
z\in(\mathbb Z/4\mathbb Z)^{|U|},\qquad Az\equiv b'\pmod4
\]
if and only if
\[
\bar A y=\bar b',\qquad
a_k y\equiv d_k\pmod2\quad(1\le k\le s).
\tag{3}
\]

Thus(3) is a finite linear system over \(\mathbb F_2\) describing exactly the liftable parity residues. This is an equivalence for the mod-four equality relaxation. It is not an equivalence for Boolean feasibility or for the full graph constraints.

### Proof

Take the canonical binary integer representative of \(y\). Once(1) holds,
\[
r(y)=\frac{b'-Ay}{2}\in\mathbb Z^m
\]
is defined component by component.

Every lift of \(y\) modulo4 has the form
\[
z=y+2w,\qquad w\in\mathbb F_2^{|U|}.
\]
Substitution gives
\[
A(y+2w)\equiv b'\pmod4
\quad\Longleftrightarrow\quad
\bar A w=\overline{r(y)}.
\tag{4}
\]

Over \(\mathbb F_2\), the column space of \(\bar A\) is the orthogonal complement of \(K=\ker(\bar A^{\mathsf T})\). Therefore(4) has a solution if and only if
\[
v_k^{\mathsf T}r(y)=0\pmod2
\quad\text{for every basis vector }v_k.
\]
Using exact integer division,
\[
v_k^{\mathsf T}r(y)
=\frac{v_k^{\mathsf T}b'}2-\frac{v_k^{\mathsf T}A}{2}y
=d_k-a_k y.
\]
These are exactly the additional equations in(3). This proves necessity and sufficiency.

If \(U\) is empty, the theorem says that every entry of \(b'\) must be divisible by4. This is still only a congruence test: exact integer equality would require \(b'=0\). If there are no input equalities, every parity residue lifts.

## 3. Basis choices and integer representatives

### A complete left-kernel basis is sufficient

The compatibility condition in(4) is a linear condition on \(v\in K\). Testing a basis therefore tests all of \(K\). Different complete bases give the same set in(3).

A collection of valid kernel vectors that does not span \(K\) is insufficient. Kernel membership alone is not a completeness certificate.

If \(r=\operatorname{rank}_{\mathbb F_2}\bar A\), a claimed kernel basis must have \(m-r\) independent vectors. An implementation can certify this by explicit kernel products, independence witnesses, and a verified rank or row-span certificate for \(\bar A\).

### Half rows need not be a linear function of binary witness bits

For binary integer representatives \(u,v\in K\), put
\[
L_v(y)=\frac{v^{\mathsf T}(Ay-b')}{2}.
\]
The exact integer identity
\[
u\mathbin{\mathrm{XOR}}v=u+v-2(u\mathbin{\mathrm{AND}}v)
\]
gives
\[
L_{u\mathbin{\mathrm{XOR}}v}(y)
=L_u(y)+L_v(y)
-(u\mathbin{\mathrm{AND}}v)^{\mathsf T}(Ay-b').
\tag{5}
\]
On solutions of the base parity equations, the last term is even. Hence the half-row tests are linear in the kernel witness only after restricting to the base parity solution set.

It is incorrect to discard(1) and claim that every kernel basis gives the same half-row-only system. A concrete counterexample appears in Section7.

### Integer lifts of a kernel vector

Replacing a binary representative \(v\) by \(v+2q\), for any integer \(q\), changes the half-row residual by
\[
q^{\mathsf T}(Ay-b').
\]
This is even on the base parity solution set. Therefore the accepted set in(3) is independent of the integer representative used for the same vector of \(K\).

The implementation should nevertheless use a fixed canonical representative and save it explicitly. That makes the integer division and coefficient replay deterministic.

## 4. Reusing a global row basis without losing branch dependencies

One global GF(2) row reduction can be reused, but its binary rows must not be reinterpreted as new integer equations.

Let \(B\) be the coefficient matrix after only the global zero substitutions. Suppose a checked global row reduction gives an independent row basis
\[
R=W B
\]
over \(\mathbb F_2\), where \(W\) records the original-row XOR witnesses. Let \(D\) be a basis of \(\ker(B^{\mathsf T})\).

The rows of \(W\), together with \(D\), form a direct-sum decomposition of the original row-coefficient space. Indeed, the rows of \(WB\) are independent, so the row span of \(W\) intersects \(\ker(B^{\mathsf T})\) trivially. Their dimensions add to the number of original rows.

For a branch, restrict to the unfixed columns \(U\). Reduce \(R[:,U]\), and let \(E\) be a basis of its left kernel. Then
\[
D\ \cup\ \{eW:e\in E\}
\tag{6}
\]
is a basis of \(\ker(B[:,U]^{\mathsf T})\).

To prove spanning, decompose any original-row witness as \(d+eW\). It annihilates \(B[:,U]\) precisely when \(e\) annihilates \(R[:,U]\). Independence follows from the same direct-sum decomposition and the independence of the chosen basis of \(E\).

The right-hand side must still be updated by exact branch substitution. If a dependency has odd substituted right-hand side, it gives a base-parity contradiction and must not be halved.

For every vector in(6), reconstruct its combination of the original integer rows before dividing. The integer coefficient matrix cannot be replaced by its0/1 parity image. In particular, a mod-two zero row can contain all of the new mod-four information.

A practical implementation may retain the null-row witnesses generated during the global and branch eliminations. Their completeness still needs a rank/independence check. If the existing controller does not save them, their existence should not be inferred from a prose summary.

## 5. Compact final certificates

The intermediate half-row construction need not be trusted when checking a final obstruction or unit.

Suppose a GF(2) combination of the rows in(3) uses original rows with coefficients \(\alpha_i\in\{0,1\}\) and half rows with coefficients \(\beta_k\in\{0,1\}\). Set
\[
t=2\alpha+\sum_k\beta_k v_k\in\mathbb Z^m.
\tag{7}
\]
The entries of \(t\) may be reduced modulo4 for the final certificate.

### Branch contradiction

If the resulting lifted parity row is \(0=1\), then
\[
t^{\mathsf T}A\equiv0\pmod4,\qquad
t^{\mathsf T}b'\equiv2\pmod4.
\tag{8}
\]
A checker can verify(8) directly from the original633 integer equations and the complete branch substitution. No optimizer, rank claim, kernel basis, or elimination transcript is needed for acceptance of this individual contradiction.

An ordinary mod-two contradiction also has this form after doubling its witness.

In original coordinates, compute \(g=t^{\mathsf T}C\) and
\[
d=t^{\mathsf T}b-\sum_{j\in F_1}g_j.
\]
Then(8) becomes \(g_j=0\pmod4\) for all unfixed \(j\), and \(d=2\pmod4\). Fixed-zero and fixed-one contributions are therefore explicit in the1214-coordinate replay.

### Conditional Boolean unit

If the lifted parity row is \(x_j=\varepsilon\), then
\[
t^{\mathsf T}A\equiv2e_j\pmod4,\qquad
t^{\mathsf T}b'\equiv2\varepsilon\pmod4.
\tag{9}
\]
Equation(9) implies \(x_j\equiv\varepsilon\pmod2\). Since the target variable is Boolean, it proves \(x_j=\varepsilon\) within that branch.

This is a mod-four original-row witness, not merely an XOR witness. It needs a distinct certificate kind from the current GF(2) calculation.

### Completeness claims require more

A valid witness proves its own contradiction or unit. Reporting that the complete lifting system is consistent, or that it has no further forced coordinate, requires the complete kernel-basis checks and both directions of row-span verification.

Even a complete consistent lifted system proves only mod-four compatibility. It does not exhibit a binary selector set, satisfy inequalities not present in the equality system, or construct a graph.

## 6. Conditional and global scope in the rook branch cover

The current branch cover comes from the exact nonnegative integer identity
\[
H_{27}+2Q=3.
\]
Each branch's positive selected set has total weight3. Selecting all its guard coordinates therefore forces every other coordinate in this positive weighted support to zero. The accepted propagation traces then imply the complete saved branch box.

Consequently, a checked contradiction for that box gives the Boolean nogood
\[
\sum_{a\in G}x_a\le |G|-1,
\]
where \(G\) is its saved positive guard. The guards can have size1,2, or3.

A checked conditional unit does not become a global unit merely because it appears in one or several branches. Global conclusions require exact coverage accounting for all remaining branches, including the four already excluded branches and the earlier complete propagation/capacity exclusions. For a common unit, every branch must either have an accepted contradiction or imply that unit. Unprocessed branches cannot silently disappear.

The all187-box GF(2) preparation currently keeps the stricter rule that every branch must have an accepted complete outcome before reporting a new common global unit. A mod-four continuation should preserve that rule unless a different complete-cover argument is explicitly prepared.

No equality is inferred from the latest fractional point making a cut tight. Such tightness is a property of that point, not a universal branch premise.

## 7. Counterexamples and boundary checks

1. **Mod-two consistency is weaker.** For \(4x=2\), the base parity equation is a tautology. Its half row is \(2x=1\), whose parity is contradictory. The original equation has no solution modulo4.

2. **A mod-two zero row may contain useful information.** For \(2x=2\), the base parity row is zero, but its half row forces \(x=1\pmod2\). Reinterpreting the zero parity row as the integer equality \(0=0\) loses this information.

3. **An odd right-hand side cannot be divided.** The equation \(2x=1\) is already inconsistent modulo2. Replacing its right-hand side by an integer floor after division would be unsound.

4. **A fixed coordinate must stay fixed.** Take \(x=2\) with branch premise \(x=0\). Exact substitution gives \(0=2\pmod4\), a contradiction. Keeping only the weaker condition \(x=0\pmod2\) would incorrectly admit \(x=2\pmod4\).

5. **The base equations cannot be omitted.** Let
   \[
   A=(1,1,3)^{\mathsf T},\qquad b'=0.
   \]
   The left kernel has basis choices \(\{(1,1,0),(1,0,1)\}\) and \(\{(1,0,1),(0,1,1)\}\). The first half-row-only system forces \(y=0\); the second permits both residues. Including the base equation \(y=0\) makes both choices equivalent, as the theorem requires.

6. **A kernel subset need not be complete.** For
   \[
   A=\operatorname{diag}(2,2),\qquad b'=(0,2),
   \]
   testing only the first kernel coordinate forces \(y_1=0\) but misses \(y_2=1\). A complete kernel basis forces both.

7. **A modular lift need not be Boolean.** The equality \(x=2\) has the modular solution \(z=2\) and liftable parity \(y=0\), but has no Boolean solution. The lifting theorem makes no Boolean-feasibility claim.

These examples also show why the proof must retain integer coefficients, exact branch fixings, all base equations, and a complete kernel basis.

## 8. Exhaustive tiny controls and provenance

The standalone V8 control source enumerates every matrix and right-hand side modulo4 in dimensions
\[
1\le m\le2,\qquad1\le n\le2,
\]
and every coordinate pattern of free, fixed0, or fixed1. It compares the lifted parity formulation with direct enumeration of all free assignments modulo4.

Observed result:

- 38,256 system/branch-substitution cases;
- 151,392 direct assignments modulo4;
- 144,816 ordered kernel-basis checks;
- 23,596 base-parity-inconsistent cases;
- 349,680 checks after changing a kernel witness's integer representative;
- all named counterexamples above checked;
- zero Gaussian-elimination, optimizer, native, or187-box calls.

All checks passed in2,013 milliseconds in V8. The proof in Sections1–5 is the general argument; the tiny controls check signs, substitution, basis dependence, and boundary cases.

Source:
experiments/workspace/rook_case4_branch_mod4_lifting_controls.js

SHA256:
e85c7c4b62807d22176780067bb8b63c97a6b9221008fa45679c2dab4d62305d

Git blob:
54276ceacf0ba78c52a8a7cb3a937d719d1f9996

Result:
experiments/logs/grids-and-triangles/rook-case4-branch-mod4-lifting-controls01.json

SHA256:
cfbc33ed8d91f82a4bed9cacf94e1fe5b179959f6148d3425aa9895017eace0a

Git blob:
12928287e13122c094621af33b5d333269f3609a

The all187-box integer-equation specification is independently frozen at SHA256
92c76adbc19e92ab22d414874b00dec0b2d8e913d13e97eb36b54928e7aff747.
Its input/preparation checks passed before the execution outage. Its case elimination remains unrun. The new mod-four layer has not been added to that specification or executed on any rook branch.

## 9. Source sketch for a separately gated continuation

    Verify all integer equations and the complete branch-proof ancestry.
    Preserve the already proved divided663 row and its integer proof.

    For each declared branch, with no feedback from another branch:
        Substitute all fixed zero/one coordinates as exact integers.
        Reduce the coefficient matrix and RHS modulo two.
        If inconsistent:
            retain an original-row parity contradiction.
        Otherwise:
            obtain and verify a complete original-row left-kernel basis.
            reconstruct each kernel combination over the integers.
            require even coefficients and even RHS before dividing by two.
            append the half rows modulo two to the original parity rows.
            perform one complete GF(2) reduction of this lifted system.
            flatten every contradiction/unit to a mod-four witness t.
            replay t directly on all original coordinates and branch fixings.
            save the complete branch record before continuing.

    In a separate checker:
        accept individual consequences only from their direct witnesses.
        require complete span/basis verification for compatibility claims.
        require the complete branch cover before any global conclusion.
        preserve partial/unprocessed branches without inferred exclusions.

This is one lifting layer only. It does not authorize repeated saturation, a mod-eight or higher search, additional branch propagation, or any native solver call.
