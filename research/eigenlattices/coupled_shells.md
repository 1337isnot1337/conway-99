# Defect cycles of a norm-16 eigenvector

Let `A` be the adjacency matrix of a hypothetical srg(99,14,1,2). An integral vector `f` satisfying `Af = -4f` and `fᵀf = 16` forces a partition of the graph into sets of sizes

    8 + 8 + 8 + 64 + 11.

The nonintegral translates of the negative eigenlattice have minimum squared norm at least twenty-two, as proved in [the level-seven note](level_seven.md). Thus every norm-16 vector in that lattice is covered by this integral case.

The first two sets support the positive and negative coordinates of `f`. The remaining sets have respectively four, two, and zero neighbors in that support. The four-neighbor vertices are described by a pairing of two eight-edge multisets. The pre-existing `signed_eight_heavy.py` census records 4,985 such incidence templates. The replay here independently recovers those counts and reduces them to 478 classes under side-preserving isomorphisms. These are partial incidence templates, not graphs or exclusions.

## The two eight-point sides

The coordinate sum of `f` is zero. If a coordinate has magnitude at least two, its eigenvector equation forces opposite-sign absolute mass at least eight. The total absolute mass is therefore at least sixteen, and the squared norm exceeds this mass by at least two. This contradicts norm sixteen. Thus `f` is +1 on eight points `P`, -1 on eight points `N`, and zero elsewhere.

Let `e_P` and `e_N` count internal edges of the two sides, and `c` count cross-edges. Summing the eigenvector equation on each side gives

    c - 2e_P = 32 = c - 2e_N.

Write the common internal-edge count as `e`. A negative vertex of internal degree `d` has `4+d` positive neighbors. Counting pairs of positive vertices with a negative common neighbor gives

    48 + 8e ≤ Σ_{x∈N} binom(4+d_N(x),2) ≤ 56 - e.

Here `binom(4+d,2) ≥ 6+4d`, and an adjacent positive pair has only one common neighbor while a nonadjacent pair has two. Therefore `9e ≤ 8`, so both sides are independent. Their cross-incidence matrix `B` is an 8-by-8 zero-one matrix with every row and column sum four and all distinct row and column inner products at most two.

## Deficit cycles

Define the two symmetric matrices

    D_P = 2(J-I) - BBᵀ + 4I,
    D_N = 2(J-I) - BᵀB + 4I.

Their diagonals are zero, their off-diagonal entries belong to `{0,1,2}`, and every row sums to two. Interpret each as a multigraph: an entry two is a doubled edge. Every component is therefore a cycle, including a doubled edge as a cycle of length two.

Every component has even order. To see this for `D_P`, let `T` be a component with `t` vertices and let `s` be the sum of the corresponding rows of `B`. The total multiplicity of deficit edges inside `T` is `t`, so

    Σ s_j = 4t,
    Σ s_j² = 4t + 2(2·binom(t,2)-t) = 2t².

Cauchy–Schwarz is an equality in eight coordinates. Thus every `s_j` equals `t/2`. Since the coordinates are integers, `t` is even. The same proof applies to `D_N`. This also proves that every opposite-side vertex has exactly half the vertices of each deficit component as neighbors.

In particular both deficit graphs are triangle-free. Their component-size partitions are among

    2+2+2+2, 4+2+2, 6+2, 4+4, 8.

The five support-core representatives already enumerated in `signed_eight.py` have these five partitions, respectively. No automorphism of the hypothetical 99-vertex graph has been assumed.

## The exterior partition

For an exterior vertex `x`, the eigenvector equation gives

    |N(x) ∩ P| = |N(x) ∩ N| = k(x).

Any pair in `N(x) ∩ P` must be an edge of the deficit graph `D_P`, because `x` supplies a common neighbor that is not in `N`. Triangle-freeness gives `k(x) ≤ 2`.

There are eighty incidences between `P` and the exterior. The total missing common-neighbor multiplicity of pairs in `P` is eight. Consequently

    Σ_x k(x) = 80,
    Σ_x binom(k(x),2) = 8.

