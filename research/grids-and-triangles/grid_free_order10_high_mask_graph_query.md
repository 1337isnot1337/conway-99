# Exact query of the decorated high-mask moment table

This package prepares one feasibility query for the complete saved high-graph domain over an independent six-vertex root. It has 200 moment equations and 18,427 distinct feature columns. The inverse column map retains all 157,711 graph decorations.

The target is the exact 48-cut count point with SHA `0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`. Preparation does not query the production model. It runs two tiny backend controls and exact arithmetic controls.

## Exact outcome

The single primal query returned an exact finite decorated-moment witness. It has 200 positive graph masses, with common denominator

\[
1,841,072,799,597,249,500,967.
\]

All 200 equations pass exact rational checks. Uniform averaging over root relabelings gives every one of the 73,263 individual pattern moments. The numerical solve used 3.210 seconds; the complete query and exact verification used 5.665 seconds and 235,360 KiB peak resident memory. The largest numerator has 103 bits and the largest denominator has 71 bits.

A separate cold invocation reloaded all bound inputs, checked the rational weights and their representative graphs, and replayed the uniform lift without invoking an optimizer. No dual optimization or second production query ran.

Thus every linear combination of these induced-pattern indicators that is nonnegative on the complete stated graph domain has nonnegative expectation at this point. This conclusion covers the empty six-root model through four high vertices. It does not resolve compatibility with other root types, low-mask vertices, or a complete graph.

## The finite domain and its moments

A high class specifies at least three of the six root neighbors. Each class has at most one vertex, since distinct vertices cannot have three common neighbors. The saved domain contains every allowed presence packing and every induced high graph satisfying the stated visible common-neighbor caps, after choosing one representative of each root-label orbit of presence packings.

The 200 row orbits contain all rooted induced patterns on at most four high vertices. A row coefficient counts the free-vertex subsets of a domain graph whose induced pattern belongs to that row orbit. It does not count arbitrary ordered free labels.

For a fixed labelled pattern (T), summing its indicator over labelled root embeddings gives

\[
m_T=|\operatorname{Aut}(F_T)|\,n(F_T),
\]

where (F_T) is the complete root-plus-free graph and (n(F_T)) is its unlabelled induced count. Thus a row orbit (R) has right side

\[
b_R=|R|\,|\operatorname{Aut}(F_T)|\,n(F_T).
\]

The separate direct-moment package checks this normalization by literal root embeddings, including root-moving automorphisms. There is no additional stabilizer divisor. All 200 right sides are positive at this point. Their constant entry is (g=72,926,995,680).

## Why the quotient preserves feasibility

Every full graph decoration has a saved distinct-column identifier. Identical columns can share one total mass because they give the same value in every equation. Conversely, that mass can be assigned to the saved representative graph of the column.

Average each chosen representative over all 720 root relabelings. For an individual pattern in row orbit (R), its average indicator is (C_{R,O}/|R|). Therefore the equations (Cw=b) recover all 73,263 individual pattern moments after this uniform lift. This averages a distribution over labelled root embeddings. It makes no claim that a hypothetical 99-vertex graph has an automorphism.

Preparation replays the full-column checksum, every column's aggregation to all 73 earlier presence equations, and the partition by free-vertex count. It also checks the saved unimodular minor. Its 200 columns are the row patterns themselves; ordering by free-vertex count makes the minor triangular with diagonal one. Thus the exact row rank is 200.

## Numerical query and exact acceptance

The single numerical invocation is

\[
Cw=b/g,\qquad w\geq0,
\]

with zero objective. The constant row gives \(\sum w=1\). There are no finite upper bounds on individual weights. HiGHS runs with one thread and a 30-second budget shared by the primal solve and any returned infeasibility ray. There is no automatic second query or dual optimization.

The complete numerical output is saved before an exact stage of at most 60 seconds. For an optimal numerical result, the saved basis proposes a support. Exact rational elimination solves the original integer equations (Cu=b) on that support. Every equation and every sign is then checked. A second support may be read from the same saved numerical primal; this does not invoke an optimizer.

A valid rational measure is saved with its representative graphs and uniform root-label lift. This is a finite moment witness. It does not construct an integer embedding measure, a compatible family over other root types, or a 99-vertex graph.

## Exact inequality from a returned ray

The old Boolean-monomial certificate helper is not used for this table. The rows retain induced high edges, so they are induced-pattern indicators.

Instead, round a proposed ray to integer row coefficients \(\lambda\), and evaluate every distinct column exactly. Let

\[
q=\min_O\lambda^TC_O.
\]

The constant row is one on every graph. Replacing \(\lambda_0\) by \(\lambda_0-q\) makes the polynomial nonnegative on every full graph decoration. Division by a positive common gcd preserves that property. Only a strict negative exact value at (b) is accepted as a separator.

The inverse column map checks the inequality on all 157,711 full decorations. Each row already has an independently audited single-coordinate induced-count form. Their exact linear combination gives the corresponding induced-count inequality. Its use in a later optimizer remains disabled until the new certificate is reviewed.

Column contractions use signed 64-bit integers only after an absolute-sum guard. The largest column sum is 386. Larger coefficients use Python integers. All moment objectives and induced-count contractions use Python integers regardless of the column guard.

## Controls and preserved preparation failure

The controls include exact feasible, negative-mass, inconsistent and dependent-support systems. Two finite-table separator controls include a 202-bit input coefficient. Twenty-five small polynomials are checked against a known positive measure. Two direct root-relabeling controls each enumerate all 720 permutations.

The first preparation failed in a tiny arithmetic control because `numpy.iinfo.max` was called as a method. Its source and log remain under `attempt01`. No production query or backend control had run. The corrected preparation changes that property access and completes all controls.

## Files

- `experiments/workspace/grid_free_order10_high_mask_graph_query.py`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-query-preparation.json`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-features-independent-review.json`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-query01.json`
- `experiments/logs/moments-and-counts/order10-high-mask-graph-query01-replay.json`

The frozen preparation contains all source, data, model and target-point hashes. Numerical failure or timeout does not exclude the count point. No result here resolves graph existence.
