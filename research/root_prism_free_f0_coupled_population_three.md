# Coupling the two F0 population-three unions

## Prepared finite scope

The two inherited count equalities are

\[
N_0+N_1=3,\qquad N_6+N_7=3.
\]

The complete frozen table for each 24-signature union has 512 literal
triples and 176 distinct count/character tuples. This preparation recovers
those literal triples from the saved representatives. It does not repeat
the old enumeration of all 2,024 triples in either union.

The proposed next census consists of all \(512^2=262,144\) ordered pairs
of triples. Their unions have six distinct signatures because the two
24-signature domains are disjoint. Every actual incidence restricts to
one such pair.

The full cross-census has not run. No surviving-pair count, new zero, or
new cross-count bound is claimed by this preparation. There is no
optimizer or production count candidate.

## Complete recovery by the common character kernel

Let \(K\) be the common kernel of all three nontrivial real characters.
Its actual core-action indices in the frozen group are \(0,3,4\).
The preparation verifies the same three signature permutations on both
unions, their multiplication, and their order-three group structure.

A count tuple is invariant under every core action. A signed population
for character \(\chi\) transforms by \(\chi(g)\). Consequently every
element of \(K\) preserves each full count/character tuple.

For every saved representative triple, its three images under \(K\) are
computed. Their distinct cardinality must equal the saved multiplicity,
which is one or three. Every image has its full 22-count and six-sign
tuple recomputed literally. Every original proved-zero pair and all
171 partial Gram capacities are also checked.

Each half has eight singleton fibers and 168 fibers of size three:

\[
8+168=176,\qquad 8+3\cdot168=512.
\]

The images are disjoint across tuples, and the minimum image equals the
saved minimum representative. Since the frozen tables already give the
complete fiber cardinalities, these checks recover every allowed triple.

No independent change of orientation is made in one union. The subgroup
acts with the same literal permutation on both halves. These actions
organize the finite domains; they are not assumed automorphisms of an
unknown completed graph.

## Additional cross constraints

There are 576 possible literal pairs between the two 24-signature
domains. They occupy 48 original selector-pair orbits. Two of these,
original pair-orbit IDs 23 and 143, are already proved zero; 46 retained
cross-count coordinates remain.

For each proposed pair of triples, the census first checks its nine
literal cross pairs against those proved zeros. It then enforces all
171 original Gram capacities on the six-signature union.

For each Gram row, the preparation computes the maximum contribution
over each 512-triple list separately. In 147 rows, the sum of those
maxima is already at most the quota. The saved maxima certify that these
rows need no per-pair check. The remaining 24 rows are checked explicitly.

This removes redundant work without removing a possible six-signature
restriction. No point values, exterior edge choices, or additional
symmetry assumptions enter the domain.

## Work and storage bounds

| Quantity | Bound |
| --- | ---: |
| Literal pair cases | 262,144 |
| Active capacity checks per case | 24 |
| Total active capacity checks | 6,291,456 |
| Cross-pair histogram contributions | 2,359,296 |
| Complete disposition ledger | 524,288 bytes |
| Joint tuple coordinates | 102 |
| Distinct joint tuples | At most 87,424 |
| Exact tuple-key payload | At most 8,917,248 bytes |

The common diagonal action of \(K\) gives the tuple bound. Its identity
fixes all 512 triples in each half; each nonidentity action fixes eight.
Burnside's count on the full ordered product is

\[
\frac{512^2+2\cdot8^2}{3}=87,424.
\]

Every combined count and signed coordinate is invariant under this
diagonal action. The preparation checks the required pair-orbit
invariance on all 1,128 pairs inside the 48-signature union, for all three
actions: 3,384 comparisons. It also retains the induced action on both
512-triple lists and the transports of the Gram rows.

The bound counts diagonal group orbits, not distinct tuples exactly.
Different orbits may have identical tuples, and the new restrictions
may remove cases. The census will count distinct tuple keys exactly
using their full byte encoding. It will export their count, multiplicity
histogram and exact stream hash, without constructing a native allowed-
assignments table.

The 102 coordinates comprise 90 count coordinates and 12 signed
populations. No exterior-edge coordinate is included.

## Census output and replay

The frozen driver has a separate 60-second cooperative census budget.
Each completed literal pair receives one unsigned 16-bit disposition:

- zero for a survivor;
- one plus the original pair-orbit ID for a witnessed proved-zero pair;
- 10,000 plus the original Gram-row ID for a witnessed capacity violation.

The pair index uses the lexicographic order of the two recovered
512-triple lists. A partial result retains its exact completed prefix.
A timeout cannot certify bounds or zeros for the unvisited suffix.

For every cross-pair orbit, the census records all observed integer
values, their minimum and maximum, and a first literal witness for each
value. New forced-zero coordinates are reported only after complete
coverage and only when at least one pair survives. On every surviving
pair the cross counts sum to nine.

The separate replay recomputes the saved finite prefix and checks the
complete disposition bytes, tuple hash, multiplicities and count-domain
summaries. It performs no optimizer call. A nonempty survivor set is only
a feasible six-signature restriction; it is not a global incidence.

## Preparation controls and bindings

Preparation passed in 1.47 seconds. Its primitive classifier was checked
against direct set calculations on 2,384 synthetic partition cases:
939 accepted, 1,258 rejected by a zero pair, and 187 rejected by a mixed
capacity. Sixty-four independent cross-histogram checks retain repeated
pair-orbit multiplicities.

- [Frozen source](../experiments/workspace/root_prism_free_f0_coupled_population_three.py), SHA256:
  effec5c6557cef35ac16cef3093959fc6c97882baa799e73f8078624a1d03229.
- [Complete preparation](../experiments/logs/root-prism-free/f0-coupled-population-three-preparation01.json.gz), SHA256:
  a46d1080a4edebf47c843bab98598920e6490bdf50447f55fe407e86ede5d156.
- [Preparation log](../experiments/logs/root-prism-free/f0-coupled-population-three-preparation01.log).

The proposed production command requires that exact preparation hash.
The production census remains subject to the coordinator's source gate.
