# Incidence implications shorten eight checked forbidden patterns

The eight independently replayed conditional joint proofs from
`complement_rook_incidence_master_pilot_01_results.md` imply shorter signed
selector clauses. The new clause sizes are

\[
22,16,18,29,28,18,18,18.
\]

These are restrictions on the complementary-rook 27-core. They do not exclude
that core. The calculation uses the existing 180 exact incidence margins and
the existing eight joint proofs; it does not solve another exterior graph model.

## Logic of the reduction

Let \(F\) be the frozen necessary joint model and let \(M\) be its binary
incidence-margin subsystem. A checked signed pattern has positive units
\(P\) and negative units \(\{-z_j:j\in N\}\). Its retained proof establishes

\[
F\land P\land\bigwedge_{j\in N}\neg z_j\quad\text{is unsatisfiable}.
\]

First remove any negative assumption whose singleton clause does not occur
in the retained input. The same retained proof remains included in the new
formula. Next, if \(M\land P\) implies \(\neg z_j\), that negative assumption
can also be removed: \(F\) already includes the incidence equations.

The verifier derives implications in two stages. In an exact quota row
\(\sum_{s\in Q}z_s=q\), it assigns all remaining variables zero when the
known ones total \(q\), and assigns all remaining variables one when they
are all needed to reach \(q\). It saves each row, current known ones,
unknown variables, quota, and forced value. It then tests every still-needed
negative variable \(z_j\) against \(M\land P\land z_j\).

Each UNSAT test has its own explicit-unit CNF and independently checked DRAT
proof. Each SAT test has a saved 72-column binary witness whose complete
\(27\times27\) Gram matrix is checked exactly. A SAT result here establishes
only that the incidence equations and these positive assumptions do not force
that individual negative literal.

## Exact results

Selector literals are numbered 1 through 252. A stored signature index is one
less than its selector number. Case numbers refer to the original eight-design
pilot.

| Case | Positive units | Original negative units | Original negatives forced by quotas | Further DRAT implications | SAT implication counterexamples | New clause size |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 14 | 26 | 18 | 0 | 8 | 22 |
| 1 | 15 | 20 | 19 | 0 | 1 | 16 |
| 2 | 14 | 15 | 10 | 1 | 4 | 18 |
| 3 | 10 | 32 | 11 | 2 | 19 | 29 |
| 4 | 11 | 30 | 11 | 2 | 17 | 28 |
| 5 | 14 | 28 | 15 | 9 | 4 | 18 |
| 6 | 13 | 28 | 14 | 9 | 5 | 18 |
| 7 | 12 | 27 | 10 | 11 | 6 | 18 |

There are 98 remaining implication queries: 34 have checked UNSAT proofs and
64 have exact SAT witnesses. None of the eight patterns becomes positive-only
by this calculation. The source replays all eight original certificate bindings
against the saved successful full-baseline replay report.

Case 1 is especially small. Its 15 positive units are

\[
4,6,11,12,16,32,33,44,57,62,72,74,85,87,143.
\]

Quota propagation from these positives forces 66 selected signatures and 174
absent signatures. The remaining negative assumption is \(-184\). The saved
incidence witness with \(z_{184}=1\) shows that this last negative cannot be
removed by the incidence equations and the positive units alone. A separate
test against the full joint model is needed to determine whether its forbidden
pattern can be shortened further.

## Artifacts and replay

The source is
`experiments/workspace/complement_rook_incidence_core_simplification.py`.
The main certificate is
`experiments/logs/grids-and-triangles/complement-rook-incidence-core-simplification.json`.
The adjacent `complement-rook-incidence-core-simplification/` directory contains
the 34 small explicit-unit formulas, their proofs, and checker logs. The
artifact manifest lists the exact published files and hashes.

The generation and independent readback replay both passed. The replay
reconstructs all quota steps, checks all 64 dense Gram witnesses, rebuilds every
small implication formula, and verifies all 34 proofs. It uses no full joint
solver.

```sh
.venv/bin/python experiments/workspace/complement_rook_incidence_core_simplification.py \
  --pilot experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.json \
  --full-replay experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-full-replay.json \
  --directory /tmp/conway-core-simplification-replay \
  --certificate experiments/logs/grids-and-triangles/complement-rook-incidence-core-simplification.json \
  --drat-trim /tmp/conway99-drat-trim/drat-trim
```

Some tiny formulas become contradictory during solver initialization. In those
cases the proof source appends an explicit empty-clause RUP claim. The
independent DRAT check must validate that claim against the exact formula; an
empty solver proof stream alone is never accepted.
