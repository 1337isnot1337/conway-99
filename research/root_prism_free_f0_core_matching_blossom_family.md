# Complete core matching three-edge family: preparation

The frozen single-row proof gives
\[
Y_{96}+Y_{103}+Y_{4477}\le12.
\]
Its interpretation and limited comparison are in
[the single-blossom note](root_prism_free_f0_core_matching_blossom.md).
The present package prepares a complete finite family. It contains no
production family census or count-point evaluation.

## Domain and coverage

For each of the 18 fixed component sites \(i\), use the complete frozen set
\[
U_i=\{a:i\in h_a,\ q_{ai}=1\}.
\]
The original Gram equations force eight selected vertices in each \(U_i\).
Their actual exterior edges form a perfect matching.

Six sets have 50 possible signatures and twelve have 61. The exact raw
scope is therefore
\[
6\binom{50}{3}+12\binom{61}{3}=549480
\]
triples. The traversal order is core site 0 through 17, then lexicographic
triples of that site's sorted domain. Every processed triple receives one
of three dispositions:

- At least one pair is not in the frozen eligible-edge domain.
- All pairs are eligible, but at least one belongs to a proved-zero
  \(Y\) orbit.
- All three edges are live, so the triangle matching inequality is retained.

The first two cases have at most two live edges. Such edges form a star,
whose sum is at most the endpoint selector by its mixed quota-one equation.
They therefore give no additional triangle matching row beyond that
equation and the selector upper bound. This reduction is structural and
uses only frozen proved zeros.

## Exact rows and comparisons

For a retained triple, sum its inequality
\[
y_{ab}+y_{ac}+y_{bc}\le1
\]
over the twelve actual core actions. An edge in orbit \(R\) contributes
\(12/|R|\) to the coefficient of its integer population \(Y_R\).
Repeated orbit coordinates are added. The source divides all coefficients
and the right-hand side by their positive gcd and deduplicates the
resulting sorted integer rows.

Each first witness for a distinct row retains its core site, three
signature IDs, three literal edge IDs, original orbit IDs, all twelve
literal transports, and the summed literal-edge coefficients.
Every live literal triple retains a reference to its normalized row.
Deduplication does not remove domain coverage.

Comparisons are deliberately limited:

- All 4,416 original literal cuts use selector variables. The new rows
  have nonempty edge-count support, so none is an identical row in that
  typed coordinate system.
- A unary row is compared exactly with the frozen single-orbit
  \(Y\)-packing bound.
- Every row is tested against the sum of its saved packing bounds and
  separately against the explicit final \(Y\)-overlay domains.

All distinct rows remain in the certificate, including rows implied by
those bounds. These tests do not decide implication by the full model,
its Fourier links, its local tables, or arbitrary combinations of old
inequalities.

## Bounded generation and replay

The source is
[the finite-family driver](../experiments/workspace/root_prism_free_f0_core_matching_blossom_family.py).
The [preparation record](../experiments/logs/root-prism-free/f0-core-matching-blossom-family-preparation01.json)
binds every input and the complete source hash. Preparation evaluated no
family triples.

The proposed census and cold replay each use one owned process with a
60-second wall deadline. The child has a 55-second cooperative budget,
including input loading. The parent kills and reaps its process group at
the hard deadline and preserves the last saved checkpoint. No retry is
automatic.

Generation writes immutable per-core compressed chunks. A final chunk
may contain an exact partial prefix. Each chunk records every processed
triple's disposition count, the live-triple coverage ledger, and its new
row certificates. The raw chunk budget is 64 MiB, with 1 MiB reserved for
metadata. Completed chunks survive a timeout or later error.

The cold pass independently contracts the actual twelve images of each
literal edge it encounters. It reconstructs the normalized forms,
first-witness order, every saved live-triple reference, all disposition
counts, and every bound comparison. It only claims the saved prefix it
has actually checked. The producer's complete scope and the cold check's
complete saved-prefix status are separate fields.

The owner entry points are:

~~~sh
python experiments/workspace/root_prism_free_f0_core_matching_blossom_family.py census \
  --preparation experiments/logs/root-prism-free/f0-core-matching-blossom-family-preparation01.json \
  --directory experiments/logs/root-prism-free/f0-core-matching-blossom-family-run01

python experiments/workspace/root_prism_free_f0_core_matching_blossom_family.py cold \
  --preparation experiments/logs/root-prism-free/f0-core-matching-blossom-family-preparation01.json \
  --directory experiments/logs/root-prism-free/f0-core-matching-blossom-family-run01 \
  --output experiments/logs/root-prism-free/f0-core-matching-blossom-family-run01-cold.json
~~~

These commands require the coordinator's frozen source gate. No native
model or optimizer appears in either path.

## Separate candidate condition

Once a fully accepted literal selection exists, each selected \(U_i\)
contains only eight vertices. Exact perfect-matching feasibility can then
be checked directly on that fixed set. If it has no perfect matching, the
original equation \(\sum_{a\in U_i}x_a=8\) turns the obstruction into the
valid positive clause
\[
\sum_{a\in T}x_a\le7,
\]
where \(T\) is the rejected selected eight-set. This candidate-dependent
test is owned by the coordinator's separate matching oracle. No candidate
exists and no such query belongs to the current family preparation.
