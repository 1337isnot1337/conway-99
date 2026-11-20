# Continuation from the first lazy terminal formula

This preparation extends the bounded search protocol from the first
lazy run. It contains no new SAT or LP query. The preceding run remains
unresolved after its declared twenty-row-pass limit.

The mathematical scope is unchanged: all 480 first-incidence selectors
are free for component zero in the globally prism-free, F-free split
$18+18$ shell case. No second component, second incidence, or fiber
alignment is fixed.

## Exact inherited state

The seed adapter performs the complete frozen mathematical and prefix
replay of the first lazy run. It checks the parent source, preparation,
terminal result, cold replay and publication manifest. The bound
lossless archive can restore missing transcript records, without
overwriting a different existing file.

All 1,008 individual-row inequalities, all 108 signed shared-edge
inequalities and all 1,980 clause explanations are retained. Each clause
keeps its original registry index and proof record. The adapter rebuilds
the original 56,994-clause incidence/direct-cut base and appends the
same necessary explanation clauses in the same order.
Only the original counters and primary lazy clauses are regenerated.
The earlier large weighted-counter and carry-adder CNFs are not rebuilt.

The prepared DIMACS is byte-identical to the parent's terminal DIMACS:

| Quantity | Value |
|---|---:|
| Primary selectors | 480 |
| Total variables | 28,308 |
| Total clauses | 58,974 |
| Explanation clauses | 1,980 |
| Registered inequalities | 1,116 |
| Literal occurrences | 319,248 |
| DIMACS bytes | 1,640,426 |
| New auxiliary variables | 0 |

Its SHA256 is
`570f9e85c7eaa724d71a77b9654f7aad2c9052825fde876aaf20a87f484e24bc`.

The explanation-clause prefix digest is unchanged. The initial registry
digest is reset to the canonical complete registry rather than the
parent's append-history digest. The exported registry binds both values
and every parent artifact. This changes bookkeeping only; no predicate,
index or clause changes.

The parent's final candidate is checked against the exact base, all
1,980 explanations, and all 1,116 inequalities. It is a positive prefix
control. The runner does not fix or prefer this candidate; SAT selects
freely from the unchanged formula. Its exterior rows remain untested
until a permitted new query tests them.

## Frozen semantics and new limits

The runner uses the frozen clause-generation, primary-inspection,
registry-evaluation, exact row/shared separation, transcript and replay
functions. A standard-library AST control compares the entire new
runner with the frozen parent after accounting for:

- the terminal-seed import and its hash binding;
- the row-pass limit changing from twenty to one hundred;
- the SAT-call limit changing from five hundred to one thousand;
- two descriptive preparation/replay labels.

The control also checks that every fresh-proof and cold-proof wrapper
function is unchanged. It imports no subject module and invokes no
solver or optimizer. The new seed adapter still requires a separate
mathematical/source review; AST equality does not replace that review.

The overall run limit remains 180 seconds. Each SAT call receives at
most ten seconds. Each row pass or shared-edge LP receives at most
sixty seconds within the remaining overall budget. The one-million-
variable and two-million-clause ceilings remain unchanged.

Every SAT candidate is checked against the original incidence and
actual clause prefix. Every registered integer inequality is evaluated
before any row LP. A violation gives both independently bounded and
population60 clause explanations, transported only through verified
core relabelings. The complete new exact cut enters the registry before
its clause consequences are generated.

There are no Gram-equality shifts, graph-automorphism assumptions,
unproved visitation blocks or changed solver heuristics. A complete
sixty-row exact-box pass remains the only route to a shared-edge LP.
Exact symmetric feasibility stops the run as a necessary-relaxation
witness. UNKNOWN, numerical uncertainty, limits and errors stop it
without an exclusion.

## Proof and preparation gates

Incremental UNSAT remains uncertified. The separate wrapper rebuilds
the full final necessary formula, then runs one fresh proof-enabled
query for at most sixty seconds. Direct DRAT checking and a separate
cold retained-input/proof replay each have a sixty-second limit.
Only all three successful gates could exclude the stated component-zero
stratum. They could not exclude all components or solve Conway99.

The preparation rebuilt the retained formula in 30.893 seconds,
without invoking an incidence solver or optimizer. Its metadata is
`f0-lazy-continuation-preparation.json.gz`. The exact registry export is
`f0-lazy-terminal-registry.json.gz`.

The implementation files are:

- `root_prism_free_f0_lazy_continuation_seed.py`;
- `root_prism_free_f0_lazy_continuation.py`;
- `root_prism_free_f0_lazy_continuation_certificate.py`;
- `root_prism_free_f0_lazy_continuation_source_controls.py`.

The separate cold preflight reconstructs the complete mathematical
prefix and verifies the DIMACS hash. A fresh coordinator gate is required
before the new bounded query.
