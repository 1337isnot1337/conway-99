# Complete local eight-neighbor tests for the F0 component

All 41 previously unqueried center representatives have an exact Boolean
eight-neighbor witness. The separate cold replay rebuilt every native model
and CNF and checked every saved witness. Together with the previously checked
center 355, this covers all 42 center types and all 480 literal center labels.

This is a feasibility result for the specified local projection. It gives no
selector zero. The independently chosen neighborhoods need not coexist in
one graph. The result also does not show that a given fractional point is a
convex combination of these local witnesses.

## Necessary local model

The frozen F0 domain has 480 possible signatures in one 18-vertex shell
component. Every signature contains three component vertices. For a fixed
selected center \(b\), the local variables are separate Boolean values
\(y_a\) for every retained literal candidate neighbor \(a\). Candidates that
share a global quotient coordinate remain separate local variables.

Let \(D\) be the adjacency matrix of the fixed 18-vertex component, and let
\(h_b\) be the center signature. The model retains all 18 exact mixed
common-neighbor equations:

\[
\sum_{a: i \in h_a} y_a = 2-(h_b)_i-(D h_b)_i.
\]

Their right sides sum to 24. Each selected neighbor contributes to three
rows, so they imply \(\sum_a y_a=8\). The encoder also retains that population
equation as a direct check.

The complete frozen local conflict graph imposes
\(y_a+y_c\leq1\) for every certified conflicting pair. Its reasons include
a mixed quota of one, two common fixed-core sites, a recorded two-edge prism
witness, or a proved selector-pair zero. The inventory keeps the distinction
between a semantically valid conflict and a homogeneous edge inequality
already present in the global relaxation.

The candidate domain omits the previously proved zero edge coordinates.
The complete native model retains every other candidate and every conflict
from the frozen inventory. It imposes no equality between distinct literal
neighbor variables.

The 12 actual core relabelings provide transports for all 480 center labels.
This is a relabeling reduction of the necessary local tests. It does not
assume that a hypothetical 99-vertex graph has an automorphism.

## Preparation and query limits

The generic builder is
`experiments/workspace/root_prism_free_f0_local_neighbors.py`.
It uses the unchanged audited cardinality encoder from the center 355
model. It reconstructs the literal domain, all conflict reasons and all
mixed quotas. It also reproduces the old center 355 CNF and checks its
saved witness without another solve.

The successful model preparation is
`experiments/logs/root-prism-free/f0-local41-preparation02/preparation.json`.

| Quantity | Complete new batch |
|---|---:|
| Representative centers | 41 |
| Literal centers covered | 468 |
| Total CNF variables | 273,859 |
| Total CNF clauses | 942,494 |
| Raw CNF bytes | 12,278,924 |
| Model preparation time | 12.567448552 seconds |

Center 336 runs first. The other 40 centers are ordered by decreasing exact
conflict density, with the center ID breaking ties. The previously queried
center 355 is reused.

The runner is
`experiments/workspace/root_prism_free_f0_local_neighbors_batch.py`.
Each center has an owned child process and a hard five-second wall deadline
including imports, input loading, initialization, search and raw writes.
The whole batch has a 60-second deadline, including the parent’s native
witness checks. The initial file-hash preflight is measured separately.
There is at most one proof-enabled solver call per center.

A timeout is persisted as UNKNOWN before killing and reaping the child.
A partial proof cannot establish a selector zero. An UNSAT answer requires
a fresh CNF reconstruction and a separately verified proof. In this batch
every answer was SAT, so no UNSAT proof was used.

## Terminal result and exact replay

The production result is
`experiments/logs/root-prism-free/f0-local41-batch01/result.json`.

All 41 records have status `SAT_EXACT_LOCAL_WITNESS`. There were no UNKNOWN,
UNSAT, error or unqueried centers.

| Timing | Seconds |
|---|---:|
| Initial hash preflight | 0.043696734 |
| Whole production batch | 8.465591295 |
| Sum of owned child wall times | 7.137642032 |
| Sum of child initialization times | 2.047687064 |
| Sum of solver search times | 0.071380955 |
| Whole cold replay | 8.418937698 |
| Cold replay input initialization | 2.005146092 |

