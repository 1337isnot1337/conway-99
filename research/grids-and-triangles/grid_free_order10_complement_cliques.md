# Clique complements of seven-root flags

The complete intersection-clique census leaves 3,939 complement matrices
after the residual-quota-one reduction. Root relabeling reduces these to
711 representatives. Their quotients have 1,196,257 lower entries, with
largest order 84. This is a point-independent preparation. It does not
claim PSD feasibility or infeasibility at a count point.

The census includes every group of high masks containing a specified
root triple whose three pair residuals are two. There are 530 such groups.
Every allowed superset mask is included, even when that mask contains a
different pair with residual quota one.

## The localizer and its zero rows

Fix a labelled seven-vertex root H. For every allowed outside neighborhood
mask a of size at least three, let X_a be its class size. Each X_a is
binary: two vertices in the same class would have at least three common
neighbors. Let X contain the constant 1 and all these high-mask flags.

If two distinct masks a and b intersect in at least three root vertices,
their classes cannot both be present. Therefore any clique C in the
graph defined by this intersection condition satisfies

\[
Z_C=\sum_{a\in C}X_a\in\{0,1\}.
\]

The corresponding necessary condition is

\[
L_C=\sum_\phi (1-Z_C(\phi))X(\phi)X(\phi)^T
    =M_7-\sum_{a\in C}C_a\succeq0,
\qquad
C_a=\sum_\phi X_a(\phi)X(\phi)X(\phi)^T.
\]

The sums run over labelled induced embeddings of H. As in the
[single-flag complement construction](grid_free_order10_complement_domains.md),
each conditional matrix is a sparse congruence of an existing eight-root
scalar block:

\[
C_a=B_aM_8(H+a)B_a^T.
\]

There is no automorphism divisor. Specifying the unique vertex of class
a gives a bijection with labelled embeddings of the extended root.
An old flag X_b becomes its selected-vertex indicator plus its possible
two child classes, according to adjacency to that selected vertex.

For a selected a, row a of B_a is the child constant. For a distinct
b with |a∩b| at least three, row b of B_a is empty. Thus, for b in C,
only the term C_b contributes to row b of the conditional sum, and that
row equals row b of M₇. Every row indexed by a member of C is zero in
L_C. Removing these rows and columns preserves the PSD question.

The exact preparation checks the parent-row identity coefficientwise
for all 5,215 high-mask lifts, before substituting any count point. It
also checks every ordered incompatible pair has the required empty
conditional row. The checks cover all 70,359 selected-row instances in
the complete clique ledger, including 4,596 instances in the 530 triple
groups. These are identities of labelled induced-count forms.

For a triple T, the complete group is

\[
C_T=\{a:\ a\text{ is allowed and }a\supseteq T\}.
\]

It is a clique because every two members share T. It is maximal because
T itself is an allowed member, and any mask compatible with T must
contain T. Its localizer implies each constituent single-mask localizer:
for a in C_T, add the positive matrices C_b for b in C_T other than a.
More generally, a maximal-clique localizer implies the localizer of
every contained clique, using the existing conditional PSD constraints.

## Quota-one reduction

For a root pair i,j, put

\[
q_{ij}=2-H_{ij}-(H^2)_{ij}.
\]

Suppose q_ij=1 and every a in C contains i,j. The exact common-neighbor
identity gives

\[
1-\sum_{a\in C}X_a
 =\sum_{\substack{b\supseteq\{i,j\}\ b\notin C}}N_b,
\]

where the sum includes every allowed outside class, including the
size-two mask {i,j}. Multiplication by XXᵀ and summation over labelled
embeddings gives

\[
L_C=\sum_{\substack{b\supseteq\{i,j\}\ b\notin C}}
          B_bM_8(H+b)B_b^T.
\]

Thus these localizers are redundant under the full child PSD family
and the SRG common-neighbor count identities. Child PSD alone with
unrelated matrix entries would not justify this conclusion. The ledger
stores a specific residual-one pair and the full list of other allowed
classes for every removed clique.

This test removes 3,245 maximal cliques. Five roots have only the
constant flag. The remaining 3,939 cliques are candidates after this
specific reduction; further dependencies are possible.

For a triple group, a residual-one pair inside T supplies the same
reduction. The 530 retained triples have all three residuals equal to
two. A superset of such a triple may have a residual-one pair outside
the triple. That fact does not remove the superset from the group.

## Complete intersection-clique coverage

Every allowed-mask graph is an induced subgraph of one graph on the
99 subsets of a seven-point set having size at least three. Two masks
are adjacent exactly when their intersection has size at least three.

Bitset Bron–Kerbosch enumeration finds 477 maximal cliques in this
universal graph. A separate explicit construction gives the identical
set. The construction has the following classes.

| Universal clique description | Number |
| --- | ---: |
| All supersets of a specified three-mask | 35 |
| No four-masks; all masks of size at least five | 1 |
| One four-mask, with all compatible larger masks | 35 |
| Two four-masks through a common triple | 210 |
| Three four-masks through a common triple | 140 |
| Four four-masks through a common triple | 35 |
| All five four-subsets of a specified five-set | 21 |
| Total | 477 |

