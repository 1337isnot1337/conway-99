# Eight checked incidence-pattern exclusions

The baseline incidence-master pilot tested eight complete 72-column
designs. All eight conditional edge models were UNSAT. Every resulting
signed selector pattern has a fresh explicit-unit proof, and every
retained proof passed an independent full-formula rebuild and replay.

The pilot stopped at its authorized eight-design limit. It did not
exhaust the incidence class. There was no partial SAT point, UNKNOWN,
visitation block, or complete graph candidate.

## Unchanged baseline

The master has 1,332 variables and 2,520 clauses, encoding the 180 exact
Gram margins over all 252 signatures. Each extracted design was checked
against all 729 entries of the core Gram matrix.

The conditional oracle is the previously audited formula with
1,156,482 variables and 2,575,728 clauses. It keeps all 20,934 eligible
exterior edges. Each call fixes all 252 selectors by signed assumptions.
No extra `a` bound, Schur clause, graph symmetry restriction, or exterior
cap was added. In particular, this remains a necessary model without
the complete exterior cap system.

The oracle was reused without proof logging. After each UNSAT result,
the signed assumption core was copied into a fresh CNF as explicit
units. A separate proof-enabled solve and DRAT check certified that
formula before its negated selector clause entered the master.

All eight designs have `a>2`. None revisits a design class already
excluded by the earlier `a<=2` results.

## Terminal outcomes

The core columns count signed assumptions. A negative assumption
requires that signature to be absent; it cannot be discarded or
converted to a positive requirement.

| Design | a | Oracle seconds | Core literals | Positive | Negative | Retained input clauses | Retained proof lines |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 11 | 0.128 | 40 | 14 | 26 | 2,616 | 1,554 |
| 1 | 14 | 0.035 | 35 | 15 | 20 | 3,429 | 3,247 |
| 2 | 12 | 0.095 | 29 | 14 | 15 | 2,153 | 2,132 |
| 3 | 17 | 0.192 | 42 | 10 | 32 | 1,938 | 1,685 |
| 4 | 17 | 0.134 | 41 | 11 | 30 | 989 | 518 |
| 5 | 17 | 0.151 | 42 | 14 | 28 | 1,996 | 1,962 |
| 6 | 19 | 0.236 | 41 | 13 | 28 | 4,913 | 5,099 |
| 7 | 18 | 0.148 | 39 | 12 | 27 | 2,028 | 1,917 |

The fresh proof stages took 4.639–8.480 seconds each, including CNF
materialization, parsing, and bootstrap before the solver returned.
The complete pilot, including proof extraction and direct proof checks,
took 146.995 seconds. Its peak process memory was 1,082.6 MiB.

These observations support a specific implementation conclusion:
conditional queries for these complete incidence designs were much
faster than the earlier unresolved whole-core branches. They do not
establish a general runtime bound or a complete incidence census.

## Full replay

All eight certificates then underwent separate full replays. Each replay:

1. Rebuilt the frozen 252-selector, 20,934-edge baseline from its bound
   mathematical source and domain export.
2. Matched the complete baseline CNF hash and source/domain bindings.
3. Appended the exact signed core units and matched that CNF's hash.
4. Checked that every retained input clause belongs to the rebuilt
   unit-augmented formula.
5. Verified the retained DRAT proof independently.

Every replay passed. The eight sequential replays took 149.898 seconds.
The generation certificates remain immutable and retain their original
`full_base_rebuild_replay_pending` field. Their later completed status is
recorded in the separate full-replay report and per-case replay logs.

The raw DRAT files are about 40 MB per case. Their paths and SHA-256
bindings are preserved, while the compact retained CNFs and proofs are
the canonical published certificates. A replay does not require the
raw proof or the cached full unit-augmented CNF.

## What the cuts assert

For each saved signed core `C`, every completion must satisfy

\[
\bigvee_{\ell\in C}\neg\ell.
\]

The core fixes 29–42 selector values. The proof therefore establishes
a forbidden signed pattern, rather than merely a failure of the exact
252-bit design used to discover it. The certificate makes no numerical
claim about how many other incidence designs that pattern excludes.

Three retained proofs do not use all original assumption units. Cases
3, 4, and 5 use respectively 40, 39, and 40 units, rather than 42, 41,
and 42. The two omitted units in each case are negative. Since those
units do not occur among the retained input clauses, the same retained
proof remains contained in the base plus the smaller unit set. This
gives a separate static refinement. It was not inserted retroactively
into the pilot.

The eight results do not yield a new global lower bound on `a`. They
also do not exclude the complementary-rook core. The original `a>=3`
bound remains unchanged. Closure of the signed cuts under verified
core relabelings is a separate follow-up analysis.

## Artifacts and replay command

The immutable artifact manifest is

`experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-artifacts.json`.

The terminal records are:

- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.json`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.log`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-full-replay.json`

The directory
`experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01/`
contains, for each design index 0 through 7:

- `design-i-core-certificate.json`
- `design-i-core-retained.cnf`
- `design-i-core-retained.drat`
- `design-i-core-drat.log`
- `design-i-full-replay.log`
- `design-i-retained-drat-replay.log`

For example, replay design zero with:

```sh
python experiments/workspace/complement_rook_incidence_master_certificate.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01/design-0-core-certificate.json \
  --drat-trim /tmp/conway99-drat-trim/drat-trim \
  --log /tmp/complement-rook-master-design0-independent-drat.log
```

Use indices 0 through 7 to replay the other cuts. The runner, proof
wrapper, master manifest, small controls, and independent model review
remain frozen from the preparation checkpoint.
