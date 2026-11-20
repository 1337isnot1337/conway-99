# Exact preparation for the remaining small six-root packing models

This package prepares 32 six-root high-mask moment models whose permitted high-mask populations have size at most four. Root 49 is handled by the separately published root-49 recovery certificate. This preparation does not load the count point or call an optimizer.

The complete preparation passed in 0.996 seconds. A fresh invocation of the same frozen algorithm reproduced its serialized output exactly in 0.969 seconds. This is an owner replay, not an independent implementation.

## Scope and result

The preparation checks 4,975 monomials of degree at most four. It retains 1,035 supported monomials and proves that the other 3,940 vanish by explicit visible common-neighbor violations. The supported monomials form 492 orbits under the actual automorphism groups of their six-root graphs.

All 1,195 permitted literal induced completions are retained, including alternative edges among the high vertices. The corresponding 294 unrooted graph classes match all 294 catalogue columns through distinct complete product-column fingerprints. No ambiguous fingerprint tie occurs. Every one of the 2,450 selected cached product rows, with 2,742 nonzero coefficients, is reconstructed exactly.

The preparation also checks all 3,987 five-mask subsets, 46 direct labelled-embedding normalization controls, and 64 synthetic distribution/Möbius controls.

| Root type | High masks | Supported atoms | Root orbits | Literal induced completions |
| ---: | ---: | ---: | ---: | ---: |
| 43 | 0 | 1 | 1 | 1 |
| 52 | 7 | 65 | 25 | 86 |
| 53 | 0 | 1 | 1 | 1 |
| 59 | 5 | 16 | 7 | 16 |
| 62 | 7 | 38 | 20 | 38 |
| 63 | 8 | 74 | 26 | 74 |
| 69 | 13 | 134 | 43 | 162 |
| 70 | 6 | 25 | 15 | 25 |
| 71 | 4 | 16 | 6 | 25 |
| 72 | 0 | 1 | 1 | 1 |
| 74 | 9 | 65 | 36 | 92 |
| 76 | 7 | 33 | 22 | 51 |
| 77 | 11 | 86 | 86 | 96 |
| 79 | 4 | 9 | 9 | 9 |
| 80 | 13 | 134 | 33 | 155 |
| 82 | 11 | 96 | 50 | 116 |
| 83 | 9 | 64 | 11 | 64 |
| 84 | 8 | 40 | 22 | 40 |
| 85 | 4 | 9 | 4 | 9 |
| 86 | 6 | 21 | 7 | 21 |
| 87 | 4 | 9 | 5 | 9 |
| 88 | 4 | 8 | 8 | 8 |
| 89 | 6 | 17 | 7 | 17 |
| 90 | 7 | 28 | 18 | 34 |
| 92 | 5 | 8 | 4 | 8 |
| 93 | 7 | 25 | 15 | 25 |
| 94 | 3 | 5 | 4 | 5 |
| 95 | 2 | 3 | 2 | 3 |
| 96 | 0 | 1 | 1 | 1 |
| 97 | 0 | 1 | 1 | 1 |
| 98 | 0 | 1 | 1 | 1 |
| 99 | 0 | 1 | 1 | 1 |

The bounds are structural. No root, class, atom, or moment is removed because its count happens to be zero at a proposed point.

## The finite domain

Let \(H\) be a fixed induced six-vertex root, with its six vertices labelled. A high mask is an allowed subset of at least three root vertices. An exterior vertex is in that class precisely when its neighborhood inside the root equals the mask.

Each high class contains at most one vertex: two vertices in the same class would have at least three common neighbors. Its class count \(X_a\) is therefore Boolean.

Every induced subgraph of an \(\operatorname{srg}(99,14,1,2)\) satisfies
\[
(A^2)_{ij}+A_{ij}\le 2\quad(i\ne j).
\]
The checker first enumerates every individual high mask using this condition. For each set \(T\) of at most four allowed masks, it constructs the root plus the corresponding independent high vertices. If this graph violates the condition, the recorded offending pair certifies \(X_T=\prod_{a\in T}X_a=0\). Adding edges cannot reduce either its adjacency entry or its common-neighbor count.

If the independent extension satisfies the condition, it is one permitted literal completion, so the mask set belongs to the structural atom domain. Every other possible induced completion is obtained by enumerating the edges whose two-vertex extension is permitted and checking the condition again on the whole graph. Collectively impossible edge assignments are rejected explicitly.

For each root, all five-mask subsets fail the same necessary condition. Any larger realized high set would contain a realized five-mask subset. Hence the complete high set has size at most four. This supplies a complete finite necessary atom domain; it does not assert that every retained atom extends to a 99-vertex graph.

## Product normalization and catalogue matching

For a supported mask set \(T\), the checker uses every partition into two disjoint groups of size at most two. It sums the permitted internal-edge variants of each two-free flag. Distinct high masks cannot identify exterior vertices across factors, so these selected products have no cross-factor overlap terms.