In the final five rows, include every compatible five-mask and every
six- and seven-mask. The program verifies pairwise adjacency and
maximality for every constructed clique, as well as exact equality
with the complete recursive enumeration.

For each root, intersect the universal cliques with its full allowed
high-mask set and retain the inclusion-maximal intersections. This
procedure is complete: any maximal root clique extends to a maximal
universal clique, whose intersection with the allowed set must equal
the original root clique. The certificate also records, for every
universal clique, a retained root clique containing its intersection.

This gives 7,189 maximal root cliques across all 208 root types. Coverage
is complete for the stated intersection-at-least-three graph. It does
not include other reasons why classes may be incompatible, and it does
not claim completeness for every Boolean localizing inequality.

## Root-automorphism quotient

For each root H, enumerate all degree-preserving permutations of its
seven vertices and retain exactly those preserving adjacency. A small
generating set is then recovered, and its explicit closure is checked
against the entire enumerated automorphism group.

Every generator is checked on H, the complete high-mask domain, the
intersection relation, every clique classification and the retained
triple groups. Breadth-first orbit traversal supplies an explicit
root-vertex transport from each chosen representative to every member.
The transports are checked directly on adjacency and on the selected
mask sets. They cover all 3,939 remaining cliques.

This quotient assumes no automorphism of the hypothetical 99-vertex
graph. Relabeling a root embedding by an automorphism of H permutes the
complete set of labelled embeddings. If P is the resulting flag
permutation and π(C) is the transported clique, then

\[
L_{\pi(C)}=P L_C P^T.
\]

The identity follows before evaluating induced counts, since root
relabeling preserves the unlabelled type of every union graph. No
root-automorphism factor is divided out. One representative per orbit
therefore suffices for this family of PSD tests.

The quotient has 711 representatives. It retains all root types and
does not use zeros or other values at a particular count point.

## Exact preparation counts and resource estimates

| Quantity | Count |
| --- | ---: |
| Root types | 208 |
| High-mask conditional lifts checked | 5,215 |
| Coefficientwise selected-row entry comparisons | 220,138 |
| Ordered incompatible rows checked empty | 48,334 |
| Complete maximal root cliques | 7,189 |
| Constant-only root cases | 5 |
| Shared-quota-one redundant cliques | 3,245 |
| Remaining cliques | 3,939 |
| Remaining triple groups | 530 |
| Degree-preserving vertex permutations tested | 36,170 |
| Root automorphisms enumerated | 7,758 |
| Verified group generators | 370 |
| Remaining clique orbits | 711 |
| Largest representative quotient order | 84 |
| Representative quotient lower entries | 1,196,257 |
| Distinct conditional lifts used by representatives | 1,244 |
| Sparse conditional lower-entry products, upper bound | 999,663 |

Direct summation on all 3,939 full matrices would use 509,306,720 scalar
subtractions. The representatives need 48,361,169 full-matrix scalar
subtractions, or 16,285,618 when only the retained lower entries are
summed. These are operation counts, not measured scan times.

Keep conditional and child count matrices only for the current root.
The largest joint cache estimate is 616,801 Python-object cells,
including two working matrices. At an illustrative 64 bytes per cell,
this is 39,475,264 bytes, in addition to the existing sparse tensor
caches and process overhead. This estimate is not a bound on runtime
resident memory. The preparation uses no count point or new tensor.

Three literal controls use cap-compatible nine-vertex hosts. They check
the sparse conditional lift and the full localizer identity when the
clique sum is zero and when it is one. They include a nontrivial old
flag outside the chosen triple group and a two-neighbor outside class.
The controls do not assert these small hosts are SRG(99,14,1,2).

## Reproduction and scope

The sources are:

- `experiments/workspace/grid_free_order10_complement_cliques.py`
- `experiments/workspace/grid_free_order10_complement_clique_lifts.py`
- `experiments/workspace/grid_free_order10_complement_clique_orbits.py`

Their source SHA256 values are, respectively:

- `765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912`
- `24e1e2dba05de424098d92fd173a3987d2f97f84c038653aac2ad3a3d555eb37`
- `5569a81838301fa54dc2401b98592a91fb302b7ed7a3110983a6f475a1107130`

The exact ledgers use the corresponding `order10-complement-cliques`,
`order10-complement-clique-lifts` and `order10-complement-clique-orbits`
prefixes in `experiments/logs/moments-and-counts/`. The lift and orbit
drivers support complete saved-certificate replay. The orbit driver
also regenerates the entire clique census and compares its JSON data.

The universal/root census took 1.02 seconds. The coefficientwise lift
preparation took 3.36 seconds, and its saved replay passed in 2.54
seconds. The complete root-automorphism preparation took 1.66 seconds.
All computations were bounded. No optimizer, dense count reduction,
new product tensor or point scan was used.

The earlier single-flag scan found no separator at integer witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
That numerical screening does not certify the current grouped family.
The present package prepares a stronger necessary family and its exact
coverage; it does not settle existence of the Conway graph.
