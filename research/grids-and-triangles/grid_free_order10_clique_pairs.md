# Six-root pairs of clique-absence conditions

## Result and scope

The complete six-root preparation contains 3,283 unordered pairs of distinct
maximal cliques after a stated quota-one reduction. They form 347 orbits under
actual root automorphisms. The representative matrices have 118,210 lower
triangle entries after their proved zero rows are removed; the largest remaining
order is 32.

The preparation uses all 62 admissible six-vertex root types and all 829 allowed
neighborhood masks of size at least three. It does not load a count point or
perform an eigensystem, optimizer, or new product enumeration. No root or flag is
removed because of its value at a particular point. The inequalities are
necessary for any SRG(99,14,1,2); prism-freeness is not assumed.

The source is
`experiments/workspace/grid_free_order10_clique_pair_domains.py`, with SHA-256
`0cde57ec1213c49b66f85c5a27a638883f7d0851bf9cb265632e3d82240de33c`.
The compressed domain certificate has SHA-256
`1812d7faa0dc865d21d970e7bff97e903693277804b341272145abc365bfcb51`.
Its cold replay passed. This is a domain and identity certificate, not a positive
semidefiniteness certificate for any count point.

## Binary classes and the localizer

Fix a labelled induced embedding of a six-vertex graph H. For each allowed mask
a of size at least three, let X_a count outside vertices with neighborhood a in
H. Such a vertex is unique when it exists: two vertices in the same class would
have at least three common neighbors. Thus X_a is binary. Put X_0=1 and let X
be the vector of the constant and every high-mask class.

For distinct masks a,b, the complete visible incompatibility test is:

* their intersection has size at least three; or
* their intersection contains a root pair whose remaining common-neighbor quota
  is one.

If neither obstruction occurs, adding the two vertices as a mutual nonedge is
cap-compatible. The source checks this criterion against both literal mutual
edge choices for all 9,118 high-mask pairs.

Let C and D be distinct maximal cliques in this incompatibility graph. Then

\[
Z_C=\sum_{a\in C}X_a,\qquad Z_D=\sum_{b\in D}X_b
\]

are binary. Summation over all labelled embeddings of H gives the necessary
positive semidefinite matrix

\[
L_{C,D}=\sum_{H\text{ embeddings}}(1-Z_C)(1-Z_D)XX^{\mathsf T}.
\]

Write M for the unweighted matrix, C_a for the matrix conditioned on X_a=1,
and C_ab for the matrix conditioned on both classes. With A=C\D and B=D\C,

\[
L_{C,D}=M-\sum_{a\in C\cup D}C_a+
\sum_{\substack{a\in A,\ b\in B\\a,b\text{ compatible}}}C_{ab}.
\tag{1}
\]

A shared class in C intersect D contributes X_a squared, which equals X_a.
It therefore cancels one of the two subtractions. Every other cross term
touching a shared class vanishes because its distinct masks lie together in C
or D. The surviving terms are exactly the compatible pairs across A and B,
each once. There is no factor of two.

The self-pair C=D gives the already defined single-clique localizer because
(1-Z_C) squared equals 1-Z_C. This preparation records distinct unordered
pairs only. It claims completeness for this specified maximal-clique family,
not for every possible Boolean localizing polynomial.

## Labelled conditional lifts

The single and double terms in (1) reuse the checked generic lift constructor in
`grid_free_order10_double_complement_domains.py`. A single term is a congruence
of a seven-root scalar moment matrix. A double term is the sum of congruences
of its admissible eight-root children, with the mutual edge present or absent.
The two choices are disjoint events.

The masks of the selected vertices are distinct and each class has at most one
vertex. Appending these specified vertices is a bijection between the parent
conditional embeddings and the child labelled embeddings. A fixed transport to
the canonical child graph preserves that bijection. No root automorphism,
free-label stabilizer, or factorial divisor is introduced.

Each old high class becomes the sum of at most two or four child classes. A
selected class becomes the constant. Every nonconstant child class still has at
least three neighbors in the child root, so it occurs in the existing complete
scalar cache. All cached products, including their diagonal multiplicities,
remain unchanged.

The six-root cache has 55 nonconstant blocks and seven constant-only roots.
The seven-root cache has 203 nonconstant blocks and five constant-only roots.
The complete eight-root cache has 916 blocks. A missing constant-only block is
represented by its single labelled root-count entry.

## Exact zero rows

Every row indexed by a mask in C union D vanishes in L. This follows pointwise
because its class indicator annihilates at least one absence factor. The
certificate also proves this using full labelled-count coefficient forms.

It stores three primitive checks:

1. The selected row of C_u equals the corresponding row of M.
2. The selected u row of C_ub equals the u row of C_b.
3. A row incompatible with a selected class is empty in every relevant child
   lift.

For u in C\D, all other singles from C vanish in its row. Each compatible
single from D\C cancels exactly with C_ub. Every double not containing u has a
selected class in C distinct from u and therefore has an empty u row. The same
argument applies with C and D interchanged. If u belongs to their intersection,
all other singles and every double have empty u rows; M and C_u cancel.

