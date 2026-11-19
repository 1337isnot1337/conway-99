# Independent audit of the full two-arm integer model

The mathematical reduction and the generated CNF pass an independent
audit. This is the full model for the remaining 27-vertex three-grid
core, with all 168 possible exterior signatures available. It does
not fix an incidence witness, identify variables along automorphism
orbits, or rely on any lazy refinement clauses.

The audit independently reconstructs the core, signatures, candidate
edges, cardinality requests, and packing clauses. Its regenerated CNF
has exactly the hash recorded in the retained DRAT certificate.
Proof replay is a separate check; the certificate wrapper verifies
the full CNF hash, inclusion of every retained clause in that CNF,
and the retained DRAT derivation.

## Audited inputs and exact model size

The two root interfaces are identities. The remaining interface is

\[
p=(0,5,7,8,6,1,4,2,3).
\]

The complete [three-grid classification](two_rook_interfaces.md)
excludes the other 58 classes. All eighteen permutations in the
remaining class are conjugate to this representative.

The independent checker constructs its adjacency as a dense integer
matrix, without importing the target's core builder. It checks every
entry of the resulting 27-by-27 Gram matrix and compares the entire
ordered signature and candidate-edge lists.

| Item | Verified count |
| --- | ---: |
| Core vertices | 27 |
| Core degree | 6 |
| Candidate exterior signatures | 168 |
| Separate signature variables | 168 |
| Separate undirected edge variables | 9,846 |
| Endpoint activation clauses | 19,692 |
| Gram/population cardinality requests | 189 |
| Conditional mixed/degree requests | 4,552 |
| Independently reconstructed packing clauses | 62,692 |
| CNF variables, including auxiliaries | 525,986 |
| CNF clauses | 1,151,148 |

The source hash is
`6f62d78af4dfca5e141e0541b4572433a08b628f474e972288ce38a18032202e`.
The independently regenerated full CNF hash is
`c2c22ac69a93bae270d23906670b24cab87f270c6db579076a0b91560d3c4e1e`.

## Why the selection variables cover every completion

Every exterior vertex has exactly one neighbor in each induced rook
grid. Its core-neighbor signature therefore contains exactly three
points, one per grid. Two different exterior vertices cannot have
the same signature, because they would share three common neighbors.
Thus every completion corresponds to a binary variable `z_s` for
each possible signature, with no loss from using at most one vertex
per signature.

Let `B` be the core adjacency matrix and `h_s` a signature indicator.
The complete core common-neighbor equations are

\[
\sum_s z_s h_s h_s^{\mathsf T}
=G:=12I+2J-B^2-B.
\]

The signature domain is generated from all 729 one-per-grid choices.
A signature is discarded only if it uses a pair with zero residual
quota or violates `(B+I)h_s <= 2`. These are necessary bounds on
already visible common neighbors. The dense reconstruction gives
exactly the same 168 signatures as the target builder.

The model includes all Gram entries, including the diagonal. It
also requires `sum_s z_s=72`. This population equation is redundant:
the sum of the 27 diagonal equations is

\[
3\sum_s z_s=27\cdot8=216.
\]

No saved 72-signature witness is read by the integer builder. The
imported `domain()` function constructs the full domain directly;
it does not invoke the separate real model's averaging machinery.

## Candidate edges and activation are necessary

For each admissible signature `t`, define

\[
c_{ti}=2-((B+I)h_t)_i.
\]

If two selected signatures `s,t` share two core vertices, they cannot
be adjacent: an adjacent pair has only one common neighbor. An edge
also cannot occur when `h_s` uses a core coordinate with `c_ti=0`,
or conversely. Such an edge would itself supply a common neighbor
where the mixed quota has already been exhausted.

The independent reconstruction applies precisely these tests to all
pairs of the 168 signatures and obtains the same 9,846 edges. Each
edge has one Boolean variable used in both endpoint equations. Its
two activation clauses require both endpoint signatures to be
selected. All 168 selection IDs and 9,846 edge IDs are distinct.

## Conditional equations and their CNF translation

For each potential vertex `t` and core point `i`, every completion
satisfies

\[
\sum_{s:\,i\in h_s}a_{st}=c_{ti}z_t.
\]

