# The retained decorated feature lattice has no new congruence

## Result

The complete retained decorated model has 200 moment rows and 17,920 distinct columns. Its integer column lattice is exactly \(\mathbb Z^{200}\). The saved columns contain a 200 by 200 integer minor with determinant 1.

The orbit-total variables must be multiples of 720 in an actual graph. After division by 720, all 200 right-hand-side forms already have integer coefficients in the induced graph counts. This lattice test therefore supplies no new congruence for the current point, or for any integer induced-count vector.

This statement does not establish a nonnegative integer solution. Nonnegative integer membership is a separate finite semigroup problem.

## The correct integer units

The root is a specified ordered independent six-set. Its root relabeling group is \(S_6\), of order 720. A full state records every vertex with at least three neighbors in the root, its root-neighborhood mask, and the induced graph on those vertices.

Fix a labelled state \(A\). Its stabilizer in \(S_6\) acts on the injective ordered root embeddings realizing \(A\) by precomposition. This action is free: a nonidentity permutation cannot fix an injective ordered tuple. If the stabilizer has order \(s_A\), the exact number of embeddings realizing \(A\) is a multiple of \(s_A\).

The orbit of \(A\) contains \(720/s_A\) labelled states. Root relabeling gives a bijection between their embedding sets. The total mass \(w_O\) of the orbit is consequently a multiple of 720. Equivalently, each unordered independent six-set contributes its 720 orderings to one state orbit.

This argument uses the symmetry of the labels, with no assumption that the hypothetical graph has a nontrivial automorphism.

When full state columns have identical feature columns, their orbit-total masses are added. The sum remains a multiple of 720. Conversely, at this finite-model level an integer total for a distinct column can be assigned to one of its retained full representatives. Deduplication therefore does not introduce another divisibility condition.

Automorphisms of the entire induced core that move the chosen roots do not give an additional unit by this argument. Such a move can change which outside vertices are high relative to the new roots, so it need not preserve the complete-state property.

## Why the right-hand sides have the same unit

A moment row is an orbit \(R\) of a partial induced pattern with at most four high vertices. Distinct high masks make its fixed-labelled-root indicator sum equal to

\[
|\operatorname{Aut}(F)|\,N_F,
\]

where \(F\) is the complete literal graph of the pattern and \(N_F\) is its unlabelled induced count. Summing over the row orbit multiplies this by \(|R|\).

The root stabilizer has order \(720/|R|\). Every such root automorphism lifts uniquely to the high vertices and is an automorphism of \(F\). Thus

\[
\frac{720}{|R|}\mid |\operatorname{Aut}(F)|,\qquad
720\mid |R|\,|\operatorname{Aut}(F)|.
\]

This is a coefficientwise property. It is checked before substituting the saved integer count point.

Writing \(w=720t\) transforms the moment equations into \(Ct=b/720\), where \(t\) must be nonnegative and integer in a graph.

## The unimodular minor

For every row pattern, select the retained full state consisting of that pattern itself. All 200 selected states survive the principal-projector and integer-incidence filters.

Order both rows and these selected columns by their number of high vertices. A larger pattern cannot occur in a smaller selected state. Within equal population, a pattern can occur only in its own rooted induced-pattern orbit, once. The resulting minor is upper triangular with every diagonal entry 1.

The standalone checker verifies the selected column identities against both saved feature matrices, checks 31,837 degree-zero conditions, checks the full triangular form after reordering, and verifies that every chosen full representative is retained. Its determinant is 1, so the full column lattice has index 1 and all 200 Smith invariants are 1. No Hermite or Smith computation on a reduced positive support is needed.

## Exact replay and scope

The checker uses the frozen refined and original feature arrays, the direct induced moment forms, and the immutable 48-cut integer count point. It checks all 200 right-hand-side divisibilities and values. It imports no query helper and runs no optimizer or domain census.

The recovered positive rational solution has common denominator 988761395399693539. That denominator belongs to one selected positive support. It is not a congruence obstruction for the complete column set.

The next possible integer test would have to use nonnegativity or further coupling between states. The present result removes the full-column modular/Hermite screen as a source of a new obstruction for this model.
