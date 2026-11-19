# Clause explanations for exact incidence cuts

The clause extraction pilot passes for all twelve transports of the
repaired shared-row inequality. It changes no existing formula or run.

Each full inequality has 480 nonzero coefficients. The carry encoding of
the twelve inequalities needs 65,856 auxiliary variables and 524,820
clauses. Two exact clause extraction rules give smaller necessary
consequences:

| Premises | Clauses | Literals per clause | New auxiliaries |
| --- | ---: | ---: | ---: |
| The signed inequality and Boolean variables | 12 | 446 | 0 |
| The same inequality and the derived population 60 | 12 | 60 | 0 |

These clauses are weaker than complete encodings of the inequalities.
The second family happens to retain all sixty selected variables. Under
the exact population equation, each clause excludes its one proved
impossible incidence. The first family can forbid other assignments as
well. Clause width alone does not compare their strength on the incidence
domain.

## Exact implication

Write a proved inequality as $a\cdot z\leq b$, with Boolean variables
$z_i$. If falsifying a proposed clause fixes coordinates in $F$ to values
$v_i$, the exact independent minimum is

\[
L(F)=\sum_{i\in F}a_i v_i+\sum_{i\notin F}\min(0,a_i).
\]

The strict inequality $L(F)>b$ proves the clause. This argument uses no
solver result. The literal is $\neg z_i$ for a fixed value one, and $z_i$
for a fixed value zero.

The helper selects the largest positive gains over the independent
minimum until their sum crosses the strict bound. This gives a clause
with minimum width among explanations using that inequality and those
assignment values. It combines repeated coefficients before extraction.
Every calculation uses Python integers.

With the explicit premise $\sum_i z_i=K$, let $s$ be the number of fixed
ones. Add the $K-s$ smallest coefficients of the free variables to the
fixed contribution. This is the exact constrained minimum. The free
universe must include variables with zero coefficients.

The population premise here follows from the original Gram equations.
There are eighteen diagonal margins of ten, and each signature belongs
to three diagonal supports. Their sum gives

\[
3\sum_a z_a=180,\qquad \sum_a z_a=60.
\]

The pilot checks every original Gram position, every diagonal margin,
and every signature size. It does not infer population from the saved
candidate's size. Starting with its sixty selected variables gives a
valid clause. Greedy deletion preserves the exact bound; no deletion
succeeds for this particular shared-row cut.

The [independent mathematical review](root_prism_free_lazy_pb_clauses_review.md)
proves the rules and records the obligations for a future lazy loop.

## Controls and replay

The generic helper checks 7,000 independent explanations and 7,000
cardinality explanations across all three-variable coefficient vectors
in $\{-2,-1,0,1,2\}^3$ and fifteen right-hand sides. It tests the emitted
clauses on 112,000 explicit Boolean assignments. Additional controls
cover repeated coefficients, 201-bit coefficients, zero coefficients
in the free universe, and invalid clauses.

The domain pilot reconstructs the twelve core actions and transports
the selected incidence. It retains the original signed cut's hash for
each explanation. Each transported candidate violates its proved cut by
26 and falsifies both associated clauses. A separate direct calculation
checks the minimum from the actual literal lists. The complete pilot
also passes cold replay.

Sources:

- `experiments/workspace/integer_cut_clause_explanations.py`, SHA-256
  `f57d51b8be3fefd7a5d1035c52cc5758c719adb6a79d16a0909f1a54fdaa59f3`.
- `experiments/workspace/root_prism_free_f0_clause_explanation_pilot.py`,
  SHA-256 `b6f701949f31a09892d8b2211e9fc64d1fb7d1fa9a2ed6775185542980c350c4`.

The pilot certificate is
`experiments/logs/root-prism-free/f0-clause-explanation-pilot.json`,
SHA-256 `f06b7658ea4447bd785bab8fe2b4df87472c97944b85703ef7491dc54460b455`.
The frozen repaired inequality has a separate full-domain arithmetic
audit; clause extraction does not replace that proof.

To reproduce, choose new output paths because the sources refuse to
overwrite frozen artifacts:

```sh
.venv/bin/python experiments/workspace/integer_cut_clause_explanations.py \
  --controls --output /tmp/conway99-clause-controls.json
.venv/bin/python experiments/workspace/root_prism_free_f0_clause_explanation_pilot.py \
  --replay experiments/logs/root-prism-free/f0-clause-explanation-pilot.json \
  --output /tmp/conway99-clause-pilot-replay.json
```

## Use in a later search

A lazy loop must evaluate every registered inequality before accepting
an incidence for further row separation. If an inequality fails, its
exact explanation removes that assignment and all its auxiliary
extensions. Every retained clause needs its own inequality binding,
literal list, exact minimum, and cardinality proof when applicable.

A final UNSAT claim still needs a rebuilt necessary CNF, arithmetic
replay of every added clause, a fresh proof, retained-input inclusion,
and independent proof verification. This pilot calls no SAT solver or
optimizer and gives no component exclusion.
