# Exact orbit populations for the F0 component model

## Scope and outcome

This package rewrites the complete frozen F0 selector, edge, and second-moment relaxation in bounded integer orbit counts. It applies to component zero in the split 18+18 shell case, with global prism and F exclusion, under the same necessary conditions as the parent model. It does not cover the connected 36-vertex shell case or other component types.

The lift has 15,038 bounded integer variables, 5,973 equalities, 21,746 inequalities, and 1,079,832 nonzero terms. It preserves all 92 held PSD directions. The equalities are consistent modulo both 2 and 3. Their exact ranks are 5,117 and 5,138, respectively. No bounded integer feasibility search was run, and these modular results do not establish a feasible count vector or exclude a graph.

The preparation is `f0-orbit-populations02-preparation.json`; the standalone check is `f0-orbit-populations02-independent-replay.json`. Both are under `experiments/logs/root-prism-free/`. The standalone checker imports neither the model builder nor the modular helper.

## Why the numerators are integers

Let the verified group of 12 core relabelings act on the 480 admissible selector signatures, eligible exterior edges, and unordered pairs of distinct signatures. Fix a hypothetical graph and its binary selector, edge, and selected-pair indicators. If an object orbit has size \(s\), each member occurs exactly \(12/s\) times among the 12 relabelings of a fixed representative.

Consequently, the group average of an indicator in that orbit is

\[
v_O=\frac{N_O}{s},\qquad 0\leq N_O\leq s,\quad N_O\in\mathbb Z.
\]

For selectors, \(N_O\) counts selected signatures in the orbit. For edges, it counts present eligible edges. For pair moments, it counts unordered pairs whose two selectors are selected. The argument uses relabelings of the same incidence and graph. It makes no assumption that a relabeling is an automorphism of the completed graph.

This is a necessary integrality condition on an average of one graph over the specified group. An arbitrary convex combination of unrelated graphs need not have these denominators. The earlier real relaxation allowed such convex combinations and did not impose these integer numerators.

## Complete domains and zero substitutions

The domain certificate reconstructs all 12 actions, their group compositions, orbit partitions, stabilizer multiplicities, and Burnside counts. It also checks every column map through both earlier reductions.

| Family | Size 3 orbits | Size 6 orbits | Size 12 orbits | Total orbits | Literal objects |
| --- | ---: | ---: | ---: | ---: | ---: |
| All selectors | 0 | 4 | 38 | 42 | 480 |
| All eligible edges | 10 | 196 | 5,599 | 5,805 | 68,394 |
| All distinct selector pairs | 12 | 306 | 9,424 | 9,742 | 114,960 |
| Retained edges | 10 | 186 | 5,447 | 5,643 | 66,510 |
| Retained selector pairs | 12 | 263 | 9,078 | 9,353 | 110,550 |

The first reduction removed 389 certified-zero pair orbits: 43 of size 6 and 346 of size 12. They account for 4,410 literal pairs. The second removed 162 certified-zero edge orbits: 10 of size 6 and 152 of size 12, accounting for 1,884 literal edges. Neither reduction removes a selector coordinate.

Thus the successive dimensions are

\[
42+5805+9742=15589,\qquad
42+5805+9353=15200,\qquad
42+5643+9353=15038.
\]

The final variables comprise 22 orbits of size 3, 453 of size 6, and 14,563 of size 12. Every removed coordinate is inserted as zero when interpreting the original model.

## Exact row transformation

For each retained parent equality or inequality,

\[
\sum_j c_jv_j\;\square\;b,
\]

substitute \(v_j=N_j/s_j\), where \(s_j\in\{3,6,12\}\). Clearing the common denominator gives

\[
\sum_j c_j\frac{12}{s_j}N_j\;\square\;12b.
\]

The builder then divides every coefficient and the right side by their positive common divisor. Positive division preserves inequality orientation. Together with \(0\leq N_j\leq s_j\), this is an exact change of variables over the reals; requiring integer \(N_j\) adds the necessary orbit-count condition.

