# Deterministic selector-population products

## Prepared model

This preparation adds 903 exact population identities to the complete F0 integer orbit-count model. All 42 selector populations remain free. The model retains the parent 27,719 linear rows, all 92 held PSD directions, and the 25 separately certified selector integer refinements.

The native CP-SAT input has 15,941 integer variables: 15,038 original count coordinates and 903 product auxiliaries. It has 28,647 linear constraints, containing 1,279,413 nonzero terms, and 903 product constraints. No solver was called. The native validator and direct serialized-proto checks passed.

This remains a necessary count model for component zero in the globally prism-free, F-free split 18+18 case. It does not construct an incidence or graph. The other component and its alignment are unspecified.

## The additional identities

Let \(O_i\) be a selector orbit and let \(N_i\) count its selected members in one incidence. Every member of the 12-element relabeling group preserves \(O_i\) as a set, so \(N_i\) is constant under this averaging. Let \(P_q\) count selected unordered pairs in a pair orbit \(q\).

For two different selector orbits,

\[
\sum_{q\subseteq O_i\times O_j}P_q=N_iN_j.
\]

Within one selector orbit,

\[
\sum_{q\subseteq\binom{O_i}{2}}P_q=\frac{N_i(N_i-1)}2.
\]

The sums count literal selected pairs in disjoint partitions of the complete pair domain. The 389 proved-zero pair orbits contribute zero. There are \(\binom{42}{2}=861\) cross blocks and 42 diagonal blocks. Each of the 9,353 retained pair-count variables occurs in exactly one block. Each block has between four and twelve retained coordinates.

These identities concern one incidence and its relabelings. They do not hold for every arbitrary mixture of unrelated incidences with different orbit populations. Integer average counts alone do not imply the identities, and no graph automorphism is assumed.

## Native representation and exact bounds

For every \(i\leq j\), introduce an integer variable

\[
T_{ij}=N_iN_j,\qquad 0\leq T_{ij}\leq |O_i||O_j|.
\]

The native product constraint includes the repeated-factor case \(T_{ii}=N_i^2\). Its linear link is

\[
\sum P_q-T_{ij}=0\quad(i<j),\qquad
2\sum P_q-T_{ii}+N_i=0\quad(i=j).
\]

Using the square avoids a negative affine factor at \(N_i=0\). Every product upper bound is 36, 72, or 144. The original count domains remain exactly their actual orbit-size bounds; no population, candidate, branch, or hint is fixed.

The 25 refinement rows are transferred from the old 15,200 coordinates by the same exact substitution used in the integer lift. For an orbit of size \(s_j\), substitute its original averaged coordinate by \(N_j/s_j\), multiply the complete row by 12, and divide by a positive common divisor. Each term and right side is checked by integer cross multiplication. The 25 rows add 189,283 terms. The 903 links add 10,298 terms.

All native linear coefficients, finite row endpoints, variable domains, and products are checked before accepting the proto. The largest absolute linear box sum remains 16,410,372,831,576, or 44 bits. Product values are at most 144. These values fit signed 64-bit arithmetic with substantial margin. The native validator also accepts the complete input.

No floating-point conversion is used to create the constraints. For a linear inequality, its native lower endpoint is the exact minimum over the count-variable box; this extra finite lower endpoint is redundant. The upper endpoint is the original exact right side.

## Controls and serialized-input checks

The mathematical preparation independently reconstructs all 9,742 pair orbits from the 12 actions and checks their complete member-list hash. Six arbitrary Boolean selections then check all 903 literal block identities, for 5,418 checks. These controls use the full pair domain, including pairs proved zero only in the graph model; they do not assert whole-model feasibility.

The native controls serialize cross-product and repeated-factor examples, parse them through the ordinary protobuf reader, and evaluate 3,200 assignments directly. No control solver is used.

The actual production proto is also serialized and read through the ordinary protobuf reader. The checker verifies all 15,941 variable domains, every coefficient and endpoint in the 28,647 linear constraints, and all 903 product targets and factors. It verifies that no objective, hint, assumption, enforced constraint, or search strategy was added. A separate cold invocation repeats that literal input check without reconstructing the native model or rerunning controls.

