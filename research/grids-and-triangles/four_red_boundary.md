# Boundary obstruction for the surviving four-base core

The 36-vertex four-rook core with root-gauged matching labels `[1,6,7]`
cannot occur in an `srg(99,14,1,2)`. Only 27 possible outside
neighborhoods satisfy its pair quotas, none can be used twice, and 63
outside vertices require such neighborhoods.

This note proves the exclusion of that explicit core. The separate
four-base interface census and Gram checks identify it as the only
remaining class. No incidence LP, SAT result, or floating-point sign
decision is needed for the boundary exclusion here.

## The explicit core

Number the four bases `0,1,2,3`. Each base has points `0,...,8` in row
order in a three-by-three array. Every matching from base zero is the
identity. The other matching maps, from the first base index to the
second, are:

| Interface | Images of `0,1,2,3,4,5,6,7,8` |
| --- | --- |
| `1 -> 2` | `0,3,6,1,4,7,2,5,8` |
| `1 -> 3` | `5,8,2,3,6,0,4,7,1` |
| `2 -> 3` | `7,1,4,8,2,5,6,0,3` |

These are labels `[1,6,7]` in the sorted eleven-map list used by
`seven_red_interfaces.py`. The checker also reconstructs that list from
the 72 rook automorphisms and verifies the indices, so the label
convention is explicit.

Let `B` be this core's adjacency matrix. Its degree is seven: four
neighbors in the same rook grid and one in each other grid. It satisfies
all common-neighbor upper bounds on its own vertices.

## Necessary outside signatures

Every vertex outside an induced rook grid has exactly one neighbor in
that grid. This follows because every pair of grid vertices already has
its full common-neighbor quota inside the grid, while the grid's ninety
outgoing edges meet its ninety outside vertices. Therefore an outside
vertex has exactly one neighbor in each of these four bases.

There are `9^4=6561` candidate signatures. For a pair of distinct core
vertices `i,j`, put

\[
G_{ij}=2-B_{ij}-(B^2)_{ij}.
\]

This is their remaining common-neighbor quota outside the core. A
signature can contain both vertices only when `G_ij>0`. The exact
enumeration retains precisely 27 of the 6,561 candidates. All 27 also
satisfy the mixed core/outside inequalities

\[
(B+I)h\le2\mathbf1,
\]

where `h` is the signature indicator.

Two different outside vertices cannot use the same signature. They
would have its four core vertices as common neighbors, exceeding the
maximum of two. Thus at most 27 outside vertices can exist, while the
graph needs `99-36=63`. This is a contradiction.

The same enumeration gives a local version: each core vertex belongs
to exactly three of the allowed signatures. It therefore has at most
three outside neighbors when signatures cannot repeat. Its degree
fourteen and core degree seven require seven outside neighbors.

## Optional Gram-range check

If `X` is the full outside-incidence matrix, the SRG identity gives

\[
XX^T=G=12I+2J-B^2-B.
\]

Every column of `X` is orthogonal to `ker(G)`. Exact rational elimination
gives a twelve-dimensional kernel. Of the 27 compatible signatures,
only nine are orthogonal to that kernel.

The nine columns can be attached as a fifth rook base: they form
bijective interfaces with all four original bases, and the resulting
45-vertex partial graph satisfies every common-neighbor upper bound.
This is an additional positive control of the signature calculations.
It is not a full graph construction. Neither the kernel calculation nor
the fifth-base control is needed for the `27<63` contradiction.

## Solver-free replay

`experiments/workspace/four_red_boundary.py` uses only Python's standard
library. It builds the explicit core, checks all 630 pair bounds,
enumerates every signature, and independently reproduces the signature
list by recursive extension. The optional range check uses exact
`Fraction` arithmetic and verifies every saved integral kernel vector.

The full signature list, core adjacency rows, kernel vectors, and
fifth-base control are saved in
`experiments/logs/grids-and-triangles/four-red-boundary.json`.

```bash
python experiments/workspace/four_red_boundary.py \
  --verify experiments/logs/grids-and-triangles/four-red-boundary.json
```

The finite count is exhaustive for the explicit core above. Extending
the conclusion to every configuration of four all-red grids uses the
separate complete interface census and its exact Gram exclusions.
