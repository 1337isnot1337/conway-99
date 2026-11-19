# Complete-cap overlay for the globally prism-free case

Four separate formulas are prepared for the hypothesis that the entire
graph is prism-free. Each retains the complete rooted SRG equations,
the canonical anchor matching, its audited lex comparisons, and the
84 zero cell-side variables from a maximum-anchor zero case. It adds
exactly the 34,440 four-edge clauses derived in
[`root_prism_free_structure.md`](root_prism_free_structure.md).

At preparation, no solver has run on these formulas. The formulas do
not include the optional minimum-partition normalization.

## Coverage and compatibility with the lex comparisons

In a globally prism-free graph, every near-anchor matching avoids the
reference mate matching. Its alternating-cycle partition is therefore
one of `222`, `24`, `33`, or `6`. The complete 10,395-matching coverage
certificate already supplies a signed-axis relabeling to one of the
four canonical representatives. All fourteen near-anchor prism counts
are zero, so every added maximum-anchor zero condition is automatic.

The new clause set is invariant under every signed permutation of the
seven root axes: its definition ranges over every root axis and every
pair of disjoint non-mate label pairs. In particular, it is invariant
under each canonical matching stabilizer. The preparer explicitly
checks the full clause set under all 19 saved generators of the four
stabilizers. Their previously verified orders are 384, 32, 72, and 12.

Taking a minimum primary Boolean vector in each finite stabilizer orbit
therefore preserves a representative satisfying the new clauses. This
uses relabeling and does not assume that a completed graph has any
automorphism.

Consequently the union of the four new cases covers every globally
prism-free SRG with the target parameters. It does not cover every
graph with only a prism-free chosen root. An UNSAT result for one new
case would not exclude the entire earlier case with the same index.

## Formula sizes

The additions use existing primary variables and introduce no auxiliary
variables. The preparer streams the unchanged earlier CNF body and the
new clause body, changing only the DIMACS clause count.

| New case | Anchor partition | Variables | Clauses | Lex generators |
| ---: | --- | ---: | ---: | ---: |
| 7 | `222` | 982,934 | 2,010,956 | 8 |
| 8 | `24` | 972,476 | 1,979,578 | 4 |
| 9 | `33` | 976,525 | 1,991,726 | 5 |
| 10 | `6` | 967,338 | 1,964,162 | 2 |

| Case | Complete CNF SHA-256 |
| ---: | --- |
| 7 | `d8895c8e46d591f1cbfb41a5a1af8c414782dd677d8746207ed2268e645f36b4` |
| 8 | `d32b65ff37554df4f2d5dda7d95bf8e72e25b420759c6984301fd9b1662446f2` |
| 9 | `3492ab0bc08fd44978c205d242a5d57f5c0498545caab56c7b9af9a78ad13d00` |
| 10 | `95b54ba116bde146244befda799d5f2fa14c7ceef7d91a66e8c75237852d0e85` |

Each manifest binds the complete earlier model and CNF, completed prior
batch, mathematical clause certificate, primary order, source files,
and exact new formula hash. The cached formulas are under
`/tmp/conway-root-prism-free/`; they can be reproduced from those inputs.

## Validation and proof handling

The preparer rederives all 34,440 clauses, compares the complete raw and
compressed clause bytes with the frozen certificate, and checks the
primary variable order against `root_full_caps.py`. It verifies clause
set invariance under each recorded generator. The four formula hashes
are checked again when the formulas are materialized.

The separate runner has no lazy constraints or fixed incidence point.
Every SAT assignment is reconstructed as an ordinary 99-vertex graph
and checked for degree 14 and every common-neighbor equation. It also
counts the actual prisms. The overlay contains necessary local
consequences of global prism-freeness, so a valid complete assignment
could still contain a prism elsewhere. Such an assignment would still
be a solution of the unrestricted graph-existence problem.

An UNSAT return is retained as unverified until the saved proof passes
the independent DRAT checker. The certificate wrapper then rebuilds
the original complete rooted formula, canonical units, lex clauses,
84 side units, and all new clauses. It matches the exact full hash,
checks that each retained input clause belongs to that formula, and
verifies the retained proof. A timeout or failed proof check is not an
exclusion.

## Prepared artifacts

Sources:

- `experiments/workspace/root_prism_free_overlay.py`
- `experiments/workspace/root_prism_free_solve.py`
- `experiments/workspace/root_prism_free_certificate.py`

Bindings and preparation records under `experiments/logs/root-prism-free/`:

- `case-07-model.json` through `case-10-model.json`
- `overlay-prepare.log` and `overlay-prepare-replay.json`
- `case-07-materialize.log` through `case-10-materialize.log`

The completed earlier runs are left unchanged. These artifacts record
preparation and exact formula checks, with no solver outcome.
