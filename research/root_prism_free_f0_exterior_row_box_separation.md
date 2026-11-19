# Complete row-capacity check of the replacement incidence

The replacement 60-triple incidence fails three necessary exterior-row
capacity tests. Each failure has a direct integer certificate. The other
57 rows have exact rational witnesses for their separate box relaxations.
All 60 rows were processed in 2.053 seconds. No incidence formula was
changed and no SAT query was made during this pass.

This excludes extension of that saved incidence to an exterior graph.
It does not exclude component zero, the split case, or a hypothetical
Conway99 graph.

## Scope and row equations

The setting is the globally prism-free and $F$-free split $18+18$ shell,
with the first component equal to the catalogued component zero. The
complete first-component domain contains 480 distinct triples. A valid
incidence selects 60 of them. The second component and its incidence
remain unspecified.

Let $A$ be the 18-point component adjacency matrix and let $h_a$ be a
selected triple column. The corresponding exterior vertex has eight
neighbors in the eventual 60-point exterior graph. Its neighbor row
must satisfy

$$
\sum_{b\in N(a)} h_b y_{ab}=q_a,
\qquad q_a=2\mathbf 1-h_a-Ah_a,
\qquad 0\leq y_{ab}\leq z_b.
$$

Here $N(a)$ is the complete universally eligible neighbor set. Its
definition uses triple intersection at most one and both zero-quota
tests. The 480-vertex eligibility graph has 68,394 edges. No unproved
symmetry or fixed second incidence enters this graph. The sum of the
18 row quotas is 24, so the displayed equations imply
$\sum_b y_{ab}=8$.

For an integer vector $v$, define

$$
d=v^Tq_a,\qquad c_b=\max(v^Th_b,0).
$$

Every actual graph satisfies the universal selector inequality

$$
\sum_{b\in N(a)}c_bz_b\geq d z_a
$$

when $d>0$. If $z_a=1$, this follows by taking the scalar product of
the row equations with $v$, discarding nonpositive products, and using
$y_{ab}\leq z_b$. If $z_a=0$, the left side is nonnegative.

For a proposed selected set $S$ containing $a$, the strict integer gap

$$
d-\sum_{b\in N(a)\cap S}c_b>0
$$

therefore proves that this incidence cannot supply the row at $a$.
The weaker cover clause is also necessary:

$$
\neg z_a\ \lor\ \bigvee_{\substack{b\in N(a)\setminus S\\c_b>0}} z_b.
$$

Falsifying this clause leaves total positive capacity strictly below
the required demand. The clause is valid for every incidence selection;
it does not fix the saved selection $S$.

## Numerical proposals and exact acceptance

One bounded dual LP was called for each selected target. It maximized

$$
q_a^Tv-\sum_{b\in N(a)\cap S}s_b
$$

subject to $-1\leq v_i\leq1$, $s_b\geq0$, and
$s_b\geq h_b^Tv$. Numerical values only proposed vectors. A cut was
accepted after an integer reconstruction and a direct exact check of
the strict capacity gap over the complete eligible domain.

When no integer obstruction was found, dual marginals proposed a row
box witness. Such a witness was accepted only after rational
reconstruction verified every one of the 18 equations, all bounds
$0\leq y_{ab}\leq1$, and the sum of eight. No claim relies on the
numerical optimality status alone.

The run processed targets in increasing signature-index order. Its
60-second total limit was not reached. Every row has an exact terminal
status; there are no unvisited or numerical-only rows.

## Three integer obstructions

Signature indices are zero-based in the complete 480-column domain.

| Target | Integer demand | Positive capacity in the saved incidence | Strict gap | Positive terms in the full inequality | Literals in the base cover clause |
| --- | ---: | ---: | ---: | ---: | ---: |
| 110 | 5 | 4 | 1 | 86 | 84 |
| 349 | 3 | 0 | 3 | 38 | 39 |
| 479 | 10 | 7 | 3 | 96 | 94 |

The exact vectors, in component vertex order $0,\ldots,17$, are:

```text
110: (-3,-3,3,3,-1,-1,-1,-3,0,2,-3,0,-1,-2,2,2,-2,-2)
349: (-2,-2,1,1,-2,1,-2,-2,-2,1,-2,1,1,-2,1,1,1,-2)
479: (1,1,1,-1,-3,-3,1,1,2,0,-3,-3,3,-1,2,-3,-3,-2)
```

The second vector has a simple counting interpretation. Put
$T=\{2,3,5,9,11,12,14,15,16\}$. Its entries are one on $T$ and
minus two elsewhere. For target 349, $q_a(T)=17$. Eight neighbor
triples can supply at most 16 incidences into $T$ unless one triple
lies wholly inside $T$. There are exactly 38 eligible such triples,
and the saved incidence selects none. Thus this row is impossible.

Each of the three inequalities was transported through all 12 verified
core relabelings. Direct integer products were recomputed after each
transport. These are changes of labels of a necessary inequality,
not automorphism assumptions about an unknown completed graph.
The result stores all 36 full weighted inequalities and all 36 distinct
cover clauses. The cover clauses have 2,604 literal occurrences in total.

## Separate rational row witnesses

The remaining 57 rows each have an exact rational box witness. Twelve
are binary. Eleven of those binary rows also have pairwise triple
intersection at most one; the binary witness for target 289 does not.
The other 45 witnesses are fractional.

These witnesses establish feasibility of separate row relaxations only.
They do not impose symmetry between different exterior rows, all
outside common-neighbor equations, or the missing second incidence.
They therefore do not construct an exterior graph. Conversely, one
of the three exact failed rows already suffices to reject extension of
the saved 60-triple incidence.

## Replay and independent review

The frozen driver is
`experiments/workspace/root_prism_free_f0_exterior_row_box_separation.py`.
Its source SHA256 is
`60366da662c74ee8d3ca367dc532c16b652952101fa5725a3248fc5a53a773bd`.

The complete result is
`experiments/logs/root-prism-free/f0-exterior-row-box-separation-run01/result.json`,
SHA256
`328fddcc22b7ee2bfdd2a5c93189cef12240a56eee5804073a0848e64e7a749f`.
Its standalone replay reconstructs the complete domain and checks all
integer certificates, rational witnesses, and transports without
calling an optimizer or SAT solver.

An independent standard-library review reconstructed all 480 triples
and all 68,394 eligible edges, checked the selected incidence Gram
matrix, and directly verified the three obstructions, all 36 transports,
and all 57 rational witnesses. Its report is
`experiments/logs/root-prism-free/f0-exterior-row-box-independent-review.json`,
SHA256
`332678fc78ca9bdd32bd767e122c0abd5c092a665abae478caea5078a82abeed`.

The result package leaves the prior incidence query, its formula, and
both saved incidence points unchanged. A subsequent free-selector loop
is separate work and is not part of this completed pass.