For every product row, the checker independently enumerates all literal induced graphs consistent with both factors and records the multiplicity of each unrooted isomorphism class. It compares these complete row families with the selected sparse tensor rows from the published cache. The exact unrooted isomorphism and automorphism routine is the frozen root-49 helper. It uses full adjacency-preserving backtracking; degree data only prune impossible comparisons.

A graph class has a fingerprint consisting of its coefficient in all 2,450 rows. Every literal class and every nonzero cached catalogue column occurs. Their fingerprints agree bijectively, and all fingerprints are distinct. Thus each literal class is identified with a unique catalogue type within this family. The full order-ten catalogue is not regenerated.

The source also contains a guarded fallback for a tied fingerprint: it would require equal cardinality on both sides and the same independently counted automorphism order for every literal class in the tie, and it would use only the common-automorphism sum of those catalogue counts. That fallback is not used in the actual preparation.

If \(F\) is a literal induced graph on the root and the selected distinct high vertices, the number of its labelled embeddings is
\[
\operatorname{Aut}(F)\,N_{\mathrm{ind}}(F).
\]
The automorphism factor includes automorphisms that move the six chosen root positions. No root-stabilizer divisor is applied. For a given labelled root embedding, each selected high class has a unique vertex, so every literal induced completion contributes exactly its labelled embedding count. Therefore the presence moment is the sum of those labelled counts over all permitted completions.

The checker counts \(\operatorname{Aut}(F)\) directly and multiplies each cached labelled-embedding coefficient by that integer to obtain an induced-count form. It verifies that all alternative product partitions produce the same form. The 46 literal-host controls independently enumerate labelled root embeddings and their high classes, including cases with several isomorphic edge completions.

## Full moment coverage and the later query

The atom domain \(\Omega\) is downward closed and every atom has size at most four. All its presence moments are supplied by the prepared degree-at-most-four induced forms. Every other such monomial has an explicit structural zero witness.

If \(m_T\) denotes the unnormalized labelled-root presence moment, the only possible full atom weights are
\[
w_A=\sum_{\substack{T\in\Omega\\T\supseteq A}}
(-1)^{|T|-|A|}m_T.
\]
The checker implements both descending inversion and this signed formula, and checks every reconstructed moment. The total mass is
\[
m_\varnothing=\operatorname{Aut}(H)\,N_{\mathrm{ind}}(H).
\]

The root-automorphism quotient is a relabelling of the labelled-root count equations. It does not assume that the hypothetical 99-vertex graph has any automorphism. The source checks the complete root group, every atom orbit, moment-form constancy on each orbit, and every quotient coefficient. Quotient weights are total orbit masses.

The separate query mode is present in the frozen source but has not been invoked in this package. It is bound to the immutable 48-cut count point with SHA-256
0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.
It uses BigInt for all moment contractions and inversion. A negative atom weight would yield a nonnegative atom-indicator polynomial with a negative exact count value. A nonnegative result would be a finite local moment distribution, not a graph construction.

## Frozen inputs and replay

The public archives are the checkpoint-42 scope arrays and the published 55-block six-root/two-free tensor cache. Only the selected arrays, flag records, and 2,450 sparse product rows were extracted. Downloading, hash validation, restricted numeric unpickling, and record selection occurred in a disposable networked process. Mathematical enumeration, isomorphism checks, preparation, and replay ran in local V8.

| Artifact | Git blob |
| --- | --- |
| Public extraction request | a00bcf9304019e39ed3a07e576d6f07d22658f64 |
| Network-only extraction source | d8b680080596a9725371ffb363b611232b2f0a43 |
| Compact public input | a2188e546dfa72363ef464c11bf89caeec547254 |
| Generic checker source | 34085dd6833ab816968ede0ba4637e44713b37fc |
| Exact preparation | 537b722f2dd4f964c5fa053d5398e41c60b4ed9d |
| Frozen root-49 isomorphism dependency | d547df71ef544fc7e36a8580bc9f7bdc311d6871 |
| Complete original 61-root scope | 4bc0045ae1447160dbf667a1918e32a9f4e3c454 |

The compact input has 353,844 bytes and SHA-256
6faade97d280df6b10552d8d4f71e5b80e7c5984ee8e069ade6a9dcc097e4d3e.

To reproduce preparation with the published files:

~~~sh
node experiments/workspace/small_roots_packing_moment_recovery_check.js prepare \
  experiments/logs/moments-and-counts/order10-small-roots-public-recovery-inputs.json \
  experiments/logs/moments-and-counts/order10-high-mask-packing-other-roots-scope01.json
~~~

The Node entry point verifies the exact Git blob hashes of its input, scope, and isomorphism dependency before running. It does not require the unavailable original execution workspace.
