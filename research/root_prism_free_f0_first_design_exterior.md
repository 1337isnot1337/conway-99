# The first saved split-shell incidence cannot extend

The saved sixty-triple incidence for component zero has no exterior
completion. This exclusion leaves the other eighteen-vertex component
and its incidence unspecified. It applies to every choice of that second
component and every fiber alignment within the stated split-shell case.

The result excludes one incidence design. It does not exclude component
zero, the complete split-shell case, or a strongly regular graph.

There are two checks. A complete exterior formula has a checked DRAT
proof with 120 retained input clauses. A separate integer potential
already contradicts one of its mixed common-neighbor rows. The potential
also gives a necessary inequality for other incidences of this component.

## Exterior equations

Let H be the saved 18-by-60 incidence matrix. Its columns are the sixty
distinct selected triples, in the order of the original component
incidence witness. Let A be the adjacency matrix of the eighteen-vertex
component, and let D be the adjacency matrix on the sixty exterior
vertices.

Every exterior vertex has six neighbors in the full thirty-nine-vertex
triangle shell. Thus D is eight-regular. The two shell components are
anticomplete, and the central triangle has no exterior neighbors. The
mixed block of the strongly regular graph identity therefore gives

\[
AH+HD+H=2J.
\]

For a fixed exterior vertex a, its required neighbor-incidence vector is

\[
q(a)=2\mathbf1-h_a-Ah_a.
\]

Every entry is zero, one or two, and the entries sum to 24. Each neighbor
column has three entries equal to one, so these equations also imply
eight exterior neighbors.

An exterior edge ab is possible only if the two first-shell triples
intersect in at most one point. Its column h_b must be supported on the
positive coordinates of q(a), and h_a must satisfy the corresponding
condition for q(b). These necessary conditions retain 1,224 possible
edges for the saved design. No edge is removed using a choice of second
incidence.

For every pair of exterior vertices, the model imposes

\[
|N_D(a)\cap N_D(b)|+h_a^T h_b+D_{ab}\leq2.
\]

The unspecified second component can only add common neighbors. This
inequality therefore holds for adjacent and nonadjacent pairs in every
completion.

## Complete formula and proof

The formula has 1,224 independent edge variables, 166,048 total variables,
426,090 clauses and 964,359 literal occurrences. It includes all sixty
degree equations, all 1,080 mixed equations and all 1,770 outside-pair
caps. A shared variable pool keeps all counter and conjunction variables
disjoint.

The source is
`experiments/workspace/root_prism_free_f0_first_design_exterior.py`, with
SHA256 `f0c5105526b9374935b4ba961859261249f44f2b311d98138ac3c8aeb5ed56cd`.
The model hash is
`d98d817a7e9410f6fd88186adacdf23b886e543f3e18f7a9ec98af07e6558078`.
The complete formula hash is
`fc4a38ba24efb5dd092b25224e6d34753382dad21a9c7bf163a7e74b48acbbc3`.

An independent reviewer reconstructs the complete 480-triple component
domain, the saved sixty-column design, every eligible edge and all row
supports. The review also checks the conjunction truth table, shared
variable pool, direct candidate inspector and replay paths. It builds
no duplicate CNF and calls no solver.

A separate preflight rebuild reproduces the full formula hash. The one
proof-enabled query returns UNSAT after 44 conflicts and 1.023 seconds,
including bootstrap. The direct proof checker retains 120 input clauses.
A separate cold process rebuilds the complete domain and formula, checks
every retained input against that formula, and verifies the retained proof.

The cold report is
`experiments/logs/root-prism-free/f0-first-design-exterior-run01-cold-replay.json`,
with SHA256
`6240d173c5f15919a74e0062f8a81f3b25bd55a3928f3bd9e94b0531ed5a4847`.
The retained formula and proof hashes are respectively
`dffc02f25e8953c387be76661960bca0955a296b783b09959427e691105649fb`
and `141cce4fe1e726e147ae2ab112662e67eb73597f39acfd00ced879cc7ee7527d`.

## A direct integer obstruction

Use component coordinates zero through seventeen. The last saved column
is the triple a={11,16,17}, which has index 479 in the full 480-triple
domain. Define the integer potential

\[
v=(1,1,1,4,-5,0,1,1,4,-5,-5,0,-2,-2,4,-5,0,-2).
\]

Direct integer arithmetic gives

\[
v^Tq(a)=6.
\]

Only 29 columns of the saved sixty-column design are eligible neighbors
of a. Every one satisfies \(v^Th_b\leq0\). Consequently any nonnegative
combination of those columns has nonpositive potential and cannot equal
q(a). This contradicts the required row of HD. The argument needs no
binary assumption, no other exterior row, and no outside-pair cap.

The coordinator independently checks every eligibility condition, all
29 nonpositive values and the scalar value six. The complete arithmetic
record is
`experiments/logs/root-prism-free/f0-first-design-exterior-row479-coordinator-arithmetic.json`,
with SHA256
`c46100d49152d7726c70a389f0ac1e419ebaf530b5055f691c97192f38845a42`.

## A necessary cut for other incidences

The full component domain has 232 eligible neighbors of a. If z_b records
whether triple b belongs to an incidence, then every valid incidence
with an exterior completion satisfies

\[
\sum_{b\in N(a)}\max(v^Th_b,0)z_b\geq6z_a.
\]

When z_a=1, write the mixed equation using the actual neighbor indicators
y_ab. The identity \(v^Tq(a)=\sum_b(v^Th_b)y_{ab}\), nonnegativity, and
\(y_{ab}\leq z_b\) give the inequality. When z_a=0, the right side is
zero and the inequality is automatic.

There are 55 positive coefficients: 36 equal three, sixteen equal six
and three equal nine. They are all outside the saved design. Divide by
three. Since the selectors are binary and the new right side is two,
coefficients above two can be replaced by two. The result has 36 unit
coefficients and nineteen coefficients equal to two. The old design
has left side zero and right side two.

This cut does not exclude a itself. The full eligible domain has an
explicit eight-neighbor solution with signature indices
`0,9,72,82,259,420,397,429`. It matches all eighteen mixed quotas; every
pair of those neighbor triples intersects in at most one point. The
arithmetic record checks this control as well.

The separate complete exterior-row preparation retains all 480
signatures and 68,394 possible edges. Verified automorphisms of the
fixed component partition the row domains into 42 orbits. These are
relabelings of the specified core, with no symmetry assumption on a
hypothetical graph. Its source is
`experiments/workspace/root_prism_free_f0_exterior_row_domains.py` and
its complete ledger is
`experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz`.

## Replay

Use a new output path and the pinned proof checker described in the
experiment guide:

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_first_design_exterior.py replay \
  --model experiments/logs/root-prism-free/f0-first-design-exterior-model.json \
  --result experiments/logs/root-prism-free/f0-first-design-exterior-run01/result.json \
  --checker /absolute/path/to/drat-trim \
  --output /tmp/f0-first-design-exterior-cold-replay-new.json
```

The replay regenerates the full formula temporarily. It needs the saved
retained formula and proof, but not the discovery run's raw DRAT file.
The earlier fixed-first/full-second incidence preparation is preserved
as a separate record. Its solver query was not run because this exterior
exclusion already rules out that first incidence for every second choice.
