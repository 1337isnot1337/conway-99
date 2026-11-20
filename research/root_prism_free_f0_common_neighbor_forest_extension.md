# Cap-one common neighbors: all subset forest rows in a compact formulation

This is a conditional polyhedral theorem. Fix distinct exterior candidates \(a,b\) for which every Boolean graph completion satisfies
\[
n_{ab}=\sum_c y_{ac}y_{bc}\le1.
\]
The accepted spectral pair census has 48 pairs with this unconditional exterior common-neighbor cap, applying whether \(ab\) is an edge or a nonedge. This note does not enumerate those pairs' common-neighbor supports.

The result uses only the cap and the existing endpoint activation bounds. It does not assume an induced bipartite subgraph: edges \(ab\) and edges between the other listed vertices may exist.

## Variables and the full forest family

Let \(C\) be any finite set of candidates distinct from \(a,b\). Write
\[
A=x_a,\qquad B=x_b,\qquad t_c=x_c,\qquad
u_c=y_{ac},\qquad v_c=y_{bc},\qquad e_c=u_c+v_c.
\]
Throughout the continuous statement assume
\[
0\le A,B,t_c\le1,\qquad
0\le u_c\le A,\ t_c,\qquad
0\le v_c\le B,\ t_c. \tag{1}
\]
An unavailable or already proved-zero edge is the constant zero. No positivity of a selector is assumed.

For every subset \(S\subseteq C\), and every root \(r\in\{a,b\}\cup S\), the forest inequality is
\[
\sum_{c\in S}e_c
 \le A+B+\sum_{c\in S}t_c-x_r. \tag{2}
\]
Here \(x_a=A\), \(x_b=B\), and \(x_c=t_c\).

To prove validity at Boolean graph completions, retain only the listed edges \(ac,bc\) for \(c\in S\). Every simple cycle in this subgraph of \(K_{2,|S|}\) would have length four and would give two common neighbors of \(a,b\), contrary to the cap. The listed edges therefore form a forest on the active listed vertices.

If the root is active, a forest on \(k\) active vertices has at most \(k-1\) edges, proving (2). If the root is inactive, endpoint activation removes its incident edges and the weaker bound of \(k\) edges suffices. This also covers inactive anchors. For \(S=\varnothing\), the two rows are just \(0\le B\) and \(0\le A\).

The assertion concerns the listed edges only. It places no restriction on unlisted edges within these vertices beyond whatever the original graph model already requires.

## Extended formulation

Introduce **continuous** auxiliaries \(z_c\ge0\) and \(Z\), and impose
\[
\begin{aligned}
z_c&\ge u_c+v_c-t_c &&(c\in C),\\
z_c&\le u_c,\qquad z_c\le v_c &&(c\in C),\\
Z&=\sum_{c\in C}z_c,\\
Z&\le A,\qquad Z\le B,\\
u_c+v_c+Z-z_c&\le A+B &&(c\in C).
\end{aligned} \tag{3}
\]
The bounds \(z_c\le1\) and \(0\le Z\le1\) already follow from (1) and (3), so they may also be declared explicitly.

**Theorem.** Under (1), the projection of (3) onto the original real variables is exactly the set defined by all inequalities (2). This is an exact projection statement for this specified forest family; it is not a claim that the formulation gives the convex hull of every graph constraint.

### Eliminate the exponentially many subsets

Set
\[
w_c=e_c-t_c,\qquad p_c=\max(0,w_c),\qquad P=\sum_{c\in C}p_c.
\]
Rows (2) rooted at \(a\) say
\[
\sum_{c\in S}w_c\le B \quad\text{for every }S\subseteq C.
\]
The maximum subset sum is \(P\): include precisely the positive \(w_c\). Thus this entire root-\(a\) family is equivalent to \(P\le B\). The root-\(b\) family similarly is equivalent to \(P\le A\).

For a fixed root \(d\in C\), write \(S=\{d\}\cup T\) with \(T\subseteq C\setminus\{d\}\). Its rows say
\[
e_d+\sum_{c\in T}w_c\le A+B.
\]
Maximizing over \(T\) gives exactly
\[
e_d+P-p_d\le A+B. \tag{4}
\]
The empty choice \(T=\varnothing\) is included. Consequently the complete forest family is equivalent to
\[
P\le A,\qquad P\le B,\qquad
e_d+P-p_d\le A+B\quad(d\in C). \tag{5}
\]

### Every feasible extension implies every forest row

The first line of (3), together with nonnegativity, gives \(z_c\ge p_c\). Hence
\[
P\le\sum_c z_c=Z\le A,B.
\]
For each \(d\),
\[
e_d+P-p_d
=e_d+\sum_{c\ne d}p_c
\le e_d+\sum_{c\ne d}z_c
=e_d+Z-z_d
\le A+B.
\]
These are all of (5), so every forest row follows. The coefficient of the root's own \(z_d\) cancels; there is no incorrect monotonicity assumption about a negative coefficient.

### Every point satisfying the forest rows has an extension

Choose the componentwise minimal extension
\[
z_c=p_c,\qquad Z=P. \tag{6}
\]
Nonnegativity and the lower bounds hold by definition. The endpoint bounds in (1) give
\[
e_c-t_c=u_c+v_c-t_c\le u_c,\qquad
e_c-t_c\le v_c.
\]
Because \(u_c,v_c\ge0\), this proves \(p_c\le u_c,v_c\). Thus both upper bounds on \(z_c\) hold. All remaining rows of (3) are precisely (5), which follows from the forest rows. This proves the reverse inclusion and the theorem.

