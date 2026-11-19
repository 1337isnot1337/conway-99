# Higher-flag products and the four-cycle separator

The complete nine-root r4s3 family rejects the repaired order-ten count
witness with SHA256
`190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d`.
Exactly one block produced an exact negative direction: the four-cycle
root, catalogue type 16. Its full product reconstruction has passed an
independent literal-edge calculation.

The two complete r2s4 blocks are exactly positive semidefinite at this
same point. These statements concern one finite count witness. They
do not exclude every count vector or settle existence of the graph.

## Product construction and normalization

The domains and labelled normalization are fixed by
[the domain preparation](grid_free_order10_higher_flags_domains.md).
The product source is
`experiments/workspace/grid_free_order10_higher_flags_products.py`,
SHA256
`32b39c98538bd5358e64e7e794c9f6464704ea7f1fe9f6f171d9243f4af88a36`.

For each pair of flags, the code retains every partial injection between
their free labels whose root masks match. It checks both edges and
nonedges on shared free vertices. Fresh right-side vertices are added
one at a time. Their edges to the root and to other right-side vertices
are prescribed; only edges to the left-exclusive free vertices remain
free. The catalogue child table rejects invalid extensions.

Every prefix transport is checked as a graph isomorphism. Normalizing a
prefix only shares a transport cache. The map is composed back to the
original vertex positions before translating future masks. Product
coefficients are never divided by a free-label stabilizer.

Preparation checks all 890 full-overlap multiplicities against their
root-fixing stabilizers. It reconstructs 211 entries with an independent
literal-prescription oracle and compares both product orders; 25 of
these entries contain order-ten terms. It also compares full matrices
against direct labelled-extension counts in the nine-vertex rook graph
for roots 2, 3, and 16, of block orders four, three, and fifteen.

Those controls passed in 5.242 seconds. A separate read-only review of
the product source also passed. The source-bound report is
`experiments/logs/moments-and-counts/order10-higher-flags-products-independent-review.json`.

## Exact r2s4 evaluation

All sixteen symbolic lower entries of the two r2s4 blocks are saved in
`experiments/logs/moments-and-counts/order10-higher-flags-products-preparation.json`.
At the repaired point, the prism-flag rows are exactly zero. The nonedge
root retains the matrix

\[
\begin{pmatrix}
8316&16632&16632\\
16632&104032&45928\\
16632&45928&71996
\end{pmatrix}.
\]

Its determinant is 21,460,346,772,480. Its principal minors of orders one
and two are also positive. The edge-root block retains only its positive
constant entry 1,386. The checker evaluates all 22 principal minors of
the original 4×4 and 3×3 matrices, including their zero rows, and verifies
the result again using rational Schur elimination. No eigensystem or
optimizer is used.

The exact evaluation source and report are:

- `experiments/workspace/grid_free_order10_higher_flags_small_scan.py`
- `experiments/logs/moments-and-counts/order10-higher-flags-r2s4-repair01-scan.json`

## Complete r4s3 generation and scan

All nine blocks completed in 13.193 seconds under a 300-second combined
generation-and-scan bound. The cache contains all 883 flags, 90,240
lower entries, and 237,296 tensor nonzeros. The largest block has order
332. Peak process memory was 292,132 KiB. There was no timeout and no
unconfirmed numerical negative direction.

The cache is independent of the count point. No root or flag was
deleted because its count was zero. Only rows whose entries were all
exactly zero at the point were removed temporarily from an eigensystem.
All product diagonals remain intact, including nonbinary products.

The cache is
`experiments/logs/moments-and-counts/order10-higher-flags-r4s3-blocks.pickle.gz`,
SHA256
`7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943`.

The scan result is
`experiments/logs/moments-and-counts/order10-higher-flags-r4s3-scan.json`,
SHA256
`c70c9efc5588e0c15b9899770a137b37937f2037456f02e6b58077bb6165bcab`.

## The exact four-cycle cut

In the saved fifteen-flag order at root 16, the integer direction is

\[
v=(0,0,0,-36,36,256,75,-131,-256,-57,-18,57,131,-75,18).
\]

Its exact quadratic value at the witness is

\[
v^TMv=-813{,}113{,}536.
\]

The induced-count coefficient gcd is eight. Dividing by that positive
gcd gives a 39-term primitive linear inequality with value
−101,639,192. The complete inequality is stored at
`unique_induced_count_cuts[0].terms` in the scan JSON, as pairs of
catalogue index and integer coefficient in unlabelled induced counts.
The associated vector, gcd, and exact contraction are stored at
`negative_blocks[0]`.

The inequality is necessary for every candidate graph because M is a
sum of rooted flag-vector outer products. The point supplies a negative
evaluation; it does not enter the definition or validity of the cut.

## Independent reconstruction

The vector has twelve nonzero entries, hence 78 supported lower-triangle
products. The fresh replay constructs every product by merging all
positive and negative adjacency prescriptions under every partial
injection, then enumerating unspecified cross edges. It uses no producer
child table, transport, or overlap routine.

All 78 independently generated coefficient rows match the saved tensor.
The full quadratic form, primitive 39-term induced form, positive gcd,
and negative value also match. This replay passed in 0.951 seconds.

Files:

- `experiments/workspace/grid_free_order10_higher_flags_fresh_replay.py`
- `experiments/logs/moments-and-counts/order10-higher-flags-r4s3-fresh-preparation.json`
- `experiments/logs/moments-and-counts/order10-higher-flags-r4s3-fresh-replay.json`

The fresh replay report SHA256 is
`0a6a50182903345149d9d6c61df745bb175bdeeb28bcd5bf0ba4cefa83c32802`.

The count witness still satisfies its previously checked original count
equations and 47 held cuts. The new four-cycle inequality explains why
that finite count witness cannot come from the requested graph. No new
LP was run in this package.
