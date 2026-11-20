# Exact zero closure of the prism-free order-ten model

## Result

The prism-free assumption forces 58 of the 549 ordinary core counts to
zero. Exactly 1,443 of the 48,965 induced catalogue types contain a prism.
After those 58 core coordinates are zero, every coefficient of each of
the 1,443 induced-count forms vanishes. This leaves 491 free core counts.

These are necessary conditions for a prism-free SRG(99,14,1,2). They do
not exclude the prism-free case and do not construct a graph. They justify
explicit zero bounds in a separately named numerical preparation. All
positive sequential-embedding bounds and all previous row scalings can
remain unchanged.

## Why prism containment is exact here

The prism is two disjoint triangles joined by a perfect matching. An
ordinary prism copy in a graph with adjacent codegree at most one is
induced. An extra edge between the triangles would give one of the edges
inside a triangle two common neighbors. Therefore an ordinary core that
contains this pattern cannot occur in a prism-free candidate.

The checker enumerates every triangle of each stored graph and every
disjoint triangle pair. It recognizes a prism when each of the six
vertices has exactly one neighbor in the other triangle. All catalogue
graphs satisfy the local common-neighbor caps. Thus this test recognizes
ordinary prism containment on the catalogue, including the 549 ordinary
core representatives. Coordinate 1 is the prism itself, catalogue type
99, with automorphism order 12.

The ordinary zero coordinates are:

```text
1, 9, 41, 42, 43, 44, 46, 52, 53, 56, 57,
171, 173, 175, 178, 180, 199, 204, 233, 237,
275, 279, 294, 303, 311, 314, 320, 341, 346, 349,
379, 385, 391, 406, 413, 430, 432, 438, 444, 446,
452, 456, 457, 460, 463, 466, 486, 500, 503, 509,
512, 514, 531, 540, 541, 542, 546, 548
```

Coordinates 56 and 57 already have zero bounds in the grid-free model.
The new preparation stores the same 547 numerical columns and fixes 56
of them to zero. Its remaining 491 columns are free.

## Independent extension argument

For an induced graph type, its unmarked one-vertex extension identity
expresses a positive multiple of its count as a positive sum of counts
of its extensions. If the parent count is zero, nonnegativity forces
each child count to zero. Starting at prism type 99 and following the
complete extension DAG reaches exactly the 1,443 types found by the
direct triangle-pair test.

This gives two exact checks of the same induced zero set: containment
inside each stored graph and reachability through the extension table.
The checker then substitutes the 58 ordinary core zeros in the exact
reduced count matrix. All 1,443 corresponding rows become identically
zero, including their constant coefficients.

## What individual row-sign propagation proves

A more limited rule starts with only `x1 = 0`. For an induced-count
inequality whose constant is zero, suppose every remaining nonzero
coefficient is negative. Since all ordinary core coordinates are
nonnegative, every coordinate in that support must be zero.

Repeated use of this rule proves 28 zero coordinates in 21 recorded
steps. It does not prove all 58 zeros. With only those 28 coordinates
removed, the prism-containing induced forms retain 9,374 nonzero
coefficients. The full 58-coordinate result uses prism containment and
the extension argument above. The certificate records this distinction.

Each sign step stores its induced type, graph, primitive exact row,
positive normalization divisor, and newly forced coordinates. Replay
checks both the implication and its equality with the saved reduction.
No numerical point or optimizer is used.

## Exact files and replay

The source is
`experiments/workspace/grid_free_order10_prism_zero_closure.py`.
Its SHA-256 is:

```text
1940942c270880ca5d8853c860074bd5c79a3dcc8d5283fd9a3bd5ad52d77bc0
```

The certificate and logs are in
`experiments/logs/moments-and-counts/`:

- `prism-zero-order10-zero-closure.json`
- `prism-zero-order10-zero-closure.log`
- `prism-zero-order10-zero-closure-replay.log`
- `prism-zero-order10-zero-closure-manifest.json`

The certificate SHA-256 is:

```text
cde1bd353eb39fe8aa713080a5acfb6ae78f3dd13244d9255c9217541060919c
```

Replay uses the existing exact reduction without regenerating it:

```bash
.venv/bin/python experiments/workspace/grid_free_order10_prism_zero_closure.py replay \
  --certificate experiments/logs/moments-and-counts/prism-zero-order10-zero-closure.json
```

Generation and replay both passed. The generation took 7.725 seconds.
The saved source, certificate, and logs remain separate from the later
IPM loop and from all earlier prism-zero proposals.
