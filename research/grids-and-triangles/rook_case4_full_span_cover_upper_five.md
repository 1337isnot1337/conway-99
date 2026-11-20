# Case4: the new 42-column parity cover has total at most five

This is a necessary-condition result for the complete original 1,214-column incidence domain. It does not exclude case4 and does not construct a graph.

Let H be the 42-column support in the checked full-span separator. Its sum of 50 original Gram equalities has right-hand side 81. On the proved zero face, its coefficient vector gives

    sum_{a in H} x_a + 2 F(x) = 81,

where F has nonnegative integer coefficients. Only the six proved zeros 126, 465, 966, 970, 973, 977 are required to remove odd coefficients outside H. Thus sum_H x is positive and odd for every nonnegative integer incidence.

## Four original rows give the upper bound

Add original Gram rows 368, 411, 431 and 590, for core pairs (12,26), (14,26), (15,26), (26,31). Their quotas are 1, 1, 1 and 2. Every member of H occurs at least once. Subtracting the indicator of H from their full 1,214-coordinate coefficient sum gives a nonnegative integer vector r. The exact identity is

    sum_H x + sum_a r_a x_a = 5.

The certificate records every coefficient. There are 38 positive residual coordinates before known-zero substitution. Therefore sum_H x <= 5 holds already for nonnegative real solutions of the original Gram equations. Combining it with the parity equation leaves exactly the necessary alternatives

    sum_H x in {1, 3, 5}.

This is stronger than the single diagonal quota sum_H x <= 7. No optimization is used.

## Conditional face when the total is five

If sum_H x = 5, nonnegativity forces every positive-residual coordinate to zero. Seven were already among the 112 globally proved zeros, leaving 31 new conditional zeros. Five lie in H: 28, 80, 807, 1016, 1017. These 31 zeros are conditional and must not be promoted to global zeros without excluding the alternatives one and three.

After substituting the 112 global zeros, the residual is the sum of 21 unit terms and ten doubled terms. Its only possible values are 4, 2, 0 in the respective alternatives H=1,3,5.

## Complete small native upper-capacity projection

A separate integer-only depth-first enumeration considers every subset of H of size at most seven. It checks the original Gram upper capacities, signature at-most-one rows, core-triple at-most-one rows and Gram conflict clauses. These project to 142 nontrivial rows, or 93 after exact duplicate removal. Rows of upper bound at least seven are redundant within the enumerated cardinality range.

The numbers of retained subsets of sizes zero through seven are

    1, 42, 524, 2302, 2903, 996, 0, 0.

The traversal visited 6,768 accepted prefixes and 68,995 attempted extensions, under declared bounds of one million prefixes and ten seconds. It completed. The certificate includes every retained subset and row provenance.

Consequently every original Boolean incidence has one of 3,340 necessary H patterns: 42 singletons, 2,302 triples or 996 five-sets. These patterns need not extend to an incidence. This enumeration does not replay the unavailable full 166,016-row triple census, does not check the complete coordinate-cover registry, and does not propagate the signed exterior-row inequalities. The four-row upper-five proof is independent of the enumeration.

## Reproduction

Use rook_case4_full_span_cover_upper_five.js with the two exact public UTF-8 input files bound in BINDINGS. Pass the small SHA helper published as Git blob e1e7eda6a06a4a4d5079ab149fb4c95429dc594f. The entry points are data(nativeText, faceText, hash), theorem(data), and census(data).

The native input raw SHA256 is a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476. The 112-zero face input raw SHA256 is c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3. Both were fetched from checkpoint62 and matched their published raw hashes before use.

All work here ran as pure JavaScript during the local execution outage. No optimizer, native solver, model rebuild, installation, or Git ref mutation was performed.
