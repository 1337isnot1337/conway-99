# Bounded LP and full-span parity continuation

This is a separate preparation. It preserves the completed fixed-family
discovery and the successful full-span query. It starts from the exact point
with denominator 67,336,409,858, which passes the three previously appended
cuts. The new 42-column cover rejects that point and is the fourth seed row.

The cycle retains the frozen 167,115-row extended matrix as an exact prefix.
It appends original-coordinate parity inequalities with complete Gram
witnesses. The initial matrix has 167,119 rows, 1,103 variables, and
10,769,728 nonzero coefficients. There are 1,102 surviving selectors and one
max-min variable. The 112 proved-zero selectors remain fixed throughout this
prepared cycle.

## Four-round contract

Each round has the following stages:

1. Run the unchanged full-pool LP generation kernel on the current registry.
   All necessary native rows, equalities, max-min rows and appended parity
   cuts are active from the start. The complete original cover pool remains
   available for exact final acceptance.
2. Use only the saved numerical basis to propose a rational point, or recover
   an exact finite-box bound. Dynamic alias and fixed-bound choices remain
   proposals. Check every current row and every original-coordinate obligation.
3. Replay the exact result in a separate process. An accepted zero-face or
   infeasibility certificate stops the cycle. No domain change is performed.
4. At a new exact positive point, make one full-span Boolean separation call.
   Save a complete native vector before inspecting it. Independently replay
   any cut and append that necessary inequality to the registry.

The cycle stops on a partial stage, error, failed exact reconstruction,
repeated exact point, missing checked cut, resource refusal, or declared cap.
There is no automatic retry. A final rejecting cut may be preserved even
when the round cap prevents another LP. Every point records the precise
registry prefix it passed; later cuts are never attributed to that point.

## Explicit limits

| Operation | Limit |
|---|---:|
| New LP rounds | 4 |
| LP native calls per round | 30 |
| Cumulative native LP time | 120 seconds |
| Numerical process wall per round | 180 seconds |
| Exact reconstruction per round | 60 seconds |
| Separate LP arithmetic replay per round | 60 seconds |
| Full-span separator calls | 4 |
| Native separator time per call | 60 seconds |
| Owned separator process per call | 120 seconds |
| Separate parity-cut replay per call | 10 seconds |
| New cut per separator | 1 |
| Total registry size, including four seeds | 8 |
| Exact residual system dimension | 512 |
| Exact output integer size | 4,096 bits |
| Native workers | 1 |
| Saved separator artifacts per call | 64 MiB |

The maximum sum of the declared child wall caps is 1,720 seconds. The
whole-cycle process group has an outer 1,860-second guard. Requested native
time is at most 120 LP seconds plus 240 separation seconds. Recorded actual
times remain visible even if a native timer slightly overshoots. No later LP
call starts after the cumulative LP budget is spent.

## Point-parameterized parity model

The generic separator reuses the frozen 286-row Gram span, all original
witnesses, all 112 zero premises, all variable IDs and all support equations.
For a new accepted point, it changes only the rounding bits, exact integer
weights and bound. In the native protobuf, only the forbidden-parity XOR and
weighted-distance row may change. All 2,491 variable domains and the other
2,206 constraint rows must remain literally equal to the frozen model.

The point, its full arithmetic replay, and the exact cut registry prefix are
explicit inputs. The new point must satisfy every original Gram equation.
Every integer activity must remain below the signed 63-bit limit. A larger
denominator is refused; it is never rounded or truncated for the search.

The full-span model represents a parity equation by basis-choice bits and
its nearest forbidden Boolean vertex by at most one support flip. Its
weighted integer distance must be at most \(D-1\). The exact proof inspector
reconstructs the full 1,214-coordinate original Gram sum and the signed cut.
The separate checker repeats that arithmetic directly from the saved vector
and original rows, with no optimizer or span search.

The LP registry uses the previously reviewed canonical closest-forbidden
certificate format. This conversion preserves a strict one-flip witness.
If the nearest vertex has allowed parity, flipping coordinate \(j\) is
strictly violated only when

\[
2\min(n_j,D-n_j)>\sum_{a\in H}\min(n_a,D-n_a).
\]

There can be only one such coordinate. Thus a strict one-flip witness already
uses the unique least-penalty flip. The conversion checks equality of the
forbidden vertex and exact deficit; it does not search for a different parity
equation or add an unchecked cut.

## Reused proof machinery

The numerical LP stage, finite-box certificate logic, dynamic basis
reconstruction, complete point inspector and separate exact LP replay are
imported unchanged from the frozen v4 kernel. The new controller does not
copy or replace their arithmetic. The complete cached-array prefix and all
appended rows receive a separate preparation check. Original cover supports
are not regenerated merely to append four rows.

Native INFEASIBLE from the parity separator remains uncertified. Even a
proved absence of a violated parity cut would not exclude the incidence
problem. A case4 exclusion can arise only from the unchanged exact LP
infeasibility-certificate gate. No result from this local case resolves the
whole Conway99 problem by itself.

## Containment diagnostic

A separate exact census checked both orientations of the 166,013 cached
selector rows and the three prior dynamic cuts. Only one nonnegative row
contains the full new 42-column support: current row 360, original native
row 585, with upper bound seven. No such row bounds the support sum by one
or two, even after exact positive rescaling. The max-min and unit-box rows
have singleton selector supports and cannot contain this support.

This census concerns literal retained rows. It does not exclude a shorter
bound obtained from a linear combination of rows. No optimizer or general
row-combination search was used for the diagnostic.