The cold result is
`experiments/logs/root-prism-free/f0-local41-batch01-replay/result.json`.
It has status `PASS_COMPLETE_MODEL_AND_AVAILABLE_CERTIFICATE_REPLAY).
It rebuilt all 41 native instances and CNFs byte for byte. It then checked
every complete SAT assignment and every native witness without a solver.

Across the new batch, the replay checks all 942,494 CNF clauses,
401,417 conflict constraints, 738 mixed equations and 17,835 visible
common-neighbor caps. Each witness has eight selected neighbors and a
30-vertex partial adjacency matrix. The visible cap count is
\(41\binom{30}{2}=17,835\).

For example, center 336 selects neighbor IDs

\[
143,\ 196,\ 197,\ 202,\ 211,\ 262,\ 312,\ 453.
\]

Their signatures are

\[
\{1,16,17\},\{2,13,17\},\{2,14,16\},\{3,4,9\},
\{3,5,11\},\{4,6,15\},\{5,8,9\},\{10,11,15\}.
\]

This example passes all 18 mixed equations, all 6,519 local conflicts and
all 435 visible pair caps. Every other witness is retained with the same
native checks.

## Preserved failed preparations and controls

The first model preparation reached its initial deadline check after a
backend delay of 130.853 seconds. It had completed zero new models and
made no solver call. Its progress and log remain under
`f0-local41-preparation01`. The unchanged second preparation completed
all 41 models.

The first supervisor-control preparation passed its normal-exit control.
The deliberate exit-code-three control returned after the two-second
deadline and was correctly recorded as UNKNOWN, with the child reaped.
The next timeout control had not run. The failure record is preserved.

A separate hash-bound continuation reused the successful first control and
ran only the two missing checks: a timely exit-code-three child was ERROR,
and a sleeping child was killed at its deadline, recorded UNKNOWN and
reaped. The frozen query preparation binds both the preserved first
attempt and this continuation. It does not reinterpret the late control
as a successful on-time error test.

These service and control outcomes have no mathematical exclusion scope.

## Exact bindings

| Artifact | SHA256 |
|---|---|
| Generic builder | `cf3f4e250ce9c33bbc3c1c0714f0188de012d0d4d36ae32d427d15771349a6e9` |
| Batch runner | `b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278` |
| Control continuation | `fa2568be85c35da9b2ce7db6db3a4d04a4750167eedbb59526cbe5a0bda431ba` |
| Complete model preparation | `2213372cd8615df2c177c08d7dfd034812eeb385a75266ada1403d331d765976` |
| Query preparation | `57bf84bdf102444aad209bf9c7fd5e62c1fc4f7bf584fa3fac8d0b75e71627ae` |
| Production result | `e71590c6b6786cec61b79b35ba70e5fc858b2c8706ca037e84f9034a9981c264` |
| Cold replay result | `4d880e00aeb3a947ba12d814a30f88bd8469cae67798793dfa82f6294bb9de91` |

The independent model-source review is
`f0-local-neighbors-independent-source-review.json), SHA256
`818199dd79253937b71040fbe30862ff89b4735be46e3b230161c5295f7dcf14`.
The coordinator’s runner review is
`f0-local41-batch-independent-source-review.json), SHA256
`56c3f59565b6b211e4f659f3310f50676160b0631701e2addae323a0ab43bad4`.

## Lossless archive and restoration

The public package includes
`experiments/logs/root-prism-free/f0-local41-complete-archive.json.gz`.
It contains every byte of the 354 raw model, assignment, control, failure,
result and log files. Each member has its original relative path, byte
length and SHA256. The archived model and result bindings are checked
against fixed anchors.

The standard-library archive tool is
`experiments/workspace/root_prism_free_f0_local41_archive.py).
Its restoration path checks every member before writing, rejects paths
outside the chosen root, and requires existing files to be identical.
It never replaces a differing file. A fresh-directory restoration and a
separate verification against the original worktree are saved with the
package. These are byte-restoration checks, separate from the native
mathematical cold replay above.

To restore a fresh checkout before inspecting the original paths:

```sh
python experiments/workspace/root_prism_free_f0_local41_archive.py restore \
  --root . \
  --archive experiments/logs/root-prism-free/f0-local41-complete-archive.json.gz \
  --report /tmp/f0-local41-restoration.json
```

The mathematical conclusion remains confined to the complete local
eight-neighbor family. Neighborhood matching constraints, common choices
across centers, and the other shell component are outside these 41 models.

