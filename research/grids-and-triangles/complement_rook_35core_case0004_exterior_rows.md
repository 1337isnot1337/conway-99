# Exterior-row inequalities for 35-core case 4

This package prepares a necessary row test for the unresolved indexed
35-vertex core 4. It does not rerun its incidence SAT formula. The saved
real incidence point remains numerical-only.

## Exact identity and eligible neighbors

Write a hypothetical adjacency matrix as

\[
A=\begin{pmatrix}B&X\\X^T&C\end{pmatrix},
\qquad A^2+A=12I+2J,
\]

where \(B\) is this 35-core. Its complete attachment domain contains 1,214
binary columns \(h_a\). The existing original-signature capacity makes
each column's selection variable \(x_a\) binary. All 64 actual remaining
vertices must use distinct columns from this domain.

For a selected column define

\[
q_a=2\mathbf1-h_a-Bh_a,\qquad d_a=14-|h_a|,
\qquad t_a=(q_a,d_a),\quad w_b=(h_b,1).
\]

The mixed block equation and the degree equation give

\[
\sum_b w_b y_{ab}=t_a x_a,
\qquad 0\le y_{ab}\le x_b,
\]

where \(y_{ab}\) is the actual exterior adjacency indicator, and is zero
when either endpoint is absent.

Every actual edge satisfies three conditions:

1. \(h_a^T h_b\le1\), because an adjacent pair has one common neighbor.
2. Every position in \(h_b\) has positive quota in \(q_a\).
3. Every position in \(h_a\) has positive quota in \(q_b\).

The prepared domain retains exactly the pairs satisfying these tests.
It checks all 736,291 unordered pairs and retains 275,578 possible edges.
Candidate neighbor counts range from 214 through 866. No automorphism,
fixed incidence design, or additional Gram-conflict filter enters this
edge domain.

## A universally necessary integer inequality

For any integer vector \(v\in\mathbb Z^{36}\), multiplication of the row
identity and endpoint activation give

\[
(v^Tt_a)x_a
=\sum_b(v^Tw_b)y_{ab}
\le\sum_b\max(v^Tw_b,0)x_b.
\]

Only vectors with \(v^Tt_a>0\) are retained. The discarded terms are
nonpositive, and every retained neighbor variable is at most its column
selector. This proves the inequality directly for every actual
completion. Its validity does not depend on the saved numerical proposal
or on any LP status. These inequalities are not asserted to follow from
the old Gram-only real cone.

The preparation includes a known rook graph control: four exact exterior
rows in SRG(9,4,1,2), with all six coordinates checked. It also checks 1,116
positive integer potentials on those rows and 3,375 elementary signed
product/activation assignments.

## Bounded discovery plan

The proposal is the immutable case 4 numerical result with the 30 checked
binary Gram cuts. Values below \(10^{-9}\) are set to zero and values
above \(1-10^{-9}\) to one, solely for numerical discovery. There are 291
positive entries. The plan takes the 32 largest entries, breaking ties by
column index. It fixes neither an incidence design nor a graph.

Across these 32 rows there are 17,477 possible neighbor variables and 94,158
nonzero entries in the matrices with columns \(w_b\). The row LP is

\[
Wy=t_a\widehat x_a,\qquad 0\le y_b\le\widehat x_b.
\]

The separately named pilot source uses the bounded dual instead:

\[
\max_{-1\le v_i\le1,\ s_b\ge0}
\widehat x_a(v^Tt_a)-\sum_b\widehat x_b s_b,
\qquad s_b\ge v^Tw_b.
\]

The planned limits are two seconds per row and 60 seconds overall, one
thread, no retries, and a stop at the first nonoptimal row status. Each
row is checkpointed. There is no new global LP or SAT query. Rational
reconstruction supplies integer potentials; the full coefficient list
is then recomputed exactly from all eligible neighbors. Reported
separation of the numerical proposal remains a numerical diagnostic.

## Files and replay

The preparation source is
`experiments/workspace/complement_rook_35core_case0004_exterior_rows.py`.
The compressed exact domain and 32-row plan are
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-exterior-rows.json.gz`.
The discovery/replay source is separately named
`experiments/workspace/complement_rook_35core_case0004_row_separation.py`.

The optimizer-free preparation replay is:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_exterior_rows.py \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-exterior-rows.json.gz \
  --replay
```

At preparation freeze, no row optimizer has been called and no new
inequality or case exclusion is claimed. Any later terminal result and
integer certificates belong to a separate artifact package.
