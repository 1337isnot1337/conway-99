# Case4: native propagation on the H=5 face and one new integer inequality

The previously checked original-Gram proof gives H in {1,3,5}. Here H denotes the sum of the same42 incidence selectors.

## Complete native branch result

The H=5 face forces38 residual coordinates to zero;31 are new conditional zeros beyond the112 global premises. Exact propagation on all2271 original native constraints plus H=5 stopped at those143 zeros with no further force. This initial fixed point was replayed separately.

All996 five-sets from the complete native upper-capacity projection were then used, in fixed lexicographic order, as exact H patterns. Every branch retained all2271 original native rows, the112 global zeros, the31 conditional zeros, and the H=5 equation. No complete coordinate-cover registry was loaded.

The run completed in16.302 seconds. It recorded813 contradictions and183 noncontradictory native fixed points, with207003 sequential forced-literal reasons in a2.67MB transcript. A separate arithmetic replay checked all996 records, including full native fixed-point exhaustion for the183 survivors, in6.317 seconds. Thus H=5 remains possible in this tested necessary projection. None of its surviving patterns is a full incidence or a graph.

The intersection of the183 surviving branch states adds only x600=x922=0 beyond the143 conditional premises. Separate failed-literal checks under H=5 refuted x600=1 and x922=1 using only original Gram rows. They used232 and176 forced literals respectively and were independently replayed within the owner package. Their results motivated the shorter proof below; the final inequality does not depend on the996-case computation.

## Direct original-coordinate certificates

A positive sum of six original Gram rows gives

    H + 3*x922 <= 7.

The rows are93,243,411,589,590,591, each with multiplier1. Every remaining coefficient is nonnegative on the full1214-column domain.

A second signed row sum gives

    3*H + 4*x600 <= 18 + x783.

Its original row multipliers are
(60,-1),(93,2),(368,1),(390,-1),(411,3),(431,1),(587,1),(589,2),(590,3),(591,2),(593,1).
After subtracting3 times the H indicator and4 times coordinate600, the only negative residual coefficient is -1 at coordinate783; all others are nonnegative. Column783 was already proved zero.

Consequently H=5 implies x600<=3/4 and x922<=2/3. Nonnegative integrality forces both to zero. Original Gram row617, for core pair(30,32), also gives x600+x922<=1. Therefore every incidence satisfies the44-term integer inequality

    H + 2*(x600+x922) <= 5.

For H=5 this uses the two conditional zero conclusions. For H=1 or3 it uses the quota-one bound. This is a necessary inequality, not a global exclusion of either coordinate.

The exact premise list is only the seven previously proved zeros
126,465,783,966,970,973,977.
Six support the original parity lift;783 supports the signed bound. The new theorem therefore does not require every one of the112 zeros used by the branch computation.

The short producer and a separate direct checker each expand every original-coordinate identity. The direct checker rejected five deliberately changed certificates. Seven feasible Boolean triples out of twelve possible (H,x600,x922) triples verify the final finite implication.

## Scope and reproduction

The JavaScript propagation engine uses signed row extrema over the Boolean box. Every force is replayed from earlier assignments and its original native-row ID. The engine's exhaustive small controls cover3616 partial states,7060 conditioned extrema and329056 row-bound cases, including negative and zero coefficients. Before any case run, two extra replay-input guards were added; the unrun initial source is retained.

The batch shares one60-second budget and a64MiB transcript cap across all996 branches, with aone-second cap per branch. It completed without hitting any cap. Its separate replay has its own60-second ceiling.

All inputs are the immutable public native model a9004e97... and the112-zero model c6cd72c9..., plus the independently replayed H-upper-five/projection package. There was no optimizer, native solver, full cover census, new unconditional zero, or case4 exclusion.

Next work on the183 survivors must use a stronger domain, such as the complete retained selector-row pool and existing proved cuts. Repeating the unchanged native closure is unnecessary.
