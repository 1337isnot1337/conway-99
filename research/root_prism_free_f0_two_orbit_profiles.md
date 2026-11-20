# Joint population-three tables for F0

Two inherited count equations give

    N_0 + N_1 = 3,     N_6 + N_7 = 3.

Each pair of selector orbits contains 24 literal signatures. Exhausting
its 2,024 three-element subsets therefore gives a small exact joint table.
This construction checks both orbit pairs, with no solver or graph symmetry
assumption.

| Selector orbits | Subsets examined | Permitted subsets | Distinct joint tuples |
| --- | --- | --- | --- |
| 0, 1 | 2,024 | 512 | 176 |
| 6, 7 | 2,024 | 512 | 176 |

Each table records 22 population and pair-count coordinates, followed by
six signed populations. The pair counts include both within-orbit and
cross-orbit pairs. The signed populations use the same globally fixed
character signings as the earlier character construction.

## Necessity and exact coverage

Rows 1 and 3 of the checked integer count model are exactly the displayed
population equations. Any actual incidence selects precisely three
signatures from each corresponding union. The enumeration visits every
such subset.

A subset is rejected if it contains a literal pair in a proved-zero pair
orbit. It is also rejected if its contribution exceeds any of the 171
original Gram quotas. These partial contributions are nonnegative, so
both rejection rules are necessary for any full incidence.

For a surviving subset, the checker counts all pairs in every retained
pair orbit contained in the union. It also computes each signed population
directly from the selected literal signatures. The actual incidence's
restriction must produce one recorded tuple. No choice of local phase or
orbit representative replaces an unexamined subset.

There are 276 literal pairs in each 24-signature union. The pair-orbit
inventory accounts for all of them, including proved-zero orbits. Each
surviving tuple has total selector population three and total pair
population three. Its restriction to either individual orbit is checked
against the earlier complete signed local table.

The tables retain all 512 literal subsets through tuple multiplicities.
For each union, eight tuples have multiplicity one and 168 have
multiplicity three. Representative subsets and a hash of every examined
subset's disposition are retained.

These tables impose joint local realizability across a pair of orbits.
They are not a global incidence. Compatibility between the two separate
unions, and with the other 38 selector orbits, remains a separate problem.
No strict independence from the entire previous constraint set is claimed.

## Frozen checks and artifacts

The initial enumeration took 2.85 seconds. The single complete cold replay
took 4.69 seconds and matched both full tables and every disposition hash.
An independent source review checks the population-three argument, pair
mapping, zero substitutions, Gram capacities and signed-coordinate scope.

- [Enumeration source](../experiments/workspace/root_prism_free_f0_two_orbit_profiles.py).
- [Complete tables](../experiments/logs/root-prism-free/f0-two-orbit-profiles01.json.gz),
  SHA256 `6a1bc6d196358ecc618355bc64d6fe6a2b60be9fa9411afd29526c9f493995b9`.
- [Complete cold replay](../experiments/logs/root-prism-free/f0-two-orbit-profiles01-cold.json),
  SHA256 `afedafe2f3009849350b1682a2c329064efd9b204ab7b5a6051e5d50449fcf41`.
- [Independent source review](../experiments/logs/root-prism-free/f0-two-orbit-profiles-literature-review.json),
  SHA256 `62348d643001fcf3f7ac1f50184e08b4bca5e84e061e6281070d4b7a33f97c24`.

The first signed-count query was already frozen before these tables were
prepared. It did not include them. Adding them to a native model requires
a separate append record.
