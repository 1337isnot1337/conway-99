# Two direct pair-population bounds in F0

The retained count coordinates 5699 and 5812 each have upper bound 2. These
are original selector-pair orbits 25 and 146, respectively. The proof uses
the existing quota-one selector incompatibilities. It does not use either
population-three equality or the coupled 262,144-pair census.

This is a necessary condition for an F0 incidence. It is not an exclusion
of F0, an incidence construction, or a graph construction.

## Pair objects

The twelve members of selector orbit 0, in the frozen literal order, are

```
0, 1, 4, 5, 88, 91, 92, 95, 210, 211, 214, 215.
```

Each target pair orbit is a perfect matching from these selectors to one
other selector orbit. Write its matching as `a -> pi(a)` and put

\[
y_a=z_a z_{\pi(a)},\qquad P_R=\sum_a y_a.
\]

Here every selector `z` is Boolean, and `P_R` is the count coordinate,
not the averaged pair coordinate. The latter equals `P_R / 12`.

| Left selector | Partner in pair orbit 25 | Partner in pair orbit 146 |
|---:|---:|---:|
| 0 | 26 | 147 |
| 1 | 145 | 27 |
| 4 | 30 | 151 |
| 5 | 149 | 31 |
| 88 | 83 | 146 |
| 91 | 144 | 81 |
| 92 | 87 | 150 |
| 95 | 148 | 85 |
| 210 | 82 | 24 |
| 211 | 25 | 80 |
| 214 | 86 | 28 |
| 215 | 29 | 84 |

Two pair objects cannot both be active if their endpoint union contains a
proved-zero selector pair. Define the compatibility graph on the twelve
objects by the absence of such a zero pair. Every active collection is a
clique in this finite graph.

## A small triangle-free certificate

For pair orbit 25, the possible neighbors of the object with left endpoint
0 are `{88, 92, 95, 214}`. For pair orbit 146 they are
`{95, 211, 214, 215}`. In each case seven explicit zero witnesses exclude
all other objects from this neighborhood. Six further witnesses make the
four remaining neighbors pairwise incompatible.

The certificate records all thirteen witnesses for each orbit, with
literal endpoints, original pair-orbit IDs, and the original quota-one
Gram row containing both endpoints. A quota-one equality with nonnegative
Boolean selectors prevents any two of its selectors from being chosen.
Thus every zero used here is checked directly against that equality.

The twelve actual core actions preserve each target matching and act
transitively on its left endpoints. Transporting these thirteen witnesses
therefore checks every neighborhood. This is symmetry of the finite
literal domain; it assumes no automorphism of a hypothetical 99-graph.

Every neighborhood is independent, so both compatibility graphs are
triangle-free. They each have twelve vertices and twenty-four edges.
Consequently a clique has size at most two, and

\[
P_{25}\leq 2,\qquad P_{146}\leq 2.
\]

The only zero pair orbits used are

- for target 25: `0, 3, 4, 143, 3087, 3089`;
- for target 146: `0, 3, 4, 23, 2684, 2688`.

The checker also supplies a four-selector partial set attaining two for
each target under these pair-zero constraints. This establishes the exact
clique bound for this compatibility test; those partial sets are not full
incidences.

## Checked scope and files

The direct check and its cold replay both passed. The source checks all
24 target pairs, 288 matching-equivariance identities, 26 base zero
witnesses, and 312 transported zero witnesses. It binds the frozen domain,
its independent replay, and the original second-moment preparation. It
does not rerun a selector census or invoke an optimizer.

- `experiments/workspace/root_prism_free_f0_pair_population_two_proof.py`
- `experiments/logs/root-prism-free/f0-pair-population-two-proof01.json`
- `experiments/logs/root-prism-free/f0-pair-population-two-proof01-cold.json`

The original column IDs are 5872 and 5993. The reduced count column IDs
are 5699 and 5812. All IDs are zero-based. The separate coupled census
remains unchanged and supplies a stronger description of its specified
48-selector domain; this proof provides a shorter justification of these
two particular upper bounds.
