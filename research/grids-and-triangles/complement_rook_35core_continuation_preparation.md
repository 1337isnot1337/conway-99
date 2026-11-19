# Preparation for the remaining twenty first-local matchings

This package prepares a finite continuation after the checked exclusions
of matching cases \(0,1,2,3,8,9,10,21\). The remaining cases are

\[
4,5,6,7,11,12,13,14,15,16,17,18,19,20,22,23,24,25,26,27.
\]

These twenty cases and the eight earlier exclusions partition all 28
admitted matchings for the first local eight-set. This package does not
cover the other local-set orbits.

## Formulas and exact input checks

For each case, the new wrapper cold-rebuilds the frozen complete 35-core
incidence formula and verifies its original hash. It replays that case's
already saved exact downdate certificate, including the complete column
domain and all integer negative vectors. It then appends precisely the
certified binary conflicts. All original clause bytes and all variable
indices remain unchanged. There are no new variables, selected incidence
designs, or graph automorphism assumptions.

The independent-form auditor imports neither the wrapper nor the
downdate machinery. It reconstructs the 35-core, all 1,225 Gram entries,
and the complete domain by testing every eight-bit attachment mask for
each eligible original signature. It checks every exported negative
vector directly against the full Gram matrix and compares the unchanged
original clause body and exact appended suffix. Running this auditor as
the author is a preparation control; a separate researcher must review
the source and bindings before the queries.

| Case | Complete attachment columns | Certified binary clauses appended |
| --- | ---: | ---: |
| 4 | 1,214 | 30 |
| 5 | 1,157 | 92 |
| 6 | 1,160 | 27 |
| 7 | 1,230 | 86 |
| 11 | 1,257 | 22 |
| 12 | 1,193 | 57 |
| 13 | 1,203 | 21 |
| 14 | 1,267 | 65 |
| 15 | 1,286 | 8 |
| 16 | 1,228 | 28 |
| 17 | 1,330 | 10 |
| 18 | 1,265 | 26 |
| 19 | 1,271 | 6 |
| 20 | 1,264 | 7 |
| 22 | 1,291 | 8 |
| 23 | 1,360 | 10 |
| 24 | 1,336 | 10 |
| 25 | 1,399 | 11 |
| 26 | 1,332 | 5 |
| 27 | 1,325 | 5 |

The mathematical necessity of the binary clauses is unchanged: selecting
columns \(h,k\) requires \(G-hh^{\mathsf T}-kk^{\mathsf T}\succeq0\).
Every appended clause has an explicit integer vector that violates this
condition. See
[`complement_rook_35core_downdate_preparation.md`](complement_rook_35core_downdate_preparation.md)
for the complete exact census and the classification of clauses already
implied by multiplicity, triple packing, or a quota-one Gram row.

## Bounded query protocol

The new runner reuses the unchanged, previously audited incidence solver.
It makes one fresh proof-enabled query per case in the displayed order,
with a maximum of 60 seconds including bootstrap. It never retries a
case. Each direct proof check and cold proof check has a separate
60-second limit.

An UNSAT result is accepted only after the direct proof check and a cold
rebuild of the original formula, exact cuts, and augmented formula. The
replay checks every retained input's inclusion and verifies DRAT. It also
records whether the retained proof uses any non-original Gram input; if
none occurs, the replay explicitly establishes an original-only proof
binding.

A SAT result is an incidence witness, with no adjacency specified among
the remaining 64 vertices. The unchanged semantic inspector checks all
1,225 Gram entries, 64 distinct original signatures, all selected-column
triple packing, attachment counts \((4,40,20)\), and the original 27-core
Gram identity. The wrapper also checks the appended binary clauses and
repeats the exact witness checks after a cold reconstruction. The batch
then stops for further completion work.

An UNKNOWN result leaves that case open and allows the next requested
case to run. Any error or uncertified proof stops the batch. Progress is
saved atomically before each query and after every accepted result, with
separate lists of started, completed, unstarted, certified UNSAT, and
UNKNOWN cases. A first SAT witness stops later queries even if it occurs
before all twenty cases are attempted.

The preparation terminal binds all models and author-run direct audits.
The later run terminal records actual outcomes. Preparation alone proves
no additional local exclusion, and twenty completed queries alone do not
exclude the local set unless every case has a checked proof.

## Sources and reproduction

The new sources are
[`complement_rook_35core_downdate_continuation.py`](../../experiments/workspace/complement_rook_35core_downdate_continuation.py)
and
[`complement_rook_35core_downdate_continuation_audit.py`](../../experiments/workspace/complement_rook_35core_downdate_continuation_audit.py).
Their frozen hashes, the exact preparation hashes, and all per-case
formula counts are recorded in the preparation artifact manifest.

Preparation uses new directories and a 120-second wall budget:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_downdate_continuation.py prepare-all \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-continuation-preparation-new \
  --cnf-directory /tmp/conway35-continuation-new \
  --seconds 120
```

After the separate source and input review, the intended query command is:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_downdate_continuation.py run-all \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-first-local-continuation01-preparation \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-first-local-continuation01-run \
  --seconds 60 --checker-seconds 60
```

Every old model, outcome, proof, and source remains unchanged. No
118-orbit sweep is included.