## Boolean interpretation and an integrality qualification

If all original variables are Boolean, the bounds force \(z_c\) to equal \(\operatorname{AND}(u_c,v_c)\), even when \(z_c\) was declared continuous. If either edge is zero, an upper bound fixes \(z_c=0\). If both edges are one, activation fixes \(t_c=1\), and the lower and upper bounds fix \(z_c=1\).

Therefore \(Z\) is the number of listed common neighbors. The two anchor caps impose \(Z\le1\) when both anchors are active and impose \(Z=0\) when either is inactive. Conversely, a Boolean point with at most one listed common neighbor satisfies every local root row: with both anchors active, either \(z_c=1\), giving \(e_c=2\) and \(Z=1\), or \(z_c=0\), giving \(e_c\le1\) and \(Z\le1\). With an inactive anchor, all \(z_c\) vanish and the remaining endpoint bound proves the row.

Thus the Boolean projection is exactly the cap-one condition on the listed support. In an integer model the auxiliaries may be declared Boolean. The real projection theorem refers to their **continuous relaxation**.

It would be false to leave \(z_c\) integral while allowing the original variables to be real and still claim the same real projection. With one candidate, \(A=B=t_c=1\) and \(u_c=v_c=3/4\), all forest rows hold, but \(1/2\le z_c\le3/4\). A real extension exists; a Boolean extension does not.

If \(C\) is the complete set of possible common-neighbor candidates, the Boolean cap is the full \(n_{ab}\le1\) statement. A deliberately smaller \(C\) imposes only the corresponding partial cap.

## Unavailable edges and empty support

Suppose \(u_c=0\) identically. Then \(p_c=0\), and the upper bound forces \(z_c=0\). The root-\(c\) condition is redundant because
\[
e_c+P=v_c+P\le B+A.
\]
The first inequality uses \(v_c\le B\) and the anchor cap \(P\le A\). If \(v_c=0\), use \(u_c\le A\) and \(P\le B\) instead.

Accordingly a candidate with either edge unavailable or proved zero can be omitted from the extension, including its auxiliary and local root row. This preserves the continuous projection of the entire forest family over the original variables. In subset maxima such a candidate has \(w_c\le0\); if it is the root, the displayed endpoint argument handles it. This omission does not require deleting its original selector or its other edge variable.

If no candidate has two available edges, every forest inequality already follows from endpoint activation. No auxiliaries are needed. Equivalently, the unreduced extension has \(Z=0\) and only redundant rows. Empty subsets require no special positive-demand assumption.

The same reasoning applies pointwise to inactive candidates, but a candidate is removed from a fixed formulation only when the missing/zero edge premise is independently established.

## Size and fractional strength

For \(m\ge1\) candidates with both edges retained, (3) uses \(m+1\) auxiliaries and \(4m+3\) linear rows, excluding ordinary variable-domain bounds:

- \(m\) lower rows and \(2m\) edge upper rows;
- one sum equality and two anchor caps;
- \(m\) root rows.

With distinct variables and no omitted terms this is \(15m+5\) coefficient occurrences. The sum variable \(Z\) keeps the root rows at constant length.

The local root rows matter for real selectors. Take two candidates \(c,d\), let \(A=B=1/2\), \(t_c=1\), \(t_d=1/2\), and set all four edge variables to \(1/2\). Then \(p_c=0\), \(p_d=1/2\), so the lower rows, edge upper rows and two anchor caps all hold with \(Z=1/2\). The root-\(c\) row fails: its left side is \(3/2\), while \(A+B=1\). Thus the root rows cannot simply be dropped from the claimed real projection.

Larger-subset rows also strengthen the C4-only continuous relaxation. On \(K_{2,3}\), set all five selectors to one and every listed edge to \(3/4\). Each four-vertex forest row has left side three and right side three. The row for all three candidates has left side \(9/2\) and right side four. This is a local fractional example only; no compatibility with the full Conway model is asserted.

## Evidence and scope

The numerical premises are imported from already accepted artifacts, not recomputed here:

- Pair-minor theorem: research/root_prism_free_f0_spectral_gap_pair_minor.md, Git blob 168ca05d66609a2ac7027d3958a4f22c63385e1c, SHA256 169a4b0c8ba1381302d0eeacb449599a5e4913cd6a55a24bb711e5d4126829ce.
- Complete independent pair census: experiments/logs/root-prism-free/f0-spectral-gap-pair-independent-cold01.json, Git blob 38ec9167df27b86de0341f8387cc894c6d2ff8cc, SHA256 e8d27725afb707867f6683604ff1f3123f8960305c721058f495883f23476349.
- Earlier four-vertex forest note: research/root_prism_free_f0_spectral_common_neighbor_forest_rows.md, Git blob 185ae22d232388d1259d6c3fb8299f9c1102d5ad, SHA256 02d689cc545e88bfbfe31822fd93ead866902a0aecd55a1586de35ba5d4e9be5.

No support census, optimizer, model construction or native query was performed for this note. No candidate graph or whole-component exclusion is claimed. Applying the formulation to the 48 accepted pairs requires a later complete support reconstruction, literal namespace checks and a separately reviewed model change.