Of the eighty-three exterior vertices, exactly eight have `k=2`, sixty-four have `k=1`, and eleven have `k=0`. Call these sets `H`, `L`, and `Z`.

Each vertex of `H` selects an edge of `D_P` and an edge of `D_N`. Each deficit-edge unit is selected exactly once, counting a doubled edge twice. Therefore the eight vertices of `H` are specified by a pairing of the two eight-edge multisets.

Once this pairing is fixed, all multiplicities of the `L` signatures are forced. If `R_{pn}` is the number of selected rectangles containing `(p,n)`, then

    multiplicity of the signature {p,n} = 2 - B_{pn} - R_{pn}.

Each multiplicity must be nonnegative. Two further necessary tests are imposed:

- The four core neighbors of each `H` vertex induce a matching. Equivalently, its selected 2-by-2 submatrix of `B` has every row and column sum at most one.
- Two distinct `H` vertices share at most two core neighbors.

## A direct obstruction on four high vertices

For a set `S ⊆ H`, let `c(h,k)` be the number of common neighbors of `h,k` in the sixteen-point core. Write `t_z = |N(z) ∩ S|`. Since every high vertex has at least four zero-class neighbors,

    4|S| ≤ Σ_z t_z.

For every nonnegative integer `t`, `t ≤ 1 + binom(t,2)`. Pair common-neighbor capacities therefore give

    Σ_z t_z ≤ 11 + Σ_{h<k in S}(2-c(h,k)).

No assumption on the edges inside `H` is needed. In particular, if four high vertices have total core pair-codegree at least eight, these inequalities say `16 ≤ 15`, a contradiction.

The overlap graph on `H`, joining two high vertices when they share a core neighbor, must consequently be connected. Its weighted degree is four at each vertex: each of a high vertex's four core neighbors belongs to exactly one other high signature. A connected component of order `s` has total pair-codegree `2s`. The subset inequality becomes

    4s ≤ 11 + s(s-1) - 2s.

Components of order one or two cannot have weighted degree four with pair-codegree at most two. Orders three and four violate the displayed inequality. Thus every component has order at least five, and an eight-vertex overlap graph has only one component.

The checker records the four vertices and both integer bounds for every exclusion. This removes 172 of the pre-existing 4,985 incidence templates, or seventeen of the 478 complete-incidence classes. The surviving counts are 4,813 templates and 461 classes. The earlier `signed_heavy_masks.py` tested aggregated zero incidences with no high-class edges. The argument here proves the indicated exclusions without that restriction.

## Exact template census

The pairing census gives the following counts. Repeated copies of the same deficit edge are not distinguished. The final column also identifies templates under arbitrary isomorphisms preserving the two eight-point sides.

| Deficit component sizes | Templates | Classes | Templates after counting | Classes after counting |
| --- | ---: | ---: | ---: | ---: |
| 2+2+2+2 | 90 | 4 | 72 | 2 |
| 4+2+2 | 326 | 27 | 320 | 24 |
| 6+2 | 681 | 118 | 681 | 118 |
| 4+4 | 2,068 | 86 | 1,920 | 74 |
| 8 | 1,820 | 243 | 1,820 | 243 |
| Total | 4,985 | 478 | 4,813 | 461 |

The first numerical column reproduces the pre-existing census in `signed_eight_heavy.py` and `experiments/logs/eigenlattices/signed-eight-heavy.log`; it is not a new exclusion or a new template count. The algebraic even-cycle proof above avoids relying on enumeration to establish the exterior partition. The 478-class quotient retains the complete core incidence, whereas the earlier `signed_heavy_masks.py` computation used 86 classes of heavy-signature overlaps.

`coupled_shells.py` enumerates every pairing. Its optional independent replay enumerates all distinct permutations of the negative deficit-edge multiset, then tests the resulting incidence products directly. The two paths agree on all five counts. The isomorphism reduction uses the canonical form of the colored 24-vertex graph comprising `P`, `N`, and `H`.

The seventeen exclusions are certified by the integer counting inequality above, independently of a SAT solver.

