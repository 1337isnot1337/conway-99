# Five-root triple-clique absence: scope census

## Scope result

The complete five-root census gives 236 triples of distinct maximal visible
incompatibility cliques after the quota-one reduction. These triples occur on
five root types and form 23 root-automorphism orbits. Their quotient matrices
have only 958 lower triangle entries in total; the largest order is 10.

This checkpoint contains domains, formal Boolean identities, root actions, and
conservative work bounds. It constructs no conditional lift and loads no product
tensor or count point. It does not evaluate a localizer or assert PSD feasibility.
All 21 admissible five-root types and all 127 allowed high masks are retained.
The family is unrestricted: no prism-free assumption or point-dependent zero is
used.

The source is `experiments/workspace/grid_free_order10_triple_clique_scope.py`,
SHA-256 `a751481867973862cd2bbbe8d0d4dab164dbbe8df733df172402ee4491fa6fec`.
The certificate is
`experiments/logs/moments-and-counts/order10-triple-clique-scope.json.gz`,
SHA-256 `7e1c352fcdfccfc2879b4cb451590173fe0d8e56d3a66db5cb28e3cb75f7573e`.
Its cold replay passed.

## Compatible-subset expansion

For a fixed labelled five-root embedding, let X_a be the indicator of an
outside neighborhood class a of size at least three. Such a class has at most
one vertex. Let X contain the constant and all these indicators.

The visible incompatibility graph joins two classes when their intersection
contains at least three root vertices, or when both classes consume a root pair
with residual common-neighbor quota one. Each maximal clique C defines a binary
sum Z_C. For three distinct maximal cliques C_1,C_2,C_3, the necessary localizer
is

\[
L=\sum_{H\text{ embeddings}}
       (1-Z_{C_1})(1-Z_{C_2})(1-Z_{C_3})XX^{\mathsf T}\succeq0.
\]

Write U for their union. A compatible set S in U meets each C_i in at most one
class. Each member a of S therefore occupies a nonempty membership set

\[
M_a=\{i:a\in C_i\}\subseteq\{1,2,3\},
\]

and these membership sets are disjoint. Hence every compatible S has size at
most three. Its coefficient in the expanded product is

\[
\prod_{a\in S}\ \sum_{\varnothing\ne T\subseteq M_a}(-1)^{|T|}
=(-1)^{|S|}.
\]

Thus, with X_empty=1,

\[
\prod_{i=1}^{3}(1-Z_{C_i})
 =\sum_{\substack{S\subseteq U\\S\text{ pairwise compatible}}}
       (-1)^{|S|}\prod_{a\in S}X_a.
\tag{1}
\]

Shared clique members introduce no multiplicity. The idempotence X_a squared
equals X_a accounts for selecting the same class from more than one factor.
Products containing an incompatible pair vanish.

The source independently multiplies the three factors as a formal polynomial,
reducing by those two rules. It compares the result to (1) for every candidate.
It also multiplies by each union indicator X_u and checks complete formal
cancellation. The saved cancellation pairs are S and S union {u}, with opposite
signs, whenever they are compatible. Terms incompatible with u vanish.

These are Boolean algebra checks, not reconstructed coefficient identities in
the cached scalar tensors. That stronger verification belongs to a later lift
preparation. In particular, a pairwise-compatible triple can still violate a
three-vertex capacity constraint. Its actual conditional contribution will then
be zero; the current scope does not assume all such triples are realizable.

## Conditional representation and normalization

A selected subset of size one, two, or three appends that many specified class
vertices to the five-root graph. Its conditional matrix is a sum of congruences
of scalar matrices rooted at six, seven, or eight vertices, respectively.
Every allowed graph among the selected vertices must be included. The mask
classes are distinct and unique, so the selected labels are fixed. There is no
factorial or automorphism divisor in this labelled embedding identity.

The largest resulting scalar product uses eight root vertices and two additional
vertices, so it remains an order-ten count form. The five-root parent matrix is
the constant and one-free principal submatrix of the existing
`induced-moments-5-2-512.pickle` family. No new parent product enumeration is
required. That cache was not loaded during this scope census.

