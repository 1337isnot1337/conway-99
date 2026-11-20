# An exact exterior-row cut for component zero

## Result

The first saved 60-triple incidence of component zero cannot extend to
the required exterior graph. A short integer inequality proves this
without a SAT solver, integrality assumptions on the exterior row, or
any choice of second component.

The same inequality gives a necessary restriction on the full
480-selector component-zero model. It has 55 positive terms, and 12
verified core relabelings give 12 valid restrictions. The target
signature itself is not excluded: an explicit eight-neighbor row works
against the full domain.

The scope remains the globally prism-free, $F$-free, split $18+18$
triangle shell case. This result neither excludes component zero nor
decides the full graph problem.

## The exterior-row equation

Let $A$ be the adjacency matrix of the first 18-vertex shell
component. Its outside incidence matrix $H$ has 60 distinct columns,
each the indicator of an admissible triple. For an outside vertex with
triple $a$, the exact mixed common-neighbor equations require

\[
\sum_{b\text{ adjacent to }a}h_b
=q(a):=2\mathbf1-h_a-Ah_a.
\]

The other shell component contributes nothing to this equation because
the shell components are anticomplete. The central triangle has zero
outside incidence. Thus the equation does not depend on the second
component graph or its fiber alignment.

An exterior edge can occur only if the two first-component triples
share at most one point. Also, each point of either triple must have
positive demand in the other endpoint's mixed equation. The complete
480-triple census gives 68,394 unordered pairs satisfying these
necessary conditions. No potentially useful pair is removed because
of an incidence choice or an assumed graph symmetry.

## The short contradiction

Use zero-based shell labels and the target

\[
a=\{11,16,17\},
\]

which is signature 479 in the frozen 480-column order. Its demand is

\[
q=(2,2,2,2,1,0,2,2,2,1,1,0,2,1,2,1,0,1).
\]

Define an integer weight vector $v$ by the following table.

| Shell coordinates | Weight |
| --- | ---: |
| $0,1,2,6,7$ | 1 |
| $3,8,14$ | 4 |
| $4,9,10,15$ | −5 |
| $12,13,17$ | −2 |
| $5,11,16$ | 0 |

Then

\[
v\cdot q=10+24-20-8=6.
\]

There are 232 universally eligible neighbors of $a$, but only 29
belong to the saved 60-triple incidence. On those 29 triples, the
weights $v\cdot h_b$ have this exact distribution:

| Weight | Number of triples |
| --- | ---: |
| 0 | 19 |
| −3 | 4 |
| −6 | 1 |
| −9 | 2 |
| −12 | 3 |

Every permitted nonnegative combination of these 29 columns has
nonpositive dot product with $v$. The required sum $q$ has dot
product 6. This is a contradiction. In particular, the saved row is
infeasible even with arbitrary nonnegative real neighbor weights.
Neither a degree-eight constraint nor any outside-pair packing
constraint is needed for this argument.

The vector was found by a numerical linear program. The stored proof
uses only the displayed integers and exact dot products. Its replay
does not call an optimizer.

## A universal weighted selector inequality

Let $z_b\in\{0,1\}$ indicate whether triple $b$ is selected in an
arbitrary component-zero incidence. If $z_a=1$, write $y_{ab}$ for
the exterior-edge indicator to a possible neighbor $b$. Then

\[
6=\sum_{b\in N(a)}(v\cdot h_b)y_{ab}
\le\sum_{b\in N(a)}\max(v\cdot h_b,0)z_b,
\]

because $0\le y_{ab}\le z_b$. When $z_a=0$, the right side is
nonnegative. Therefore every realizable incidence satisfies

\[
6z_a\le\sum_{b\in N(a)}\max(v\cdot h_b,0)z_b.
\]

Exactly 55 eligible triples have positive weight: 36 have weight 3,
16 have weight 6, and 3 have weight 9. All 55 are absent from the saved
incidence. The certificate records their complete signature indices
and coefficients.

Divide by 3. On binary selectors, coefficients above 2 can be truncated
to 2 without changing the threshold condition. If any such selector is
chosen, it already reaches the threshold 2; otherwise no truncated
coefficient contributes. Let $U$ be the 36 weight-one signatures and
$V$ the 19 signatures whose capped weight is two. The cut is

