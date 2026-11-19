# Smaller clauses for a minimum-type near anchor

This is a separate normalization analysis. It changes no formula in the
running global-prism-free pilot and includes no full graph solve.

At a prism-free root, each near-anchor matching avoids the reference
mate matching. Its alternating component partition is one of

\[
222<24<33<6.
\]

Choose a near anchor with the earliest type in this order, relabel it
as anchor zero, and normalize its matching as before. Each of the other
thirteen near anchors must then have the same or a later type. The
chosen anchor already has its prescribed canonical type and needs no
additional exclusions.

This preserves the union of the four cases. It does not preserve every
earlier same-index case individually. Alternating component type is
invariant under signed-axis relabeling. The canonical matching
stabilizer fixes the chosen anchor, permutes the other thirteen
anchors, and preserves all these restrictions. The existing lex
minimum argument therefore remains valid under this normalization.

## Short forbidden components

An alternating component on two reference axes consists of two
anchor-matching edges. There are two possible matchings on any chosen
pair of reference axes, giving

\[
\binom62\cdot2=30
\]

two-edge forbidden patterns. A component on three reference axes has
eight possible matchings, giving

\[
\binom63\cdot8=160
\]

three-edge patterns.

For a minimum type of `33`, the excluded earlier types are `222` and
`24`. These are exactly the no-reference-mate matchings with a
two-axis alternating component. Thirty two-edge negative clauses per
other anchor therefore suffice.

For a minimum type of `6`, exclude both two-axis and three-axis
alternating components. A no-reference-mate partition of six with
neither type of component can only be `6`. This needs thirty two-edge
clauses and 160 three-edge clauses per other anchor.

For a minimum type of `24`, only type `222` is excluded. There are
120 complete matchings of this type, each supplying a six-edge clause.
There is also a shorter-clause alternative: forbid two disjoint
two-axis alternating components. Their four reference axes can be
chosen and paired in

\[
\binom64\cdot3\cdot2^2=180
\]

ways. Under the no-reference-mate hypothesis, the remaining two axes
must form the third two-axis component. Thus the 180 four-edge clauses
are equivalent to the 120 six-edge clauses in the intended domain.

| Minimum type | Encoding | Clauses per other anchor | Lengths | Total over 13 anchors |
| --- | --- | ---: | --- | ---: |
| `222` | No earlier type | 0 | — | 0 |
| `24` | Complete earlier matchings | 120 | 6 | 1,560 |
| `24` | Two disjoint short components | 180 | 4 | 2,340 |
| `33` | One two-axis component | 30 | 2 | 390 |
| `6` | One two-axis or three-axis component | 190 | 30 of length 2; 160 of length 3 | 2,470 |

The two alternatives for type `24` both have 720 literal occurrences
per anchor. The four-edge version has 780 more clauses over the thirteen
anchors, with shorter maximum width.

## Complete finite check and the scope qualification

The verifier directly enumerates all 10,395 perfect matchings on twelve
points. It reproduces all eleven alternating-component type counts.
Exactly 6,040 matchings avoid the reference mate edges, with counts

\[
222:120,\qquad24:1440,\qquad33:640,\qquad6:3840.
\]

Every forbidden-pattern equivalence above is checked against every
one of those 6,040 matchings. The surviving matching counts are 5,920
for either type-`24` encoding, 4,480 for type `33`, and 3,840 for type
`6`. The actual global primary-variable clauses are generated and
hashed. Their sets are checked under the saved stabilizer generators.
The corresponding matching-complete partial controls from
[`root_prism_free_structure.md`](root_prism_free_structure.md) satisfy
all the new restrictions.

The two type-`24` encodings are not equivalent without the
no-reference-mate hypothesis. Exactly 180 matchings of type `1122`
contain two two-axis components but no complete `222` matching. The
verifier records all 180 as outside-scope counterexamples. The
normalization must retain the prism-zero side constraints.

## A local propagation comparison

The source includes a direct Boolean unit-propagation implementation;
it calls no SAT solver. Its local matching CNF has the sixty possible
non-reference-mate edges, one at-least-one clause per point, and
pairwise at-most-one clauses. This gives 552 base clauses.

Set the four edges

\[
03,\quad12,\quad47,\quad56
\]

to true. They form two disjoint two-axis alternating components. Only
two complete no-reference-mate matchings remain, and both have type
`222`. The four-edge component encoding detects the conflict
immediately. With the six-edge complete-matching encoding, unit
propagation stops with the four remaining edge variables unassigned.

This proves a strict propagation improvement for this explicit local
encoding. It does not establish a runtime improvement in the complete
SRG formula. The four-edge type-`24` variant is a reasonable default
for a later normalized comparison because it has the same literal
count and exposes the shorter forbidden pattern directly.

## Frozen artifacts and replay

Source:
`experiments/workspace/root_prism_free_anchor_min.py`, SHA-256
`99b1150b33997665bc6be80696c829d7a34a3501414b59da117e4142d5c722b5`.

Records under `experiments/logs/root-prism-free/`:

- `anchor-min-certificate.json`
- `anchor-min-generation.log`
- `anchor-min-replay.log`

The certificate contains the complete local forbidden-pattern lists,
global clause-set hashes, matching census, invariance checks, and the
unit-propagation control.

```sh
python experiments/workspace/root_prism_free_anchor_min.py \
  --lex-analysis experiments/logs/root-full-caps-lex/analysis.json \
  --certificate experiments/logs/root-prism-free/anchor-min-certificate.json --replay
```

No full graph CNF has been built from this refinement. The earlier
four formulas and their ongoing outcome records remain unchanged.
