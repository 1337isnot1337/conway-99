# A spectral-gap pair test for the split F0 exterior

This is a necessary-condition theorem for an actual graph in the existing
prism-free, F-free split18+18 branch with component zero fixed on the first
side. The other eighteen-vertex component and its relative fiber alignment
remain unspecified. This note prepares a finite pair-state test. It contains
no pair census, accepted graph, exclusion of a component, or native query.

The new matrix is
\[
 L=\frac{S^2-9S}{81}
   =\frac23S-R+\frac16\eta^T\eta \succeq0,
 \tag{1}
\]
where S is the full-core plus Schur matrix on the actual sixty exterior
vertices, R is the residual second-incidence Gram matrix, and eta records
the first incidence's three fiber occupancies. The proof below derives
every term and the positive integer scaling used by a future census.

## 1. Scope and notation

Partition the vertices into the central triangle, the fixed component
C0 of order eighteen, the other component C2 of order eighteen, and
the sixty exterior vertices. C0 and C2 are anticomplete. The central
triangle has no exterior neighbors. Both component adjacency matrices
are cubic. Each has three fibers of size six, and every component
vertex has exactly one neighbor in each fiber.

Let H and H2 be their respective 18-by-60 binary incidences to the
exterior, whose adjacency matrix is D. Every column of each incidence
has weight three. D is a simple eight-regular graph.

For the second component let U be the 18-by-3 matrix of fiber
indicators. Thus U^T U=6I, U*1=1, and C2 U is the all-ones matrix.
Put
\[
 F=UU^T,\qquad \Pi=I-F/6,\qquad W=\ker U^T.
\]
The first component has its own fiber-indicator matrix U0. Set
\[
 \eta=U0^T H,\qquad d=\eta-J_{3,60},\qquad
 \eta_2=U^T H_2.
\]
Every exterior vertex has two neighbors in each full twelve-vertex
fiber. With the actual global fiber correspondence,
\[
 \eta_2=2J_{3,60}-\eta=J_{3,60}-d.
 \tag{2}
\]
This correspondence need not agree with a separately canonicalized
labeling of C2. A permutation of its three fibers leaves every dot
product in (1) unchanged.

Because every column of eta sums to three,
\[
 \eta_2^T\eta_2=\eta^T\eta.
 \tag{3}
\]
Equation (3) also follows by expanding (2); the constant and mixed
terms cancel. No matching of individual vertices between the two
components is assumed.

The exterior block of the strongly regular graph equation gives
\[
 R=12I+2J-H^TH-D^2-D=H_2^TH_2.
 \tag{4}
\]
In particular, R_aa=3. For distinct selected vertices a,b, put
\[
 s=|h_a\cap h_b|,\quad y=D_{ab},\quad n=(D^2)_{ab}.
\]
Then
\[
 R_{ab}=2-s-n-y,\qquad
 n\in\{0,1,\ldots,2-s-y\}.
 \tag{5}
\]
The upper bound in (5) uses only R_ab>=0. Keeping every integer in
that interval is conservative: it does not assert that each value
can actually occur with the other rows or the second component.

## 2. Conditioning a scaled orthogonal projection

For the full graph,
\[
 Q=27I-9A+J
\]
is 63 times an orthogonal projection of rank 44. This follows from
the SRG eigenvalues 14,3,-4 and their multiplicities 1,54,44.

Here is the needed general fact. If Q=cVV^T with V^T V=I and a set I
of m coordinates has positive-definite Q[I,I], let E be the
orthogonal projection in the column-coordinate space onto the
orthogonal complement of the rows V_I. The Schur complement is
\[
 Q/Q[I,I]=cV_J E V_J^T.
\]
Since E V_I^T=0 and V_J^T V_J=I-V_I^T V_I,
\[
 (Q/Q[I,I])^2=c(Q/Q[I,I]).
 \tag{6}
\]
Its rank is rank(Q)-m. This is a statement about a Schur complement
of a scaled projection, not an arbitrary positive-semidefinite
matrix.

The accepted full-core audit proves that the fixed plus 21-core has
rank twenty. Conditioning on C0 and two central vertices uses a
positive-definite 20-core. The third central residual row is zero.
Deleting that zero row leaves the 78-by-78 matrix
\[
 M=\begin{pmatrix}S&V^T\\V&T\end{pmatrix}
\]
on the exterior and C2, satisfying
\[
 M^2=63M,\qquad M\succeq0,\qquad \operatorname{rank}M=24.
 \tag{7}
\]
S is precisely the plus full-core Schur matrix already represented
by the accepted 480-signature kernels, restricted to the selected
sixty signatures. It is not the earlier 18-core matrix.

## 3. The omitted-component blocks

First condition on C0 alone. Its plus block is
\[
 K=27I-9C0+J,\qquad K1=18\,1.
\]
The C0-to-C2 block is J. The C0-to-exterior column is 1-9h_a.
Therefore the C2 block after this first conditioning is 27I-9C2,
and the C2-to-exterior block is
\[
 \frac32J-9H_2.
\]
The latter constant is important:
1^T K^{-1}(1-9h_a)=(18-27)/18=-1/2.