The necessary pairing conditions are exhaustive for the stated template definition. They are not sufficient for completion to a strongly regular graph. A valid completion would have to realize one of these templates whenever a norm-16 eigenvector exists; a graph without such a vector is outside this reduction.

## Forced exterior degrees

For an exterior vertex `x`, write `d_H(x)`, `d_L(x)`, and `d_Z(x)` for its numbers of neighbors in the indicated sets. Summing the common-neighbor equations against the sixteen core vertices gives

    4d_H(x) + 2d_L(x) = 32 - 5d_core(x).

Combining this with degree fourteen yields:

| Vertex set | Core degree | `d_L(x)` | `d_Z(x)` |
| --- | ---: | ---: | ---: |
| H | 4 | `6 - 2d_H(x)` | `4 + d_H(x)` |
| L | 2 | `11 - 2d_H(x)` | `1 + d_H(x)` |
| Z | 0 | `16 - 2d_H(x)` | `d_H(x) - 2` |

In particular the graph on `H` has maximum degree three, every vertex of `Z` has at least two neighbors in `H`, and

    e(Z) = 5 + e(H).

The last identity follows by counting `H`–`Z` edges from both sides. It implies that the eleven zero-signature vertices are never independent.

In fact `H` has at most one edge. Put `e=e(H)` and `k_z=d_H(z)`. Then `Σ_z k_z=32+2e`. The integer inequality `binom(k,2) ≥ 3k-6` gives

    Σ_z binom(k_z,2) ≥ 30+6e.

Every core vertex has exactly two high neighbors, so core vertices account for sixteen common-neighbor incidences across pairs of high vertices. The twenty-eight high pairs have total common-neighbor budget `56-e`. After also counting common neighbors in `H`,

    Σ_z binom(k_z,2) ≤ 40-e-Σ_h binom(d_H(h),2).

Thus `7e+Σ_h binom(d_H(h),2) ≤ 10`, proving `e≤1`. The zero-class graph consequently has exactly five or six edges.

The remaining high-pair budget sharply limits repeated low incidences. If `e=0`, the minimum of `Σ_z binom(k_z,2)` at total degree thirty-two is thirty-one, attained at ten threes and one two. If `e=1`, the minimum at total degree thirty-four is thirty-six, attained at ten threes and one four. Hence

    Σ_{l∈L} binom(d_H(l),2) ≤ 9  if e=0,
    Σ_{l∈L} binom(d_H(l),2) ≤ 3  if e=1.

There are respectively forty-eight or forty-four `H`–`L` edges.

[The zero-class structure note](coupled_zero_structure.md) strengthens
these restrictions: the graph on `Z` is one of eleven forests, with
components only `K1`, `K2`, `P3`, `K1,3`, or `P4`. Each listed forest has
a directly checked witness at the high/zero incidence level. This does
not remove another complete-incidence class.

`coupled_shells_filter.py` tests symmetric graphs on the eight `H` vertices. For each proposed `H` neighborhood it solves the required `L` incidences exactly as an integral bipartite b-matching with the forced signature capacities. It also imposes all common-neighbor upper bounds already visible inside `P ∪ N ∪ H`. A SAT result means these necessary constraints have a witness; it does not certify the remaining graph.

`coupled_shells_zero.py` models all edges within the nineteen vertices `H ∪ Z`, imposes the exact degree identities, and tests the necessary low-signature row matchings. Of the 478 complete-incidence classes, seventeen are UNSAT and the remaining 461 have directly checked partial witnesses. The seventeen coincide exactly with the counting exclusions; this solver test contributes no further exclusion.

`coupled_shells_low.py` adds all 512 possible high-to-low adjacency bits, the exact high/core common-neighbor equations, and the exact common-neighbor counts of high pairs. It also checks every codegree upper bound visible in the resulting partial graph. Edges from `L` to `Z` and within `L` remain unchosen, so SAT still means only a partial completion.

The complete high/low census has no unresolved entries. It removes fourteen further classes by UNSAT proofs: one in the `6+2` core, one in the `4+4` core, and twelve in the `8` core. They account for ninety-three labeled templates. Together with the direct counting obstruction, this leaves 4,720 of the original 4,985 templates, in 447 classes:

