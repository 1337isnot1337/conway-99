# Remaining triangle counts with seven all-red grids

If seven all-red grids exist, their 36-vertex complement U must have
18, 27, or 36 vertices lying in exactly two U triangles. Equivalently,
the number lying in three U triangles is 18, 9, or zero.

This is a necessary condition, not an exclusion of seven all-red grids.
The nine-vertex case below uses a complete finite residual-core catalogue
and exact rational spectra. The larger remaining cases have not been
enumerated.

## The residual operator

Every U vertex has seven neighbors in U and one in each all-red base.
Each base projection has fibers of size four and selects two U triangles
through every vertex. Thus each vertex belongs to two or three U
triangles in total.

Let Y be the vertices with two triangles and put y=|Y|. Let F consist of
the U edges lying in no U triangle. Its degrees are three on Y and one
on U minus Y. Set

    D = I_Y + A_F.

For the direct sum W of the seven rook eigenvalue-one spaces, let T be
the incidence lift to U and Z=im(T). The same selected/omitted triangle
calculation used in
[`eight_red_exclusion.md`](eight_red_exclusion.md) gives

    C T = D T,    C|Z = D|Z,

where C is the adjacency matrix on U. The space Z is rational and
invariant, and is orthogonal to constants. With

    r=dim(Z),    s_j=trace((D|Z)^j),

the required identities are

    12r-s_1-s_2 = 112,
    7p = 140-3r+s_1,    0<=p<=28-r,
    s_3+s_2-12s_1 = 32-4y/3.                              (1)

The final identity is the
[cubic trace identity](red_grid_cubic_trace.md). Its modular corollary
gives 9|y. Therefore y is initially one of 0, 9, 18, 27, 36.

## The case y=0

If y=0, F is a perfect matching on 36 vertices and D=A_F. Its only
eigenvalues are one and minus one. If their multiplicities on Z are a,b,
the energy equation is

    10a+12b=112.

Its nonnegative integer solutions are (a,b)=(4,6) and (10,1). The
numerators 140-3r+s_1 are respectively 108 and 116. Neither is divisible
by seven, contradicting (1). Thus y is nonzero.

## The case y=9 reduces to 408 cores

Let H be the restriction of F to Y. It is triangle-free and subcubic,
and every pair has at most two common neighbors. These conditions are
necessary because F is a subgraph of U and no edge of F lies in a U
triangle.

Every vertex outside Y has F-degree one. Consequently H determines F
up to relabeling: attach 3-deg_H(v) private leaves to each v in Y, then
pair the remaining vertices outside Y into isolated edges. If H has e
edges, there are 27-2e private leaves and e isolated edges. This gives
exactly 36 vertices.

The catalogue contains all 408 unlabeled graphs H with the stated
properties. Its generation starts with the empty graph and adds one
vertex with every possible neighborhood, retaining precisely the
triangle-free, subcubic, codegree-at-most-two extensions. These conditions
are hereditary under vertex deletion, so every target graph has a parent
in the preceding level. Exact pynauty certificates remove isomorphic
duplicates.

Every level through order seven is independently compared with the
complete NetworkX graph atlas. The complete level counts are:

| Order | Graphs |
|---:|---:|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 7 |
| 5 | 12 |
| 6 | 28 |
| 7 | 60 |
| 8 | 161 |
| 9 | 408 |

The catalogue run completed, rather than reaching its explicit time or
size limit. The final representatives and completion status are saved in
[`seven-red-type2-core-catalog.json`](../../experiments/logs/grids-and-triangles/seven-red-type2-core-catalog.json).

## Exact factor census

For each core, construct its 36-by-36 integer matrix D and factor its
characteristic polynomial over the rationals. A rational invariant
subspace has a characteristic polynomial consisting of whole irreducible
factors, with multiplicities no larger than those available in D.

Every eigenvalue on Z is less than three: the ambient nonconstant
Rayleigh bound gives at most three, and TT*=12I-C_Z^2-C_Z is positive
definite on Z. If an irreducible factor has a root at or above three,
none of that factor can appear on Z. The implementation makes this
decision by exact rational root counting. There is no lower-bound issue:
Gershgorin's bound gives every eigenvalue of D at least minus two.

For every remaining factor, its degree and its first three power sums
are computed by integer companion-matrix powers. The search exhausts
all bounded multiplicity tuples satisfying (1), with y=9 and r<=28.
All 408 cores have zero surviving spectra.

The saved nine-vertex pass uses the full available multiplicity of
every allowed factor. It does not need the additional Krylov-space
orthogonality filter implemented by the small-case scout. A separate
replay restoring all original multiplicities gives the same exclusion.

Therefore y=9 is impossible. Combined with 9|y and the y=0 argument,
the remaining values are

    y in {18,27,36}.

The corresponding U triangle counts are 30, 27, and 24.

## Reproduction and scope

```sh
.venv/bin/python experiments/workspace/seven_red_core_catalog.py --order 9 --seconds 45 --output /tmp/seven-red-catalogue.json
.venv/bin/python experiments/workspace/seven_red_nine_spectra.py --catalogue /tmp/seven-red-catalogue.json --seconds 50 --output /tmp/seven-red-spectra.json
make verify-seven-red-residual
```

The first command exhausts the core catalogue; the second reads the saved
complete catalogue and exhausts its spectra. The saved spectral result is
[`seven-red-nine-spectra.json`](../../experiments/logs/grids-and-triangles/seven-red-nine-spectra.json).
Its completion flag records that all 408 cores were processed.

The independent replay in
[`seven_red_nine_audit.py`](../../experiments/workspace/seven_red_nine_audit.py)
uses direct neighbor-subset extensions instead of the original extension
helper. It reproduces all catalogue levels and all 408 isomorphism classes.
It obtains each characteristic polynomial from a leaf-twin quotient and
isolated-edge factors, uses a separate rational Sturm calculation, and
computes traces by Newton sums. With full factor multiplicities and no
Krylov subtraction, it checks 2,441 irreducible factors and 1,695,332
multiplicity tuples. Of these, 2,101 pass the quadratic conditions and none
passes the cubic condition. The exact replay output is
[`seven-red-nine-independent-audit.json`](../../experiments/logs/grids-and-triangles/seven-red-nine-independent-audit.json).

An earlier redundant audit of y=0,3,6 is retained in
`seven-red-residual-spectra.json`. The divisibility-by-nine lemma now
excludes y=3 and y=6 directly. Neither this audit nor the nine-vertex
census constructs the U triangle edges or the full 99-vertex graph.