The accepted residual central-triangle block is 18I-6J. Its inverse
on the sum-zero plane is 1/18. The residual central-to-exterior
block is -3d, and the residual central-to-C2 block is
\[
 3J-9U^T.
\]
Both have columns in that plane. Conditioning the remaining two
central directions consequently gives
\[
 T=27I-9C2-\frac92F+\frac32J
   =9(3I-C2)\Pi,
 \tag{8}
\]
and
\[
 V=\frac32J-9H_2-\frac32Ud=-9\Pi H_2.
 \tag{9}
\]
For (9), use U^T H2=eta2=J-d. The 1/18 factor in the central
correction produces (27/18)Ud=(3/2)Ud.

The subspace spanned by the three fiber indicators is invariant
under C2, and its orthogonal complement W is invariant as well.
Equation (8) is zero on the fiber-indicator space. On W it is
27I-9C2. A symmetric cubic adjacency matrix has spectrum in [-3,3],
so
\[
 0\preceq T\preceq54I.
 \tag{10}
\]
The inequality (10) does not require connectedness or a catalogue
classification of C2. Connectedness is needed only for the exact
multiplicities stated later.

## 4. The gap and the new positive matrix

From (7),
\[
 S^2+V^TV=63S,\qquad VS+TV=63V.
 \tag{11}
\]
Every eigenvalue lambda of S lies in [0,63]. If 0<lambda<63 and
Sv=lambda v, then
\[
 \|Vv\|^2=\lambda(63-\lambda)\|v\|^2>0,
 \qquad T(Vv)=(63-\lambda)Vv.
\]
Equation (10) implies 63-lambda<=54, hence lambda>=9.
The endpoint lambda=63 already has that property. Thus
\[
 \operatorname{spec}S\subseteq\{0\}\cup[9,63],
 \qquad S^2-9S\succeq0.
 \tag{12}
\]

Using (9), (4), and (3),
\[
 V^TV
 =81H_2^T\Pi H_2
 =81\left(R-\frac16\eta_2^T\eta_2\right)
 =81\left(R-\frac16\eta^T\eta\right).
 \tag{13}
\]
Substitute (13) into the first identity in (11):
\[
 \frac{S^2-9S}{81}
 =\frac{54S-V^TV}{81}
 =\frac23S-R+\frac16\eta^T\eta.
\]
This proves (1). In particular, the fiber term has a plus sign,
its coefficient is 1/6, and the coefficient of R is minus one.

The argument is applied to one actual graph before any averaging.
Neither S^2 nor integer n-state enumeration may be applied to an
averaged moment matrix as if it came from a single graph.

## 5. Exact entries from the accepted integer kernel

The accepted plus kernel represents N=60S. Its common numerator
divisor is one and its adjacency coefficient is -540. Denote its
diagonal coefficients by d_a and its off-diagonal selector-pair
coefficients by z_ab. For a selected pair,
\[
 N_{aa}=d_a,\qquad N_{ab}=z_{ab}-540y.
\]
Define
\[
 B=180L=2N-180R+30\eta^T\eta.
 \tag{14}
\]
Thus
\[
 B_{aa}=2d_a-540+30\|\eta(a)\|^2,
 \tag{15}
\]
and, for a distinct selected pair,
\[
 B_{ab}
 =2(z_{ab}-540y)-180(2-s-n-y)
                 +30\,\eta(a)\cdot\eta(b).
 \tag{16}
\]
An equivalent off-diagonal expression is
\[
 B_{ab}=2z_{ab}-360+180s+180n-900y
                         +30\,\eta(a)\cdot\eta(b).
\]
Every coefficient is an integer.

The existing domain has only profile 111 or a permutation of 210.
Consequently the profile norm squared is three or five. Together
with the accepted plus diagonal range 746 through 1238, (15) gives
the conservative positive bounds
\[
 1042\le B_{aa}\le2086.
\]
These bounds use the accepted range and profile identities; they
are not a new enumeration.

A valid pair state must satisfy the two-by-two principal-minor test
\[
 B_{aa}B_{bb}-B_{ab}^2\ge0.
 \tag{17}
\]
There is no floating-point tolerance or eigenvalue threshold in (17).

## 6. Complete state scope and activation

A proposed finite census should inspect all 114,960 unordered pairs
of distinct signatures in the original 480-signature domain.

For every pair, test y=0. Test y=1 only when the edge belongs to the
original complete 68,394-edge namespace. Ineligible pairs have no
edge variable. For each state, keep every integer n in (5).
Additional accepted zero rows may be recorded as a later
disposition; they should not silently remove pairs from the stated
universe.

Fiber membership must be read from the original 21-core adjacency:
for central index i=0,1,2, count signature sites j for which bit
j+3 is set in component_core_rows[i]. This reconstructs eta without
assuming contiguous fiber labels or a canonical alignment of C2.

The coefficients d_a and z_ab come from the plus full-core kernel
and its original complete pair order. The checker must bind that
order and denominator explicitly.

The following deductions are valid, conditional on both signatures
being selected.

