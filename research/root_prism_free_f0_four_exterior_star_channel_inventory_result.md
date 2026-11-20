# Retained four-exterior star-channel inventory result

The complete encoding inventory passed. It replaces the 23,010 accepted retained four-exterior inequalities by 23,010 three-term inequalities and 2,448 shared channel definitions. The replacement block has 91,410 coefficient occurrences, compared with 401,874 in the original block: 310,464 fewer terms.

This is an exact reformulation of those inequalities. It adds no graph exclusion or independent mathematical constraint. No native model was built or queried in this inventory.

## Exact representation

For a center \(b\) and one exact original live-star edge set, define

\[
p_b+\sum_{e\in E_b}y_e-x_b=0.
\]

The checked quota-one mixed support contains every star edge with coefficient one. Its other edges are nonnegative, so \(0\leq\sum_{e\in E_b}y_e\leq x_b\). Thus the unique value of \(p_b\) lies in \([0,1]\), and is Boolean on Boolean original variables.

Each original row becomes

\[
y_{bc}-p_b-p_c\leq0.
\]

The identity preserves both the Boolean feasible projection and the real projection with relaxed channel domains. The complete proof, including the distinction from keeping auxiliary integrality while relaxing original variables, is in [the encoding note](root_prism_free_f0_four_exterior_star_channels.md).

## Measured sizes

| Quantity | Exact count |
|---|---:|
| Retained original rows checked | 23,010 |
| Original block terms | 401,874 |
| Original repeated star-edge occurrences | 332,844 |
| Distinct shared channels | 2,448 |
| Distinct-star edge occurrences | 17,484 |
| Channel-definition terms | 22,380 |
| Three-term inequality terms | 69,030 |
| Replacement block rows, including definitions | 25,458 |
| Replacement block terms | 91,410 |
| Term reduction | 310,464 |
| Complete endpoint-origin links | 46,020 |
| Distinct quota-one mixed witnesses | 1,002 |

If this change alone is applied to the accepted model, its variable count becomes 71,382 and its row count becomes 260,042. These are proposal dimensions. The existing native model remains unchanged.

Channels were deduplicated only by the same center selector and exactly the same sorted original star-edge IDs. Every core-pair origin and quota-one mixed witness was retained. Only the 1,884 original literal zeros used by the accepted four-row family define these stars; no later zero was silently substituted.

## Execution and preservation

The separate exact controls passed once in 75 milliseconds. They checked 754 scaled-integer grid points and unique channel extensions, 13 Boolean clause grid points, 75 quota-one subsets, three rejected support/coefficient mutations, exact deduplication with all origins, and all eight native signed-clause assignments. They did not read actual case data or evaluate the inventory factory.

The one gated inventory passed in 34.336 seconds through validation and serialization. The elapsed time from inventory start through serialization was 1.948 seconds. The complete report is 1,903,849 bytes, within the declared 16 MiB bound. Both report and finalization passed. Their exact text was preserved before publication hashes were computed. No retry occurred.

The complete four-row input was restored from its three previously uploaded immutable chunks and checked against its full bytes, SHA256 and Git blob identity. The unrun v1 source and configuration, the executed v2 source and configuration, the label-only timing correction and both independent source reviews remain preserved.

## Exact artifact bindings

- [Complete inventory](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-inventory01.json): SHA256 f522a8aa9ae699660a36dc78a97ca63bfe19bf97c4a075362a8951db0db71df3; Git blob f832577546031f48359dcb583b22f1cfd834a65a.
- [Inventory finalization](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-inventory01-finalization.json): SHA256 0ce007feb9bba740240d7b0fb2f506deb0571f90152ffa47ad841597c16b50fe.
- [Actual controls](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-controls01.json): SHA256 70969bc33d7ee35fd58eb2e18d7592cf2606fee779c73625ba9e0291a778a1ea.
- [Controls finalization](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-controls01-finalization.json): SHA256 d98ce18d41989549d7b12f6cfe52619514d1d683291b60825cdff72ff6a1a81b.
- [Root gate](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-root-gate01.json): SHA256 50b78ede9acf3ab66f9ecef126e960ddff0ad26db87bc4a75530ff3e4d3f5769.

A future native formulation still needs a frozen builder and an independent complete replay of its original rows, replacements, channel definitions and variable identities. Runtime improvement has not been measured. This result alone gives no feasible graph or whole-component contradiction.
