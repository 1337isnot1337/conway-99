# Independent checks of the two follow-up count witnesses

Two new integer count assignments satisfy the order-ten count system,
the prism-containment zeros, and all 25 retained linear cuts. The second
also satisfies `x521=0`. Neither assignment is a graph or an exact PSD
certificate.

The checker `experiments/workspace/audit_prism_zero_followup_witness.py`
imports the original extension-equation generator and a direct prism
containment test. It imports no optimizer, point finder, or moment
separator. It uses the small graph catalogue, not the dense reduced
count matrix.

For each saved assignment, it checks:

- all 48,965 induced counts are nonnegative integers;
- all 180,445 original extension equations;
- the total number of induced subsets at each of eleven orders;
- all 1,443 prism-containing induced types and all 58 prism-containing
  ordinary core coordinates are zero;
- all 549 original ordinary-core upper bounds;
- all 25 retained cuts, with exact integer evaluations;
- agreement of `x521` with induced type 48936, including zero for the
  second assignment.

| Assignment | SHA-256 | x521 | Smallest retained-cut value | Audit seconds |
| --- | --- | ---: | ---: | ---: |
| Rounded zero-closure loop point | `3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326` | 116 | 629575 | 5.951 |
| Rounded x521-zero face point | `ee8e22f070e0529be5be8bf14c853c6ad9ed97127570223abf6e1529ab8857f9` | 0 | 1156044 | 6.015 |

Both audits pass. The original-equation audit is independent of the
reduced-matrix evaluation used by the producers. It does not repeat the
core-to-induced matrix reconstruction. The separate full-model replay
for the face point performs that reconstruction.

The first assignment comes from the
[zero-closure moment loop](grid_free_order10_prism_zero_moments_loop.md).
Its preceding moment scans concern the unrounded numerical proposal.
The second comes from the
[x521-zero face](../root_prism_free_x521_face.md). Its separate
[2,332-block scan](../root_prism_free_x521_moments.md) uses the exact
integer assignment. Neither scan proves PSD of all passing blocks.

The reports and process logs are:

- `experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure-root-audit.json`
  and the corresponding `.log`;
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-root-audit.json`
  and the corresponding `.log`.

The source SHA-256 is
`520da449f35fab8a8175dc7546ac2a20f23a2707d09a980296c7099dcf4cb1b1`.
`make verify-prism-zero-followup-counts` rebuilds the small catalogue and
repeats both original-equation audits without calling an optimizer.
