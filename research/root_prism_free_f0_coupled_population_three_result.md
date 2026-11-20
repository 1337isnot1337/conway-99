# Complete coupled population-three census

## Exact outcome

The authorized census checked all 262,144 ordered pairs of literal triples
from the two frozen 24-signature unions. It completed in 12.67 seconds.
The separate cold replay checked the full saved ledger and every summary
in 9.97 seconds.

| Disposition | Literal pairs |
| --- | ---: |
| Survive | 178,304 |
| Rejected by a previously proved zero cross pair | 83,840 |
| Additional rejection by an original Gram capacity | 0 |
| Total | 262,144 |

The Gram capacities remain part of the checked necessity model. The
complete result shows that they add no rejection after the zero-pair
filter on this particular finite product.

No actual full count candidate was queried. A surviving six-signature
restriction is not a 60-signature incidence or a graph completion.

## Exact cross-count domains

The complete domain has 48 original cross-pair orbits:

| Original pair-orbit IDs | Reduced count columns | Exact attainable values |
| --- | --- | --- |
| 23, 143 | Already removed as proved zero | \(\{0\}\) |
| 25, 146 | 5699, 5812 | \(\{0,1,2\}\) |
| The other 44 cross-pair orbits | Listed in the full record | \(\{0,1,2,3\}\) |

There is no new forced-zero coordinate. Every minimum, maximum, and
intermediate value in this table has an explicit first literal-pair
witness in the result.

The two upper bounds are

\[
P_{25}\le2,\qquad P_{146}\le2.
\]

Here \(P_p\) is the literal selected-pair population of original pair orbit
\(p\). In the original 15,589-column count namespace these are columns
5,872 and 5,993. In the reduced 15,038-column namespace they are columns
5,699 and 5,812.

These bounds apply to a complete F0 count assignment. Each relevant pair
orbit has both endpoints inside the two unions, so its full population is
already determined by their six selected signatures. Any actual
assignment must restrict to one of the completely enumerated survivors.
No other signature outside the 48-member union contributes to those
pair orbits.

All nine literal cross pairs are counted with multiplicity. Their
cross-count populations sum to nine on every survivor. The bounds do
not assert selector zeros or an F0 exclusion. Independence from every
previous count-model inequality has not been established.

## Joint tuple cost

The survivors produce exactly 59,376 distinct joint tuples, each with
90 count coordinates and 12 signed population coordinates.

| Literal preimages of a joint tuple | Number of tuples |
| ---: | ---: |
| 1 | 56 |
| 3 | 59,224 |
| 6 | 96 |

The multiplicities sum to 178,304. Multiplicity six means that different
orbits of the common order-three action can have identical complete
joint tuples; the preparation's Burnside bound was an upper bound on
distinct tuples.

An explicit 59,376-row, 102-column allowed-assignments table would contain
6,056,352 cells. No such native table was built. The census retained exact
byte keys in memory, then exported the tuple count, multiplicity
histogram and exact sorted-stream hash.

The tuple stream SHA256 is
d1ac85bcb1e1b64c4e81fe7a64c23403f1067f8ac7273d967117da4ce61d6c82.

## Certificate and replay

The complete disposition ledger contains one unsigned 16-bit code per
literal pair. The order is the lexicographic product of the two
recovered 512-triple lists. Each rejection code identifies a proved-zero
original pair orbit or an original Gram row.

The ledger's uncompressed SHA256 is
bade8cd4fdfa10dc971bb6723cb09347cc938b29125a48c9b80306d21c40af46.

The cold replay recomputed all 262,144 cases and reproduced:

- every disposition byte;
- all cross-count value sets and attaining witnesses;
- both new bound-two consequences;
- the joint tuple multiplicities and sorted-stream hash.

No optimizer, native allowed-assignments table, production count
candidate, or automatic retry was used.

## Frozen artifacts

The earlier [preparation note](root_prism_free_f0_coupled_population_three.md)
and its source/domain package remain unchanged.

- [Coordinator source gate](../experiments/logs/root-prism-free/f0-coupled-population-three-root-source-review.json)
- [Complete census](../experiments/logs/root-prism-free/f0-coupled-population-three-census01.json.gz)
- [Literal disposition ledger](../experiments/logs/root-prism-free/f0-coupled-population-three-dispositions01.u16le.gz)
- [Census log](../experiments/logs/root-prism-free/f0-coupled-population-three-census01.log)
- [Cold replay](../experiments/logs/root-prism-free/f0-coupled-population-three-census01-cold.json)
- [Cold replay log](../experiments/logs/root-prism-free/f0-coupled-population-three-census01-cold.log)

The complete census SHA256 is
bc6f74139acbc3f995bea5cfe8d61877dab5b8457b968cffe8bef6d2fb69d80d.
The cold replay SHA256 is
6f70a1092952df17ad04ebfe2287a82aa71479241d4e2f17e3857dee0f78a5d4.
