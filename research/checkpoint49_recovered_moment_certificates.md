# Recovered transcripts and finite moment certificates

Checkpoint 49 restores the remaining reviewed pre-outage evidence and publishes two completed finite-distribution tests. No result here constructs a strongly regular graph or proves its nonexistence.

## Complete F0 continuation

The [recovered continuation](root_prism_free_f0_allocated_lazy_run01_recovered.md) retains all 363 archived records and all 4,404 final selector inequalities. The older file named `f0-allocated-lazy-terminal-registry.json.gz` contains the 2,928-cut initial seed. The final 3,948 individual and 456 shared inequalities are in the archived run directory.

The original search checked 94 SAT candidates, completed 63 full row passes and one partial pass, and recorded 3,701 exact individual-row boxes and 14 exact shared-edge obstructions. It stopped at its time limit with status UNKNOWN. Every added clause has a checked necessary inequality; no visitation block is treated as a mathematical consequence.

A fresh replay reconstructs all saved candidates, formula prefixes and certificates with optimization entry points disabled. Its output is byte-identical to the original mathematical replay, SHA256 `4c437fb8ad028bc9aa55753cc0da33d557d884c75962531e991fc2743b2dde9a`. The archive, recovery audit, new replay wrapper and original sources are all preserved.

## Refined high-graph measure

The recovered refinement retained 135,534 of 157,711 decorated high graphs, with 17,920 distinct feature columns. Its saved witness gives 200 positive rational masses with common denominator 988761395399693539 and total mass 72,926,995,680.

The [portable audit](../experiments/workspace/audit_refined_query_portable.py) directly verifies all 200 original moment equations against the immutable induced counts. It also checks the 200 support graphs against the literal graph caps, 400 exact projector characteristic polynomials and 200 shifted integer-incidence inequalities. The positive witness proves feasibility of the refined finite measure model. The portable audit does not rerun the complete domain census or every exclusion certificate.

Run the arithmetic audit from the repository root with the pinned research environment:

```sh
python experiments/workspace/audit_refined_query_portable.py --root .
```

## All 33 decorated small roots

The [complete decorated models](grids-and-triangles/small_root_decorated_moments_result.md) retain both high-neighbor masks and the edges between their vertices. The complete enumeration has 1,275 states across 33 roots. At the current count point, 1,092 exact atom masses are positive and 183 are zero. Every original decorated moment, product row and stabilizer divisibility passes.

The direct verifier reconstructs incidence from the frozen states. It uses neither the query's inversion nor its extension lists. A separate root replay of that verifier passed in the restored runtime. This extends the earlier 1,115-atom presence result; it does not reject the count vector.

## Root 42 presence interval

For the six-vertex root consisting of a four-leaf star and an isolated vertex, the packing bound permits at most five high vertices. Its 253 presence atoms contain 241 known moment states and 12 fifth states in one symmetry orbit.

The [exact interval certificate](grids-and-triangles/root42_packing_moment_interval_result.md) proves that the missing fifth moment is an even integer in the closed interval [0,9794]. At zero, all 253 atom masses are nonnegative: 241 are positive and 12 are zero. All original moment equations and all root-stabilizer divisibilities pass an independent direct replay.

The fifth states require moments of order eleven, which are not fixed by the current order-ten count vector. The interval therefore expresses a completion of this finite necessary model. It is not a claim that the order-eleven or full graph system has a completion.

## Publication boundaries

The recovered F0 run remains UNKNOWN. The finite moment models remain feasible at the same immutable count point. Stronger Boolean cuts, joint selector moments, decorated root-42 fifth states, triangle-incidence projector blocks and the compressed rook computation have separate records. Their results must retain their own hypotheses and certificates.
