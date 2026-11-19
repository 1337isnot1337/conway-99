# Domains for shared exterior triangles

The current complementary-rook joint model has 252 possible exterior
signatures and 20,934 eligible edges. This note derives a possible
strengthening by all adjacent exterior common-neighbor equations. It
records exact domains and prospective CNF sizes. No large formula has
been built and no triangle-model solve has been run.

## Necessary triangle equations

Suppose exterior vertices `u,v` are adjacent. Their total number of common
neighbors is one. If their signatures share one core point, they have no
common exterior neighbor. Thus every exterior triangle must have three
pairwise disjoint core signatures.

If their signatures are disjoint, they must have exactly one common
exterior neighbor. Consequently every selected eligible edge with core
overlap zero lies in exactly one exterior triangle.

There are 14,652 eligible edges with overlap zero and 6,282 with overlap
one. The complete eligible-edge graph contains 750,708 triangles:

| Number of overlap-one edges | Candidate triangles |
| ---: | ---: |
| 0 | 209,952 |
| 1 | 379,368 |
| 2 | 132,912 |
| 3 | 28,476 |

Exactly 209,952 triangles can occur in a completion. Every one of their
three edges is globally shared with all other row systems. Each
overlap-zero edge belongs to between 24 and 64 such candidate triangles.

For each allowed triangle `T={u,v,w}`, introduce a Boolean variable

\[
t_T\ \longleftrightarrow\ c_{uv}\wedge c_{uw}\wedge c_{vw}.
\]

For every overlap-zero eligible edge `e`, impose

\[
\sum_{T\supset e}t_T=c_e.
\]

For each candidate triangle containing an overlap-one edge, forbid its
three edges from being simultaneously present.

The triangle definition uses all four clauses: three implications from
the triangle variable to its edges, and the reverse implication from
the three edges to the triangle variable. The reverse implication is
essential. The octahedral graph has eight actual triangles, and its
twelve edges can be partitioned into four of them. Selecting only those
four triangle variables satisfies the forward implications and a
one-selected-triangle-per-edge condition. Every graph edge nevertheless
lies in two actual triangles. The reverse implications reject this false
encoding witness. The script checks that control exactly.

## What is redundant

The triangle equivalences only define auxiliary variables. The edge
quotas and forbidden triangles express the missing adjacent-pair
conditions. A model that already enforces all strongly regular
common-neighbor equations implies them. The present necessary joint
model does not explicitly enforce all those equations.

Some forbidden triangle clauses have a direct proof from a single mixed
row already present in the base formula. Suppose `u,v` share core point
`i`, and the third triangle vertex `w` has mixed demand `d_w(i)=1`.
The two edges `wu,wv` already exceed that demand. Edge activation makes
this argument valid even when `w` has a selector variable.

This proves direct redundancy for 344,340 of the 540,756 forbidden
triangles. The remaining 196,416 have no such two-edge mixed-row
obstruction. This classification does not assert that each remaining
clause is logically independent of the entire base formula.

The proposed constraints give every adjacent exterior pair the correct
common-neighbor count. Nonadjacent exterior common-neighbor caps remain
absent, except for the already encoded core-pair packing consequences.
A SAT point of this strengthened model would still require a full
99-vertex defect check.

## Exact prospective sizes

Using a sequential at-most-one counter for every overlap-zero edge, the
additional quantities are:

| Component | Variables | Clauses |
| --- | ---: | ---: |
| Triangle definitions | 209,952 | 839,808 |
| At-least-one triangle for a selected overlap-zero edge | 0 | 14,652 |
| At-most-one counters | 615,204 | 1,830,960 |
| All forbidden triangles | 0 | 540,756 |

The old full-core base has 1,156,482 variables and 2,575,728 clauses.
Including every forbidden triangle gives 1,981,638 variables and
5,801,904 clauses. Omitting only the 344,340 directly redundant triangle
clauses leaves 5,457,564 clauses with the same variables. A two-unit
tip-pair branch adds two clauses to either total.

The counter-size calculation is checked against small independent calls
to the cardinality encoder for every input length that occurs. It does
not allocate the prospective full CNF.

## Reproduction

`experiments/workspace/complement_rook_triangle_domains.py` reconstructs
the exact existing domain hash, enumerates all eligible graph triangles,
and records hashes for the allowed and forbidden triangle lists. It also
records every overlap-zero edge's candidate-triangle multiplicity
distribution and representative mixed-row redundancy witnesses.

```sh
.venv/bin/python experiments/workspace/complement_rook_triangle_domains.py \
  --output experiments/logs/grids-and-triangles/complement-rook-triangle-domains.json
```

The output is a domain/size certificate for a proposed encoding. It is
neither an exclusion certificate nor a graph witness.
