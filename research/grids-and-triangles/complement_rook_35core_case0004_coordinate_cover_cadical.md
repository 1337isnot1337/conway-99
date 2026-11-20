# CaDiCaL preparation for the unchanged case4 formula

## Scope

This package prepares one alternative-backend query of the exact coordinate-
cover CNF used by the previous Glucose4 query. It changes no variable,
clause, assumption or symmetry restriction. The production query has not
run in this preparation checkpoint.

The full formula has 134,852 variables and 439,604 clauses, with SHA-256
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.
The previous Glucose4 UNKNOWN result remains unchanged. A different backend
does not strengthen the mathematical model.

## Runtime and tiny controls

The installed Python-SAT version is 1.9.dev23. The preparation binds the
actual Python wrapper, native extension, backend class and relevant method
sources. The two main runtime hashes are:

| Runtime component | SHA-256 |
| --- | --- |
| Python solver wrapper | `21aaf31fd1e4fa42806b384c2d34674119a1d0f1f8f95338d3ba41e9472891c3` |
| Native solver extension | `838ebc59f0c3d266c3d551c52a3c5078f342f1840a70020d1617302a3a311d99` |

CaDiCaL300 passed the required tiny controls, so the fallback CaDiCaL195
control was not needed. Both controls use the same proof-enabled solver
constructor and streamed clause addition as the prepared production child.

The first control contains seven of the eight clauses that forbid the
eight assignments on three variables. It is SAT, with the expected unique
assignment. The second contains all eight clauses and is UNSAT. The parent
independently checks all eight truth assignments and the returned SAT model.
The UNSAT proof is checked by drat-trim against the exact tiny CNF. That
check returned VERIFIED, with eight retained input clauses, six retained
lemmas and thirteen resolution steps.

The proof API and its binary-to-text conversion are therefore exercised on
an actual checked proof. This control is not a proof about the production
formula.

## Hard process deadline

The installed CaDiCaL Python wrapper does not implement interruption.
The production solver therefore runs in an owned child process. Its parent
starts a 180-second wall clock before creating the child, so imports,
formula loading and solving are included.

If the deadline expires, the parent first saves UNKNOWN. It then sends
SIGKILL to that child and waits for it to be reaped. Any partial result or
proof from the child is ignored for exclusion purposes. An exception in the
parent's wait or timeout recording path also kills and reaps the child.
There is no automatic retry.

A deliberate watchdog control used a 0.1-second limit on a sleeping child.
The parent saved UNKNOWN before termination, received return code minus9,
and reaped the child after 0.109 seconds. This control uses no solver.

The production child reads one clause at a time. It does not allocate a
Python list of all 13.5 million literal occurrences. Default CaDiCaL settings
are used; there are no assumptions or phase preferences.

## Result verification

After a normally exiting SAT child, the parent runs the existing complete
partial-incidence checker. It verifies all original 35-core and 27-core
Gram identities, distinct-signature and triple constraints, attachment
counts, thirty Gram conflicts, sixty uncapped row inequalities, and every
coordinate-cover origin. The remaining 64-vertex graph is unspecified, so
SAT would still be a partial incidence result.

After a normally exiting UNSAT child, the parent requires direct DRAT
verification against the unchanged complete CNF. It verifies that every
retained input occurs in that formula. A separate cold replay reconstructs
the entire model, checks the full CNF hash, checks retained-input inclusion
again, and verifies the retained proof. The direct and cold proof checkers
each have a separate 60-second limit.

A timeout is never interpreted as UNSAT. A proof from a timed-out or
nonzero-exit child is never promoted. Even a fully verified UNSAT proof
would exclude only indexed 35-core case4.

## Bindings and commands

Source:
`experiments/workspace/complement_rook_35core_case0004_coordinate_cover_cadical.py`

SHA-256:
`1921f71964795d819e0369c9679dc1526df97c29bb1920a932c7ca449ba3de25`

Preparation:
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json`

SHA-256:
`e7a4185a300a48edbe01d7103da8e765dab1ad9653e2678992d3f1c4e986d731`

After the separate production gate, run once in a fresh result directory:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_cover_cadical.py solve \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-run01 \
  --seconds 180 --checker-seconds 60
```

Cold result replay uses a fresh output:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_cover_cadical.py replay \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-run01/result.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-run01-cold-replay.json \
  --checker-seconds 60
```
