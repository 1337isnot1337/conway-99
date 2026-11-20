# Complementary-rook 35-core case 2 is excluded

The original exact binary incidence formula for indexed case 2 is
unsatisfiable. A retained DRAT proof has 23,913 input clauses, all belonging
to that original formula. A cold rebuild checked its complete attachment
domain, exact formula hash, retained-input inclusion, and proof.

This excludes one matching on the first local eight-set. It does not
exclude that local set, another matching case, or the complementary-rook
configuration as a whole.

## Core and necessary incidence model

The local original-signature indices are

\[
(0,1,9,10,18,20,26,27),
\]

and case 2 has local matching

\[
(0,4),\ (1,5),\ (2,6),\ (3,7).
\]

The frozen original model retains all 1,287 admissible attachment columns.
Its 114,512 Boolean variables and 233,919 clauses impose all 630 unordered
Gram equalities, at most one column per original three-point signature,
and all necessary core-triple capacities. A graph completion would supply
a solution to this model. No exterior edges or graph symmetry assumption
enter it. See `complement_rook_35core_incidence.md` for the complete
construction and domain audit.

## Discovery and independent gate

The exact downdate calculation in `complement_rook_35core_gram_downdate.md`
produced 886 additional explicit pair conflicts. Each has a full integer
negative vector for its Gram remainder. A separate reviewer rebuilt the
3,120 raw attachment candidates and recovered exactly the same 1,287
admitted columns, then checked all 886 vectors directly against the
35-by-35 integer matrix. This audit did not use the quotient or Schur
calculation that found the conflicts.

The overlay preserved the entire original clause body and appended exactly
those 886 binary clauses, producing 234,805 clauses with no new variables.
An independent byte comparison checked this claim. A fresh proof-enabled
Glucose4 query had a 60-second budget including bootstrap. It returned
UNSAT after 11.009 seconds; bootstrap took 0.329 seconds. Direct DRAT
verification and retained-input extraction completed successfully. Total
solve and direct-check time was 15.308 seconds, with peak reported RSS
95,608 KiB.

The earlier original-formula query had only a 10-second budget. These runs
do not isolate a runtime benefit from the extra clauses.

## Original-only proof

The retained proof uses none of the 886 added clauses. The separate
`complement_rook_35core_case0002_original_certificate.py` verifier imports
the original model builder only. It does not import the downdate or
overlay modules and does not require their certificates. It performs:

1. A cold rebuild of the complete original case 2 domain and CNF.
2. An exact comparison with the original recorded CNF hash.
3. Inclusion checks for every retained input clause in that original CNF.
4. An independent DRAT replay of the retained formula and proof.

All checks passed. Thus the exclusion does not require any spectral or
downdate premise. The downdate certificate remains a separately verified
collection of consequences of the same Gram equations.

The principal bindings are:

| Artifact | SHA-256 |
|---|---|
| Original case 2 CNF | `1f6089828e644e52b2aaebb0d082ec6e9410a6101b26cae9300894f74a8bc80e` |
| Discovery overlay CNF | `f23dba5ab0cbb266dad36d99d4f7b8e226b2ee1e6bbe181b025612b9845b8db3` |
| Retained CNF | `a8c4127d12996380d0ccfe54d9ceacdba0331897a8cc99e48cb636dfcdcd2ec2` |
| Retained DRAT proof | `e852639b89d5768a28625176c7107c46f114b36c9d3417042f11966d78978f06` |

## Coverage and replay

Combining this result with the immutable first-local sweep, the excluded
matching indices are now

\[
\{0,1,2,3,8,21\}.
\]

The other 22 matching cases remain unresolved:

\[
\{4,5,6,7,9,10,11,12,13,14,15,16,17,18,19,20,22,23,24,25,26,27\}.
\]

The original sweep files retain their original results, including its
case 2 UNKNOWN. This separate package records the later certified
exclusion. No additional matching query was run in this package.

To replay the exclusion with only the original formula as a premise,
choose a new output path inside the repository:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0002_original_certificate.py \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0002-original-only-independent-replay.json \
  --checker-seconds 60
```

The full discovery-overlay replay is also available:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_gram_downdate_overlay.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0002-gram-downdate-overlay-model.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0002-gram-downdate-overlay-run01/result.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0002-overlay-independent-replay.json \
  --checker-seconds 60
```

Both replays accept `--drat-trim` to select the checker executable. Full
CNFs are regenerated. The retained CNF and retained proof are published;
the larger raw discovery proof is bound by its hash and need not be
archived or present during replay.
