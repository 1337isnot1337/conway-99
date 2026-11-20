# The first 35-vertex core has no binary incidence completion

The indexed complementary-rook core zero cannot occur in a
$\operatorname{SRG}(99,14,1,2)$. Its complete attachment-domain model is
UNSAT. Both direct DRAT checking and a separate cold domain/formula
reconstruction with retained-input inclusion and DRAT replay passed.

This excludes one local eight-vertex set with one specified matching.
That local set has 28 eligible matchings; the other 27 were not tested in
this run. The complete census has 2,521 indexed core descriptions. This
result does not exclude the complementary-rook case as a whole.

## Exact tested core

The old core is

\[
B_{27}=
\begin{pmatrix}
R&I&I\\
I&R&I\\
I&I&J-I-R
\end{pmatrix},
\]

where $R$ is the nine-vertex rook adjacency matrix. The eight neighbors of
$R_0$ outside this old core have original signature indices

\[
(0,1,9,10,18,20,26,27).
\]

In that order their matching is

\[
\{\{0,2\},\{1,5\},\{3,7\},\{4,6\}\}.
\]

These data are case zero in the
[complete local-core index](../../experiments/logs/grids-and-triangles/complement-rook-35core-domains-prefix01/all-core-index.json).
Its matching orbit under the stabilizer of this local set has one indexed
member. The local set itself has eight equivalent labelings at $R_0$.

The
[domain note](complement_rook_35core_domains.md)
proves that every completion supplies a subset of the 1,206 admitted
attachment columns. The
[model note](complement_rook_35core_incidence.md)
describes the exact Gram equalities, original-signature multiplicity, and
core-triple capacities. The formula has 106,697 variables and 217,833
clauses. It imposes no condition on graph automorphisms and fixes no
remaining incidence design.

## Checked result

A fresh proof-enabled Glucose4 instance received the full formula with no
assumptions. The requested solve budget was 60 seconds including
bootstrap. It returned UNSAT after 1.276 seconds, including 0.405 seconds
of bootstrap. Direct proof checking finished within the separate
60-second checker budget. The full solve and direct-check stage took
2.069 seconds and used 88,608 KiB peak process RSS.

The retained certificate contains 12,258 input clauses. A separate replay
rebuilt the complete attachment domain and full CNF from the frozen
sources. It matched the exact full-formula hash, checked every retained
clause against that rebuilt formula, and verified the retained DRAT proof.
The
[cold replay record](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-pilot01-cold-replay.json)
is the final verification gate.

The retained inputs comprise 11,907 Gram clauses, 62 original-signature
multiplicity clauses, and 289 clauses from the additional triple
capacities. This describes the saved proof support. It does not assert
that each of those constraint groups is logically necessary for every
possible proof.

The independent
[domain and encoding audit](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-independent-audit.json)
used a different attachment enumeration. It reconstructed the 35-core
matrix, considered all 256 local masks per original signature, recovered
the same 1,206 admitted columns, and checked all Gram and triple support
coverage. It did not import the new domain builder or run its solver.

## Replay

The preparation manifest binds the complete domain and full CNF:

- Model: [case0000-model.json](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-model.json).
- Retained inputs: [retained.cnf](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-pilot01/retained.cnf).
- Retained proof: [retained.drat](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-pilot01/retained.drat).
- Original terminal record: [result.json](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-pilot01/result.json).

The terminal record preserves the status immediately after the direct
check; the separate cold replay record confirms the subsequent gate.
The retained files suffice for replay. The raw proof hash is recorded,
but the raw proof need not be published.

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_incidence.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-model.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-pilot01/result.json \
  --drat-trim /tmp/conway99-drat-trim/drat-trim \
  --checker-seconds 60 \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0000-independent-proof-replay.json
```
