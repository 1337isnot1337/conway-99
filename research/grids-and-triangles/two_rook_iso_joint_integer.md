# Integer exclusion of the surviving two-arm rook core

The 27-point core with matching

\[
p=(0,5,7,8,6,1,4,2,3)
\]

cannot extend to an `srg(99,14,1,2)`. A necessary binary incidence and
edge model is unsatisfiable. Its frozen CNF has a checked DRAT proof.
The model retains all 168 admissible outside signatures and all 9,846
potential edges. It imposes no orbit equalities or graph symmetries.

This excludes the entire core class, not just the fixed 72-column
assignment excluded in [the earlier edge-LP test](two_rook_iso_completion.md).
The [joint real LP](two_rook_iso_joint_incidence.md) has exact rational
feasible points, including the same packing constraints. Integrality
is therefore essential to the exclusion established here.

## The core and all possible outside vertices

There are three disjoint induced rook grids, numbered `0,1,2`. The
two interfaces incident to grid zero are rook isomorphisms and are
gauged to the identity. The remaining interface is the permutation
`p` above. If `R` is rook adjacency and `M` is its permutation matrix,
the induced core is

\[
B=\begin{pmatrix}R&I&I\\I&R&M\\I&M^{\mathsf T}&R\end{pmatrix}.
\]

Every exterior vertex has exactly one neighbor in each grid. Its
core signature is therefore one of the 729 triples having one point
in each base. Put

\[
G=12I+2J-B^2-B,\qquad d_s=2\mathbf1-(B+I)h_s.
\]

Retain a signature `s` precisely when `G_ij > 0` for every pair in
it and `d_s >= 0`. These are necessary visible common-neighbor
conditions. Exactly 168 signatures remain.

A signature cannot occur twice: its two exterior vertices would
share three core neighbors. Introduce one binary selection variable
`z_s` for each retained signature. Every completion satisfies

\[
\sum_s z_sh_sh_s^{\mathsf T}=G,\qquad \sum_s z_s=72.
\]

## Exterior edges and exact mixed quotas

Two selected signatures `s,t` can be adjacent only if they share at
most one core point. In addition, every core point in `h_s` must
have positive remaining quota in `d_t`, and conversely. These tests
leave 9,846 possible edges.

For each possible edge introduce a binary variable `a_st=a_ts` and
require

\[
a_{st}\le z_s,\qquad a_{st}\le z_t.
\]

For each potential exterior vertex `t` and core vertex `i`, require

\[
\sum_{s:\,i\in h_s} a_{st}=d_t(i)z_t.
\]

The exterior degree equation is `sum_s a_st = 11 z_t`.
These conditions are exactly the core/exterior block of
`A^2+A=12I+2J` and the required degree fourteen, conditional on
the vertex being selected.

The CNF implements a conditional count `sum literals = q z_t`
by an unconditional upper bound of `q` and a lower bound of `q`
guarded by `z_t`. Activation already makes all literals zero when
`z_t=0`. If fewer than `q` eligible literals exist, it forces
`z_t=0`. An exhaustive small truth-table control checks this logic.

## Core-pair neighbor packing

For any core pair `i,j` and potential exterior vertex `t`, impose

\[
\sum_{s:\,i,j\in h_s}a_{st}\le z_t.
\]

If two selected vertices in that sum were both neighbors of `t`,
they would have the three common neighbors `i,j,t`. This violates
the maximum of two regardless of whether the two vertices are
adjacent. The constraint is therefore necessary in every graph.

The binary encoding uses pairwise at-most-one clauses. Activation
supplies the zero right side when `t` is absent. There are 62,692
distinct clauses of this form. No assumptions about an exterior
automorphism, orbit-constant selection, or a chosen incidence
assignment enter the encoding.

## Checked unsatisfiability

The initial search had a declared 60-second budget and at most twenty
refinement rounds. It returned UNSAT in about four seconds, before
finding any binary point. Consequently no lazy common-neighbor
clauses were added: the certificate proves inconsistency of the
initial necessary model itself.

The full CNF has 525,986 variables including cardinality auxiliaries
and 1,151,148 clauses. Its SHA-256 is

```text
c2c22ac69a93bae270d23906670b24cab87f270c6db579076a0b91560d3c4e1e
```

A second run generated a DRAT proof from that exact CNF. The
independent `drat-trim` checker verified it. The retained proof uses
14,860 input clauses and 1,088 lemmas, with 97,873 resolution steps
and no RAT lemmas. The retained CNF and proof together occupy less
than one megabyte.

The replay wrapper regenerates the full CNF, checks its hash and all
frozen source hashes, verifies that every retained input clause
belongs to that CNF, and invokes `drat-trim` on the retained proof.
It also reruns the conditional-count truth-table control.

```bash
.venv/bin/python experiments/workspace/two_rook_iso_joint_integer_certificate.py \
  experiments/workspace/two-rook-iso-joint-integer-certificate.json \
  --drat-trim /path/to/drat-trim
```

The manifest, retained CNF, and proof are the files with prefix
`experiments/workspace/two-rook-iso-joint-integer-`. The complete
necessary-model builder is `two_rook_iso_joint_integer.py` in the
same directory. Its signature-domain helpers are frozen and listed
by hash in the manifest.

The separate [encoding audit](two_rook_iso_joint_integer_independent_audit.md)
rebuilds the domain and logical constraint requests independently, checks
all packing clauses and 37,888 Boolean controls, and reproduces the full
CNF hash. The coordinating worker also completed the rebuilt-CNF and DRAT
replay. An [independent CP-SAT model](three_rook_case48_cp_audit.md) matched
the domain and passed a nine-rook positive control; its bounded target run
was UNKNOWN during presolve. That run is not an additional UNSAT proof.

## Relation to the interface census

The separate [two-arm census](two_rook_interfaces.md) enumerates all
2,720 neighbor-avoiding third permutations, reduces them to 59 core
classes, and excludes the other 58 by exact binary quota propagation.
The proof here supplies the missing exclusion of its final class.

Together these rule out three disjoint rook grids with two
rook-isomorphic interfaces incident to one of them. Translating this
into a bound on the number of isomorphic partners also uses the
separate fact that distinct isomorphic partners of one grid are
disjoint. No all-red assumption is used.

The resulting [one-partner theorem](rook_partner_bound.md) combines those
facts explicitly.
