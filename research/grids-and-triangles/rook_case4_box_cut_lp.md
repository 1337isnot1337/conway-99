# One LP continuation with the box-cover capacity

The latest accepted case4 point satisfies five appended parity inequalities.
It violates the independently checked capacity

\[
x_{23}+x_{260}+x_{399}+x_{403}+x_{406}+x_{761}+x_{762}
+x_{763}+x_{764}+x_{765}+x_{803}\le1.
\]

The new model retains all 167,120 old extended rows and appends this one row
with lower bound zero and upper bound one. It has 167,121 rows, 10,769,766
nonzero coefficients, and 1,103 variables: 1,102 surviving selectors and
the existing max-min variable. The 112 proved zeros are unchanged.

Every original native constraint and coordinate-cover obligation remains
accounted for by the frozen prefix. The complete retained cover pool has
164,044 rows. Numerical generation starts with all native rows, inherited
fixed rows, the max-min rows, and all six appended cuts. The latest accepted
numerical record has no carried cover rows, giving 3,077 initially active
rows. No selector is fixed from the previous point or its basis.

## Two different proof types

The first five registry entries retain their original Gram-row parity
certificates unchanged. The sixth has proof kind
`cold_complete_branch_box_capacity`. Its verifier binds the completed
260-branch forward and cold results, the 191 authenticated final boxes, and
the separate low-face arithmetic replay. It checks the three-Gram identity
and the new capacity maximum on every box. The cut is not presented as a
parity inequality.

Its validity depends on the complete branch cover, including the proved
inequalities used during propagation. Those accepted branch proofs are
reused; preparation does not repeat propagation or its original trace
reasons. The separate note `rook_case4_box_low_face_units.md` states the
conditional-unit argument and the equivalent signed row.

## Reused numerical and exact routines

The adapter is reproduced by
`rook_case4_box_cut_lp_adapter_reuse.py`. Its complete ledger compares every
retained function with the reviewed v4 source. Twenty-three functions are
identical in text and AST. The two changes are the registry's explicit proof
dispatch and acceptance metadata that counts five parity rows and one box
row. The numerical iteration, finite-box arithmetic, dynamic saved-basis
reconstruction, complete-point inspector, and cold routines retain their
previous implementations. The exact arithmetic helper remains a frozen
import. No old module or result is modified.

The initial point remains a five-cut point until a new candidate passes all
six rows. It supplies proof provenance; it is not an incidence assignment
or a restriction on the new solve.

## Preparation and execution contract

Preparation checks the exact source-point deficit and the proof registry.
A separate native preflight loads the cached arrays, compares every old
array prefix with the accepted five-cut point's matrix bindings, and checks
the appended row. It then constructs the initial native LP and compares all
its coefficients, bounds, objective coefficients, and variable domains with
the exact data. Preflight makes no optimizer call.

Production requires a later source and preparation gate. Its fixed scope is
one numerical generation round, at most 30 native calls and 120 cumulative
native seconds, inside a 180-second numerical stage. One 60-second exact
stage and one 60-second independent cold stage follow. The complete owner
has a 360-second hard limit. No second round or separation search is exposed.

The exact stage may return a finite-box contradiction, a certified zero
face, or a rational point. A basis is only a proposal: a point must pass all
167,121 rows, the original 2,271 native rows, all 178,533 original covers,
and every original-coordinate obligation. An incomplete numerical result,
failed reconstruction, or incomplete cold check remains unresolved. Saved
proposals and terminal artifacts are retained without an automatic retry.

The generic 191-box LP is unrun. Its intended point was already rejected by
the finite conditional-unit scan, so that older separation query is no
longer needed at this point.
