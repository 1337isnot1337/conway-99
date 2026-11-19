# Two-dimensional arithmetic for the F0 core group

The stored 480-signature action identifies the core group as
\(S_3\times C_2\). The four real one-dimensional representations have
multiplicities \(42,38,42,38\). The two remaining irreducible representations
have dimension two and multiplicities 84 and 76.

For one literal selector assignment, each corresponding multiplicity Gram
matrix has rank at most two. Its two-by-two determinants are three times
integer squares. These are nonlinear necessities of a realizable count
assignment. Arbitrary mixtures of different assignments need not satisfy them.

The preparation builds only three columns of the 84-column block and their
six exact count forms. It also checks nine combinations from one pair of
already-frozen local profiles. No full block, local subset census, optimizer,
or production count point was evaluated. The small preparation took 0.839
seconds.

## The actual group and integer representations

The source recomputes all 144 products from the saved literal permutations,
using \((ab)(j)=a(b(j))\), and compares the result to the character record.
In that fixed numbering, let

\[
r=3,\qquad r^2=4,\qquad s=1,\qquad z=6.
\]

The checked relations are

\[
r^3=s^2=z^2=1,\qquad srs=r^{-1},\qquad zg=gz.
\]

The twelve expressions \(r^is^jz^k\), with \(0\le i<3\) and
\(0\le j,k<2\), are distinct. The center is \(\{0,6\}\). The common kernel
of all four real characters is \(\{0,3,4\}=\langle r\rangle\).

Use the integer matrices

\[
R=\begin{pmatrix}0&-1\\1&-1\end{pmatrix},\qquad
S=\begin{pmatrix}0&1\\1&0\end{pmatrix},\qquad
H=\begin{pmatrix}2&-1\\-1&2\end{pmatrix}.
\]

The two representations are
\(\rho_\epsilon(r^is^jz^k)=\epsilon^kR^iS^j\), for
\(\epsilon\in\{1,-1\}\). The source checks every matrix product and
\(\rho_\epsilon(g)^TH\rho_\epsilon(g)=H\). The matrix \(H\) is positive
definite and has determinant three.

The six character vectors are pairwise orthogonal, with squared norm twelve
under the unnormalized group sum. Their squared dimensions sum to twelve.
Thus these are all irreducible representations. Their inner products with
the literal permutation character give the multiplicities above.

There are 38 selector orbits of size twelve and four of size six. Every
size-six orbit has stabilizer \(\{0,6\}\). A free orbit contributes two
copies to each two-dimensional representation. A size-six orbit contributes
two copies to \(\rho_+\) and none to \(\rho_-\). Hence

\[
m_+=38\cdot2+4\cdot2=84,\qquad m_-=38\cdot2=76.
\]

The full isotypic subspaces have dimensions 168 and 152. Their multiplicity
Gram matrices have sizes 84 and 76 and rank at most two. The full averaged
isotypic moment blocks can have rank four.

## Literal columns and their normalization

Fix a selector orbit \(O\), an anchor \(a\in O\), and an integer vector
\(u\) fixed by \(\rho(G_a)\). Define

\[
f_{O,u}(ga)=\rho(g)u.
\]

This is well-defined: two transports to the same selector differ by an
anchor stabilizer, which fixes \(u\). For a literal Boolean assignment
\(x\in\{0,1\}^{480}\), let

\[
w_{O,u}(x)=\sum_{a\in O}x_a f_{O,u}(a)\in\mathbb Z^2.
\]

Relabeling the entire assignment by \(g\) sends every column simultaneously
to \(\rho(g)w_{O,u}(x)\). It is not an assumption that the graph has this
automorphism. It is a change of the fixed core labeling.

Collect these vectors as columns of \(W\), and define

\[
B=W^THW.
\]

Every entry is invariant under the simultaneous group action. It is therefore
an exact linear form in the existing selector-orbit populations \(N_i\) and
unordered selector-pair populations \(P_R\).

The coefficient extraction uses

\[
B_{pq}=\sum_a x_a f_p(a)^THf_q(a)
 +\sum_{a<b}x_ax_b\bigl(f_p(a)^THf_q(b)+f_p(b)^THf_q(a)\bigr).
\]

