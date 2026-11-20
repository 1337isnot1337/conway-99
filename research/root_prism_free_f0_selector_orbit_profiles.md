# Exact subset tables for the F0 selector orbits

The 42 selector orbits admit 5,733 distinct local count profiles after the
proved pair zeros and original Gram capacities are imposed. Exhaustive
enumeration examined all 155,904 subsets and retained 64,144 literal subsets.
The complete cold replay passed. No solver ran in this construction.

These are necessary conditions for the fixed component-zero F0 branch.
They do not establish a global incidence or exclude that branch. The other
component and its alignment remain free.

## Why the count tables are necessary

Let T be the selected subset of the 480 literal signatures in a hypothetical
graph. Let O_i be one of the 42 selector orbits under the 12 checked core
relabelings. Set N_i = |T intersect O_i|. For a pair orbit R, set
P_R = |R intersect choose(T, 2)|.

Averaging the Boolean incidence over the relabelings gives the existing
orbit coordinates

    x_i = N_i / |O_i|,     Z_R = P_R / |R|.

This is an orbit-stabilizer count. The relabelings act on labeled copies of
the incidence. They need not be automorphisms of the hypothetical graph.

Every pair in a proved-zero pair orbit is forbidden: P_R is a sum of
nonnegative Boolean products, so P_R = 0 forces each product to vanish.
For every original Gram equation, the contribution from T intersect O_i
is nonnegative and cannot exceed the full equation's quota.

The construction enumerates every subset of O_i, rejects subsets that
violate either condition, and records the remaining tuple

    (N_i, P_R1, ..., P_Rs),

where R1 through Rs are all retained pair orbits contained in choose(O_i, 2).
The actual restriction T intersect O_i is one of these subsets. Its tuple
must therefore occur in the table. No orbit representative is selected in
place of an unexamined subset. Deduplication uses equality of the complete
count tuple only.

The 42 tables use the current 15,038-column integer count model. They cover
all 42 selector populations and 320 within-orbit pair populations. Every
retained tuple also satisfies

    2 * sum(P_R for R inside O_i) = N_i * (N_i - 1).

The tables impose more local information than this single identity.
Cross-orbit compatibility is not checked by the enumeration.

## Enumeration and coordinate consequences

There are 38 orbits of size 12 and four of size 6. Thus the complete subset
count is 38 * 4096 + 4 * 64 = 155,904. Each table stores the literal pair
map, the applicable Gram capacities, all distinct tuples, a representative
subset for each tuple, and its multiplicity. A hash binds the disposition
of every enumerated mask.

The maximum local selector populations are 3 for five orbits, 6 for 25
orbits, and 12 for 12 orbits. Projection of the tables gives 222 upper
bounds smaller than the raw orbit-size bounds. Of these, 26 are selector
population bounds.

| Previous bound | New bound | Count columns |
| --- | --- | --- |
| 6 | 1 | 20 |
| 6 | 2 | 31 |
| 6 | 3 | 94 |
| 12 | 2 | 5 |
| 12 | 3 | 10 |
| 12 | 4 | 7 |
| 12 | 6 | 55 |

There are also 67 coordinate domains with missing values below their
maximum. For example, current count columns 5757 and 6215 each have local
domain {0, 1, 3}; the value 2 is impossible in their complete local tables.
The coordinate-domain record supplies a table-row witness for every
retained value. These projections add nothing beyond the full tables.

All these bounds are local maxima. A tuple's presence in a table does not
mean it extends to any assignment satisfying the other tables, the full
count equations, or the exterior graph constraints.

## Artifacts and checks

- [Complete enumeration source](../experiments/workspace/root_prism_free_f0_selector_orbit_profiles.py).
- [Frozen tables](../experiments/logs/root-prism-free/f0-selector-orbit-profiles01.json.gz),
  SHA256 `93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d`.
- [Complete cold replay](../experiments/logs/root-prism-free/f0-selector-orbit-profiles01-cold.json),
  SHA256 `cb10cd7dc77236d9caed7c7b8a410a33f7b998bea8d257b500d3c9f8561a76f8`.
- [Coordinate projection source](../experiments/workspace/root_prism_free_f0_selector_profile_domains.py).
- [Coordinate domains](../experiments/logs/root-prism-free/f0-selector-profile-domains01.json),
  SHA256 `0e307bbe9e39fe4e80e7f5dc3db84dbb62e5b855ac66c753e5b5111ee8b3dbf6`.

The initial enumeration took 4.80 seconds. The one complete cold replay
took 5.29 seconds. Both used a 60-second cooperative limit and compared
the deterministic full result, including every table and mask-stream hash.
The construction derives each Gram support from its core pair and the
original literal triples. All inherited inputs are bound by SHA256.

The intended consumer is an append-only table overlay on the integer
orbit-population model. This note records table preparation only; it makes
no claim about a subsequent integer query.