- If every allowed n fails (17) for y=1, then that exterior edge is
  impossible. Since an edge activates both endpoints, y_ab=0 is an
  unconditional Boolean model row.
- If every available y,n state fails, then x_a+x_b<=1.
- If only y=0 fails, adjacency is forced whenever both endpoints
  are selected: y_ab>=x_a+x_b-1, provided that edge exists.
- If some n values survive, record the exact allowed state list.
  Survival is only this necessary minor test; it is not a local or
  global completion certificate.

All-zero or all-one claims require the complete stated n interval.
No assumption of independence among the different n_ab is made.

## 7. Relation to earlier conditions and exact spectrum

The previous full-core tests inspect principal minors of S and of
the minus Schur matrix. They do not explicitly test (1). Formula
(1) also contains the exterior common-neighbor count n through R.

A spectral lower bound S>=0 and upper bound S<=63I permits
eigenvalues in (0,9). The new condition forbids them. This explains
the additional mathematical ingredient, but does not prove that a
specific resulting Boolean row is independent of every existing
cut. Any novelty claim needs a comparison with the accepted rows.

For connected C2, its eigenvalue three occurs only on the constant
vector. The eigenvalues lambda_i of C2 on W therefore lie in [-3,3),
and T has fifteen positive eigenvalues 27-9lambda_i, all below63.
The complementary projection blocks in (7) then give
\[
 \operatorname{spec}S
 =\{0^{(36)},\,63^{(9)},\,36+9\lambda_i:\ 1\le i\le15\}.
 \tag{18}
\]
This also checks the exact rank24 assertion. These multiplicities
are not needed to prove (17).

The resulting moments are tr(S)=1080 and tr(S^2)=56862.
If C2 is triangle-free, tr(S^3)=3219264. Component triangles are
forbidden by a prism with the central triangle; exterior triangles
are not forbidden. The third moment corresponds to exactly32
exterior triangles when both shell components are triangle-free.

The second moment is redundant with the current binary degree,
first-incidence Gram, and mixed equations. Indeed im(H^T) has
dimension18 and is D-invariant. D on this space has eigenvalues
8, -1 twice, and -1-lambda_i(C0|W). Its trace is -6 and the trace
of its square is120. Since tr(D)=0 and tr(D^2)=480, on ker(H) they are6
and360. The full-core S is zero on im(H^T) and is 9(3I-D) on
ker(H). Therefore
\[
 \operatorname{tr}S^2
 =81(9\cdot42-6\cdot6+360)=56862.
\]
No extra trace-squared row should be advertised as new.

## 8. Frozen source and data bindings

The derivation was compared with the following repository notes at
commit cd7e6404f37861003dcdd0fe1757bb2543ebd6fb:

- research/root_prism_free_f0_components.md,
  Git blob e9ba184ee254130652c252b981487266ad078c15;
- research/root_prism_free_f0_full_core_schur.md,
  Git blob 7d6dba5508bb101d1b18e1bae807730b61545145;
- research/root_prism_free_f0_full_core_schur_cuts.md,
  Git blob 178eabf8d79130e0364f6714e9a6f28d7f75a109;
- research/root_prism_free_f0_fixed_exterior_residual.md,
  Git blob 0e4c2625bad64b80782e6a87f506d92dc7955a43;
- research/root_prism_free_f0_first_design_exterior.md,
  Git blob 6757de8df7ffbeccada3b7f0590487d7036c1b1a;
- research/root_prism_free_f0_coupling.md,
  Git blob 57eb8c8d8c83fe762a536945c123a33f5c10374e.

The complete accepted kernel producer was reread for its fiber
construction, pair order, denominator reduction, and adjacency
coefficient:
experiments/workspace/root_prism_free_f0_full_core_schur_kernels.py,
SHA256 141392693e8d4b7e140c329cfa4128b8794bd376713558394ef014975e2fc63f,
Git blob be029b2bade8561f0367d96a09c094e50e6a0c8a.

The actual full-core independent audit was reread and rehashed:
experiments/logs/root-prism-free/f0-full-core-schur-independent-audit.json,
SHA256 d8031c629bfb9f5b050c55e218b872aa68a0de08a84abff99da5e029fe572c75,
Git blob a7ed9d7d07e7b48e3facb4fd651451e1a872880a.
It certifies the positive20core, compatible21st row, all480 residual
columns, and all115440 full-versus-old kernel entries.

The intended input kernels are
experiments/logs/root-prism-free/f0-full-core-schur-kernels01.json.gz:
archive SHA256 a49b8309032b2c599c637285f4a4584bb7d55659640e594df1e6fdd50bf826c1,
raw SHA256 a963a88606a9fad78576d711f6ef7bf67eb03032176cebc2af5af700ea7c6708.
The plus primitive-kernel value SHA256 is
91017b1ad1ea6ff3433e91030586ec820f939a158f8cf3aab0cbf77e4ef574ed.

The intended domain is
experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz:
archive SHA256 665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4,
raw SHA256 fa3bd2e5bb541d58cb647aa1d3df95a9d3c17e394836a657ad4f4bf6eb5f6bfe.

No newly generated pair states, cut count, source execution, or native
acceptance is asserted in this theorem note.
