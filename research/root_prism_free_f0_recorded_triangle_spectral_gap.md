# Spectral-gap minors on the recorded exterior triangles

This note prepares one exact test of the 5,364 triangle indicators already
present in the accepted F0 model. Its scope is the globally prism-free,
F-free split18+18 branch with the first component fixed to F0. The second
component and its alignment remain unspecified.

No test has been executed by this note. No new row is installed in the
frozen native model. Passing the test means only compatibility with this
necessary spectral condition.

## The matrix for one actual triangle

Let H and H2 be the first and second 18-by-60 exterior incidence matrices,
and let D be the actual exterior adjacency matrix. The accepted
spectral-gap theorem proves
\[
B=180L=2N-180R+30\eta^T\eta\succeq0,
\qquad
R=H_2^TH_2=12I+2J-H^TH-D^2-D,
\]
where N=60S is the accepted plus full-core Schur matrix and eta contains
the three first-component fiber occupancies.

Suppose distinct exterior vertices a,b,c form a triangle. The SRG
parameter lambda=1 says that each edge has exactly one common neighbor.
For edge ab, vertex c is already that neighbor. Consequently ab has no
common neighbor in either shell component, and its exterior codegree is
exactly one. The same argument applies to ac and bc. Thus
\[
h_a\cap h_b=h_a\cap h_c=h_b\cap h_c=\varnothing,\qquad
R[\{a,b,c\}]=3I.
\]
The diagonal identity uses the weight-three columns of H2. This conclusion
does not choose H2 or assume a labeling of the second component.

The accepted kernel has diagonal d_a and off-diagonal selector-pair
coefficient z_ab, with adjacency coefficient -540. Therefore
\[
B_{aa}=2d_a-540+30\|\eta(a)\|^2,\qquad
B_{ab}=2z_{ab}-1080+30\eta(a)\mathbin{\cdot}\eta(b).
\]
These are integers. The three profiles are reconstructed from the
original 21-core central-neighbor bits and compared with the accepted
kernel's profiles. No contiguous-fiber convention is assumed.

## Exact necessary inequalities

Write the symmetric block as
\[
\begin{pmatrix}A&P&Q\\P&B&R\\Q&R&C\end{pmatrix}.
\]
Here the scalar R in the display is only the bc entry, not the residual
Gram matrix used above. Its seven nonempty principal minors, in the
implementation's order, are
\[
A,\ B,\ C,\ AB-P^2,\ AC-Q^2,\ BC-R^2,\
ABC+2PQR-AR^2-BQ^2-CP^2.
\]
Each must be nonnegative. The implementation uses BigInt for all matrix
entries, products and determinants, and saves decimal strings. It never
compares floating-point eigenvalues or rounds a determinant.

Failures are separated into negative diagonal, negative two-by-two
minor with no negative diagonal, and negative determinant with every
proper principal minor nonnegative. A proper-minor failure can already
be latent in the accepted pair-state theorem; it is not advertised as
a new spectral phenomenon. A negative three-by-three determinant can
also be implied by other existing constraints. The test does not prove
row independence.

For every rejected recorded triangle, either of these necessary Boolean
rows can be proposed:
\[
t_{abc}=0,\qquad y_{ab}+y_{ac}+y_{bc}\le2.
\]
The accepted model makes t the AND of its three edge variables. The
edge cover needs no selector guard because all three active edges
activate all three vertices. Both rows describe the same forbidden
triangle on Boolean edge assignments. The test only records proposals;
future model use needs the separate acceptance required by root.

## Complete stated input scope

The universe is exactly the 5,364 lexicographically indexed triples in
the accepted indicator inventory. It is not all eligible triples or
all triangles on 480 signatures. Every saved triple is tested, even if
another constraint could already rule it out. The checker binds and
verifies its three original edge IDs, unique target origin, native
indicator index, pairwise disjoint first signatures and complete
target-incidence table.

The original edge namespace is reconstructed from all 480 saved
neighbor lists and compared with the accepted 68,394-edge value hash.
This checks IDs and input consistency; it is not a new eligible-domain
census. The plus kernel's complete primitive coefficient hash, its
denominator and adjacency coefficient are checked against the separate
full-core audit. The accepted combined configuration and native root
receipt bind the indicator offset 71,382 and all 5,364 indicator
variables. The raw native model is not loaded or changed.

Every test record retains the triangle and edge IDs, original origin,
matrix entries, all seven minors and a negative-minor bit mask. Every
failure retains both proposed row keys. The report keeps passes,
singular cases and failures; there is no old-zero pruning.

## Controls and bounded execution

The frozen source includes an independent permutation-expansion
determinant oracle. Controls compare all seven minors of all 729
symmetric matrices whose six independent entries lie in {-1,0,1}.
They also cover a positive matrix, singular positive semidefinite
matrix, negative diagonal, negative pair minor, negative determinant
with nonnegative proper minors, and diagonal integers above 2^53.

These controls are prepared but unrun. One future gated call runs them
and the exact finite test. Its 30-second worker budget includes input
bindings, controls, complete report serialization and the report hash.
The separate V8 owner records a 45-second elapsed bound; it does not
claim OS-process preemption. The report cap is 8 MiB. An overrun,
incomplete traversal or input error remains unaccepted, with every
available record preserved. No automatic retry is permitted.

## Fixed evidence

The spectral theorem is
research/root_prism_free_f0_spectral_gap_pair_minor.md,
Git 168ca05d66609a2ac7027d3958a4f22c63385e1c,
SHA256 169a4b0c8ba1381302d0eeacb449599a5e4913cd6a55a24bb711e5d4126829ce.
Its independent mathematical review is
f0-spectral-gap-pair-minor-independent-review01.json,
Git 4358f7123e3459d78d0efc1670da8031c1fc989d,
SHA256 9132b5b87497a608e40ea07361257c963731a5dc758f41ba1d9605726af18099.

The full-core kernel archive has SHA256
a49b8309032b2c599c637285f4a4584bb7d55659640e594df1e6fdd50bf826c1;
its decompressed SHA256 is
a963a88606a9fad78576d711f6ef7bf67eb03032176cebc2af5af700ea7c6708.
The separate full-core audit has SHA256
d8031c629bfb9f5b050c55e218b872aa68a0de08a84abff99da5e029fe572c75.

The indicator inventory has SHA256
8606d51ced038b40135fa22bc16d056873b80c16c26d2c34db7e24ac8effd2c7.
Its complete literal-support root acceptance has SHA256
9d4e3a9b44a2140d95091425a346396ed84dd8d9d88f3a4e7fa3e67d47cd51d4.
The accepted combined native root receipt has SHA256
20fef49c4a6a1b190dfc2869d77152deb4afd53b4411e6ec92a0fad53cf209b1
and binds the unchanged raw model SHA256
2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6.