The first sum uses \(x_a^2=x_a\). Both orders in the second sum are required,
including when the two columns have different supports. Each coefficient is
checked on all literal members of its orbit. There is no division by twelve,
by a stabilizer, or by a representation dimension in this definition of
\(B\). The populations are counts, and the displayed expansion directly
counts their contributions.

The six prepared entries use the basis vector \((1,0)^T\) on selector orbits
2, 3, and 4 in \(\rho_+\). The record retains original pair coefficients,
the separately listed proved-zero terms, and the resulting reduced native
count forms. The full 84- and 76-column blocks would contain 3,570 and 2,926
lower-triangle entries; those blocks were not constructed.

## Integer square and cubic conditions

For any two integer columns \(u,v\),

\[
\det\begin{pmatrix}u^THu&u^THv\\v^THu&v^THv\end{pmatrix}
=\det(H)\det[u,v]^2
=3\det[u,v]^2.
\]

Consequently,

\[
B_{pp}B_{qq}-B_{pq}^2\in\{3t^2:t\in\mathbb Z\}.
\]

Also \(B_{pp}=2(a^2-ab+b^2)\) is even. A nonnegative two-by-two determinant
alone is weaker than the integer-square condition.

All three-by-three minors vanish because \(W\) has two rows. For a principal
submatrix

\[
\begin{pmatrix}a&b&c\\b&d&e\\c&e&f\end{pmatrix},
\]

the exact necessary equation is

\[
adf+2bce-ae^2-dc^2-fb^2=0.
\]

Its six entries are linear count forms, so this is a cubic equality in the
native counts. Vanishing principal minors should not be confused with a
complete rank certificate without the other matrix conditions. The full
rank-two condition requires all relevant minors; any single violated minor
is already a valid obstruction for that fixed count assignment.

## The small profile pair is already constrained

The tested profiles are tuple index 4 on selector orbits 2 and 3. Each has
population one, all within-orbit pair counts zero, and all three signed
populations equal to one. Each saved inverse domain is
\(\{1,4,1024\}\), containing three singleton masks.

Their vectors are the three cyclic images
\((1,0)^T,(0,1)^T,(-1,-1)^T\). Both diagonal Gram entries equal two. Among
the nine literal combinations, the cross entry is two in three cases and
minus one in six cases. Every case satisfies the exact area-square identity.

Prior pair zeros remove six combinations. The three remaining literal pairs
are \(\{8,203\}\), \(\{19,9\}\), and \(\{202,16\}\); all belong to
original pair orbit 1127 and have cross entry minus one.

This particular pair supplies no new restriction beyond the current
one-dimensional products, nonnegative pair counts, and pair zeros. Under
these profiles, average the trivial product and the three signed-character
products. Character orthogonality selects the relative-kernel pair orbits
942, 949, and 1127 and forces their total to be one. The first two are already
zero, so \(P_{1127}=1\). The preparation does not claim new strength from this
small table.

## Why the rank condition needs its stated scope

For three singleton columns, compare the vector triples

\[
((1,0),(1,0),(1,0)),\qquad
((1,0),(0,1),(-1,-1)).
\]

The source realizes these vectors through literal selector sets
\(\{8,9,10\}\) and \(\{8,203,18\}\). Their N populations and all 118
one-dimensional signed populations agree because each change uses the
common order-three kernel. Their two-dimensional Grams are
\(2J\) and \(3I-J\). The mean Gram is \((3I+J)/2\), whose determinant is
\(27/4\), although both individual Grams have determinant zero.

This is an algebraic mixture control. It is not a feasible F0 count point,
an integer count candidate, or a pair of completed graphs. It shows that the
one-dimensional outer-product identities alone do not imply the missing
rank-two condition. It does not establish nonredundancy against every other
constraint in the current F0 model.

The next useful application would be an exact minor or square test at a
future accepted count assignment, or a separately prepared small table for a
pair of profiles whose cross entries are not already forced. Neither was
run here.

## Frozen files

Source:
`experiments/workspace/root_prism_free_f0_two_dimensional_moments.py`, SHA-256
`31793743ba11fb56f42bcc9f383fe8b3268dae1cd8ebf6ec0271160a1d58d2fd`.

Record:
`experiments/logs/root-prism-free/f0-two-dimensional-moments-scope01.json`,
SHA-256 `948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f`.

The source binds the existing action, count, character, and complete inverse
records by SHA-256. The literal-lift intake remains a separate package.