| Deficit component sizes | Classes after counting | Additional proof exclusions | Surviving classes | Surviving templates |
| --- | ---: | ---: | ---: | ---: |
| 2+2+2+2 | 2 | 0 | 2 | 72 |
| 4+2+2 | 24 | 0 | 24 | 320 |
| 6+2 | 118 | 1 | 117 | 675 |
| 4+4 | 74 | 1 | 73 | 1,904 |
| 8 | 243 | 12 | 231 | 1,749 |
| Total | 461 | 14 | 447 | 4,720 |

Each additional exclusion has a saved CNF core, trimmed DRAT proof, and JSON manifest with the explicit incidence template and SHA-256 digests. `coupled_shells_certificate.py` regenerates the full CNF, checks its digest, verifies that every retained input clause belongs to the full formula, then checks the saved proof with [drat-trim](https://github.com/marijnheule/drat-trim) at revision `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`. All retained proof steps are RUP steps in the checked certificates. The graph-to-CNF reduction uses the necessary equations stated here; the certificate proves that the encoded partial-completion conditions are inconsistent for the listed template.

Every SAT entry contains explicit adjacency bits. The replay builds the corresponding 99-vertex partial adjacency, checks all degrees and common-neighbor equations on `P ∪ N ∪ H`, and verifies every common-neighbor upper bound visible in the partial graph. It leaves the missing `L`–`Z` and `L`–`L` edges unresolved.

The stronger `coupled_shells_incidence.py` also chooses `L`–`Z` edges and imposes the full Gram equations on the 35-point core `P ∪ N ∪ H ∪ Z`. A thirty-second Glucose run and a sixty-second CaDiCaL run on core zero, class one, did not decide that instance. These limits give no exclusion and no completion.


## Reproduction

The complete representatives and partial witnesses are archived in
`experiments/logs/eigenlattices/coupled-shells-orbits.json` and
`experiments/logs/eigenlattices/coupled-shells-low-all.json`.
`make verify-coupled-shells DRAT_TRIM=/absolute/path/to/drat-trim` regenerates
the census, checks agreement with the archive, and replays all 478 outcomes.
`make verify-global-constraints` includes the independent integer-only
checker for the seventeen counting exclusions and the exact scalar-theta
witness replay.

From the repository root, use Python with NumPy, SciPy, pynauty, z3-solver, and python-sat installed. If using the project virtual environment, prefix the commands with `.venv/bin/`:

```bash
python experiments/workspace/coupled_shells.py --independent --orbits /tmp/coupled-shells-orbits.json
python experiments/workspace/coupled_shells_filter.py /tmp/coupled-shells-orbits.json --output /tmp/coupled-shells-filter.json
python experiments/workspace/coupled_shells_zero.py /tmp/coupled-shells-orbits.json --output /tmp/coupled-shells-zero.json
python experiments/workspace/coupled_shells_low.py /tmp/coupled-shells-orbits.json --output /tmp/coupled-shells-low.json
python experiments/workspace/coupled_shells_theta.py --verify experiments/workspace/coupled-shells-zero-theta.json
python experiments/workspace/coupled_shells_replay.py /tmp/coupled-shells-orbits.json experiments/logs/eigenlattices/coupled-shells-low-all.json --drat-trim /path/to/drat-trim
```

The five support cores are read from `experiments/workspace/signed-eight-cores.json`. The support-core census can separately be regenerated with `signed_eight.py --regenerate` from its workspace directory.

## Limit of short-shell scalar inequalities

An exact rational check with `level_seven_exact.constraints`, Fourier order eighteen, both scaled-dual inclusions, and the existing sparse-vector floors still admits a solution at each modular rank `34,36,38,40,42`, even after setting both norm-14 and norm-16 coefficients of `H` to zero. The five exact coefficient witnesses are saved in `coupled-shells-zero-theta.json`; `coupled_shells_theta.py --verify` substitutes them into every rational inequality without invoking a solver. Therefore merely excluding these two shells does not settle the current scalar theta relaxation. The incidence reduction above retains information that those scalar coefficient conditions discard.
