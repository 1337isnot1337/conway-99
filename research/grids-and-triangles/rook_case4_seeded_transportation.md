# Transportation on the certified 99-zero face

This is a separate continuation of the
[unseeded transportation closure](rook_case4_transportation_results.md).
It begins with the union of 88 Gram/triple zeros and 14 published
empty-cover units. The intersection is exactly 352, 354 and 957, so the
union contains 99 of the 1,214 original columns.

The seed is rederived before preparation, forward closure and replay.
No earlier numerical LP point or numerical active-set guess is used.

## Explicit seed proofs

The 88 Gram/triple zeros are checked by the six original-row combinations
in `rook_case4_transportation_short_faces.py`. This proof uses nonnegative
real weights and the four stated triple capacities.

The other seed source is the complete frozen coordinate-cover registry.
The seed checker reads and hashes all 178,533 records and identifies its
14 empty covers. It also proves each empty cover directly, without relying
only on that registry entry.

Let \(B\) be the 35-core adjacency matrix, and let \(h_a\) be an original
attachment column. Its augmented exterior-neighbor target is

\[
t_a=(2\mathbf1-h_a-Bh_a,\;14-|h_a|).
\]

The last coordinate is the exterior degree. For each of the 14 targets,
the checker reconstructs every eligible neighbor among all 1,214 original
columns. It requires core overlap at most one and the zero-quota support
condition at both endpoints. Every actual exterior edge must pass these
tests.

For each unit target it finds and records coordinates \(i,j\) with
\(t_a[i]>t_a[j]\), while every eligible augmented neighbor
\(w_b=(h_b,1)\) satisfies \(w_b[i]\le w_b[j]\). The exact activated
neighbor equations would imply

\[
(t_a[i]-t_a[j])x_a
=\sum_b(w_b[i]-w_b[j])y_{ab}\le0.
\]

Nonnegativity therefore forces \(x_a=0\). The certificate contains the
complete eligible neighbor list and every difference product for each
unit. It checks the saved core Gram matrix and all 630 attachment supports
against the literal core and columns. Proposal values stored in the old
domain artifact are ignored.

## Continuation scope

The continuation runs one capacitated stage over all 105 projections.
It does not repeat the unseeded Gram-only stage. Every new cut expands into
the original Gram, triple and selector-upper-bound rows. Each negative
coefficient cites either one of the replayed seed proofs or an earlier
new zero event.

The forward stage has a 60-second budget, including preparation reload.
There can be at most 1,115 new zero columns. A completed fixed point saves
all 105 final projected flows. The separate 60-second replay rechecks the
seed, every full-column cut, the zero induction and the residual-cycle
coverage of those flows. No LP or SAT optimizer is called.

A feasible projection remains only a necessary condition. Neither
preparation nor a projected fixed point claims that the joint attachment
incidence is feasible. Any strict cut must pass the complete replay before
it can exclude case4.

Files:

- `experiments/workspace/rook_case4_transportation_seed.py`: standalone
  seed proof, including all 14 empty-cover dominance witnesses.
- `experiments/workspace/rook_case4_transportation_seeded.py`: new bounded
  closure wrapper, using the unchanged exact flow/cut routines.
- `experiments/logs/grids-and-triangles/rook-case4-transportation-seed-certificate.json`:
  exact seed and provenance.
- `experiments/logs/grids-and-triangles/rook-case4-transportation-seeded-preparation01/`:
  frozen continuation definition and preparation.

This note describes preparation. A production outcome, if authorized,
belongs to its separately bound result and replay files.
