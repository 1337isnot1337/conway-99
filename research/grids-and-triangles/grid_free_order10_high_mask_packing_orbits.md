# Exact root-label quotient of the packing moment model

The empty six-root moment model reduces to **73 equations in 249
nonnegative variables**, with 3,951 nonzero coefficients. This is equivalent
to the full 17,903-row, 90,776-column moment model at the bound count point.
No optimizer was called by this preparation.

## The action and its coverage

The symmetric group \(S_6\) acts on the six specified root positions. It
permutes the 42 high neighborhood masks, their squarefree monomials, and
the complete atom domain. This is a relabelling of root embeddings. It
does not assume an automorphism of the hypothetical host graph.

The preparation uses the five adjacent root transpositions. These generate
all of \(S_6\). It checks their induced actions on all 132,062 baseline
atoms, all 90,776 structurally allowed atoms, and all 124,314 monomial rows.
It also checks exact constancy of the saved moments under every generator.
There are 1,735,760 domain-closure checks and 621,570 moment comparisons.

Deterministic breadth-first search gives complete orbit partitions. Every
nonrepresentative row and atom has a saved predecessor and generator step,
which form an explicit transport from its representative. All orbit sizes
divide 720. Every saved transport has length at most 15.

There are 249 atom orbits and 500 monomial orbits. Of the latter, 427 have
identically zero support on the structural atom domain. The other 73 cover
all 17,903 positive moment rows.

## Integer quotient and uniform lift

Let \(R\) be a monomial orbit and \(O\) an atom orbit. Choose representatives
\(T_R\) and \(S_O\), and define

\[
C_{R,O}=\#\{T\in R:T\subseteq S_O\},\qquad
b_R=\sum_{T\in R}m_T.
\]

The quotient variable \(u_O\) is the **total** mass assigned to atom orbit
\(O\). The quotient equations are

\[
\sum_O C_{R,O}u_O=b_R,\qquad u_O\ge0.
\]

The constant row has coefficient one in every column. Its right side is
72,926,995,680, the labelled empty-root mass.

An arbitrary solution of the original model can be averaged over root
relabellings. Moment invariance preserves every equation, and nonnegativity
is preserved. Its orbit totals therefore solve the quotient.

Conversely, a quotient solution assigns mass \(u_O/|O|\) to each atom in
\(O\). To verify this lift, define

\[
D_{R,O}=\#\{S\in O:T_R\subseteq S\}.
\]

Double-counting incidences between the two orbits gives

\[
|O|C_{R,O}=|R|D_{R,O}.
\]

For each \(T\in R\), the lifted moment is consequently

\[
\sum_O \frac{u_O}{|O|}D_{R,O}
=\frac1{|R|}\sum_O C_{R,O}u_O
=\frac{b_R}{|R|}=m_T.
\]

The source computes \(C\) from the saved complete feature matrix. It
computes \(D\) independently from literal bit-subset tests on every
structurally allowed atom. All 124,500 entries of the displayed identity
are checked exactly. No automorphism-order division is inserted into the
labelled moment data.

## Controls, bounds, and artifacts

Literal averaging controls use empty roots of orders two, three, and four.
They enumerate every root permutation and every admissible high-mask atom.
They check 422 transports and recover all 34 individual moments from their
quotients by exact rational uniform lifts.

The actual quotient coefficients are at most 60. The verified incidence
product bound is 518,400. The right-side summation bound is
52,507,436,889,600, below \(2^{63}\). Python integers establish these bounds
before fixed-width multiplication.

Preparation took 2.94 seconds with peak RSS 120,672 KiB. It loaded the
frozen matrix and moment arrays; it loaded no graph-product tensor or
reduced count matrix.

Source: experiments/workspace/grid_free_order10_high_mask_packing_orbits.py,
SHA256
59af3f038c1f2795d03d11a80eaee363832f748bcc9863245b8237c71d8d73cd.

Result: experiments/logs/moments-and-counts/order10-high-mask-packing-orbits01.json,
SHA256
a6ca65e8edeb1d4545e89c28833bf7526c693ce6066ec5b6f15a47d31853c61d.

The result binds the complete orbit, transport, quotient, and literal
incidence arrays. A later numerical query must separately produce an exact
rational primal witness or an exactly checked separating polynomial.
Neither outcome would by itself decide the Conway graph problem.
