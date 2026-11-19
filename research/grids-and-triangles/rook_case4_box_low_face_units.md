# A capacity cut from the 191 checked H27 boxes

The complete H27 branch cover has 2,835 weighted patterns. Original native
capacities reject 2,391 patterns. The first exact propagation stage rejects
184 of the remaining 444 branches. Full-row propagation rejects another 69
and leaves 191 boxes. Every rejection and surviving fixed point has a separate
accepted cold record. A surviving box is an outer approximation, not a
feasible incidence construction.

The sum of original Gram rows 214, 344, and 582 has right-hand side 3.
After substituting only the 112 proved zero coordinates, its coefficients
are 1 on 26 columns, 2 on nine columns, and 3 on column 764. Set

\[
H=\sum_{a\in H_{27}}x_a,\qquad
Q=x_{260}+x_{399}+x_{403}+x_{406}+x_{761}+x_{762}
  +x_{763}+x_{764}+x_{765}+x_{803}.
\]

Here (H_{27}) is the support of the odd coefficients; it includes 764.
The exact identity is

\[
H+2Q=3.
\]

Thus a nonnegative Boolean solution has (H=1) or (H=3). The 191 final
boxes split into 54 boxes with (H=1), comprising one weight-three singleton
and 53 weight-one/weight-two pairs, and 137 boxes with (H=3).

All 54 boxes with (H=1) set (x_{23}=0). This is the only common zero
among their 1,102 surviving coordinates; there is no common one. For the
other 137 boxes, (H=3) and the Boolean bound (x_{23}\le1) suffices.
Consequently every integer case4 realization satisfies

\[
H-2x_{23}\ge1.
\]

Using (H+2Q=3), the same inequality has the shorter capacity form

\[
\boxed{x_{23}+x_{260}+x_{399}+x_{403}+x_{406}+x_{761}+x_{762}
 +x_{763}+x_{764}+x_{765}+x_{803}\le1.}
\]

This is an inequality on eleven distinct original selector coordinates.
It does not assert that (x_{23}=0) globally. The lower bound zero follows
from the selector boxes.

The latest independently accepted rational point has denominator
3,461,944,222, (H=Q=1), and

\[
x_{23}=37,621,464/3,461,944,222.
\]

It violates the signed cut by (75,242,928/3,461,944,222), or equivalently
the capacity cut by (37,621,464/3,461,944,222). The conditional-unit scan
does not invoke an optimizer. The generic 191-box LP is left unrun because
this exact finite scan already separates its intended source point.

`rook_case4_box_low_face_units.py` restores the cold-bound boxes and expands
the three original Gram rows on all 1,214 coordinates. Its helper's LP
methods are not invoked. The separate
`rook_case4_box_low_face_units_replay.py` imports neither source. It checks
all 260 forward/cold record bindings, authenticates all 191 final box states,
repeats the new conditional intersection and point arithmetic, and checks
both cut forms on every box. It also checks the coefficient identity linking
the signed and capacity rows, including the removed known-zero terms.
No prior propagation or trace-reason check is repeated.

The inputs, complete low/high partition, all box minima, exact point values,
and source hashes are in `rook-case4-box-low-face-scan01`. This result cuts
the fractional point. It does not exclude case4 or resolve Conway99.
