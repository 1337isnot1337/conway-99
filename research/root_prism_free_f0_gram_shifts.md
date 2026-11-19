# Exact Gram shifts of a shared-row cut

## Result

An exact combination of existing Gram equalities reduces one large shared-row cut.
Its full encoding decreases from 43,735 clauses to 26,583 clauses.
Its independent Boolean explanation decreases from 446 literals to 244 literals.
The exact violation remains 26 in all twelve core transports.

This pilot changes no existing formula and excludes no additional component.
The original inequality comes from the [separate shared-ray repair](root_prism_free_f0_shared_ray_repair.md).
The [clause explanation note](root_prism_free_f0_clause_explanations.md) gives the two explanation rules.

## Exact identity

Let the original necessary inequality be

\[
a^Tz\le b.
\]

Let the existing Gram equalities be \(Ez=q\).
For any integer vector \(\lambda\), define

\[
a'=a+E^T\lambda,\qquad b'=b+\lambda^Tq.
\]

Then \(a'^Tz-b'=a^Tz-b\) whenever \(Ez=q\).
Thus the shifted inequality is equivalent on the original incidence model.
The saved incidence only supplies the initial violated cut and an exact control.
The shifted inequality does not assume that incidence.

The generator reconstructs all 171 Gram positions from the complete 480-signature domain.
It checks each support size and quota.
Deduplication leaves 150 nonempty equalities.
The saved shift uses 148 nonzero integer multipliers.

The twelve core actions permute the signatures and Gram positions.
The generator checks every transported coefficient and every transported equality support.
These actions relabel necessary constraints. They impose no symmetry on an unknown graph.

## Coefficient reduction

The heuristic changes one equality multiplier at a time.
Each accepted change strictly decreases a three-part lexicographic objective.
The objective contains the coefficient L1 norm, total coefficient bit count, and largest absolute coefficient.
The heuristic considers the two integer medians of each affected coefficient list.

The run records 593 changes and reaches a fixed point at pass index 16.
This is a coordinate fixed point. It is not a proof of a global minimum.
The exact coefficient identity determines validity independently of the heuristic.

| Quantity | Original cut | Shifted cut |
|---|---:|---:|
| Coefficient L1 norm | 805,330 | 229,498 |
| Total coefficient bit count | 2,743 | 1,670 |
| Largest absolute coefficient | 8,493 | 7,437 |
| Auxiliary variables in full encoding | 5,488 | 3,342 |
| Clauses in full encoding | 43,735 | 26,583 |
| Literal occurrences in full encoding | 174,769 | 106,177 |
| Independent explanation width | 446 | 244 |
| Population explanation width | 60 | 60 |
| Exact violation | 26 | 26 |

The shifted right-hand side is 101,266.
Its value at the source incidence is 101,292.
The encoder uses the signed threshold \(\sum_{a_i'>0}a_i'-b'\).
The original zero-right-hand-side specialization is insufficient here.

The population explanations still fix all sixty selected variables.
Their shorter literal lists do not establish stronger propagation than the independent explanations.

## Checks and artifacts

The [generator](../experiments/workspace/root_prism_free_f0_gram_shift_pilot.py) records every integer shift and every transported explanation.
The [certificate](../experiments/logs/root-prism-free/f0-gram-shift-pilot.json) binds the original sources and inputs.
Its SHA256 is `580442e8c3404a15685270fd139d565ae1924ac37edd8cad0d8975cfb23554ba`.
The [cold replay](../experiments/logs/root-prism-free/f0-gram-shift-pilot-replay.json) reproduces the complete certificate without a solver or optimizer.
An [independent arithmetic audit](../experiments/logs/root-prism-free/f0-gram-shift-pilot-independent-audit.json) reconstructs the original Gram positions and all integer updates.
It checks every coefficient, right-hand side, transport, and clause bound.
It also reproduces the two standalone encodings with the previously audited encoder.
It imports no subject generator and rebuilds no ancestor formula.

From the repository root, run the following command for a new replay output.

```bash
.venv/bin/python experiments/workspace/root_prism_free_f0_gram_shift_pilot.py \
  --replay experiments/logs/root-prism-free/f0-gram-shift-pilot.json \
  --output /tmp/conway99-gram-shift-replay.json
```

The model scope remains component zero of the globally prism-free, `x521=0`, split `18+18` case.
All original Gram equalities remain premises of the shifted cuts.
