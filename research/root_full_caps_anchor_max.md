# Choosing a near anchor of maximum matching count

This gives a new exhaustive eleven-case normalization for the mandatory
rooted model. It adds only small cardinality clauses. No full formula
using these clauses has been built or solved at this checkpoint.

The coverage statement concerns the **union of the eleven new cases**.
It does not preserve every original partition case individually. A graph
can move to a different partition case when the maximizing anchor is
chosen. This differs from the frozen stabilizer lex overlay, which
preserves every original case separately. The maximum-anchor clauses
were not added to that pilot.

## The count and the label choice

Fix a root. Its fourteen near vertices occur in seven mate pairs. Write
the mate of near label `a` as `a^1`. The exterior vertex `x_{a,b}` exists
uniquely whenever `a` and `b` belong to different mate pairs.

For any near vertex `a`, its twelve exterior neighbors are

\[
F_a=\{x_{a,b}:b\ne a,a^1\}.
\]

The induced graph on `F_a` is a perfect matching `M_a`. Indeed, the mixed
common-neighbor equation for an exterior point in `F_a` requires exactly
one neighbor in `F_a`.

Define

\[
c_a=\sum_{\{b,b^1\}\text{ a near mate pair},\ b\notin\{a,a^1\}}
       A_{x_{a,b},x_{a,b^1}}.
\]

There are six terms. This counts the edges of `M_a` that also belong to
the reference matching on its twelve endpoint labels. If the union of
the two matchings has alternating half-length partition `lambda_a`,
then `c_a` is exactly the number of parts equal to one in `lambda_a`.

Choose a near vertex `a` attaining `max_b c_b`. A signed permutation of
the seven mate axes sends `a` to label 0 and its mate to label 1. Next,
normalize `M_0` using a signed permutation of the other six axes, exactly
as in the original matching reduction. The counts are merely permuted
by these coordinate changes. Consequently the resulting partition
`lambda` satisfies

\[
c_b\leq c_0=m_1(\lambda)\qquad\text{for every near label }b.
\]

Every rooted graph has such a labeling. This uses no automorphism of the
completed graph and no grid-existence assumption. Ties need no extra
choice rule: each maximizing anchor gives one of the covered cases.

The stabilizer generators from `root_full_caps_lex.md` preserve these
bounds. They fix near label 0 and permute the other count supports. The
two reductions can therefore be combined in a future model, provided its
coverage statement uses the new maximum-anchor convention.

## Exact clauses and size

For each of the fourteen rows of six edge variables, forbid every
`m_1(lambda)+1` element subset from being simultaneously true. This is a
direct cardinality encoding with no auxiliary variables.

| Case | Partition | Bound on every `c_b` | Added clauses |
| --- | --- | ---: | ---: |
| 0 | 1+1+1+1+1+1 | 6 | 0 |
| 1 | 1+1+1+1+2 | 4 | 84 |
| 2 | 1+1+1+3 | 3 | 210 |
| 3 | 1+1+2+2 | 2 | 280 |
| 4 | 1+1+4 | 2 | 280 |
| 5 | 1+2+3 | 1 | 210 |
| 6 | 1+5 | 1 | 210 |
| 7 | 2+2+2 | 0 | 84 |
| 8 | 2+4 | 0 | 84 |
| 9 | 3+3 | 0 | 84 |
| 10 | 6 | 0 | 84 |

The fourteen supports are disjoint and contain exactly the 84
sign-changing side edges of the 21 four-point cells. Thus the last four
maximum-anchor cases set all those side variables to zero. No diagonal
cell edge is forbidden by this argument.

## Domain audit and controls

The standard-library program independently reconstructs the 84 exterior
labels and 3,486 primary edge indices and reproduces the frozen root
model's domain hash. It exports all fourteen count supports and every
new clause.

It enumerates all 10,395 perfect matchings of twelve points and checks
that reference edges equal one-parts of the alternating partition. Their
count distribution is:

| Reference matching edges | Matchings |
| ---: | ---: |
| 0 | 6,040 |
| 1 | 3,264 |
| 2 | 900 |
| 3 | 160 |
| 4 | 30 |
| 6 | 1 |

Five reference edges cannot occur: the two unused endpoints would form
the sixth reference edge.

The support action is checked under the seven axis flips and six
adjacent axis interchanges that generate all signed near-label
permutations. An explicit normalization transports a chosen maximizing
anchor to 0, then transports its matching to the canonical partition.
It verifies all fourteen counts before and after the change.

There are 154 normalization controls: each of fourteen anchor choices
combined with each of eleven matching types. These controls satisfy all
fourteen fiber-matching conditions. They are not asserted to be SRG
completions. Four further controls normalize a directly constructed
nine-vertex rook graph and verify all degree and pair equations after
relabeling. Finally, all 64 Boolean assignments to six bits are checked
for each of the six possible count bounds, giving 384 direct cardinality
checks. No solver is used.

Files:

- `experiments/workspace/root_full_caps_anchor_max.py`
- `experiments/logs/root-full-caps-anchor-max/anchor-max-certificate.json`
- `experiments/logs/root-full-caps-anchor-max/anchor-max-generation.log`
- `experiments/logs/root-full-caps-anchor-max/anchor-max-replay.log`

Replay:

```sh
python experiments/workspace/root_full_caps_anchor_max.py \
  --certificate experiments/logs/root-full-caps-anchor-max/anchor-max-certificate.json
```

These files establish the new normalization and its exact clause domain.
They exclude no case and make no claim about its effect on search time.