The 27,719 row divisors are 1 for 27,081 rows, 2 for 614 rows, and 4 for 24 rows. All 5,973 equality coefficient gcds are 1 after this normalization, so no individual equality gives an immediate divisibility contradiction. The largest coefficient uses 31 bits. The largest absolute row box sum or right-side magnitude is 16,410,372,831,576, which uses 44 bits.

The domain and model retain the complete provenance of all 92 PSD directions. No old cut is discarded because it has large coefficients or is numerically inconvenient. Earlier numerical scales are retained as provenance only; this package defines an exact integer model and does not prepare a numerical transport.

The standalone checker verifies every transformed term by integer cross multiplication,

\[
c'_j\,g\,s_j=12c_j,
\]

and checks the corresponding right side. It also independently clears denominators in all 6,135 equalities of the unreduced 15,200-coordinate parent, using row-specific least common multiples. The zero insertion and prior row-removal witnesses link the retained equalities to that parent.

## Controls and finite-field checks

The modular helper was checked on all 793 two-equation, two-variable systems over the fields with 2 and 3 elements, using 6,817 explicit point checks. Its ternary bit-plane addition has nine scalar truth controls.

A previously checked 60-signature incidence supplies a separate positive control for selector Gram rows, population, lifted selector rows, and integer orbit averaging. It checks 18 Gram equalities, one population equality, and 5,287 selector RLT equalities. This old incidence is not asserted to satisfy mixed-edge equations, the 4,416 selector cuts, or the 92 PSD rows. Its hypothetical edge coordinates are zero for this restricted control only. No design is fixed in the new model.

The complete 5,973-row equality system was then reduced modulo 2 and modulo 3:

| Field | Status | Exact rank | Complete point supplied |
| --- | --- | ---: | --- |
| \(\mathbb F_2\) | Consistent | 5,117 | Yes |
| \(\mathbb F_3\) | Consistent | 5,138 | Yes |

Each rank certificate gives its echelon rows and explicit combinations of original rows. The independent replay reconstructs those combinations with ordinary sparse integer arithmetic, checks pivot independence, verifies that every original row lies in their span, and checks the complete modular point. It does not import the production bit-plane implementation.

Preparation took 49.72 seconds under the declared cooperative 120-second limit. Independent full replay took 28.56 seconds. No optimizer or eigendecomposition was called. Consistency in these two finite fields does not imply consistency over the integers, compatibility with the variable bounds, or satisfaction of any inequality.

## Preserved failed preparation

The first builder expected the archived `fixed_zero_original_variables` field to contain bare variable identifiers. The archive contains pairs of a variable identifier and its original equality identifier. The first attempt stopped at that schema assertion, before production modular elimination.

The original source and failed log remain frozen. The separate v2 builder extracts the same 389 variable identifiers and directly verifies each archived singleton-zero equality. Only the `domains` function changed; the repair record contains the exact text and AST delta. No accepted arithmetic result depends on the failed attempt.

## Further deterministic identities are separate

For selector orbits \(O_i\), write \(N_i\) for their selected populations and \(P_q\) for pair-orbit counts. A single incidence also satisfies

\[
\sum_{q\subseteq O_i\times O_j}P_q=N_iN_j\quad(i<j),\qquad
\sum_{q\subseteq\binom{O_i}{2}}P_q=\binom{N_i}{2}.
\]

There are 861 cross-orbit and 42 within-orbit identities. The domain artifact already labels every pair orbit by its selector-orbit block. These 903 nonlinear identities are not imposed by the frozen linear lift. They require a separate formulation and acceptance check. In particular, integer mean counts alone do not enforce deterministic population products.

## Frozen entry points

- Builder: `experiments/workspace/root_prism_free_f0_orbit_population_lift_v2.py`.
- Modular helper: `experiments/workspace/root_prism_free_f0_orbit_population_modular.py`.
- Standalone checker: `experiments/workspace/root_prism_free_f0_orbit_population_replay.py`.
- Domain, model, and arithmetic certificates: `experiments/logs/root-prism-free/f0-orbit-populations02-{domains,model,arithmetic}.json.gz`.
- Preparation, independent replay, and peer source review are included in the publication manifest.

The manifest binds raw file hashes and Git blob identities. Compressed certificate hashes refer to the compressed bytes; their canonical JSON hashes are recorded separately in the preparation.
