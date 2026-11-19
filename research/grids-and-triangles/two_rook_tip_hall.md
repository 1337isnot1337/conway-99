# Exact local constraints on the nine matching-edge tips

## Scope and result

Suppose an SRG(99,14,1,2) contains two disjoint induced rook grids whose
matching is a rook isomorphism. Label both grids by
`p=3r+c`, with `r,c` in `{0,1,2}`, so their matching is the identity.
The forced exterior incidence consists of nine vertices `z_p` with core
neighbors `(R_p,S_p)`, and two vertices for each ordered rook-nonadjacent
pair `(p,q)`, both with core neighbors `(R_p,S_q)`.

This note gives necessary constraints on the graph induced by the nine
vertices `z_p`. It does **not** assume that this graph is a rook grid and
does not exclude the two-grid configuration.

At each fixed tip there are 256 possible neighborhoods among the other
eight tips. Exactly 103 survive the mixed core equations and the local
consequence that a tip cannot meet both vertices of a duplicate pair.
Each of the other 153 patterns has a saved integer Hall cut. Each of the
103 admitted patterns has a saved binary matrix witness. The earlier
inequality `d_near <= d_far` admits 163 patterns, so the full local check
excludes 60 additional patterns.

Nine explicit inequalities characterize these 103 patterns. This
equivalence is an exact finite statement about the local projection;
an admitted pattern need not extend to the full graph.

## Why duplicate-pair packing is necessary

The two vertices with core neighbors `(R_p,S_q)` are nonadjacent. They
already have two common neighbors in the core. Their exterior
neighborhoods are therefore disjoint. In particular:

- A tip meets at most one member of any duplicate pair.
- Edges between two duplicate pairs form a partial matching.
- A tip `z_t` cannot meet a vertex whose signature contains `R_t` or
  `S_t`. Such an edge would exceed the common-neighbor quota at the
  corresponding core vertex.

These conclusions justify the duplicate-pair packing clauses in
`two_rook_iso_pair_integer.py`. Its remaining mixed equations are the
entrywise identity

\[
XC=2J-(B+I)X,
\]

where `B` is the 18-vertex core adjacency matrix, `X` its forced exterior
incidence, and `C` the unknown exterior adjacency matrix. Each exterior
vertex has degree 12 in `C`. Candidate edges are removed only when they
already exceed a core common-neighbor quota or join a duplicate pair.

## The local matrix at one tip

Fix `t=0`, and write `z_p` for the binary indicator that tip 0 is adjacent
to tip `p`, for `p=1,...,8`. The same symbol denotes a vertex elsewhere;
in the formulas below it always denotes this binary indicator.

Let `M[p,q]` count neighbors of tip 0 in the duplicate pair with core
signature `(R_p,S_q)`. Duplicate packing gives `M[p,q]` in `{0,1}`.
The only possible cells satisfy `p,q != 0`, `p != q`, and `p,q` are
rook-nonadjacent. The mixed equations give both margins:

\[
\sum_q M[p,q]=\sum_q M[q,p]=d_p,
\qquad d_p=2-A_{0p}-z_p,
\]

where `A` is the nine-vertex rook adjacency matrix. Thus the near points
`N={1,2,3,6}` have demand `1-z_p`, and the far points
`F={4,5,7,8}` have demand `2-z_p`.

For any sets `S,T` of the eight points, a necessary Hall inequality is

\[
\sum_{p\in S}d_p\ \le\
\sum_{q\in T}d_q+
\#\{(p,q):p\in S,\ q\notin T,\ (p,q)\text{ is a possible cell}\}.
\]

The certificate stores `S,T` and both integer sides for every forbidden
mask. No optimization library or numerical tolerance is used to replay
these contradictions.

## Nine inequalities suffice for this projection

Write `D=sum(z_p)` and `z(L)=sum_{p in L}z_p`. The necessary inequalities
are:

1. The existing near/far inequality,

   \[
   z_1+z_2+z_3+z_6\le z_4+z_5+z_7+z_8.
   \]

2. For each of the four rook lines not containing 0,
   `L={3,4,5},{6,7,8},{1,4,7},{2,5,8}`,

   \[
   D-2z(L)\le2.
   \]

3. The four implications written as linear inequalities,

   \[
   z_1+z_3-z_8\le1,\quad z_2+z_3-z_7\le1,
   \]
   \[
   z_1+z_6-z_5\le1,\quad z_2+z_6-z_4\le1.
   \]

For the first inequality, far rows require `8-z(F)` entries. At most
four lie in far columns, because only four ordered cells join two far
points. Near columns can supply at most `4-z(N)` more.

For a line `L` in the second group, there are no possible cells within
`L`. Its row demand is `5-z(L)`, and the total demand in the other
columns is `7-D+z(L)`. Comparing these gives the stated inequality.

For the third group, consider row 8. Its only possible columns are
1, 3, and 4. Those columns can supply at most
`(1-z_1)+(1-z_3)+1` entries, while row 8 requires `2-z_8`.
The other three inequalities follow in the same way.

The first five inequalities admit 107 masks. The last four remove
exactly four more, leaving the 103 masks for which explicit integral
matrices are saved. For example, neighborhood `{1,4,5}` passes the
near/far inequality but fails the line inequality for `{6,7,8}`:
those three rows require five entries and the remaining columns can
supply only four.

## Sound duplicate-label symmetry breaking

For each duplicate pair, compare the two binary adjacency vectors to
the nine **fixed** tips, in increasing tip order. The pair can be
relabelled so the first vector is lexicographically at least the
second. Swapping one duplicate pair does not change any other pair's
coordinates to these fixed tips. All 36 orders can therefore be imposed
simultaneously on a labelled representative of every completion. This
does not assert an automorphism of the completed graph.

The two vectors have disjoint supports. Consequently the order is
equivalent to the clauses

\[
\neg b_j\ \lor\ \bigvee_{k<j}a_k.
\]

The two ineligible tip coordinates of each duplicate pair are zero in
both vectors and may be omitted. This gives seven clauses per pair,
or 252 clauses. Equal vectors must both be zero. Ordering the full
81-coordinate exterior rows would require a different justification.

## Reproduction and use as SAT clauses

The standalone exact verifier is
`experiments/workspace/two_rook_tip_hall_audit.py`; its certificate is
`experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json`.

```sh
python experiments/workspace/two_rook_tip_hall_audit.py \
  --certificate experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json
```

Add `--write` to regenerate all certificates. Generation uses an integer
augmenting-path flow routine and checks every subset for Hall cuts.
Replay checks the saved flows and cuts directly. It also verifies the
equivalence to the nine inequalities on all 256 masks and checks the
nine coordinate translations used to move any tip to 0.

For the mask-table SAT form, bit `p-1` is the value of `z_p`. For a
forbidden mask, use the eight-literal clause that disagrees with at
least one specified bit: use `-edge(0,p)` for a 1-bit and `edge(0,p)`
for a 0-bit. Translate the point labels by subtracting the row and
column of the chosen tip modulo 3. This gives 153 clauses per tip,
or 1,377 clauses in total. These clauses are consequences of the
existing local equations and packing, so they are propagation aids,
not additional assumptions.
