# Complete retained-pair packing preparation for F0

For each retained selector-pair orbit \(R\), form a finite graph whose
vertices are the literal unordered pairs in \(R\). Two vertices are
compatible exactly when the union of their endpoints contains no
previously proved-zero selector pair. Shared endpoints remain part of
this literal union; they do not create a false conflict or a multiplicity
factor.

If the Boolean selectors are \(z_a\), the pair population is

\[
P_R=\sum_{\{a,b\}\in R}z_a z_b.
\]

The active pair objects form a clique. Therefore \(P_R\leq\omega(G_R)\).
This is valid for actual Boolean incidences. A generic fractional
second-moment point need not obey it until the inequality is added.

## Complete finite scope

The preparation retains all 9,353 nonzero pair orbits, containing 110,550
literal pair sites. Their sizes are:

| Pair-orbit size | Retained orbits |
|---:|---:|
| 3 | 12 |
| 6 | 263 |
| 12 | 9,078 |

The other 389 original pair orbits are the already proved zeros. Their
4,410 literal pairs comprise 4,320 quota-one Gram witnesses and 90
previously cold-checked binary-motif witnesses. The preparation preserves
this distinction. It directly checks the former supports and binds the
existing complete cold record for the latter.

All twelve actual core actions are checked as permutations and as a
closed group on the 480 selectors. The preparation checks the entire
zero set under each action and recovers every original pair orbit from
its anchor. The retained compatibility graph is consequently
vertex-transitive. No automorphism of a hypothetical 99-graph is assumed.

Every maximum clique can be transported to contain the anchor, so

\[
\omega(G_R)=1+\omega(G_R[N(\text{anchor})]).
\]

The scan will also explicitly check the action on each constructed graph.

## Exact certificate and workload

The reusable helper uses the elementary recurrence

\[
\omega(S)=\max\bigl(\omega(S\setminus\{v\}),
  1+\omega((S\setminus\{v\})\cap N(v))\bigr).
\]

Its certificate gives every visited subset value and a clique of the
claimed size. Replay verifies the closed recurrence set and the clique
without rerunning the maximum-clique search.

There are at most 603,129 pair-object comparisons and 3,618,774 literal
endpoint-pair checks. The full anchor-subset bound is 18,600,208 states;
memoization usually visits fewer states. This is a workload bound, not a
production result.

Each completed orbit will retain its complete adjacency, a literal
proved-zero witness for every incompatibility, its anchor certificate,
the exact count bound, and a partial selector set attaining that bound
under the pair-zero premises alone. The latter is not a full incidence.
The independent cold path reconstructs adjacency from literal endpoint
combinations rather than the producer's bitset test.

The planned scan has a 60-second cooperative limit and a 64 MiB raw
certificate-stream limit. Its separate saved-prefix cold replay also
has a 60-second limit. Completed records survive a timeout; no automatic
retry is allowed. Neither stage invokes an optimizer.

## Comparison and controls

Every bound is compared with the original orbit-size box and with the
exact domains in the frozen character-pool plan
`f0-character-pool-model01/plan.json.gz`, SHA256
`b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef`.
That model's first 15,038 native IDs are unchanged. A smaller explicit
upper bound is not a claim of independence from every existing equation
or inequality.

The preparation passed in 1.71 seconds. It checked all 1,100 simple
graphs through five vertices against 33,867 exhaustive subsets and
rejected two corrupted certificates. It also checked all 729 choices
of a zero set and retained pair-site set on four selectors against
11,664 Boolean assignments. Of those models, 425 contain shared
endpoints. Both previously proved bound-two graphs are reproduced by
the generic helper.

The complete production compatibility family remains unqueried in this
preparation package. No incidence or graph existence claim follows.

## Files

- `experiments/workspace/finite_graph_clique_certificate.py`
- `experiments/workspace/root_prism_free_f0_pair_orbit_packing.py`
- `experiments/logs/root-prism-free/f0-pair-orbit-packing-preparation01.json.gz`

The preparation source binds every input and the helper. Production and
cold records will be separate immutable artifacts after their review gate.
