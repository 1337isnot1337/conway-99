# The three-row cover has 363 surviving triples

The completed full-span cycle produced a 27-column parity cover from original Gram rows 214, 344 and 582. Their right-hand sides sum to 3. After the already certified 112-zero substitutions, the exact original-coordinate identity is

H27 + 2 Q = 3,

where H27 is the sum over the retained 27-column parity support and

Q = x260 + x399 + x403 + x406 + x761 + x762 + x763 + x764 + x765 + x803.

The column 764 belongs to both sums. All coefficients are nonnegative integers. Therefore an integral incidence has H27 = 1 or H27 = 3. In the second case all ten Q columns are zero. In the first case Q = 1. These implications give no global zero by themselves.

A separate finite projection checked every one of the 2,925 three-element subsets of H27 against all relevant original nonnegative native upper capacities. The inventory consists of 630 Gram rows, 186 signature capacities, 1,365 triple capacities and 30 conflict clauses. Exactly 64 projected rows can reject a triple. The check rejected 2,562 triples and retained 363. Each rejection saves its first original-row witness and selected intersection. The complete survivor list is retained.

The independent cold pass uses literal set membership and integer counts, rather than the forward bit-mask test. It checked the full 1,214-coordinate Gram identity, every rejection witness, every survivor against every relevant projected row, and completeness of the 2,925-element partition. It passed in 9.143340616 seconds after the forward pass took 3.943782431 seconds.

This proves that the tested capacity projection does not eliminate H27 = 3. A surviving triple is not an extendible incidence or graph. The 60 signed native row inequalities, complete coordinate-cover matrix, other appended cuts and branch propagation were not evaluated in this census. Those stronger systems remain separate. No optimizer was called.
