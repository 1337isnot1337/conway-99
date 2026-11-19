# An eleven-signature forbidden pattern

In the complementary-rook 27-core, the following eleven exterior signatures
cannot all be selected. This is a positive-only restriction: it places no
assumption on the absence of any other signature.

| Selector | Signature \((p,q,t)\) |
|---:|---|
| 16 | \((0,7,2)\) |
| 32 | \((1,3,5)\) |
| 33 | \((1,3,6)\) |
| 44 | \((1,6,2)\) |
| 57 | \((2,3,0)\) |
| 62 | \((2,3,7)\) |
| 72 | \((2,6,1)\) |
| 74 | \((2,6,4)\) |
| 85 | \((3,1,0)\) |
| 87 | \((3,1,4)\) |
| 143 | \((5,0,3)\) |

Here \(R\) is the fixed nine-vertex rook adjacency matrix, the three core
grids have adjacency

\[
B=\begin{pmatrix}
R&I&I\\ I&R&I\\ I&I&J-I-R
\end{pmatrix},
\]

and a signature \((p,q,t)\) means adjacency to core vertices
\(R_p,S_q,T_t\). Selector numbers are one-based in the fixed 252-signature
domain. Thus the checked clause is

\[
\neg z_{16}\vee\neg z_{32}\vee\neg z_{33}\vee\neg z_{44}
\vee\neg z_{57}\vee\neg z_{62}\vee\neg z_{72}\vee\neg z_{74}
\vee\neg z_{85}\vee\neg z_{87}\vee\neg z_{143}.
\]

## Proof scope

Let \(F\) be the frozen joint incidence/edge model in
`two_rook_tip_boundary_joint_integer.py`, representative 3943553752.
It has 252 binary selectors, all 20,934 eligible exterior edge variables,
the exact Gram equations, endpoint activation, conditional mixed and degree
equations, and core-pair neighbor packing. Every graph completion of the
core gives a solution of \(F\).

A fresh explicit-unit formula \(F\land\bigwedge z_i\), with exactly the
eleven units above, is UNSAT. The independent certificate replay rebuilt
the entire baseline and exact unit-augmented CNF, checked both hashes,
checked every retained input clause against that formula, and verified the
retained DRAT proof. The certificate contains 15,276 retained input clauses
and 17,868 retained proof lines.

The model remains a necessary relaxation; it does not include every exterior
common-neighbor cap. An UNSAT proof in this relaxation is sufficient for the
forbidden-pattern conclusion. It does not exclude the complementary-rook
core, prove that this pattern occurs, or solve the 99-vertex problem.

## Bounded deletion test

The starting pattern was the independently checked case 1 reduction in
`complement_rook_incidence_core_simplification.md`: fifteen positive units
and \(-184\). One deterministic pass tried removing \(-184\), then each
positive unit in ascending order. It used one proof-free baseline oracle.

The first five trials removed \(-184,4,6,11,12\). Each returned UNSAT.
The other eleven trials returned UNKNOWN, so all those literals were kept.
There were no SAT trials. The full search, including bootstrap, took
33.806 seconds within its 60-second allowance. Each query requested a
two-second interrupt; observed return times are saved, including scheduling
overshoot up to 4.264 seconds.

The final eleven-unit set then received a separate fresh explicit-unit
proof. That proof took 10.393 seconds and passed the direct DRAT check.
The subsequent independent full-baseline rebuild and retained-proof replay
also passed. The final proof certifies the shorter set independently of the
unproved intermediate assumption cores.

No minimality claim follows from the eleven UNKNOWN trials. Quota propagation
alone does not recover a removed literal from the other ten in any of those
eleven trials. With all eleven present, it forces 33 selected signatures and
121 absent signatures; that propagation is exported separately.

## Relabelled clauses and earlier antecedent reductions

The previously verified 144 core relabellings give 144 distinct images of
this positive-only pattern. These relabellings act on the signature domain,
Gram data, mixed demands, and eligible edges. No automorphism of the unknown
graph is assumed, and no permutation of auxiliary counter variables is
needed for the mathematical transport.

The static export also closes all eight incidence-refined patterns from the
earlier implication package. There are 1,296 distinct patterns before
subsumption. The new eleven-unit images subsume the 144 images of the older
sixteen-unit case 1 pattern. The export therefore has 1,152 nonsubsumed
clauses, with lengths 11, 18, 22, 28, and 29.

On the finite set of 1,152 relabelled designs from the original eight-design
pilot, the new positive-only images cover exactly the 144 case 1 images.
This is a static coverage statement about previously excluded designs.
No master enumeration or new joint solve used the orbit closure.

## Files and replay

The deletion runner is
`experiments/workspace/complement_rook_core_deletion_pilot.py`.
Its terminal transcript is
`experiments/logs/grids-and-triangles/complement-rook-core-deletion-pilot01.json`.
The direct proof certificate and compact retained proof are in the adjacent
`complement-rook-core-deletion-pilot01/` directory. Raw full-formula/proof
caches use proof index 1001, which preserves the original eight pilot caches.

Replay the decisive proof:

```sh
.venv/bin/python experiments/workspace/complement_rook_incidence_master_certificate.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-core-deletion-pilot01/design-1001-core-certificate.json \
  --drat-trim /tmp/conway99-drat-trim/drat-trim \
  --log /tmp/conway-positive-eleven-drat-replay.log
```

The separate `complement-rook-core-deletion-pilot01-full-replay.json`
records the successful full replay and its exact bindings. The creation-time
pending flag in the original direct certificate remains unchanged.

Replay the static clause export:

```sh
.venv/bin/python experiments/workspace/complement_rook_refined_pattern_orbits.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-refined-pattern-orbits.json
```

That replay also reruns the prior complete semantic action audit and compares
its result with the frozen earlier certificate. All new files and hashes are
listed in `complement-rook-core-deletion-pilot01-artifacts.json`.
