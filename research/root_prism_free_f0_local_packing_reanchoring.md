# Reusing the local packing potentials at every anchor

The twelve accepted local pair-packing potentials give no further rows when
applied to all 480 possible anchors. The complete exact census checks 5,760
anchor-potential pairs. Only twelve have positive demand, and these reproduce
the original twelve inequalities. Every positive demand is one, with 69
positive eligible-neighbor weights. This closes this finite reuse test; it
does not exhaust other potentials or exclude component zero.

The validity argument permits arbitrary reanchoring. Fix an anchor `a`, integer
site potentials `v_i`, and nonnegative integer pair potentials `mu_p`. The mixed
equations and common-core-pair capacities imply

\[
t_a x_a \leq \sum_{b\in N(a)} w_b x_b,\qquad
t_a=v\mathbin{\cdot}q_a-\sum_p\mu_p,\qquad
w_b=\max\left(v\mathbin{\cdot}h_b-\sum_{p\subset h_b}\mu_p,0\right).
\]

Indeed, each pair of core sites belongs to at most one exterior neighbor of
`a`. Two such neighbors would have those sites and `a` as three common
neighbors. Apply the mixed equalities, subtract these pair capacities, and
bound each remaining positive edge term by its selector. If `x_a=0`, the
inequality follows from nonnegativity. No core automorphism taking the original
anchor to `a` is needed.

For positive `t_a`, replacing each `w_b` by `min(w_b,t_a)` gives an equivalent
inequality on binary selectors. If any selected weight reaches `t_a`, both
forms hold; otherwise their values agree. The census retains both forms.
Nonpositive demands give inequalities already implied by nonnegative selectors
and weights, so the census records them without creating a row.

The standard-library source
[`root_prism_free_f0_local_packing_reanchoring.py`](../experiments/workspace/root_prism_free_f0_local_packing_reanchoring.py)
reconstructs every target and all 68,394 eligible edges directly from the
21-vertex core and 480 triples. It uses the twelve previously certified
potentials, checks every anchor, and retains all attempts, positive weights,
row origins and normalized inequalities in the
[complete compressed certificate](../experiments/logs/root-prism-free/f0-local-packing-reanchoring01.json.gz).
The [archive record](../experiments/logs/root-prism-free/f0-local-packing-reanchoring01-archive.json)
binds the exact uncompressed bytes. A separate
[arithmetic review](../experiments/logs/root-prism-free/f0-local-packing-reanchoring-independent-review01.json)
recomputes every demand and retained row. No optimizer runs, no candidate
selection is fixed, and no current native model changes.
