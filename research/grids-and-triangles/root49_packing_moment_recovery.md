# Exact high-mask moments at the six-vertex root 49

The fixed order-ten count point `0b78eb2c...` has a complete nonnegative
presence distribution for root 49. All 80 labelled atom weights are integers:
74 are positive and six are zero. Their sum is 11,975,040, the number of
labelled embeddings assigned to this root. Every one of the 80 moment
equations and all 19 orbit equations holds exactly. The normalized
probabilities have common denominator 11,975,040.

This is a finite moment witness. It does not construct an SRG(99,14,1,2),
and it gives no new exclusion of that graph.

## The complete local domain

The root adjacency rows are

`[48,32,32,32,1,15]`.

Its edges are 0–4, 0–5, and 5–i for i in {1,2,3}. A high class consists of
outside vertices with a specified root neighborhood of size at least three.
Each class contains at most one vertex: two vertices in the same class
would have at least three common neighbors.

There are nine possible classes:

- A_i = {0,4,i};
- C_i = {4,5,i};
- B_ij = {4,i,j}, for i<j in {1,2,3}.

Let a, b and c count the selected A, B and C classes. The root-pair quotas
are exactly

\[
a\leq1,\qquad c\leq1,\qquad
A_i+C_i+\sum_{j\ne i}B_{ij}\leq2.
\]

The remaining root-pair inequalities are the individual Boolean bounds.
Summing the last three inequalities gives a+c+2b≤6. Together with
a,c≤1, this proves a+b+c≤4.

No two high vertices can be adjacent. An A vertex already shares root 0
with root 4, so it cannot have another neighbor in the neighborhood of
root 4. Two B classes, or two C classes, intersect in two root vertices.
A possible B_ij–C_k edge with k distinct from i,j would give B_ij and
root 5 the three common neighbors i,j,C_k. The remaining B–C pairs
already intersect in two root vertices.

The checker verifies these statements directly on literal adjacency
matrices. It checks all 256 high-mask subsets of size at most four.
Exactly 80 give valid induced extensions; all 176 others have a visible
common-neighbor violation and a zero cached product form. All 126
five-class subsets also have explicit violations. Thus the population
bound and complete domain do not depend only on saved orbit counts.

## Count normalization

For a selected class set T, all its high vertices are distinct and all
edges among them are forced absent. There is therefore one literal
induced extension F_T of the six-root graph.

The count

\[
m_T=\sum_{\text{labelled root embeddings}}\prod_{a\in T}X_a
\]

equals Aut(F_T) times the unlabelled induced count of F_T. There is no
division by a root or free-vertex stabilizer.

To recover the existing catalogue index, the checker partitions T into
two sets of size at most two and reads their frozen product row. Distinct
high masks cannot identify vertices across the two factors. The sole
raw coefficient must be 1 in labelled induced embeddings. The checker
independently counts Aut(F_T) on the literal graph and uses that as the
coefficient in unlabelled induced counts.

The 80 monomials have 19 distinct catalogue types, one per actual root
orbit. The numbers of types of orders 6 through 10 are 1,3,7,7,1.
Literal graph isomorphisms are checked against all repeated local type
identities. Five direct embedding controls, with hosts of orders 6
through 10, independently check the normalization.

The global catalogue is not rebuilt. Catalogue indices come from the
published frozen product cache; the literal completion, coefficient,
local type consistency, and automorphism factors are checked separately.

## Exact inversion

Let Ω be the complete downward-closed domain of 80 atoms. Every atom
has size at most four. Its mass is determined by the known moments:

\[
w_A=\sum_{\substack{T\in\Omega\\T\supseteq A}}
(-1)^{|T|-|A|}m_T.
\]

The corresponding polynomial is the exact indicator of A on Ω.
The implementation computes the weights by descending subtraction,
then independently checks this signed formula and reconstructs every
moment. All arithmetic involving counts is JavaScript BigInt.

The six root automorphisms identify 19 atom orbits. The quotient variable
is total mass on an orbit. Its matrix entry counts the monomials of a
row orbit contained in a representative atom, and its right-hand side is
the orbit size times the fixed-monomial moment. All 19 equations are
checked in addition to the 80 individual equations. No automorphism of
a hypothetical full graph is assumed.

The six zero masses are the three pairs A_i,C_i and those pairs together
with B_jk, where {i,j,k}={1,2,3}. Each such extension contains the
triangular prism on {0,4,A_i,5,i,C_i}, which is consistent with the
prism-zero input point.

## Recovery and replay

The source and numerical data are separate from the unavailable local
workspace. The public input extraction checked the exact SHA256 hashes
of the published NPZ and pickle archives and allowed only numeric
array/CSR constructors and basic containers during unpacking.
The extraction performed no mathematical query or optimization.

Files:

- `experiments/workspace/root49_packing_moment_recovery_check.js`
- `experiments/workspace/root49_packing_moment_recovery_replay.js`
- `experiments/logs/moments-and-counts/order10-root49-public-recovery-inputs.json`
- `experiments/logs/moments-and-counts/order10-root49-packing-moment-recovery-preparation.json`
- `experiments/logs/moments-and-counts/order10-root49-packing-moment-recovery-result.json`
- `experiments/logs/moments-and-counts/order10-root49-packing-moment-recovery-replay.json`

The separate replay imports no subject checker. It verifies the saved
80 nonnegative masses, all 80 direct moment equations, and all 19
quotient equations using the published count point and preparation.
It reuses the preparation's graph and tensor proof.

No optimizer was called. The other 32 population-at-most-four root
models have not been evaluated by this package.