For every pair and every union mask, the certificate saves the bijection between
surviving single registry entries and cancelling double registry entries. It
also checks every other term has an empty lifted row. This certifies 41,413
union rows, representing 1,718,650 matrix entries. These repeated entries are
certified by the saved primitive identities and cancellation maps; they were not
all separately expanded into count forms.

The primitive comparisons include 10,566 single selected-row entries and
157,726 double selected-row entries. There are 4,050 single incompatible-row
checks and 43,382 double-child incompatible-row checks. These are unrestricted
coefficient identities, without substitution of prism-zero counts or any point.

## Quota-one reduction

Suppose every mask in C contains a root pair i,j whose remaining quota is one.
For the actual graph, exactly one outside vertex is a common neighbor of that
pair. If N_m denotes a class of any size, then

\[
1-Z_C=\sum_{\substack{m\supseteq\{i,j\}\\m\notin C}}N_m.
\tag{2}
\]

The sum includes the size-two class. Multiplying (2) by
(1-Z_D)XX transpose and conditioning on its specified vertex expresses L as a
positive sum of seven-root clique-absence congruences. If the chosen class
belongs to D, its contribution is zero. Otherwise the classes from D split into
a clique of high child classes.

For a child clique that is not maximal, extend it to a maximal clique. Its
complement localizer is the maximal-clique complement plus positive
single-class conditional matrices. Thus this redundancy uses the required
child clique localizers, conditional scalar Gram matrices, and the SRG count
identities. It does not follow from child scalar positive semidefiniteness
alone. The saved ledger records an explicit residual pair and every other mask
in (2) for each deleted clique.

## Complete enumeration and root actions

Bron-Kerbosch enumeration and a separate incremental maximal-clique enumeration
agree for every root. Their common output is checked for pairwise adjacency and
maximality.

| Quantity | Count |
| --- | ---: |
| Six-root graph types | 62 |
| High-mask classes | 829 |
| Maximal cliques | 541 |
| Constant-only empty cliques | 7 |
| Cliques with a shared quota-one pair | 272 |
| Remaining nonempty cliques | 262 |
| All distinct unordered maximal-clique pairs | 4,688 |
| Pairs removed by the quota-one reduction | 1,405 |
| Candidate pairs | 3,283 |
| Roots with candidate pairs | 18 |
| Root-automorphism pair orbits | 347 |

For each candidate root, the source tests all six-vertex permutations, with a
degree prefilter, to obtain the full automorphism group. It verifies each action
on the root, every high mask, the incompatibility graph, and clique
classification. The 950 automorphisms across the 18 candidate roots supply
explicit representative-to-member maps for every pair, including a flag for
interchanged clique sides. All 3,283 pairs occur exactly once in the orbit
partition.

Relabeling the labelled root embeddings gives a congruence of the matrices. This
uses no automorphism assumption about a hypothetical 99-vertex graph.

## Workload and controls

The full registries contain 318 single lifts and 2,078 double lifts. Scanning
only orbit representatives needs 270 single registry entries and 688 double
entries, shared per root.

| Representative workload | Bound |
| --- | ---: |
| Quotient lower triangle entries | 118,210 |
| Largest quotient order | 32 |
| Full-matrix additions and subtractions | 9,423,438 |
| Quotient lower-entry additions and subtractions | 2,270,664 |
| Sparse lower-entry lift products | 253,552 |
| Peak per-root matrix object cells | 343,989 |

The object-cell estimate includes the required single/double matrices, distinct
child matrices, and two working matrices. At an illustrative 64 bytes per
object cell it is about 22 MB. It is not an RSS guarantee; catalogue, tensor,
certificate, and interpreter storage are separate.

Six literal small-host controls check the full lifted formula. They include
neither, either, and both clique events, both mutual edge choices where relevant,
and a shared class present in C intersect D. These hosts satisfy the visible
caps; they are not claimed to be 99-vertex strongly regular graphs.

The complete preparation took 6.394 seconds with peak RSS 243,776 KiB. A fresh
process reconstructed and compared the entire certificate in 6.466 seconds,
with peak RSS 406,580 KiB. Both had a 60-second internal limit.

## Files and replay

The manifest is
`experiments/logs/moments-and-counts/order10-clique-pair-domains-manifest.json`.
It binds the source, this note, the compressed certificate, generation and replay
logs, and the preserved first failed attempt. That attempt stopped on a local
variable-shadowing error before completing a root. The corrected run is the
certificate described above; the failed attempt is not evidence about any
mathematical case.

From the repository root, use a new output path:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_clique_pair_domains.py \
  --replay experiments/logs/moments-and-counts/order10-clique-pair-domains.json.gz \
  --output /tmp/order10-clique-pair-replay.json --seconds 60
```

The replay verifies input hashes, rebuilds the complete domain and all exact
primitive identities, and compares the JSON-normalized certificate. The source
refuses to overwrite its output. No point scan is included in this checkpoint.
