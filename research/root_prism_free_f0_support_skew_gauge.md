# Finite support-restricted skew gauges

The accepted run03 support certificate has demand 176, positive internal
capacity 172, and gap 4. Its sixty supported potentials use all eighteen
sites. The earlier single-anchor reanchoring construction does not apply
directly to this certificate.

This construction changes the supported potentials while preserving that
gap. It considers every site pair and both unit signs. The family contains
306 gauges and at most 3,672 transported rows before exact deduplication.
The construction makes no optimizer call.

## Universal allocation inequality

Let `h_a` be the eighteen-coordinate incidence vector of signature `a`, and
let `q_a` be its mixed-row target. Write `x_a` for a selector and `y_ab` for
an eligible exterior edge. Every admissible exterior graph satisfies

\[
\sum_{b:\{a,b\}\text{ eligible}} h_b y_{ab}=q_a x_a,
\qquad 0\le y_{ab}\le x_a,\quad y_{ab}\le x_b.
\]

For arbitrary integer potentials `v_a`, define

\[
\delta_a=v_a\mathbin{\cdot}q_a,
\qquad w_{ab}=v_a\mathbin{\cdot}h_b+v_b\mathbin{\cdot}h_a.
\]

Choose one endpoint `e(ab)` for every edge with positive weight. Multiplying
the mixed equations by the potentials gives

\[
\sum_a\delta_a x_a
=\sum_{\{a,b\}}w_{ab}y_{ab}
\le\sum_{w_{ab}>0}w_{ab}x_{e(ab)}.
\]

This is a universal selector inequality. The chosen support selects the
potentials and the endpoint allocation; it is not a premise about the next
selector assignment. The frozen allocator charges an internal positive edge
to its smaller support endpoint and a boundary positive edge to its outside
endpoint. All outside potentials are zero.

## Gap-preserving changes

For each `p < q` and `t` in `{-1, 1}`, use the skew matrix with entries
`M[p,q] = t`, `M[q,p] = -t`, and all other entries zero. On the saved support,
replace `v_a` by `v_a + M h_a`. Keep every outside potential zero.

For an internal edge, the weight change is

\[
(Mh_a)\mathbin{\cdot}h_b+(Mh_b)\mathbin{\cdot}h_a=0.
\]

The total demand change is

\[
t\sum_{a\in S}
\bigl(h_a[q]q_a[p]-h_a[p]q_a[q]\bigr).
\]

Preparation checks these 153 integer sums directly on the accepted saved
candidate. All are zero. This uses the actual data and does not assume an
additional unverified Gram identity. Generation also recomputes the demand
and every internal edge weight from each modified potential array.

For a boundary edge from `a` in the support to `b` outside, the change is

\[
t\bigl(h_a[q]h_b[p]-h_a[p]h_b[q]\bigr).
\]

The producer enumerates these derivatives from every boundary edge in the
complete 68,394-edge domain. It updates the outside endpoint coefficient by
the exact change in `max(0, w_ab)`. Internal allocations remain unchanged.
There are 15,643 boundary edges and 136,280 nonzero pair/edge derivatives.
The prepared baseline contains 1,223 internal edges.

## Transports and completeness

The producer reconstructs all twelve core actions and checks that they
preserve every signature, target, and eligible edge. A transported cut uses
the transported original endpoint allocation. Its internal tie order is the
inverse transported order, as in the frozen lifting source. Permuting a
valid coefficient row therefore gives a valid transported inequality.

The catalogue retains all 306 raw coefficient vectors, their potential
digests, gcds, and invariant checks. It also retains all 3,672 gauge/action
coverage records. Deduplication compares complete canonical terms and the
right-hand side against all 12,481 parent rows and every new row. Every new
row keeps all gauge/action origins. No row is selected by its effect on a
previous candidate, and every parent row must remain.

At most 3,672 new rows can result, so the following registry has at most
16,153 rows. This fits the existing 16,384-row capacity and leaves room for
96 further rows. This bound does not predict the number of distinct new rows.

## Execution state

Source: `experiments/workspace/root_prism_free_f0_support_skew_gauge.py`.
Configuration: `f0-support-skew-gauge-configuration01.json`.
Preparation: `f0-support-skew-gauge-preparation01`.

Preparation passed in 6.647 seconds of owner time, with no optimizer or native
solver import. It reconstructed the complete accepted baseline certificate,
including all twelve old transported rows. The finite census has a separate
120-second owner and requires a root gate. Its proposed rows require an
independent cold before use as new master seeds. The main census and any
later native query are separate actions.

This construction does not claim a graph or exclusion of the whole F0
component.
