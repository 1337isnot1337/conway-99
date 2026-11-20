# Smaller conditional models indexed by one core point

Two earlier conditional contradictions fit inside a one-core-point subsystem
of the complementary-rook joint model. The prepared reduced subsystem has
4,456 edge variables and 144,864 clauses. It keeps every incidence selector;
it does not fix a 72-column design or impose graph symmetry.

The preparation makes no new SAT query. Its controls reconstruct the exact
old baseline and transport two already checked retained proofs into the new
subsystems. The reduced models and their proofs also passed an exact readback
replay.

## Definition of the subsystem

Use the fixed complementary-rook 27-core, its complete 252-signature domain,
and its complete 20,934-edge eligibility domain. Let \(z_s\) select signature
\(h_s\), a three-element subset of the core. For a core point \(i\), define

\[
S_i=\{s:i\in h_s\}.
\]

There are 28 candidates in \(S_i\). The Gram diagonal requires exactly eight
of them to be selected. Retain every eligible edge with an endpoint in
\(S_i\), every selector, every Gram equation, and all endpoint activations
for retained edges. Retain all mixed rows for a source in \(S_i\). For each
other source, retain its mixed row targeting \(i\). These latter rows use
only edges to \(S_i\), so they require no omitted edge variable. Retain every
core-pair packing clause whose two edges are retained.

The first prepared version also keeps the explicit population row and the
degree row of each source in \(S_i\). It is exactly a selected subsystem of
the frozen full formula, up to an explicit renaming of counter variables.
Every full completion restricts to a solution. The reverse assertion is not
claimed: a star solution need not extend to the full joint model.

For a selected source \(s\in S_i\), the mixed demand at \(i\) is one. Hence
the eight selected vertices in \(S_i\) form a perfect matching among their
retained edges. This condition is already encoded by the mixed rows and
activation.

## Removing the population and degree counters

The reduction deletes two kinds of redundant cardinality encoding. It keeps
all conditional mixed gates and endpoint activations.

The core Gram diagonal is eight at each of 27 coordinates, and every
signature has weight three. Summing the diagonal equations gives

\[
3\sum_s z_s=27\cdot8=216,
\qquad \sum_s z_s=72.
\]

Thus the explicit population counter is unnecessary.

The core adjacency matrix \(B\) has row sum six. The mixed demand for source
\(s\) is

\[
d_s=2\mathbf1-(B+I)\mathbf1_{h_s},
\qquad \sum_{j=0}^{26}d_s(j)=54-7\cdot3=33.
\]

If \(s\in S_i\) is selected, all 27 mixed rows are retained. Each incident
edge appears in exactly three of those rows, once for each core neighbor of
its other endpoint. Their sum therefore gives

\[
3\sum_t a_{st}=33,
\qquad \sum_t a_{st}=11.
\]

If \(s\) is absent, activation forces every incident edge to zero. Thus the
conditional degree equation follows in both cases.

Deleting the explicit degree and population counters preserves the primary
solutions of the star subsystem. One direction is restriction. In the other
direction, the identities above give every omitted cardinality equation;
its counter variables can be supplied independently, because all counter
blocks have disjoint auxiliary variables. This proves equivalence to the
parent star on selectors and retained edges, not equivalence to the full
joint model's existential projection.

## Exact sizes

The two prepared instances use \(i=R_8\) and \(i=R_3\).

| Formula | Eligible edge variables | Declared variables | Clauses |
|---|---:|---:|---:|
| Frozen full joint model | 20,934 | 1,156,482 | 2,575,728 |
| One-point star with redundant counters | 4,456 | 187,262 | 387,840 |
| Reduced one-point star | 4,456 | 65,774 | 144,864 |

Each reduced instance retains 208 distinct Gram equations, 952 distinct
mixed equations, 8,912 activation clauses, and 35,356 packing clauses. The
reduction deletes 51,840 population clauses and 191,136 degree clauses.

Primary variable numbers stay unchanged to preserve selector and edge
bindings. Consequently, 16,478 primary-number gaps are declared but unused.
These gaps do not represent additional modeled edges and must not be read as
edge decisions when inspecting a solver assignment. The retained edge list
in each model manifest is authoritative.

## Existing proof controls

The original case 4 proof fits the \(R_8\) star; the original case 5 proof
fits the \(R_3\) star. Preparation regenerates the full baseline as a stream,
checks its exact hash, and records an explicit counter-interval map for each
selected group. An all-nine-\(R\)-points control selects every source and
reproduces the complete old baseline byte hash after the same mapping code.

Every retained old input clause is then checked against the star formula
plus its signed selector units. The renamed proof is verified by DRAT. In
the second reduction, every one of those input clauses survives the removal
of population and degree counters. No substituted input lemma is needed.
The two proofs again pass DRAT after the remaining counters are compacted.
Neither transport requires a fresh proof-only variable.

The newer eleven-positive-signature proof has broader saved support. Its
retained input uses 541 mixed equation groups and counters from 87 source
vertices. The smallest core-point set containing its recorded proof support
has size nine, attained by all nine \(R\) points. This does not rule out a
different proof in a smaller subsystem.

## Canonical queries and the tip star

The reduced preparation exports 18 explicit core relabellings taking
canonical point \(R_8\) to every \(R\) or \(S\) core point. Each transport
is checked on signatures, core adjacency, mixed demands, and the entire
retained edge domain. To query an actual incidence pattern at another point,
apply the inverse signature action before querying the canonical model.
Transport a certified selector cut back with the forward action. This is
relabelling of possible completions, not a graph automorphism assumption.

The \(T_0\) domain has 28 candidate signatures and 4,346 eligible incident
edges. The present package records that domain count only. It does not build
or solve a tip-star formula.

## Files and replay

The frozen full-star source is
`experiments/workspace/complement_rook_core_star_oracle.py`.
Its models, exact support audit, and transported proofs are in
`experiments/logs/grids-and-triangles/complement-rook-core-star-preparation/`.

The separate reduced source is
`experiments/workspace/complement_rook_core_star_reduced.py`.
Its models, identities, 18 transports, and transported proofs are in
`experiments/logs/grids-and-triangles/complement-rook-core-star-reduced-preparation/`.

```sh
.venv/bin/python experiments/workspace/complement_rook_core_star_reduced.py \
  --directory experiments/logs/grids-and-triangles/complement-rook-core-star-reduced-preparation \
  --cache-directory /tmp/conway-complement-rook-core-star-reduced \
  --drat-trim /tmp/conway99-drat-trim/drat-trim \
  --replay
```

If the optional full-star CNF caches are absent, replay regenerates them from
the frozen parent source and verifies their hashes. The replay rebuilds the
reduced formulas, verifies their exact hashes, checks all retained-input
inclusions, verifies both proofs, and rechecks all 18 transports. It makes no
SAT query. No free-star feasibility result or new master enumeration is
claimed in this preparation.
