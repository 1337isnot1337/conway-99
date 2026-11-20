# Prism-free clique complements

Under the additional assumption that the ambient graph contains no
triangular prism, the seven-root pair-incompatibility graphs gain
1,604 edges. Of these, 449 involve a structurally absent high flag.
The other 1,155 join flags whose individual extensions are prism-free.
Every genuine added edge has an explicit induced-P4 certificate.

The resulting graphs have 5,967 maximal cliques. After the existing
shared-quota-one reduction, 4,584 remain, represented by 1,225 root
orbits. The representative quotients have 1,417,349 lower entries.
This package prepares those constraints; it performs no point scan.

All statements using the new edges are conditional on global
prism-freeness, equivalently the prism count coordinate x₁ being zero.
They are not unconditional exclusions for the Conway problem.

## Structural zero classes

The proved prism-zero closure contains 1,443 induced types through
order ten. Its distribution is 1 type at order six, 3 at order seven,
19 at order eight, 133 at order nine and 1,287 at order ten. Every
induced-count form for those types vanishes after the 58 prism-containing
ordinary core coordinates are set to zero.

The sizing scout verifies prism containment for all 6,535 catalogue
types through order nine, comparing an explicit triangle/matching
witness with the frozen independent detector and the zero-closure
ledger. It then reconstructs all 5,215 conditional flag lifts and checks
every one of the 104,854 high-mask pairs.

Three seven-root types are absent under the assumption. Across all
rooted domains, 81 high flags are also absent because their one-vertex
extension contains a prism. The complete original flag domains are
retained in the ledger. These structural zeros are recorded separately;
no class is removed because of a value at a particular count point.

A pair already incompatible by the visible caps remains incompatible.
For a previously compatible pair, the sparse child lift lists every
allowed mutual-edge continuation. The pair becomes incompatible in a
prism-free graph exactly when all those continuations contain a prism.
The forward and reverse constructions produce the same multiset of
canonical continuation types for every pair.

This gives 34,480 edges in the new graphs, compared with 32,876 in the
complete visible graphs. All 3,208 new directed conditional rows are
supported on prism-containing child flags. Their sparse rows have
3,264 child-column entries in total.

## The P4 certificate for every genuine added edge

Suppose H+a and H+b are individually prism-free and the cap-compatible
mutual-nonedge extension H+a+b contains a prism. The prism must use
both added vertices. They are nonadjacent, so deleting them from the
prism leaves an induced path

\[
w-x-y-z
\]

inside H. Up to interchanging a and b, the required neighborhoods are

\[
\{w,x,z\}\subseteq a,
\qquad
\{w,y,z\}\subseteq b.
\]

The two masks already share w,z. Their visible compatibility forces
their intersection to be exactly {w,z}, with residual quota two on
that root pair. Hence the mutual edge a–b is impossible: it would
make an adjacent pair with two common neighbors. The six displayed
vertices form two triangles joined by a perfect matching.

Conversely, any induced root path and two visibly compatible masks
with these neighborhoods form that prism when their mutual edge is
absent. Thus this P4 rule classifies every genuine added edge.

A separate standard-library verifier enumerates all induced root P4s
and generates the pair edges from this rule. Its set agrees exactly
with all 1,155 genuine edges from the child-domain scout. It rebuilds
the complete 34,480-edge graph by adding these edges and the edges
incident with absent flags to the old visible graph. It uses no child
catalogue or transport.

That verifier also independently tests all 5,215 single flags for a
prism by examining six-vertex subsets. On six vertices, a 3-regular
graph containing a triangle is a triangular prism: the triangle has
three edges to the other vertices, each of which needs at least one
such edge, leaving a second triangle and a perfect matching. This
test agrees with all 81 absent-flag records and all three absent roots.

The P4 replay finds 1,127 induced root paths across the 208 root types.
The 1,155 pair additions occur across 96 root types. Every pair retains
its root path and shared quota-two endpoints as a short certificate.

## Exact support of the conditional zero rows

For a clique C in the new graph, its class sum is binary in a
prism-free ambient graph. The localizer remains

\[
L_C=M_7-\sum_{a\in C}B_aM_8(H+a)B_a^T\succeq0.
\]

The sparse lift B_a and the labelled embedding normalization are
unchanged. No automorphism divisor occurs. Individual selected-row
identities reuse the frozen coefficientwise check of all 5,215 masks.

For an old visible incompatibility, the appropriate conditional row
is literally empty. The preparation rechecks all 65,752 such directed
rows. For a newly forbidden pair, that row can be nonempty before
the prism-zero substitution. The preparation therefore records its
actual tensor terms rather than calling it an unrestricted identity.