When `z_t=1`, this is the exact mixed common-neighbor equation.
When `z_t=0`, activation makes every incident edge zero, so both
sides vanish. Every selected vertex has three core neighbors, hence
the model also requires

\[
\sum_s a_{st}=11z_t.
\]

This degree equation is redundant as well. Since the core is
six-regular and each signature has size three,

\[
\sum_i c_{ti}=54-7\cdot3=33.
\]

Summing the 27 mixed equations therefore gives
`3 sum_s a_st=33z_t`.

The CNF helper uses an unconditional upper cardinality bound and a
lower bound whose clauses are guarded by `-z_t`. This is exact
because all its literals already imply `z_t`:

- If `z_t=0`, activation sets every counted literal to zero. The
  upper bound holds and the guarded lower clauses are inactive.
- If `z_t=1`, both cardinality bounds are active, imposing equality.
- If the quota exceeds the number of available literals, selecting
  `t` is impossible, and the helper correctly adds `-z_t`.
- A zero quota requires all counted literals to vanish.

One shared variable pool allocates all counter auxiliaries after
the distinct primary variables. The audit captures the target's
actual cardinality requests and compares them with independently
derived Gram, mixed, and degree equations. The conditional quotas
are exactly `0,1,2,11`. Deduplication only removes requests with the
same selected variable, the same counted literals, and the same
quota.

The audit also exhausts 37,888 complete Boolean assignments in 58
small conditional-count settings. These include every quota through
one above the number of literals for sizes zero through eight,
the actual degree quota eleven at sizes eleven and twelve, and the
boundary cases twelve and thirteen at size twelve. Every result
agrees with the direct equation `sum(literals)=quota*selected` under
activation. These are encoding controls, not claims about graph
existence.

## Core-pair neighbor packing is sound

Fix an outside vertex `t` and two distinct core vertices `i,j`.
Suppose two distinct neighbors `s,u` of `t` both have signatures
containing `i,j`. Then `s,u` have the three distinct common neighbors
`i,j,t`. This violates the maximum common-neighbor count of two,
regardless of whether `s,u` are adjacent.

Therefore at most one neighbor of `t` can have a signature containing
the specified pair. Pairwise negative edge clauses encode this
at-most-one restriction. Activation already makes all those edges
zero when `t` is unselected; no additional guard is needed.

The target groups neighbors by a selected core pair. The independent
audit instead chooses two candidate neighbors of each `t` and tests
whether their signatures intersect in at least two points. These
different enumerations give exactly the same 62,692 distinct clauses,
including their literal IDs and signs.

## Proof binding and scope

The audited CNF is the initial model. The discovery log has no SAT
point and no lazy cuts, and the proof manifest records zero lazy
cuts and zero orbit equalities. The CNF hash produced by the
independent audit matches the proof manifest exactly.

The certificate wrapper checks all source-file hashes, reconstructs
that same CNF, and verifies that every clause in the retained
14,860-clause core is an original CNF clause. It then runs `drat-trim`
on the retained proof. The saved manifest records 1,088 retained
lemmas, 97,873 resolution steps, and no RAT lemmas. These proof
checks are distinct from the mathematical and encoding audit here.

Together, a verified DRAT derivation and this necessity audit exclude
the whole remaining three-grid interface class. They do not merely
reject either of the previously saved incidence assignments. Combined
with the other 58 exact class exclusions, they rule out three
disjoint rook grids with two rook-isomorphic root interfaces.

The disjoint-partners lemma then implies that a rook grid has at
most one rook-isomorphic partner. This is a restriction on the grid
system. It is not a proof of nonexistence of the strongly regular
graph.

## Reproduction

```sh
python experiments/workspace/two_rook_iso_joint_integer_independent_audit.py \
  --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-integer-independent-audit.json
```

This rebuilds the full CNF, so it should not be run concurrently
with several other full-CNF regenerations in a memory-constrained
environment. The saved JSON and log record the completed audit;
execution-service delays during the session were not interpreted as
mathematical outcomes.

The separate proof command is:

```sh
python experiments/workspace/two_rook_iso_joint_integer_certificate.py \
  experiments/workspace/two-rook-iso-joint-integer-certificate.json \
  --drat-trim /path/to/drat-trim
```
