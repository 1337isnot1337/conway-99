# Boolean parity separation on the case4 face

The equality system has both a strictly positive rational point and a
signed integer point. Neither settles its Boolean feasible set. This
package prepares a finite family of valid Boolean parity inequalities and
an exact test at the saved rational point. Preparation has not evaluated
that point.

## Fixed family and original-row provenance

The published modulo-two certificate has 286 independent reduced rows on
the 1,115 surviving coordinates. The other 99 original coordinates are
already proved zero. The proposed family consists of all 286 basis rows
and all 40,755 unordered XORs of two distinct basis rows. It contains
41,041 equations and no larger basis combinations.

These equations are distinct. The pivot coordinates of the reduced basis
form an identity matrix. Therefore a single basis row retains its own
pivot and a pair retains exactly its two pivots. Distinct one- or
two-element subsets cannot yield the same equation support.

For every basis row, preparation expands the saved combination of the 396
distinct native equations back to the original 1,214 coordinates. It
records the original native row IDs, integer right-hand side, full
coefficient-array hash, full parity support and the odd terms removed on
the known zero coordinates. Each proposed pair has the XOR of those two
saved combinations. Any emitted cut will receive a fresh direct expansion
of that combined original-row proof.

Only the 99 previously proved zeros may be removed. The starting rational
point supplies no additional equality or zero premise. All selected
native rows are original equalities; inequalities are not silently reduced
modulo two.

## Forbidden-vertex inequalities

Consider one necessary Boolean equation

\[
\sum_{i\in H}x_i\equiv r\pmod2,\qquad r\in\{0,1\}.
\]

For a Boolean vector $f$ on $H$ with forbidden parity $1-r$, every allowed
Boolean vector differs from $f$ in at least one position. Hence

\[
\sum_{i:f_i=0}x_i+\sum_{i:f_i=1}(1-x_i)\ge1.
\]

Writing $F=\{i:f_i=1\}$ gives the integer linear inequality

\[
\sum_{i\in F}x_i-\sum_{i\in H\setminus F}x_i\le |F|-1.
\]

These inequalities are valid for every Boolean completion satisfying the
original equations and the established zero face. They need not hold for
every real point in the old relaxation.

## Exact nearest forbidden vertex

Write the saved point as $x_i=N_i/D$, with
$D=1661041997$. Round each coordinate on $H$ to its nearest Boolean value;
ties are rounded to zero. Let the resulting parity be $s$. Its distance
numerator is

\[
C=\sum_{i\in H}\min(N_i,D-N_i).
\]

If $s\ne r$, this nearest vertex is already forbidden and is optimal.
If $s=r$, a forbidden vertex must differ from it in an odd number of
positions. Flipping position $i$ adds $|D-2N_i|$, a nonnegative quantity.
The cheapest odd collection is therefore one position of minimum penalty.
The exact minimum forbidden distance numerator is

\[
C+\begin{cases}
0,&s\ne r,\\
\min_{i\in H}|D-2N_i|,&s=r.
\end{cases}
\]

For equal penalties the implementation selects the smallest original
coordinate ID. A minimum numerator below $D$ supplies a strict violated
inequality. Its exact upper-row violation numerator is $D-C_{\min}$.
No tolerance or floating arithmetic enters the test.

An empty support with right-hand side zero is tautological and has no
forbidden vertex. An empty support with right-hand side one yields the
contradiction $0\le-1$. Neither occurs in the prepared case4 family, whose
supports are nonzero by the pivot argument.

## Preparation result and controls

The complete structural preparation took 1.894 seconds. The 41,041
supports range from 3 to 451 coordinates and contain 7,344,314 coordinate
occurrences in total. A conservative exact cost bound is 750,790,982,644,
below $2^{40}$. Python integers are used throughout, so the bound is a
sizing check rather than an overflow assumption.

The generic formula controls read no case4 point or domain. They checked
5,938 small instances against 180,817 literal vertex distances and checked
180,814 inequalities on allowed Boolean vertices. They include 1,932 tie
cases, empty supports, a strict fractional separator and six large-integer
controls. A separate set of 64 original-row XOR controls verifies signed
coefficients, signed right-hand sides and removal of only a declared zero
coordinate.

The structural ledger SHA256 is
`0a46cfcc886d15cce3e6fc13df30aea40764f19321a5bf1a09682e6140496606`.
The complete basis specification is saved in
`rook-case4-face99-parity-preparation01/basis.json.gz` under
`experiments/logs/grids-and-triangles`.

## Proposed bounded scan and replay

The frozen driver permits one 60-second scan of the fixed family, followed
by a separate 60-second exact replay. It binds the saved point and its
earlier full-relaxation replay. At scan time it also rechecks the unit box,
the 99 zeros and all 2,271 original native rows.

Each examined equation receives a compact evaluation record. Each strict
cut saves its exact inequality and original-row proof. The inequality
uses original-coordinate bitsets: `support_original_hex` gives $H$,
`positive_original_hex` gives $F$, and `upper` gives $|F|-1$. Thus every
coefficient is explicit: $+1$ on $F$, $-1$ on $H\setminus F$, and zero
elsewhere. Original native row combinations are also saved as bitsets.

The driver checkpoints after each 256 candidates and has a 64 MiB combined
transcript limit. A time or byte limit leaves an explicitly partial prefix.
It adds no optimizer call, retry, or larger row combination. The cold
replay reconstructs every examined minimum and every emitted 1,214-coordinate
proof. Completeness requires all 41,041 candidate records.

A strict cut rejects the saved fractional point, not the graph case. A
complete scan with no strict cut only closes this finite separation family
at that point. Neither outcome establishes Boolean incidence feasibility.

## Frozen sources

The generic formula source is
`experiments/workspace/rook_case4_parity_polytope.py`, SHA256
`048df509b05601f15d6cb4230750b36d221276cce66e625b0cf9c720ecb89062`.

The case4 domain, scan and replay source is
`experiments/workspace/rook_case4_face99_parity_separation.py`, SHA256
`101595222904d8576bcadf430b3a2ff37e6060b8c8690f27437108294008f0da`.

The production scan remains unrun pending a separate source and model gate.
