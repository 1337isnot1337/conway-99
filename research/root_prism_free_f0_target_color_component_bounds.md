# Componentwise target-color bounds

This is an uninstalled corollary of the accepted [twelve-bound proof](root_prism_free_f0_target_color_twelve_bound.md). It changes no frozen source, native model, or query.

Let E0,E1 be the two connected components of the complete 84-edge target graph, and let P0,P1 be their private vertices. The accepted certificate records 42 edges and 36 private vertices in each component, belonging to six private colors. Every Boolean completion satisfies
\[
\sum_{e\in E_i}y_e\le\sum_{a\in P_i}x_a\le6
\qquad(i=0,1).
\tag{1}
\]

## Proof

Apply the existing charging proof separately inside a target component. Selected private components are stars, edges, or singletons. Each has at most one shared attachment edge. A private component K contributes at most |K|-1 internal edges and one attachment, so at most |K| edges in total. There are no shared-to-shared target edges. All edges charged here lie inside the same target component; the partition has no crossing target edge.

Summing these charges proves the first inequality in (1). The six private colors have original Gram equations with right-hand side one. Their target supports are disjoint, and dropping the non-target, nonnegative selector terms gives the second inequality.

The two homogeneous inequalities imply both component bounds of six. Summing gives the proposed global target bound of twelve. This implication from the homogeneous rows and the six Gram inequalities is linear, although the validity proof of each homogeneous row uses Boolean selections.

The two components have different private colors. Their shared vertices use the same six shared colors in pairs across the components. This coupling does not invalidate the charging argument, because each attachment is charged at its private endpoint and no target edge joins the components.

## Exact uninstalled row descriptions

An original edge e is native variable 540+e; selectors retain their original IDs. For each component, the homogeneous row key is
[-36,0, sorted([[a,-1] for a in P_i] + [[540+e,1] for e in E_i])].
The lower bound -36 is a safe Boolean box bound. Each row has 78 terms.

The corresponding constant row key is [0,6,[[540+e,1] for e in E_i]], with edges ascending. The two constant rows together have 84 terms. All SHA-256 values below use compact JSON with no trailing newline.

### Component 0

Private selector IDs:

```text
0, 1, 8, 9, 16, 19, 33, 35, 37, 72, 73, 88, 91, 96, 99, 104, 107, 109, 154, 155, 176, 177, 180, 202, 203, 210, 211, 217, 233, 236, 278, 285, 287, 306, 325, 327
```

Original target edge IDs:

```text
30, 193, 363, 471, 2409, 2499, 2817, 2962, 4917, 5101, 5858, 5871, 9985, 9990, 10523, 10524, 10554, 11025, 20650, 24553, 25269, 25351, 26389, 27146, 27249, 38681, 38813, 38864, 38887, 42814, 42831, 43001, 43509, 47548, 47704, 47805, 48938, 48996, 49076, 57851, 57869, 58653
```

The homogeneous key has SHA-256 9f6a8043366cccc1158c6c9ba27231105d4badc0b740528bf3dcef715f405b6e; the constant key has SHA-256 2525371082e4a28074dd3435213ca383513886c9cf4b7c4c6a44882e53354d7b.

### Component 1

Private selector IDs:

```text
4, 5, 12, 13, 20, 23, 42, 54, 65, 76, 77, 92, 95, 100, 103, 114, 126, 136, 158, 159, 165, 189, 198, 206, 207, 214, 215, 222, 245, 249, 270, 283, 295, 311, 323, 333
```

Original target edge IDs:

```text
1241, 1385, 1564, 1675, 3650, 3731, 4042, 4181, 6155, 6306, 7084, 7107, 12391, 12392, 12449, 15559, 18563, 18571, 21635, 25474, 26195, 26276, 27345, 28097, 28202, 39516, 39624, 39694, 39720, 40802, 45135, 46811, 46815, 48205, 48358, 48450, 49535, 49611, 49682, 56904, 59873, 59882
```

The homogeneous key has SHA-256 130c8bdd54665dc0dfcdf7180236142e65d43f0417f72555a84f436a8ffa78e1; the constant key has SHA-256 8fdc872eea8628b8fe3739c21cc9d34ddf107fb8bd4d062a81e644e8ab4bfa23.

## What the refinement establishes

The global twelve-bound alone can lose component information in a continuous color/activation relaxation. To see this exactly, give each private target selector value 1/6 and each shared target selector value 1/2. Set every E0 edge to 1/6 and every E1 edge to 5/42. All eighteen target-color equations and all target endpoint activations hold. The edge totals are seven and five, hence twelve globally. Component zero violates (1).

This is only a restricted fractional control. The other original Gram equations, triangle definitions, mixed equations, all prior cuts, and full native feasibility are not asserted. It does not prove nonredundancy against the complete current model.

The previous attaining Boolean witness restricts to six target edges in each component, so neither constant six-bound can be lowered using only the stated at-most-one target-color/activation relaxation.

## Immutable premises and boundary

The structural report is experiments/logs/root-prism-free/f0-target-color-twelve-certificate01.json, Git c418e402626e0a2d216422ac62bef6165d962191, SHA-256 ba987fe7ff39fe088bc66cb2fbd9f81c4e17a0b457af70642bc1f61d37d6d1e3. The root acceptance is f0-target-color-twelve-root-acceptance01.json, Git f71469c7a5b9ac380ba6159f15a4121628028461, SHA-256 10dd8fbfd42dc695bae9c83a3f61f7b9694d940a092e8e67e034781fd3eb0ebc.

The lists above are a projection of that existing report. Small direct metadata checks confirm the two vertex/edge partitions, no crossing edge, and the 36 private vertices and six private colors per component. No source main, signature enumeration, assignment search, model build, or solver was run for this corollary.

The frozen three-family append continues to use its accepted single global_target_total row. These two homogeneous inequalities and their constant corollaries are retained only as a possible later formulation change.
