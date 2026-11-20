# Rows used by the eight retained joint proofs

The original eight retained proofs use several source rows each. They are
not retained proofs of infeasibility of just one exterior vertex's neighbor
row. Two proofs nevertheless fit in a subsystem indexed by one core point.
This suggests a smaller conditional oracle without changing the signature
domain or imposing graph symmetry.

The exact audit regenerates all 2,575,728 baseline clauses as a stream and
matches the baseline CNF hash. It records every possible equation origin of
each retained input clause. Cardinality-counter variables have disjoint
ownership intervals, so a retained counter variable identifies its equation
even if a primary-only clause has more than one possible origin.

| Case | Mixed equations used | Packing clauses used | Sources with retained mixed counters | All local source centers | Primary edges used by multiple source rows |
|---:|---:|---:|---:|---:|---:|
| 0 | 97 | 31 | 18 | 28 | 72 |
| 1 | 124 | 40 | 20 | 28 | 70 |
| 2 | 71 | 26 | 14 | 24 | 48 |
| 3 | 67 | 28 | 9 | 22 | 47 |
| 4 | 25 | 8 | 3 | 5 | 6 |
| 5 | 58 | 12 | 8 | 10 | 17 |
| 6 | 187 | 67 | 39 | 50 | 169 |
| 7 | 57 | 40 | 7 | 26 | 53 |

None of these retained inputs uses a degree counter or population counter.
They do use the shared Gram equations and endpoint activation clauses. These
facts describe the saved proofs, not every possible proof of the same cuts.

## A subsystem indexed by core points

For core coordinates \(I\), let \(S_I\) be the candidate signatures that
contain at least one point of \(I\). Keep all 252 selectors and the complete
Gram equations. Keep every eligible exterior edge with an endpoint in
\(S_I\), all mixed and degree rows for sources in \(S_I\), and the mixed
rows targeting \(I\) for every other source. Such an outside row uses only
edges to \(S_I\), so it is expressible in the retained edge domain. Also keep
the endpoint activations and every packing clause on retained edges.

Every full completion satisfies this subsystem. Satisfying the subsystem
does not establish extendibility to the full model.

To contain a retained mixed row with source signature \(h_s\) and target
\(i\), the set \(I\) must meet \(h_s\cup\{i\}\). To contain a used edge
\(st\), it must meet \(h_s\cup h_t\). The audit solves this finite hitting
problem exactly for its recorded row attribution.

| Case | Smallest recorded core-point set | Candidate signatures touching the set | Eligible edges incident to those candidates |
|---:|---|---:|---:|
| 0 | \(R_2,S_3,T_0,T_1\) | 92 | 12,335 |
| 1 | \(R_0,R_4,T_1,T_2\) | 97 | 12,773 |
| 2 | \(R_2,S_3\) | 49 | 7,477 |
| 3 | \(S_2,S_4,T_1\) | 76 | 10,592 |
| 4 | \(R_8\) | 28 | 4,456 |
| 5 | \(R_3\) | 28 | 4,456 |
| 6 | \(R_0,R_2,R_3,R_6,R_8,S_4\) | 140 | 17,120 |
| 7 | \(R_6,S_4\) | 49 | 7,477 |

For a single core point, exactly eight of the 28 candidates containing it
must be selected. The proposed subsystem has 1,008 raw mixed/degree rows
before identical-row deduplication. Its smaller candidate-edge domain gives
a concrete alternative to repeatedly loading the full joint formula.

The word "smallest" refers to the hitting problem for these retained input
origins. The audit does not prove that a smaller subsystem could not yield a
different proof. No new model was solved by this audit.

## Reproduction

Source:
`experiments/workspace/complement_rook_incidence_master_core_inspection.py`.
Certificate:
`experiments/logs/grids-and-triangles/complement-rook-incidence-master-core-inspection.json`.

```sh
.venv/bin/python experiments/workspace/complement_rook_incidence_master_core_inspection.py \
  --pilot experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.json \
  --replay experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-full-replay.json \
  --output /tmp/conway-retained-row-support.json
```

The rebuilt JSON should equal the saved certificate exactly. The source
uses no solver and writes no large baseline CNF.
