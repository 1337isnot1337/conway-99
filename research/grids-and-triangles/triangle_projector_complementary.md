# Complementary triangle-projector blocks

Let B be point–triangle incidence in a hypothetical SRG(99,14,1,2), and let
Q = 210(I − Bᵀ(7I+A)⁻¹B). The previously proved identity Q² = 210Q and
symmetry show that both Q and 210I − Q are positive semidefinite.

Fix an injective labelled embedding of a four-vertex root H. Partition
all triangles by their intersection S with H and the multiset of
H-neighborhood masks of their vertices outside H. Let X be the matrix
whose columns are the class indicators on the triangle set. Different
classes have disjoint supports, so

```
XᵀX = diag(n_C).
```

Consequently the complementary class matrix is

```
Xᵀ(210I − Q)X = 210 diag(n_C) − XᵀQX.
```

Summing this identity over labelled embeddings of H gives the necessary
condition

```
210 diag(p_C) − M_Q >= 0.
```

Here p_C is the class first moment and M_Q is the frozen full-class
triangle-projector matrix. The preparation retains all 574 classes in
the nine blocks of orders 107, 93, 72, 49, 79, 58, 41, 34, and 41.
It adds no pair products to the existing 135,819-term tensor.

## Exact first-moment normalization

For a class C, form the literal graph F = H union T: the root retains its
labels, S is the prescribed root intersection, and the remaining vertices
form the outside part of the triangle. All root-to-outside edges are
specified by the masks.

Each induced unlabelled copy of F has Aut(F) isomorphisms from this
literal graph. Two such isomorphisms give the same labelled-root,
unlabelled-triangle realization precisely when their quotient fixes every
root vertex and permutes outside triangle vertices with identical root
masks. Those vertices form a clique. Thus that stabilizer has order

```
s_C = product over masks m of multiplicity_C(m)!.
```

Therefore

```
p_C = (Aut(F) / s_C) * N_F,
```

where N_F is the unlabelled induced count. There is no additional
root-automorphism factor.

The divisor includes repeated nonzero masks. For example, when T meets H
in exactly one vertex r, two outside vertices with equal mask {r} must be
divided by 2. For a triangle wholly inside the root, the empty product is
1 and the coefficient is Aut(H).

The source independently enumerates every outside-label permutation to
check s_C. Among the 574 classes, 427 have s_C = 1, 138 have s_C = 2, and
9 have s_C = 6. Exactly 36 classes have a repeated nonzero mask.

## Preparation and controls

The complete preparation took 1.7350531330012018 seconds. The 574 first
moments each contain one induced-count term on at most seven vertices.

All 300 catalogue hosts of orders 4 through 7 were checked. For each host,
the source directly enumerated labelled root embeddings and unlabelled
triangles, then compared all 574 class totals with the induced-subset
evaluation of the first-moment forms. These controls covered 44,750
labelled root embeddings and 29,442 root/triangle pairs. They test
normalization; they do not assert projector positivity for the small hosts.

Three synthetic exact characteristic-polynomial controls include two
indefinite matrices, one with a zero diagonal. The negative-vector branch
also reconstructs and verifies its primitive count form.

The source and preparation are frozen at:

- Source: `experiments/workspace/triangle_projector_complementary.py`,
  SHA256 `cc35693952e351bafec2920ebb3f241170a7ca1d67b961f505095c11703f1c0d`.
- Forms: `experiments/logs/moments-and-counts/triangle-projector-complementary-preparation01/first-moments.json`,
  SHA256 `3c3b957f6cfaebafa448804d9c61759b3a0fc448c484a7b590095f831ecc6184`.
- Preparation: the same directory's `preparation.json`,
  SHA256 `67cd2f67e3276b23f1ad7d6e7e7ca023320172a265402e5c9d8202d14fd8725e`.

No count point was loaded during preparation. The query requires a
separate source/model gate and performs exact integer contraction and
characteristic-polynomial checks. A negative direction must reproduce a
strictly negative induced-count linear form. No optimizer is used.

The complementary block is also
210 XᵀBᵀ(7I+A)⁻¹BX. This factorization proves its positivity in an actual
graph. It does not by itself establish that the tested finite vertex-flag
families already contain the required triangle-incidence class vectors.
No independence from the complete earlier relaxation is asserted here.
