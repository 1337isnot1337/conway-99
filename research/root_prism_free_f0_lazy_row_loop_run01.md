# First lazy incidence and row-separation run

The single authorized run stopped at its twenty-row-pass limit after
35.807 seconds. It did not reach the time or formula-size limits.
Component zero remains unresolved.

This is the same conditional scope as the preparation: all 480 first
incidence selectors are free in component zero of the globally
prism-free, F-free split $18+18$ shell. The second component and its
incidence remain unrestricted.

## Outcome

The run produced 25 SAT primary selections. Four violated already
registered inequalities and received checked clause explanations
without any row LP. Twenty received complete sixty-row passes.
The final selection passed all 1,116 registered inequalities, but the
runner did not test its rows because twenty passes had been used.

| Exact result | Count |
|---|---:|
| SAT selections checked against the actual prefix | 25 |
| Registry-only clause refinements | 4 |
| Complete sixty-row passes | 20 |
| Integer individual-row obstructions | 29 |
| Rational individual-row boxes | 1,171 |
| Exact symmetric shared-edge rays | 3 |
| Exact symmetric shared-edge points | 0 |
| New individual cuts, including twelve transports | 348 |
| New signed cuts, including twelve transports | 36 |
| Final individual-cut registry | 1,008 |
| Final signed-cut registry | 108 |
| Final total registered inequalities | 1,116 |

There was no incremental UNSAT answer. The fresh proof driver and
DRAT checker were therefore not invoked.

## Formula size and exact shared rays

The formula grew from 58,206 to 58,974 clauses. It retained 28,308
variables throughout. No auxiliary variable was added. The final
formula has 319,248 literal occurrences and 1,980 primary explanation
clauses, including the 1,212 prepared seed clauses.

The final DIMACS SHA256 is
`570f9e85c7eaa724d71a77b9654f7aad2c9052825fde876aaf20a87f484e24bc`.
Peak process RSS was 155,688 KiB. These observations concern this
bounded run; they do not establish a general search bound.

The three shared-edge obstructions occurred at zero-based iterations
7, 9, and 12. Every ray was checked by direct integer arithmetic.

| Iteration | Exact ray RHS | Nonzero multipliers | Maximum absolute multiplier |
|---|---:|---:|---:|
| 7 | -1 | 31 | 8 |
| 9 | -139 | 927 | 6,338 |
| 12 | -1 | 28 | 9 |

Each ray has nonnegative coefficients on all nonnegative primary and
upper-slack variables, and its right side is strictly negative.
The full-domain endpoint allocation then gives a universal signed
selector inequality. All twelve verified core transports are retained.
No fixed-incidence conclusion was substituted for that lifting proof.

## Prefix and witness replay

The cold replay passed. It reconstructed the original incidence base,
all 732 inherited proved inequalities, and the prepared explanations.
It then reproduced every later registry update and explanation batch.
Every accepted explanation was checked against an exact independent
or population60 minimum.

The replay checks all 25 candidate prefixes, all 29 integer row
obstructions, all 1,171 rational row boxes, all three exact shared rays
and their full-domain lifts. It reproduces the final registry and CNF
hash. It invokes neither an optimizer nor a solver.

The terminal candidate is still an incidence candidate. Passing the
registered inequalities does not construct the exterior graph or prove
that every individual or shared neighbor row is feasible. The saved
terminal record expressly leaves its row pass unperformed.

## Durable transcript

The 79 hash-bound JSON or gzipped-JSON records are stored in a
deterministic lossless archive. Their original bytes total 8,504,598;
the archive is 1,254,718 bytes. It includes candidates, row witnesses,
shared rays and lifts, clause batches, all final registries, and the
terminal result. The rebuildable final DIMACS is omitted.

`root_prism_free_f0_lazy_transcript_bundle.py` checks every member hash,
the raw result hash, archive metadata, and the exact fixed path prefix.
Its restore operation writes only missing records. It refuses to
overwrite a different existing file. Missing-file, equal-file and
mismatch-refusal controls run in a disposable directory.

The bundle's optional cold-replay mode restores the records and calls
the frozen mathematical/CNF replay.

| Artifact | SHA256 prefix |
|---|---|
| Terminal result | `93037f2b7c0055aa` |
| Cold exact replay | `7cdfde151e90d154` |
| Transcript archive | `311222d9a71fce71` |
| Transcript bundle manifest | `0a61ba67d02d8e58` |

The preparation sources, their controls, the exact proof registry, and
the original run outcome remain unchanged. Any continuation must use
a separately reviewed preparation and preserve the scope of this
unresolved result.
