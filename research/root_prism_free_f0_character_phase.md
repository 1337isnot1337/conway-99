# A common character phase for the F0 count model

The signed count model has an exact fourfold symmetry. Two linear conditions
choose one representative without changing feasibility. This reduction concerns
the count model. It does not assume an automorphism of a hypothetical graph.

## The action

The three nontrivial real characters have the four joint values

\[
(a,b,ab),\qquad a,b\in\{-1,1\}.
\]

Each value occurs at three of the twelve actual core actions. Apply one common
phase to all signed populations: multiply every population for character one
by \(a\), every population for character two by \(b\), and every population for
character three by \(ab\). Keep every unsigned count and product variable fixed.

This transformation preserves the model:

- Each signed product has two factors from the same character. Their product
  stays fixed.
- Each character-Gram equation is homogeneous and uses one character. Its
  left side changes by one common sign.
- Every one of the 42 local profile tables and both population-three joint
  tables is closed under all four phases. The preparation checks every tuple
  and preserves its literal multiplicity.
- All inherited count constraints, including the 117 dense rows, use only
  unsigned count variables.

The table closure also preserves coordinate domains obtained from these
tables. Any additional count-only domain restriction is fixed by the action.

## A unique representative

The inherited equality \(N_0+N_1=3\) implies that

\[
S_c=L_{c,0}+L_{c,1}
\]

is odd for each character \(c\). Each \(S_c\) lies in \([-3,3]\), so none is zero.
There is exactly one common phase that makes \(S_1\) and \(S_2\) positive.
Therefore the two conditions

\[
1\le S_1\le3,\qquad 1\le S_2\le3
\]

choose one representative of each four-element phase orbit. The native variable
IDs and the two rows are stored in the preparation record.

The first joint table has 176 profiles. Exactly 44 satisfy these conditions.
Their literal multiplicities sum to 128, compared with 512 before normalization.
The 20 possible triples of signed sums have five representatives:

\[
(1,1,-1),\ (1,1,3),\ (1,3,1),\ (3,1,1),\ (3,3,3).
\]

These conditions must be imposed once, globally. Choosing signs independently
for different selector orbits would not preserve cross-orbit products.
The two rows are symmetry conditions, not inequalities valid for every
labelled signed assignment.

## Exact records

The source is
`experiments/workspace/root_prism_free_f0_character_phase.py`
(SHA-256 `39a12ceb362fea57944637f94f79911ddcfac3c11c9a4478406cf8f6a34025e1`).
It checks all four phase actions, all 2,385 signed products, all 32
character-Gram rows, and all 44 retained tables. It makes no optimizer call.

The preparation is
`experiments/logs/root-prism-free/f0-character-phase-normalization01.json`
(SHA-256 `737389ccfd5290072e8dd4cb12a63bfa3a6cae2d10a6ece2793c0a891aff7e04`).
The separate cold record is
`experiments/logs/root-prism-free/f0-character-phase-normalization01-cold.json`
(SHA-256 `56c67d0049db09454abc33d2801a9a66edb0b75e120df8c5f6c07f9ce65fb36b`).
The runs took 0.33 and 0.51 seconds. No frozen native model was modified by
these checks. The revised F0 search can use the reduction after binding the
records and retaining full original-parent acceptance.