For every new ordered pair (a,b), and every parent column j, it forms
the exact labelled-count expression

\[
\bigl(B_aM_8(H+a)B_a^T\bigr)_{b,j}.
\]

All 111,816 entries are checked. The 41,900 nonempty entries contain
49,268 recorded nonzero tensor terms. Every coefficient is positive,
and every type index belongs to the proved prism-zero support. Thus
every newly incompatible conditional row vanishes after that
substitution. Together with the old selected-row identity, this proves
all 67,203 clique-selected row instances vanish on the prism-free face.

The preparation also checks all 84 structurally absent parent rows:
81 high-flag rows and three root constants. Their 1,161 entries contain
687 nonzero terms, again supported entirely on the zero types. Across
the conditional and parent checks, 1,120 distinct zero types occur.
The full coefficients and type indices are saved for replay.

These are exact identities modulo the stated prism-zero support. They
are not unrestricted polynomial identities, and they do not use
approximate values or accidental zeros of a proposed count vector.

## Complete clique and orbit coverage

Bitset Bron–Kerbosch and the separate incremental maximal-clique
enumeration agree for every root. Every generated clique is checked
for maximality. All original high-mask domains, including the absent
roots and flags, remain present. Five roots retain only their constant
base flag.

Every old visible clique has an explicit containing maximal clique
in the new graph. The 530 residual-two triple groups are still covered;
518 remain maximal, and the other 12 have saved containing cliques.
Those covering indices need not be distinct. A later scan must count
the covered triple groups with their multiplicities, rather than
counting distinct covering cliques.

The shared-quota-one reduction remains valid. It uses the SRG pair
identity and a positive sum over all other allowed child classes,
including the size-two class. It removes 1,378 cliques. The remaining
4,584 cases have 1,225 root-automorphism orbits across 160 roots.

The root groups are again enumerated exactly among all degree-preserving
permutations. Generator closures and their actions on the new graph,
the absent flags and every clique classification are checked. Explicit
transports cover every retained clique. This only relabels labelled
root embeddings; it assumes no automorphism of a hypothetical
99-vertex graph.

| Quantity | Exact count |
| --- | ---: |
| Root types retained | 208 |
| High-mask flags retained | 5,215 |
| Structurally absent roots / high flags | 3 / 81 |
| Genuine new prism pair edges | 1,155 |
| New pair edges involving an absent flag | 449 |
| Complete prism-free incompatibility edges | 34,480 |
| Maximal cliques | 5,967 |
| Constant-only cases | 5 |
| Shared-quota-one redundant cliques | 1,378 |
| Remaining cliques | 4,584 |
| Root-orbit representatives | 1,225 |
| Largest representative quotient order | 84 |
| Representative quotient lower entries | 1,417,349 |
| Conditional lifts needed by representatives | 2,103 |
| Sparse conditional lower-entry products, upper bound | 1,275,701 |
| Full-matrix conditional subtractions | 53,444,911 |
| Retained lower-entry conditional subtractions | 17,843,397 |

The largest per-root matrix-cache estimate remains 636,801 Python
object cells, or an illustrative 40,755,264 bytes at 64 bytes per cell.
This excludes sparse caches and process overhead. It is not an RSS
guarantee. The full clique/support preparation took 12.44 seconds and
used 236,224 KiB under a 30-second bound.

## Frozen sources and certificates

The three sources are:

- `experiments/workspace/grid_free_order10_complement_prism_scout.py`
- `experiments/workspace/grid_free_order10_complement_prism_p4.py`
- `experiments/workspace/grid_free_order10_complement_prism_domains.py`

Their SHA256 values are:

- `0ab805ac978d6c5d398e9f5f255b3f3e4b5b56feab0b8deb1aee70b38b8f5fbf`
- `ce4fdce52e927ebb03931d3812e2c486847efa47379fd68e0c74e9dc64fd7705`
- `da0eacfe7d2d5b252eede66eee7934106e97ed011148bf99d57dbb2545e24c7f`

The corresponding ledgers use `order10-complement-prism-scout`,
`order10-complement-prism-p4` and `order10-complement-prism-domains`
prefixes in `experiments/logs/moments-and-counts/`. The P4 driver and
full preparation driver support exact saved-certificate replay.

The scout took 2.16 seconds. The independent P4 reconstruction took
0.68 seconds. No stage loaded a count point or dense reduction, built
a new product tensor, performed a point scan or called an optimizer.
This package provides necessary constraints for the prism-free case;
it does not exclude that case or settle the full existence problem.
