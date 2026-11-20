# Triangle-incidence query source, held before execution

The [accepted native model](../experiments/logs/root-prism-free/f0-triangle-incidence-native-root-acceptance01.json) has 80,730 variables and 300,795 rows. Its query runner, separate terminal checker, CI driver and [actual configuration](../experiments/logs/root-prism-free/f0-triangle-incidence-query-configuration01.json) pass source and receipt-interface review. No preflight or production query has run, and no execution gate has been issued for this configuration.

The next search is held for a stronger model. The [bounded spectral-gap test](root_prism_free_f0_recorded_triangle_spectral_gap_results.md) rejects 3,156 recorded triangles. Complete independent literal replay is in preparation; if it passes, exactly those triangle indicators will be fixed to zero in a new append before the next query. These prepared sources and the unused configuration remain preserved as the basis for that adaptation.

The explicit portfolio is `no_lp`, `quick_restart_no_lp`, `portfolio_no_lp`, with three full subsolvers and four total workers. The runner uses the repeated protobuf field's `extend` method and compares the entire native text/wire parameter message. The independent checker verifies every returned vector, domain and complete row activity with Python integers. The fixed limits remain 600 solver seconds, 610 measured native seconds and a 720-second query owner, with separate bounded terminal replay and no automatic retry.

Before any execution, review caught a root-receipt convention mismatch. The current runner reads `driver_source` for the native CI Python source, while `driver` retains the actual CI terminal JSON. The one-line correction and CI hash update are separately reviewed; both unrun predecessors are preserved.

## Source preparation record

The record below describes the initial source preparation. Its statements about pending native outputs are historical; the actual model is now accepted, and the prepared query remains unrun.

The fresh runner is source preparation for the prospective accepted 80,730-variable, 300,795-row model. The native model outputs and new model root acceptance are pending. No actual query configuration, preflight, solver call, or terminal replay has run.

The preceding combined-model query returned UNKNOWN with no vectors. This proposed query concerns a different model: the three appended families contain 3,325 valid inequalities and 26,916 terms. The runner never edits the accepted model.

## Parameters and bounds

The explicit full-subsolver list is ordered as no_lp, quick_restart_no_lp, portfolio_no_lp. There are three full subsolvers and four workers. Seed zero, presolve enabled, probing zero, linearization zero, and symmetry zero are explicit. Search progress, stdout logging, and response logging remain enabled.

The solver clock is 600 seconds. The measured native allowance is 610 seconds, and the process-group owner is 720 seconds. The source requires at least 670 owner seconds before constructing the single solver: 610 for the call and 60 for finalization. Otherwise it records a no-call unresolved result. There is no automatic retry.

Repeated strings use the protobuf repeated-field extend operation. The zero-solve preflight must round-trip the complete parameter text and wire, including subsolver order, through the pinned native wrapper. It must also validate and export the complete model with byte identity. Its limits are 60 measured seconds under a 75-second owner.

## Preserved acceptance

The complete native-call and response-preservation function is text-identical to the consumed combined query runner. So is the exact integer vector checker. Every primary and additional vector is saved before parsing. Native response text is saved directly; the separately retained protobuf wire is explicitly reconstructed from that text.

Every returned value must be a Python integer. All 80,730 variable domains and all 300,795 linear rows are checked using Python integer arithmetic. Full row activities are saved losslessly. The original selectors stay at indices 0 through 479, and original edge variables stay at indices 540 through 68,933. The edge stop is separate from the 80,730-variable parent size.

A numerical INFEASIBLE result remains unproved. UNKNOWN, overruns, incomplete responses, and failed arithmetic checks remain unresolved or errors with their original files preserved. An exact model vector still needs the independently implemented terminal replay, and does not establish a full graph or a compatible second component.

## Source changes

Eleven explicit substitutions reconstruct the complete new source from the accepted combined runner. Eleven whole functions remain text-identical. Changes are limited to namespaces and statuses, new model receipt acceptance, dimensions, and the explicit non-LP portfolio parameter assignment. The accepted-model loader uses the actual new native checker fields; it does not assume the obsolete replacement-span metadata from the older combined-model checker.

The source pins the reviewed producer, independent native checker, and corrected native CI driver. Future model/archive/report/owner hashes must come from actual successful model preparation and root acceptance. The source preparation record deliberately does not fill those pending values.

Root owns the actual query configuration, preflight workflow, production gate/request/workflow, and repository publication. This package authorizes none of those executions.
