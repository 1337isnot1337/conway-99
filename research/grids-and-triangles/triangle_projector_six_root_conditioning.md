# Six-root triangle conditioning

This package contains all 30 six-vertex root types that contain a triangle.
It retains every triangle class that meets the root. There are 2,374 classes
and 127,647 lower-triangular matrix entries. No count point was used to
construct or select the classes.

Let Q be the triangle-index matrix with diagonal 120, entry -20 for two
triangles meeting once, and entry 7e-6 for disjoint triangles with e cross
edges. In any SRG(99,14,1,2), Q is 210 times an orthogonal projector.

For the one or two triangles contained in the root, let C be the corresponding
principal matrix of Q. Its positive definiteness was checked in the frozen
scope census. The tested kernel is

    det(C) Q(U,V) - q_U^T adj(C) q_V,

where q_U records Q between U and the core triangles. This is the positive
multiple of the per-embedding Schur complement. Every core-triangle row
vanishes. Since the complete family of triangles through each root vertex is
retained, the six point-star vectors also lie in the kernel.

## Complete products and normalization

Every class has at most two vertices outside the root. A pair union therefore
has at most ten vertices. The constructor enumerates every partial injection
between the two outside label sets, retains every compatible overlap, and
enumerates all missing cross-edge choices. Visible common-neighbor caps remove
only impossible extensions.

A literal ordered pair of labelled flag extensions has exactly one overlap
map. Each ordered pair of actual triangle sets has the product of the two
outside-mask factorial stabilizers many independent labellings, including
when the triangles overlap. After summing contributions by induced graph type,
the constructor divides by that product. All 239,743 divisions were exact.
There is no additional same-class factor two because these products are
already ordered.

The complete preparation considered a conservative bound of 2,967,175 union
candidates. It retained 263,589 cap-valid unions and 230,648 nonzero tensor
coefficients. The preparation completed in 61.052 seconds. Five balanced
chunks each completed in less than 13 seconds; the configured bounds were
60 seconds per chunk and 180 seconds overall.

A second construction directly enumerated labelled root embeddings and
ordered triangle pairs inside selected host graphs. Across 674 chunk/host
controls, it checked 46,482 labelled root embeddings and 455,190 ordered
triangle pairs against contraction of the saved tensors. These controls
include 311 ten-vertex host cases. They do not assume the host graph is an
SRG; they check the literal induced-count expansion.

## Files and query scope

The source is `experiments/workspace/triangle_projector_six_root_conditioning.py`.
The full model, per-root checkpoints, five chunk models and their direct
controls are under
`experiments/logs/moments-and-counts/triangle-projector-six-root-preparation01/`.
The model has raw SHA256
`3474f83d65a7fd4ffbc84b124b147f8cafc6ab4b0fcd2ed3ba3c39eed58d1550`.

The separate `triangle_projector_six_root_query.py` binds this model and the
unchanged 48-cut count point. Its proposed single query has a 30-second bound.
It contracts using Python integers and checks the exact coefficients of
det(tI+M), retaining all rows. A negative numerical direction is accepted only
after exact integer-vector and induced-form verification. A timeout preserves
the completed blocks and does not claim coverage of all 30 blocks.

At this preparation checkpoint, no count query has run. Passing these blocks
would certify only this finite necessary family at the saved point; it would
not construct a graph or settle the existence question.
