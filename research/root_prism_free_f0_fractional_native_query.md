# One bounded joint fractional baseline query

## Scope

This query concerns component zero in a globally prism-free, F-free split 18+18 triangle shell. All 480 first-component incidence selectors are free. The second component and its alignment remain free. The model contains the complete fractional incidence and shared-edge baseline; it does not include the inaccessible terminal registry of 4,404 selector cuts or the earlier twelve weighted cuts.

The twelve verified core relabelings reduce the convex feasibility problem to 42 selector orbits and 5,805 edge orbits. Averaging preserves every baseline constraint. It does not require a completed graph to have an automorphism. The quotient has 5,847 variables in the unit box, 686 equalities, 11,373 inequalities, and 57,801 nonzeros.

The production question is joint feasibility. The recovered strictly positive selector point is only a control and is not fixed in this query. A rational feasible point establishes a limitation of this baseline relaxation. A checked Farkas certificate excludes this conditional component-zero stratum. A numerical status or failed rational reconstruction establishes neither conclusion.

## Frozen sources

- Node export and independent replay: experiments/workspace/root_prism_free_f0_fractional_native_io.js.
- Exact arithmetic and reconstruction: experiments/workspace/root_prism_free_f0_fractional_native_exact.py.
- Owned-process supervisor and the single numerical query: experiments/workspace/root_prism_free_f0_fractional_native_query.py.

The preparation manifest binds their complete source hashes and Git blobs. The sources are frozen. The exact model's canonical JSON SHA256 is a30179bd5b2b7c58bb5458a3371a947997da17288a355452469d47a59ab81413. Its compact JSON file with one trailing newline has SHA256 eb872efde0768eb514c954c57a1f8049785980d2a73e158f1d29842cc0a072cb.

## Required preflight

Before the production query, native CI must check the four pinned dependency versions: numpy 2.3.5, scipy 1.17.0, highspy 1.16.0, and python-flint 0.9.0. It must run the Python helper controls, including an actual flint Dixon solve on the small alias-face example; run the Node integer-certificate controls; and rebuild the exact model from the published literal structural, motif, and interior-certificate inputs.

The V8 controls already passed 153 feasible-box multiplier checks, three strict infeasibility controls including a 131-bit multiplier, and rejection of a negative inequality multiplier. Native Python controls and the production query have not run at this preparation checkpoint.

The CLI names and argument order are:

`node experiments/workspace/root_prism_free_f0_fractional_native_io.js controls OUTPUT.json`

`python experiments/workspace/root_prism_free_f0_fractional_native_query.py controls --output OUTPUT.json`

`node experiments/workspace/root_prism_free_f0_fractional_native_io.js export experiments/logs/root-prism-free/f0-fractional-structural-recovery-input.json experiments/logs/root-prism-free/f0-fractional-motif-recovery-input.json experiments/logs/root-prism-free/f0-gram-interior-recovery-certificate.json FRESH_EXPORT_DIRECTORY`

The export writes model.json, export.json, and io-controls.json. The latter two files record exact controls and bindings. The workflow must inspect their PASS statuses and the model hash before calling query.

## One query and one exact phase

After successful preflight, the command is:

`python experiments/workspace/root_prism_free_f0_fractional_native_query.py query --model EXPORT_DIRECTORY/model.json --directory FRESH_QUERY_DIRECTORY --lp-seconds 60 --exact-seconds 60`

There is one HiGHS simplex run, one thread, with a requested 60-second budget including setup. The supervisor permits five additional seconds solely as a termination grace and records actual elapsed time. It starts no retry. The separate exact phase has a hard 60-second child limit.

The numerical phase saves the returned floating point values, solver status, and basis information. On a reported infeasible model, it asks getDualRayExist first. It calls getDualRay only if a ray already exists. This avoids an implicit auxiliary optimization to construct a missing ray.

For a proposed primal point, the exact phase first tries a finite list of denominator bounds. It may then construct one active-face proposal using numeric activation equalities and bounds. A modular minor identifies a square subsystem; at most 800 reduced coordinates and 32 nonpivot coordinate proposals are accepted. One flint Dixon solve reconstructs that subsystem. These numerical choices are proposals for reconstructing a point. They do not remove production constraints, and every reconstructed coordinate must pass the complete exact model afterward.

For a proposed infeasibility ray, equality multipliers are unrestricted integers and inequality multipliers must be nonnegative. Write w=A^T lambda+C^T mu for Ax=b, Cx<=d, and 0<=x<=1. The helper accepts only the strict integer inequality

lambda^T b + mu^T d + sum_j max(-w_j,0) < 0.

This follows by minimizing w^T x over the unit box. Ray reconstruction uses a finite list of scales and an exact dyadic candidate; floating status alone cannot pass this gate.

## Independent replay

If exact.json contains a point or a ray, run:

`node experiments/workspace/root_prism_free_f0_fractional_native_io.js replay EXPORT_DIRECTORY/model.json QUERY_DIRECTORY/exact.json REPLAY.json`

The Node checker uses BigInt arithmetic. A point is lifted to every literal selector and eligible edge and checked against all 145,690 full rows and 68,874 bounds. A ray is checked independently against the exact quotient and its unit box. The separately reviewed complete averaging proof transfers a quotient infeasibility certificate to the full baseline.

Timeout, missing output, reconstruction failure, and unresolved records retain their stated scope. There is no component exclusion until an independently replayed strict certificate exists. All numeric and exact outputs, process statuses, and logs must be preserved. This preparation makes no claim about a production outcome.