\[
2z_a\le\sum_{b\in U}z_b+2\sum_{b\in V}z_b.
\]

The old incidence violates it with left side 2 and right side 0.
The inequality applies to every first incidence; the old incidence is
used only to discover and exhibit the violated cut.

## Why the target remains possible

The complete domain admits the following eight neighbors of $a$:

\[
\{0,2,6\},\ \{0,3,9\},\ \{1,2,7\},\ \{1,3,10\},
\quad
\{4,6,12\},\ \{7,14,15\},\ \{8,12,13\},\ \{8,14,17\}.
\]

Their indicator sum equals $q$ in all 18 coordinates. Every pair of
these triples intersects in at most one point, so the shared exterior
neighbor does not itself violate the common-neighbor cap. This is an
exact row control, not a full incidence or graph construction.

## Relabeling and Boolean encoding

The verified core-generator closure has order 12. Each map preserves
the central triangle and the full 21-core adjacency. The audit checks
its action on all 480 triples, the target demands, and eligible
neighbors. Transporting $v$ gives 12 cuts at 12 distinct targets:

\[
336,337,360,390,404,405,427,445,454,455,467,479.
\]

This uses relabelings of the known core, not automorphisms of a
hypothetical completed graph. The source reconstructs each transported
coefficient list directly and compares it with the transported base
list.

Each binary cut has a 37-clause encoding on the existing selectors.
There is one clause

\[
\neg z_a\ \lor\ \bigvee_{b\in U\cup V}z_b,
\]

and, for every $i\in U$, one clause

\[
\neg z_a\ \lor\ \neg z_i\ \lor\
\bigvee_{b\in(U\setminus\{i\})\cup V}z_b.
\]

When $z_a=1$, these clauses exclude a selection with no positive terms
and a selection with exactly one weight-one term. They permit a
weight-two selection or at least two weight-one selections. That is exactly the threshold
inequality. When $z_a=0$, every clause holds.

The 12 cuts add 444 distinct clauses of length 56, without auxiliary
variables. Exhaustive controls check 1,922 small guarded-threshold
assignments and 4,096 coefficient-truncation cases. The original
480-column model and its first saved point remain unchanged.

## Independent attribution and replay

The exterior SAT proof retained 120 input clauses. A separate audit
reconstructs the 1,224 eligible edges for the saved incidence and
attributes 115 clauses to 13 mixed-count equations at its last outside
vertex, whose signature is $a$. The other five clauses are
outside-pair capacity clauses at that same vertex. Each is already
implied by a quota-one mixed coordinate. No other exterior row or
degree equation appears in the retained input core.

The direct integer proof above checks all 18 valid mixed equations,
rather than relying on the cardinality auxiliaries in that retained
core. The coordinator independently checked its 232-neighbor domain,
29 saved dot products, all 55 positive coefficients, and the explicit
eight-neighbor row control.

The independent audit and exact cut certificate are:

- `experiments/workspace/root_prism_free_f0_first_design_exterior_row_audit.py`
- `experiments/logs/root-prism-free/f0-first-design-exterior-row-certificate.json.gz`

The audit imports no subject builder, canonicalizer, optimizer, or SAT
solver. It uses the cardinality encoder only for exact retained-clause
attribution. The contradiction, domain, group transports, and cut
controls use integer arithmetic.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_first_design_exterior_row_audit.py \
  --certificate experiments/logs/root-prism-free/f0-first-design-exterior-row-certificate.json.gz \
  --replay
```

The separate overlay source is
`experiments/workspace/root_prism_free_f0_exterior_row_cut_overlay.py`.
It binds and rebuilds the original component-zero CNF, then appends
exactly these 444 clauses. It fixes no incidence design. A later SAT
point must pass the original Gram, profile, motif, and new cut checks;
it remains only a necessary incidence point. A checked UNSAT result
would concern component zero in the stated conditional shell case.

The prepared overlay has 28,308 variables and 56,994 clauses: the exact
original 56,550-clause body followed by the 444 new primary clauses.
Its SHA256 is
`419a570047e7c1fd61cc2ddbeb6eade45af0a2570518c5fe1ea78954ad9142b0`.
The cold preflight replays the complete shell/component coverage,
reconstructs the original formula and all cut coefficients, and
reproduces that hash. The preparation does not solve this new formula.
