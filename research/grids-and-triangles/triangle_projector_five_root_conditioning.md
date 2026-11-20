# Five-root triangle conditioning

This package contains all triangle classes that meet each five-vertex
catalogue root containing a triangle. There are eight roots, with
257 classes and 4,859 lower matrix entries. No class is removed using
count values.

Let C be the Q principal matrix on all triangles contained in the root.
For a triangle U meeting the root, let q_U list Q(T,U) over those core
triangles. Every C in this domain is positive definite. The necessary
conditioned kernel is

```
K(U,V) = det(C) Q(U,V) - q_U^T adj(C) q_V.
```

This is det(C) times the Schur complement of C in Q, so it is positive
semidefinite. For one core triangle it is 120Q-q_Tq_T^T. For the bowtie
root, the two-triangle C matrix is [[120,-20],[-20,120]], with determinant
14,000.

Every retained triangle has at most two vertices outside the root.
A pair union therefore has at most nine vertices. The preparation uses
the existing induced catalogue, with no order-ten catalogue extension.

## Complete product construction

A class is an unordered triangle with a fixed root intersection and
a multiset of outside root-neighborhood masks. Its labelled-extension
multiplicity is the product of the factorials of the mask multiplicities.

For each ordered pair of labelled extensions, the shared outside vertices
give one partial injection. The source enumerates every such partial
injection, checks equality of shared root masks, and tries every unspecified
edge between the two exclusive outside sets. Every retained union satisfies
the visible common-neighbor caps.

For each union graph F, the source accumulates Aut(F) times the integer
kernel. It collects all partial injections and completions of that type
before dividing by the product of the two class stabilizers. Each actual
ordered pair of unlabelled triangles has exactly that many independent
slot labelings, including when the triangles overlap. Same-class pairs
are already ordered products; no additional factor of two is inserted.

The construction retains all lower entries, including those involving
core triangles. All core-triangle rows vanish coefficientwise.

## Preparation outcome

| Root type | Classes | Nonzero tensor terms | Cap-valid union completions |
| --- | ---: | ---: | ---: |
| 26 | 56 | 3,224 | 3,915 |
| 27 | 44 | 1,773 | 2,168 |
| 28 | 26 | 679 | 905 |
| 32 | 34 | 914 | 1,163 |
| 33 | 34 | 1,243 | 1,673 |
| 34 | 28 | 747 | 980 |
| 35 | 19 | 346 | 526 |
| 37 | 16 | 201 | 310 |

The preparation finished in 3.039609396000742 seconds. It considered
11,640 cap-valid union completions under the conservative 108,481
candidate bound, verified 9,642 exact stabilizer divisions, and retained
9,127 nonzero tensor terms. Each completed block was checkpointed before
continuing.

The normalization was checked independently on 131 catalogue hosts:
8 of order five, 7 of order six, 25 of order seven, 23 of order eight,
and 68 of order nine. The control directly enumerates labelled root
embeddings and ordered triangle pairs. It compares the resulting
matrices with contraction over all induced subsets of the host. The
checks cover 17,162 labelled root embeddings and 148,544 ordered
triangle pairs. This control does not use the partial-injection
enumerator.

## Bound inputs and query gate

- Builder: `experiments/workspace/triangle_projector_five_root_conditioning.py`,
  SHA256 `578f8db7c51c7f5b934e7f7275b295a9a5908bf09d5f6a9d9662366914046e5c`.
- Preparation:
  `experiments/logs/moments-and-counts/triangle-projector-five-root-preparation01/preparation.json`,
  SHA256 `ed9e636277398aadb39077a344456412619bd40ea970717ebffdb148102ef73c`.
- Raw model SHA256:
  `9011737fb1459d5c6c4db1dca51f777c49b3306b3ce27ca336096961ed768a06`.
- Compressed model SHA256:
  `395d56df140bcdc30554ef8bed48663d11f006abb5cd72f1d94aff018f216ff8`.
- Separate query driver:
  `experiments/workspace/triangle_projector_five_root_query.py`,
  SHA256 `ca578502aa0048428f2bb3a7a13b4d5fd969870adc6f82b1c92b7dbf804c7a54`.

The preparation has not loaded a count point. The query driver requires
the immutable integer count point and exact model/source hashes. It
contracts with Python integers and checks characteristic polynomials
exactly. Negative directions must reconstruct a strictly negative induced
count form. It also checks the core-triangle zero rows and all five root
point-star kernel vectors. The latter follow from QB^T=0 because every
triangle through a root point is retained.

The point query requires the coordinator's separate source/model gate.
The six-root tensor family is not included and remains unbuilt.