The binary proto is 11,588,655 bytes. Its SHA256 is `aa43ef31991213634b0cc812b61a5d1247c1915c6690def64a54247854ee8589`. The publication stores a deterministic gzip archive with an explicit restoration binding. The restore helper checks both archive and raw hashes before making the original file available.

The native preparation took 7.19 seconds and cold input replay took 7.61 seconds. The mathematical preparation recorded 121.34 seconds overall under a cooperative 120-second check schedule; validation reached its final deadline check before serialization. The serialization and report step account for the recorded overrun. This was static preparation, not a search.

The first invocation had already written the complete specification when a relative output-path conversion failed. Its source, log, and partial artifact are preserved. The corrected invocation uses an absolute output prefix with the same source. Both specification artifacts have identical bytes and SHA256; no mathematical or encoding change was made.

## Comparison with a direct CNF

The 15,038 count variables require 59,655 ordinary binary bits under their raw orbit-size bounds. The product targets would require another 7,052 bits. These counts are small enough by themselves, but the weighted linear rows dominate a straightforward arithmetic translation.

An explicit bucket-and-carry estimate for all 28,647 linear rows gives 28,497,610 initial weighted bit occurrences. A generic full Tseitin adder construction uses at most 56,760,992 adder auxiliaries and 396,840,290 adder clauses, with another 1,493,088 clauses in the stated comparison bound. Product circuits and count-domain clauses are additional. This is an estimate for that concrete generic construction, not a lower bound on all possible CNF encodings.

A direct roughly 398-million-clause construction is unsuitable for the present workspace. CP-SAT preserves the bounded linear and product relations directly and is the more practical first route for seeking a count witness. An infeasible CP-SAT status would remain unproved without a separate checkable certificate.

A later proof-oriented alternative is a smaller bit-vector formula with exact product circuits and a lazy set of necessary linear-row explanations. Each added clause would need an exact worst-case bound over its falsifying bit assignments. A final UNSAT claim would still require a fresh bound formula, retained-input checks, and an independently verified proof. No such CNF or query is created here.

## Separate selector-profile tables

The coordinator's next overlay enumerates every subset of each actual selector orbit. It rejects a subset only for a proved-zero pair or an original nonnegative Gram capacity violation, then records its exact population and within-orbit pair-count tuple.

The independent audit in this package rederives all 171 Gram quotas from the literal 21-core, reconstructs all pair orbits from the group actions, and independently enumerates the 155,904 subsets in combination order. It reproduces all 64,144 accepted subsets and all 5,733 distinct tuple multiplicities, and checks each stored representative. The 42 tables cover the 42 populations and 320 within-orbit pair-count coordinates. This audit calls no solver and imports no subject builder.

Those tables are not part of this immutable product parent. A separate overlay will append them as exact allowed-assignment constraints without changing the existing variable or constraint prefix. The coordinator's sign-character work is also outside this model.

## Acceptance and future runtime scope

The exact count inspector checks every inherited count row, all 25 refinement rows, all 903 deterministic identities, and every count bound. It then inserts the proved zeros, lifts to the original 15,200 averaged coordinates using a common denominator of 12, and checks all 28,043 parent rows and their bounds again.

A point passing those checks would be an exact count/moment witness only. It would not establish a compatible 480-selector incidence, an exterior graph, or an SRG. A later single owned 180-second CP-SAT query, using one worker and a fixed seed, requires a separately frozen table overlay, runner, and execution gate. No production query is included in this preparation.

## Files

- Mathematical source: `experiments/workspace/root_prism_free_f0_population_products.py`.
- Native preparation and cold reader: `experiments/workspace/root_prism_free_f0_population_products_cpsat.py`.
- Archive helper: `experiments/workspace/root_prism_free_f0_population_products_archive.py`.
- Specification and mathematical report: `experiments/logs/root-prism-free/f0-population-products02-*`.
- Native proto archive and report: `experiments/logs/root-prism-free/f0-population-products-cpsat01/`.
- Independent profile audit: `experiments/workspace/root_prism_free_f0_selector_profiles_independent_audit.py` and its report under `experiments/logs/root-prism-free/`.
