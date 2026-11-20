# Signed-character count model: native preparation

This package prepares one CP-SAT model for the existing conditional F0 stratum: a globally prism-free, F-free SRG with a split 18+18 shell and component zero. It imposes necessary integer count and moment conditions. A solution would be a count witness. It would still need a compatible 480-selector incidence and exterior graph.

The preparation makes no solver call. The immutable product parent and its basic profile-table overlay remain unqueried intermediates. The signed-character model is the prepared input for the first bounded native count query.

## Retained parent

The parent has 15,038 integer orbit counts. For a selector orbit of size s, its averaged selector coordinate is N/s, where N counts selected literal signatures in that orbit. The edge and pair coordinates use their respective actual orbit sizes. This is averaging under relabelings of the fixed core; it assumes no automorphism of a hypothetical completed graph.

All 27,719 integer linear parent rows remain. They include all 92 retained PSD directions. The 25 later selector integer refinements also remain. For each of the 903 unordered pairs of the 42 selector orbits, the product parent imposes the deterministic identity

\[
\sum_{a\in O_i,b\in O_j} z_a z_b=N_iN_j\quad(i\ne j),
\qquad
2\sum_{a<b\in O_i}z_a z_b=N_i^2-N_i.
\]

The associated 903 product auxiliaries are exact integer products. The basic profile overlay then adds 42 allowed-assignment tables, with 5,733 tuples in total. These tables come from complete enumeration of all subsets of each actual selector orbit, subject only to proved zero pairs and original Gram capacities.

## Signed-character extension

The 12-element core relabeling group has three nontrivial sign characters. Their compatible selector-orbit signings define 118 signed populations. If w is a signing for a character chi, then

\[
L_i=\sum_{a\in O_i}w(a)z_a,
\qquad L_i(gz)=\chi(g)L_i(z).
\]

Products of two populations with the same character are invariant under the group. Thus their averaged pair-count expressions equal the deterministic products L_i L_j for the original incidence. The frozen character certificate gives all 2,385 such expressions. The new native model adds one bounded product auxiliary and one linear link for each expression.

The signings are balanced. Their raw bounds are minus and plus half the orbit size, hence either [-3,3] or [-6,6]. A square auxiliary has domain [0,u²]. A product of distinct signed populations has domain [-uv,uv]. No sign choice or signed population is fixed.

The refined local tables couple each orbit's original count columns to every supported signed population on that orbit. The 42 new tables have 19,331 tuples. Their projection, including literal-subset multiplicities, is exactly the old 42-table data. The old tables are retained as an unchanged prefix.

The final 32 homogeneous signed-population equations come from explicit character-weighted combinations of original Gram rows. They are included for propagation. Independent strength over complete RLT and the character product identities is not claimed.

## Native layout and validation

All ranges below use an inclusive first index and an exclusive last index.

| Variables | Range | Count |
|---|---:|---:|
| Original count coordinates | 0–15,038 | 15,038 |
| Trivial-character product auxiliaries | 15,038–15,941 | 903 |
| Signed populations | 15,941–16,059 | 118 |
| Signed product auxiliaries | 16,059–18,444 | 2,385 |

| Constraint family | Count |
|---|---:|
| Linear constraints | 31,064 |
| Exact integer products | 3,288 |
| Allowed-assignment tables | 84 |
| Total | 34,436 |

The complete basic overlay's 15,941 variables and 29,592 constraints remain byte-equivalent as a parsed protobuf prefix. The signed extension adds 29,075 linear terms. Its largest absolute linear box sum is 276 and its largest absolute product is 36. The inherited largest absolute linear box sum is 16,410,372,831,576, which fits within 44 bits. The literal native reader checks all coefficient, endpoint, and product bounds before accepting the model.

The model is built through public OR-Tools constructors. An earlier toy attempt to mutate an internal model protobuf caused a process crash before any solver was called. That attempt is preserved separately. It is not part of the current construction path.

The native preparation uses OR-Tools 9.15.6755. Its raw model protobuf has SHA256 `5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb` and contains 12,498,481 bytes. The gzip archive is lossless. Preparation checked 450 signed-product assignments and 36 joint-table/square assignments by direct evaluation of exported native protobufs, without search. Separate cold replay reads the archive and checks the complete parent prefix and every appended constraint.

## Bounded query contract

The separate runner prepares one owned child with a 180-second hard deadline. This includes imports, public model construction, native serialization, one solve call, exact candidate inspection, and output writes. The solver uses one worker and seed zero. Its internal time limit is the actual remainder after setup, less an eight-second finalization reserve. The parent kills and reaps an unfinished child. A late or failed child is never accepted.

Before the solve, the newly constructed native model must match the frozen raw protobuf hash. The runner saves the complete native response and every integer variable value, including all signed populations and all product auxiliaries. It supplies no hint or fixed population.

For a returned candidate, exact Python-integer inspection checks all variable domains, every inherited count row, the 25 refinements, every product and link, all 84 tables, and all 32 character-Gram equations. It also restores the original 15,200-coordinate vector and checks every one of the original 28,043 mathematical rows. The standalone terminal replay additionally evaluates every native protobuf constraint directly.

A native infeasible status is recorded as `UNPROVED_NATIVE_INFEASIBLE`. This package has no independently checkable infeasibility proof exporter. It cannot exclude the component or the F0 stratum from that status. A timeout remains `UNKNOWN`. A checked feasible result establishes only the bounded count model's feasibility; the later literal-mask coupling check is a separate task.

## Files

- `experiments/workspace/root_prism_free_f0_population_profile_cpsat.py`: immutable basic 42-table overlay.
- `experiments/workspace/root_prism_free_f0_character_cpsat.py`: signed overlay, native reader, and exact inspector.
- `experiments/workspace/root_prism_free_f0_character_query.py`: one owned bounded query and no-query preparation controls.
- `experiments/workspace/root_prism_free_f0_character_query_replay.py`: cold preparation and terminal arithmetic replay.
- `experiments/logs/root-prism-free/f0-population-profile-cpsat01/`: basic prepared archive and report.
- `experiments/logs/root-prism-free/f0-character-cpsat01/`: signed prepared archive, controls, and report.
- `experiments/logs/root-prism-free/f0-character-query-preparation01/`: frozen query definition and owner-stop controls.

This note records preparation only. No count feasibility or exclusion is asserted here.
