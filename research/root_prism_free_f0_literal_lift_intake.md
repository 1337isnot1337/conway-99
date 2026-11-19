# Accepted count-vector intake for the literal selector lift

The production intake is prepared. No count candidate, literal CSP search, or
optimizer was run. The one preparation finished in 1.558 seconds and returned
`PASS_PREPARATION_ONLY`.

The intake connects a future exact 18,444-integer count witness to the frozen
literal-lift checker. Its result concerns the 480 selector signatures in the
fixed F0 model. It does not construct the exterior Y edges or a 99-vertex graph.

## Required count acceptance

The input candidate is a plain JSON array of exactly 18,444 integers. Booleans,
floating-point numbers, decimal strings, and arrays of another length are
rejected. Every coordinate is checked against the final exact interval domain.

A separate arithmetic receipt must have status `EXACT_COUNT_WITNESS` and all
four Boolean fields set to true:

- `accepted`;
- `count_feasibility_claimed`;
- `full_target_checks_passed`;
- `restored_original_parent_checks_passed`.

The receipt must bind the candidate file hash and the canonical integer-vector
hash separately. Canonical hashing uses compact sorted JSON without a trailing
newline. It must also bind the exact target proto, model preparation, query
preparation, and `acceptance_source_sha256`. The intake hashes the explicitly
supplied receipt source. It does not import that checker or repeat its count
arithmetic.

The independent restored-parent acceptance checker was not implemented when
this preparation was frozen. Its source-bound accepted receipt remains an
external required premise. The count query's provisional full-target record
cannot substitute for it. An actual lift also requires the coordinator's
execution gate; this preparation authorizes no candidate query.

The frozen target bindings are:

| Item | SHA-256 |
| --- | --- |
| Final target proto | `a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153` |
| Model preparation | `a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061` |
| Final domain plan | `4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4` |
| Count-query preparation | `b8bce3bd80f42417df1fc360fc8663eb8f3f9a3c1066606c864c3ac4e24d5cb4` |

## Exact coordinate restoration

The native coordinate intervals are half-open:

| Native coordinates | Meaning |
| --- | --- |
| `[0, 15038)` | Original reduced N, Y, and Z counts |
| `[15038, 15941)` | Trivial-character product auxiliaries |
| `[15941, 16059)` | 118 signed populations |
| `[16059, 18444)` | Signed-product auxiliaries |

The frozen map from the first 15,038 coordinates to the original 15,589
coordinates restores all 9,742 Z populations. The 389 removed Z coordinates
are explicit zero targets. Y coordinates are not interpreted as selector pairs.
Auxiliary products are not interpreted as signed populations.

The existing inverse record supplies 42 local mask domains and all 861 pairs
of selector orbits. Its 19,331 refined tuples have 64,144 total preimages; a
chosen tuple has at most 12 preimages. The input retains the original literal
member order and character orientation. Independent relabeling of individual
orbits is not used.

The 358 within-orbit pair populations are enforced by the chosen local tuple.
The 9,384 cross-orbit pair populations are enforced by the full literal
histogram in each binary relation. Extra nonzero counts in an omitted or
proved-zero pair orbit fail that relation. Candidate construction needs at most
70,596 choice-pair comparisons and 4,519,476 literal histogram visits under the
saved per-orbit bounds.

## Bounded execution and acceptance

The future runner uses the previously reviewed owned-child supervisor. One
60-second deadline covers imports, input loading, relation construction,
search, trace replay, and child writes. Relation construction receives at most
15 seconds. The deterministic CSP search receives at most 30 seconds and
4,096 visited nodes, leaving a 10-second finalization reserve. There is one
search call and no automatic retry. Total raw artifact output is limited to
64 MiB, with 1 MiB reserved for the final worker record.

The complete candidate-specific relation bundle is saved before search. The
returned CSP tree, including a partial UNKNOWN tree, is saved before its exact
arithmetic replay. A late or failed child cannot certify a rejection. A hard
stop is persisted as UNKNOWN before the owned child is killed and reaped.

The outcomes have different scopes:

- `EXACT_LITERAL_SELECTOR_GRAM_LIFT` means an explicit literal selector set
  matches all 42 N counts, 9,742 Z counts, 118 signed populations, and all 172
  original selector equalities.
- `EXACT_MOMENT_LIFT_WITH_FAILED_SELECTOR_EQUALITIES` preserves a moment lift
  whose returned set fails an original selector equality. It makes no incidence
  claim and does not reject the count assignment.
- `FIXED_SELECTOR_COUNT_PROJECTION_UNREALIZABLE` requires a complete checked
  finite CSP tree. It excludes only that fixed count projection, and therefore
  that fixed native candidate, from literal selector realization.
- `UNKNOWN_LITERAL_LIFT`, a time limit, or an execution error gives no
  rejection.

A separate cold mode rebuilds the candidate relations from the frozen inverse
tables and verifies the saved deletion/branch tree and literal witness. It
does not repeat the search or enumerate local subsets. Its output is also
bounded by one owned 60-second stage.

## Preparation checks and files

Preparation reused the existing 4,096-system CSP controls and owned-supervisor
controls by hash. It did not execute them again. Three saved tiny literal
fixtures tested the new native-coordinate adapter, with sentinel values in
both auxiliary namespaces. Eleven single-field mutations of a synthetic
receipt were rejected. These fixtures are not production count candidates.

The new sources are:

- `experiments/workspace/root_prism_free_f0_literal_lift_intake.py`, SHA-256
  `cf7e34ce6705455d9adc5f09fc53034b74dda06c4603b78bedf76ccd8175138f`;
- `experiments/workspace/root_prism_free_f0_literal_lift_intake_runner.py`,
  SHA-256 `364fb825dd61a45a9315722645546ca8c20779925b13b2bbb05c58cd8f0e05b1`.

The preparation is
`experiments/logs/root-prism-free/f0-character-literal-lift-intake-preparation01/preparation.json`,
SHA-256 `298fdc6c573ec5982836ac043b598189fe384ee733a26299d4110a2befb0cd17`.
The same directory retains the immutable request, supervisor record, child
logs, worker result, and owner result. The owner result hash is
`1169ac872ecf47df119eaaa4af8ed2feb00b52bbca566e1f558b766b9a41fef7`.
