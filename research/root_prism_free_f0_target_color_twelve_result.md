# Exact twelve-edge bound on the recorded target family

The 84 live must-triangle target edges satisfy
\[
\sum_{e\in E_*} y_e\le12
\]
in every Boolean solution of the original selector Gram equations and endpoint activations. This replaces the weaker bound of eighteen as a proposed aggregate row for this family. It does not exclude the fixed F0 component or construct a graph.

The proof is in [root_prism_free_f0_target_color_twelve_bound.md](root_prism_free_f0_target_color_twelve_bound.md). The exact structural certificate is [f0-target-color-twelve-certificate01.json](../experiments/logs/root-prism-free/f0-target-color-twelve-certificate01.json), SHA-256 ba987fe7ff39fe088bc66cb2fbd9f81c4e17a0b457af70642bc1f61d37d6d1e3. Its row key has SHA-256 36c10df91bd844086786344beb942a2fd271e2cb9fafc6712f9168d215a7a446 over compact JSON with no trailing newline.

## Structural proof

A target signature contains exactly one fixed-core edge. Use that edge as its color. Each of the eighteen colors has an original Gram equation with right-hand side one, so a Boolean solution selects at most one target vertex of each color.

The 84 target vertices consist of 72 private vertices, in twelve colors of six vertices, and twelve shared vertices, in six colors of two vertices. The target graph has two components, each with 42 vertices and 42 edges. The certificate reconstructs all target edges, all original color supports, and the original native Gram indices.

It checks the complete following conditions:

- There is no shared-to-shared target edge.
- Private vertices of private degree three, called centers, form an independent set.
- A center has no shared neighbor.
- Every noncenter's private neighbors have at most one color.
- Every private vertex has at most one shared neighbor.
- Each center has at most one private neighbor that has a shared neighbor.
- No private edge joins two vertices that have shared neighbors.

In a color-feasible Boolean selection, each noncenter therefore has selected private degree at most one. A selected private component is a star, an edge, or a singleton. The remaining conditions give each such component at most one possible shared attachment edge. A component with k private vertices contributes at most k-1 internal edges and at most one attachment. Summing over private components bounds all selected target edges by the number of selected private vertices. The twelve private-color quotas bound that number by twelve.

A shared vertex can connect several private components. This does not change the proof: each attachment is charged to the private component at its other endpoint. The absence of shared-to-shared edges accounts for every target edge.

## Exact check and timing

The authorized single pure-V8 structural call completed successfully. It performed no assignment enumeration, new signature or triangle census, model construction, or optimization.

| Receipt | Status | Elapsed time | Declared bound |
| --- | --- | ---: | ---: |
| Source finalization | PASS_COMPLETE_STRUCTURAL_CERTIFICATE_SERIALIZATION | 2,761 ms | 30,000 ms |
| Outer owner | OWNED_COMPLETE_STRUCTURAL_TWELVE_TARGET_CERTIFICATE_ACCEPTED | 2,851 ms | 45,000 ms |

The source deadline includes input binding, complete report serialization, and hashing. The owner records one invocation, no retry, and successful preservation of all exact output texts. It does not claim an operating-system child or hard operating-system preemption.

The report, finalization, and owner are separate immutable files. The [independent source and theorem review](../experiments/logs/root-prism-free/f0-target-color-twelve-independent-source-review01.json) read the complete frozen source, configuration, and corrected proof before this call. Root's subsequent artifact reconstruction and model-use acceptance are separate authority records.

## Witness and continuous scope

The certificate checks an explicit sixteen-vertex assignment attaining twelve target edges in the at-most-one target-color and endpoint relaxation. It selects all twelve private colors and four shared colors. Shared colors (8,15) and (9,14) remain unused. This assignment does not saturate all eighteen original Gram equalities and is not asserted to satisfy the full native model.

That scope was corrected before execution. The initial proof is preserved at [root_prism_free_f0_target_color_twelve_bound_initial_scope.md](root_prism_free_f0_target_color_twelve_bound_initial_scope.md). The [exact scope-clarification record](../experiments/logs/root-prism-free/f0-target-color-twelve-proof-scope-clarification01.json) binds both versions and the reversible wording changes. The source, configuration, upper-bound argument, and checked witness were unchanged.

A separate exact fractional control sets each private target selector to 1/6, each shared target selector to 1/2, and every target edge to 1/6. It satisfies the eighteen target-color equations and endpoint bounds and has target-edge sum fourteen. This shows where the Boolean argument adds information to that restricted continuous relaxation. It is not a fractional feasible point of the full parent model, so no full-model nonredundancy conclusion follows.

## Proposed native append

The row uses the original edge variables only:
\[
0\le\sum_{e\in E_*}\mathrm{var}_{540+e}\le12.
\]
Its 84 terms have coefficient one and ascending original edge ID. There are no new variables or auxiliary choices.

Root selected this row as the family global_target_total after the 2,904 side-edge capacity rows and 420 local-selector capacity rows. The planned native index is 300794. The resulting proposed append has 3,325 rows and 26,916 terms, for totals of 80,730 variables and 300,795 rows.

This certificate package does not modify the existing native model or the active query. A separately reviewed producer, exact native preparation, and independent full append replay must bind the accepted row before a later query uses it.

The target-indicator inventory assigns each of its 5,364 distinct triangles to exactly one of the 84 targets. Its existing target equalities therefore also give the bound twelve on the sum of these recorded triangle indicators. Completeness is only for this recorded family; this statement does not bound the total number of exterior triangles by twelve.
