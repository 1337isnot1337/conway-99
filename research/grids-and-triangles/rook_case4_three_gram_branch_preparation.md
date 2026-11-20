# Complete three-Gram branch cover for rook case 4

This preparation partitions every Boolean solution on the 112 proved-zero face into 444 remaining patterns. It does not propagate those patterns or exclude case 4.

The sum of original Gram rows 214, 344 and 582 has right side 3. After substituting only the 112 proved zeros, its positive coefficients are 1 on 26 columns, 2 on nine columns, and 3 on column 764. Every Boolean solution therefore chooses exactly one of:

* column 764;
* one coefficient-one column and one coefficient-two column;
* three coefficient-one columns.

Every other column with a positive coefficient in this identity is zero within that branch. Columns outside the 36-column positive support remain free apart from the common 112 zeros.

There are 2,835 raw patterns: one singleton, 234 pairs and 2,600 triples. Original native capacity rows reject 2,391 patterns with explicit row witnesses. The remaining list contains one singleton, 80 pairs and 363 triples. The complete earlier triple certificate and its cold replay supply the 2,600 triple decisions; this preparation directly checks the other 235 patterns. It retains the original raw-pattern order and a hash of each full 1,214-coordinate initial Boolean box.

The native row file contains all 2,271 original rows and 28,784 nonzero terms: 630 Gram equalities, 186 signature capacities, 1,365 triple capacities, 30 Gram conflicts and 60 signed integer row cuts. The preparation checks every row against the frozen native inventory. The capacity census uses only applicable nonnegative upper rows; it does not claim closure under all signed rows.

The preparation completed in 0.585 seconds, and the separate cold reconstruction passed in 0.988 seconds. Both were run in separate owned processes with 40-second hard bounds. The source also checks 72 small weighted partition domains against 6,615 literal Boolean vectors. No case branch was propagated and no optimizer was called.

The identity is often written H27 + 2Q = 3, where column 764 lies in both supports. Its overlap is why the singleton 764 must be retained. The branch cover is unconditional on the separate H42 occupancy: H42 = 5 and its conditional zero premises are not used.

The numerical and logical limits of this result are explicit. The preparation proves a finite disjunction and its native capacity deletions. It does not establish feasibility of a retained branch, a global new literal, or an exclusion. Any subsequent propagation has a separate source, model, budget and transcript.
