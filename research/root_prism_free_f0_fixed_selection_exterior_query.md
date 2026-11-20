# Fixed-selection exterior query and proof gate

## Mathematical scope

The accepted direct literal selection is the 60-element set in
`f0-direct-literal-query-run01/selection.json`, SHA-256
`6c1434b1dbb5a28f19707a3048cb43d64f14370856d03ef7496a3a58fabf4aaa`.
This query fixes that first incidence and leaves the second 18-vertex component
and its alignment free. It seeks a necessary exterior partial graph.

Root's model `f0-fixed-selection-exterior-direct01/model.json` has SHA-256
`ec482e37e989a4657a0f7efb801c875062575fa2786efea72ba37c111974b3a9`.
The complete CNF hash is
`d5bb8807367519fc32e7a4d05305533154d7ecf134483cde2d9ee2c96a1532a6`:
1,219 edge variables, 165,148 total variables, 423,682 clauses and 958,948
literal occurrences. There are 60 degree equations, 1,080 mixed equations
and 1,770 outside-pair caps. It retains the original eligible-edge domain.
The later 162 zero-edge orbits are not imposed.

For fixed incidence H, component adjacency A and exterior adjacency D, every
completion satisfies

\[
D\mathbf1=8\mathbf1,\qquad HD=2J-H-AH,
\]

and, for every exterior pair u,v,

\[
|N_D(u)\cap N_D(v)|+h_u^Th_v+D_{uv}\le2.
\]

These conditions are necessary because the unspecified second component can
only supply additional common neighbors. The new query imports root's frozen
adapter API for `build`, `inspect` and `read_clauses`. Their historical ASTs are
bound exactly, but the historical incidence loader is never called. No new
clauses, assumptions or symmetry conditions are added by this wrapper.

## Execution and acceptance

The source is `root_prism_free_f0_fixed_selection_exterior_query.py`, SHA-256
`bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3`.
Configuration hash
`3d9a7873be11b0121da1b7b8640c6cd32c5d7a2f1651e45ab6c8e4ba9c1c337a`
binds the actual model, selection, accepted model cold, input evidence and
runtime files.

One owned process group has 180 seconds for initialization, one Glucose4 query,
raw artifact writes, exact inspection and any direct proof check. The native
phase, including imports, loading and bootstrap, has at most 60 seconds.
Actual elapsed time is checked; an overrun stays UNKNOWN. The full signed
assignment is saved before all-clause and direct graph inspection.

For an UNSAT return, the raw proof is saved first. A terminal empty clause is
appended if absent, and the checker must validate it. Direct DRAT has at most
60 seconds, clipped to the actual remaining owner allowance. Acceptance needs
a timely zero exit and an exact `s VERIFIED` line. The retained clauses are
checked as a multiset subset of the complete original formula.

The separate cold has a 60-second owner. It rederives the current domain and
rebuilds the whole CNF, checks the byte hash and every result/owner binding,
checks retained-input inclusion again, and performs a second DRAT check within
the remaining allowance. The supervisor stops its process group, including
checker descendants, and reaps its worker. Late or incomplete records cannot
produce a cut.

If S is the fixed 60-signature set, a fully checked UNSAT proof gives

\[
\sum_{a\in S}z_a\le59.
\]

The justification uses the original population equation: an incidence has
exactly 60 distinct signatures, so selecting every member of S fixes this
incidence. Only after the cold owner accepts the completed replay does it
write `certified-selector-cut.json`. This excludes one incidence, with the
second component free. It does not exclude the whole component or graph case.
A SAT answer is only an exterior partial graph.

## Checker provenance

The existing local checker and accompanying C file were copied byte for byte
to `f0-fixed-selection-drat-trim.bin` and `.c` under `experiments/workspace`.
Their hashes are respectively
`5ca39774377ac993136fb7c65be9ab414437970305fd6d4614932ec3d343d124` and
`5c122001267171230ccf08587ab6b5cc247b8d0e72e3485ff95dc399f17862c7`.
The executable must retain mode 755. No recompilation was performed; the C
file is recorded provenance, not a claim of a reproducible binary build.
PySAT 1.9.dev23, its Glucose4 wrapper and its native extension are separately
hash-bound in the configuration.

## Frozen preparation

The optimizer-free preflight passed in 1.1369 owner seconds, without overrun.
Report SHA-256:
`6b8e05d6987ae30dad1e452d0674a7146f0b88e1c2e98b667a498ef2d8eea17b`.
Owner SHA-256:
`afdb897c9d7125e3f49be20765b2c9f16ff539cfbec3c7d0c4746cf817fd6693`.
It imported the native API and parsed all clauses, without constructing a
solver or making a solve call.

Separate controls passed seven checker-result cases, six assignment cases,
three retained-multiset cases and four owned-process cases, including a
descendant termination check. Their report hash is
`ea3c8206a14b89dc3999bb24010369f549e9373ca3c06dd3bf4f3994b17d23cd`.
They read no production CNF and used no native solver.

Root source/production gate:
`79fc8b7154626a2da2db31b85e149102c4ae49ee4b9363c38d1a950f2dca8b99`.
Independent source review:
`78bc9973b138fc8365f52d0145ffdfbeb6af944bb73fbd951d6cd46a4f20ee7f`.
The preparation package contains no production outcome; the terminal package
is separate.