Every row indexed by U vanishes pointwise. Therefore the planned quotient keeps
the constant and all other high classes. No class is omitted from the domain.

## Quota-one reduction and its limits

If a clique C has a common root pair with residual quota one, then

\[
1-Z_C=\sum_{\substack{m\text{ contains that pair}\\m\notin C}}N_m.
\]

The sum includes the size-two class. Conditioning on the chosen vertex expresses
the triple absence as a positive sum of six-root two-clique absence matrices.
A chosen class belonging to either remaining clique gives zero. Otherwise the
two remaining cliques split into child cliques. Equal or nested child factors
reduce to the appropriate single absence factor.

If a child clique is not maximal, extending it to a maximal clique adds positive
conditional terms. With two absence factors, these terms require the relevant
child pair localizers, single-clique localizers, conditional scalar matrices,
and SRG count identities. This is not a deduction from unweighted child PSD
alone, and it is not a certification at any count point.

The ledger saves a residual pair and all other classes for every removed
clique. Repeated factors are outside this census of distinct triples; their
products reduce to lower-order absence conditions by idempotence.

## Enumeration and root actions

Direct cap checks agree with the analytic pair criterion for all 620 high-mask
pairs. Bron-Kerbosch and a separate incremental maximal-clique enumeration agree
for every root. Every enumerated clique is checked for adjacency and maximality.

| Quantity | Count |
| --- | ---: |
| Five-root types | 21 |
| High masks | 127 |
| Maximal cliques | 84 |
| Constant-only empty cliques | 3 |
| Quota-one redundant cliques | 49 |
| Remaining cliques | 32 |
| Distinct maximal-clique triples | 391 |
| Triples removed by the quota-one reduction | 155 |
| Candidate triples | 236 |
| Root types with candidates | 5 |
| Root-action orbits | 23 |

All degree-preserving five-vertex permutations are tested. The census obtains
248 automorphisms from 462 candidate permutations across the 21 roots. It checks
each action on the root graph, full high-mask domain, incompatibility graph,
clique classification, and each formal expansion. Explicit representative-to-
member maps cover all 236 triples exactly once. The matrix congruence comes from
relabeling labelled root embeddings, without any symmetry assumption on a
hypothetical 99-vertex graph.

The 236 formal factor comparisons include 1,895 union-row cancellation checks.
The 23 representatives contain 171 union rows.

## Conservative workload

Across the representatives, the selected-subset registries need 45 singletons,
83 pairs, and 38 triples. The pairwise edge-choice bounds give 45, 93, and 55
conditional child cases, respectively. These are upper bounds for triples:
some choices may fail a joint visible cap. No canonical child or lift has yet
been constructed.

| Work estimate | Bound |
| --- | ---: |
| Representative quotient lower entries | 958 |
| Largest quotient order | 10 |
| Full-matrix additions and subtractions | 107,897 |
| Sparse lower-entry lift products | 764,624 |
| Peak matrix cells with one child streamed at a time | 67,474 |
| Peak child cells if every uncanonicalized child were cached | 1,690,837 |

The lift bound permits up to 2 to the selected-subset-size child coordinates
per old class. It includes every pairwise-allowed mutual-edge choice. Child
scalar orders are bounded by 43, 100, and 220 for roots of size six, seven, and
eight. These cell counts exclude the existing tensor-cache and interpreter
storage; they are not RSS predictions.

The scope census took 2.840 seconds with peak RSS 163,900 KiB. A fresh-process
replay took 3.910 seconds with peak RSS 173,964 KiB. Both used a 60-second bound.
No lift cache or point scan is part of this checkpoint.

## Replay

From the repository root, use a new output path:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_triple_clique_scope.py \
  --replay experiments/logs/moments-and-counts/order10-triple-clique-scope.json.gz \
  --output /tmp/order10-triple-clique-scope-replay.json --seconds 60
```

The manifest `experiments/logs/moments-and-counts/order10-triple-clique-scope-manifest.json`
binds the source, certificate, note, and generation/replay logs. The source
refuses to overwrite an output file.
