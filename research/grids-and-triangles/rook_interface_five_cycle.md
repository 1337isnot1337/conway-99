# Five rook-isomorphic interfaces cannot form a cycle

The later [one-partner bound](rook_partner_bound.md) gives a stronger
restriction. The present proof remains an independent finite argument
using visible common-neighbor quotas.

In a hypothetical `srg(99,14,1,2)`, five distinct induced rook grids
cannot form a cycle of rook-isomorphic matching interfaces. The proof
reduces to a complete staged enumeration, and every case fails a
common-neighbor quota already visible in the selected grid cores.

Combining this with the
[star and four-cycle exclusions](rook_interface_star.md), the graph of
rook-isomorphic interfaces has maximum degree two and its cycles
have length at least six. No red-triangle assumption is used.

## All five grids are disjoint

Suppose the cycle is

\[
R_0,R_1,R_2,R_3,R_4,R_0.
\]

Adjacent grids are disjoint by the definition of a matching
interface. Every nonadjacent pair on a five-cycle has a common
neighbor in the cycle, so its two grids are distinct partners of
that neighbor. The
[disjoint-partners lemma](rook_interface_star.md#distinct-partners-are-disjoint)
makes those grids disjoint as well. Thus all five grids are pairwise
disjoint, giving a 45-vertex induced core.

## Exact gauge and permutation domains

Let `H` be the 72-element rook automorphism group. Let `O` be the
eighteen-element orbit of

\[
P=(0,5,7,8,6,1,4,2,3).
\]

The [three-grid classification](two_rook_interfaces.md) proves that,
when two matching interfaces of a three-grid configuration are rook
isomorphisms and are gauged to identities, the remaining matching
belongs to `O`.

Transport labels along the path `0 -> 1 -> 2 -> 3 -> 4`, making
those four cycle interfaces identities. Write `r in H` for the
closing interface `0 -> 4`. The diagonal `0 -> 2` lies in `O`.
Apply a common rook relabeling to all five grids to make that
diagonal exactly `P`. This preserves the identity interfaces and
conjugates `H` and `O` to themselves.

The other four diagonals can now be written in the following form,
where composition acts on the rightmost factor first:

| Interface | Permutation | Reason |
| --- | --- | --- |
| `0 -> 2` | `P` | Fixed by common conjugation |
| `1 -> 3` | `q in O` | The two interfaces through root `R_2` are identities |
| `2 -> 4` | `s in O` | The two interfaces through root `R_3` are identities |
| `0 -> 3` | `t r`, with `t in O` | Gauge the triple rooted at `R_4` |
| `1 -> 4` | `r w`, with `w in O` | Gauge the triple rooted at `R_0` |

For the fourth row, transport from `R_4` to `R_0` is `r^{-1}`,
and transport to `R_3` is the identity. Therefore the remaining
normalized interface is `p_03 r^{-1} in O`, giving `p_03=t r`.
For the fifth row, root transport from `R_0` to `R_4` is `r`,
so `r^{-1}p_14 in O`, giving `p_14=r w`.

This covers every configuration with

\[
r\in H,\qquad q,s,t,w\in O.
\]

There are `72*18^4=7558272` assignments after the justified gauge.
The computation does not construct all their full cores. A smaller
core excludes almost all assignments immediately.

## First stage: 23,328 four-grid cores

The core on grids `0,1,2,3` depends only on `(q,t,r)`. Its six
interfaces are

\[
p_{01}=p_{12}=p_{23}=I,
\qquad p_{02}=P,\quad p_{13}=q,\quad p_{03}=tr.
\]

There are `18*18*72=23328` assignments. Every completed core has
degree seven. For each distinct pair of its vertices, the checker
requires

\[
|N_B(u)\cap N_B(v)|+B_{uv}\le2.
\]

The exact counts are:

| First-stage step | Count |
| --- | ---: |
| Values of `q` failing before the `03` interface is added | 2 |
| Assignments covered by those early failures | 2,592 |
| Completed four-grid cores checked | 20,736 |
| Four-grid assignments passing every quota | 8 |

Thus 23,320 assignments fail and only eight require extension.
The certificate records all eight survivors by their `(q,t,r)`
indices in explicitly saved, sorted permutation domains.

## Second stage: 2,592 five-grid extensions

For each surviving four-core, add grid `R_4`, its internal rook
edges, and the known interfaces `04=r` and `34=I`. The two remaining
choices are `14=r w` and `24=s`, with `w,s in O`.

The complete second-stage count is:

| Second-stage step | Rejected choices | Full assignments covered |
| --- | ---: | ---: |
| Failure before either remaining interface | 4 partial cores | 1,296 |
| Failure after `14`, before `24` | 68 choices | 1,224 |
| Completed five-grid cores checked and rejected | 72 | 72 |
| Total | | 2,592 |

The accounting identity is

\[
4\cdot324+68\cdot18+72=2592.
\]

Every completed five-grid core has degree eight. All 72 that reach
the last stage already exceed a common-neighbor quota. No core
survives, so a five-cycle of rook-isomorphic interfaces is impossible.

## Explicit certificates and independent replay steps

The saved JSON has one integer code for each of the 23,328
first-stage assignments and each of the 2,592 second-stage
assignments. For an `n`-vertex core, the code `n*i+j` identifies a
pair violating its common-neighbor quota. The first-stage code `-1`
identifies one of the eight cores that passes every pair check.

Discovery uses early rejection and bit-set intersections. The replay
rebuilds every completed core, including all assignments rejected
before their last matching was added. It decodes each recorded pair
and counts its common neighbors by direct membership checks. For
the eight survivors, it checks every pair. Thus early rejection
cannot hide an unchecked extension or depend on an assumption about
the missing matching.

The replay also checks that completed four-cores and five-cores have
degrees seven and eight, respectively. Its domains are independently
constructed from coordinate permutations and conjugation of `P`;
the eighteen-map list is compared with the separate complete
three-grid classification artifact.

```sh
python experiments/workspace/two_rook_interfaces.py \
  --verify experiments/logs/grids-and-triangles/two-rook-interfaces.json

python experiments/workspace/rook_interface_five_cycle.py \
  --verify experiments/logs/grids-and-triangles/rook-interface-five-cycle.json
```

The second command uses only the Python standard library and completes
in under one second in the project environment. The proof uses no
floating-point spectrum, linear-programming status, or SAT solver.

The separate `rook_interface_dense_audit.py` rebuilds all 23,328 first-stage
cores using dense integer matrices. It finds the same eight survivors and
checks all 2,592 full extensions without early rejection. It also checks
the 324 stars and all 23,328 normalized four-cycle assignments directly.

This result excludes a particular cycle in the grid-interface graph.
It does not exclude longer cycles, and does not resolve existence of
the strongly regular graph.
