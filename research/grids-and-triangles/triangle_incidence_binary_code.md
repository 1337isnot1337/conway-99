# Binary point-triangle kernel

Let G be an SRG(99,14,1,2), with adjacency matrix A. Let B be its 99 by
231 point-triangle incidence matrix. All ranks and kernels in this note
are over F2 unless stated otherwise. Set C = ker(B^T).

## Allowed weights

A support S of a word in C meets each triangle in zero or two points.
Each point of S therefore has exactly seven neighbors in S. If x is
outside S, its neighbors in S occur in pairs in the seven triangles
through x. Write s = |S| and k_x = |N(x) intersect S|. Thus every k_x is
even, and s is even because G[S] is 7-regular.

The constant vector is not in C: every column of B has three ones.
For a nonzero word, 0 < s < 99. For the centered real indicator
v = 1_S - (s/99)1, the Rayleigh quotient is

    v^T A v / (v^T v) = (693 - 14s)/(99 - s).

The two nonprincipal eigenvalues are 3 and -4. Comparing this quotient
with both gives 36 <= s <= 121/2. Hence 36 <= s <= 60.

Counting edges from S to its complement gives sum_x k_x = 7s. Count
common neighbors of pairs in S, then subtract those inside S. Adjacent
pairs have one common neighbor; other pairs have two. This gives

    sum_x binom(k_x,2) = s(2s-51)/2,
    sum_x k_x^2 = 2s(s-22).

The sums here and below range over x outside S. Put y_x = k_x/2. Then

    sum_x y_x = 7s/2,
    sum_x y_x^2 = s(s-22)/2.

Since y_x^2 and y_x have the same parity, s(s-29) is divisible by four.
As s is even, s-29 is odd, so s is divisible by four. Every nonzero
weight of C belongs to

    {36, 40, 44, 48, 52, 56, 60}.

This does not assert that C contains a nonzero word.

## An elementary rank consequence

The code C is doubly even. For u,v in C, the weight identity
wt(u+v)=wt(u)+wt(v)-2|supp(u) intersect supp(v)| shows u dot v = 0.
Thus C is self-orthogonal.

Over F2, BB^T = I+A and A^2=A. Reducing the known characteristic
polynomial of A gives t^45(t+1)^54. Idempotence implies rank(A)=54.
The image of this symmetric idempotent is nondegenerate for the usual
dot product: it is the orthogonal complement of ker(A), and its
intersection with ker(A) is zero. It is alternating because A has zero
diagonal. Since C is contained in ker(I+A)=im(A), a totally isotropic
subspace bound gives dim(C)<=27 and rank(B)>=72.

## Exact finite bound

Write A_w for the number of codewords of weight w, so A_0=1. For each
degree j from 1 through 99, define the binary Krawtchouk polynomial by

    K_j(w) = sum_l (-1)^l binom(w,l) binom(99-w,j-l).

For a linear code, summing the character (-1)^(u dot x) over x in C
gives |C| if u is in C-perp and zero otherwise. Summing this identity
over the weight-j words u proves

    K_j(0) + sum_w K_j(w) A_w >= 0.

The program `triangle_incidence_binary_code.py` prepares these 99
integer inequalities on the seven possible nonzero weights. One
bounded numerical LP call may propose a dual support. Exact rational
reconstruction must then check every multiplier and every dual column.
The code size is a power of two; any certified upper bound U implies
dim(C)<=floor(log2 U), hence rank(B)>=99-floor(log2 U).

The calculation concerns a necessary code condition. It cannot by
itself exclude the graph, since the zero-dimensional code satisfies
all of these inequalities.

The single bounded query has an exact primal and dual optimum

    |C| <= 5834276864000/755087 < 2^23.

Consequently dim(C)<=22 and rank_F2(B)>=77. The seven positive dual
multipliers, indexed by Krawtchouk degree, are:

| Degree | Multiplier |
| --- | --- |
| 2 | 869888/6795783 |
| 3 | 50861/24917871 |
| 4 | 973447/74753613 |
| 5 | 22664/74753613 |
| 6 | 23512/24917871 |
| 7 | 1355/74753613 |
| 8 | 307/8305957 |

For each of the seven allowed nonzero weights, the negative weighted
sum of the corresponding Krawtchouk values is exactly one. Multiplying
the 99 prepared inequalities by these nonnegative multipliers proves
the displayed bound. All other multipliers are zero.

The saved primal has seven positive rational entries and satisfies all
99 inequalities. Its objective equals the dual bound, so this finite
LP is solved exactly. Its fractional word counts do not define a code.
The query, cold replay and separate source review are in the
`triangle-incidence-binary-code-*` records under
`experiments/logs/grids-and-triangles/`.

## Forced dual words improve the rank bound to 82

The original seven-variable LP does not use the known words of C-perp.
Every triangle supplies a distinct word of weight three, so the dual
code contains at least 231 such words.

Two triangles through a common point c have a symmetric difference of
weight four. Its support induces two disjoint edges, because N(c)
induces seven disjoint edges. These two edges are determined by the
support, and their unique common-neighbor centers determine c. Hence
different intersecting triangle pairs give different words. There are
99*binom(7,2)=2079 of them.

Two disjoint triangles give a word of weight six. Cross edges between
the triangles form a matching: an outside point cannot meet two
points of a triangle, since their edge already has its unique common
neighbor inside the triangle. Their induced six-point support therefore
has exactly the two original triangles. Its decomposition is unique.
There are binom(231,2)-2079=24486 such words.

Let L_3=231, L_4=2079, L_6=24486, and let every other L_j be zero.
MacWilliams now gives the stronger linear inequalities

    sum_w (L_j-K_j(w)) A_w <= binom(99,j)-L_j.

Let y be the nonnegative dual above. Its seven column values are all
exactly one. Divide every y_j by

    1 + sum_j y_j L_j = 38999405/755087.

The result is an exact dual for these stronger inequalities, with bound

    |C| <= 1166855372800/7799881 < 2^18.

Therefore dim(C)<=17 and rank_F2(B)>=82. This strengthening requires no
new optimizer call. The separate checker
`triangle_incidence_binary_dual_word_bound.py` reconstructs the original
certificate, checks all seven strengthened dual columns, and checks
the triangle-pair word counts directly on the nine-vertex rook graph.
Its result is `triangle-incidence-binary-dual-word-bound.json` under
`experiments/logs/grids-and-triangles/`.

No optimum is claimed for the stronger LP. A zero-dimensional kernel
still satisfies the bound, so the existence question remains open.
