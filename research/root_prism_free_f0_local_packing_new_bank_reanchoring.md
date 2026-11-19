# Forty-eight further packing rows by changing the anchor

The 24 potentials from the new all-anchor packing batch apply at more than
their original transported anchors. An exact census over all 480 anchors
produced 72 distinct positive-demand rows. Of these, 48 are absent from
both the frozen 157-row prefix and the later 253-row registry.

This calculation uses no optimizer. It does not change either completed
master query or its saved prefix.

## Why an arbitrary anchor is allowed

For every anchor a, the same local mixed equations and common-core-pair
packing inequalities give

\[
\left(v\cdot q_a-\sum_p\mu_p\right)x_a
\le\sum_{b\in N(a)}
\max\left(v\cdot h_b-\sum_{p\subseteq h_b}\mu_p,0\right)x_b
\]

for any integer v and nonnegative integer mu. The potential need not have
been discovered at a, and no automorphism sending its original anchor to a
is required. The full eligible neighbor set is used for each new anchor.

The earlier 12-potential bank yielded only its original 12 rows when tested
at all anchors. This result concerns the new 24-potential bank from anchors
4 and 202.

The base potential discovered at anchor 4 has positive demand at anchors
4, 42 and 170, with demands 3, 1 and 1. The base potential from anchor 202
has positive demand at anchors 202, 210 and 211, with demands 1, 2 and 2.
The 12 actual core relabelings of each potential give the complete bank.

Across all 11,520 anchor/potential pairs, 72 demands are positive: 36 are 1,
24 are 2, and 12 are 3. The resulting 72 rows are distinct. The 48 rows
outside the previous 157-row prefix have 69 to 80 terms, maximum absolute
coefficient 5, and maximum absolute coefficient sum 149.

The census also records the binary-equivalent rows obtained by replacing
each positive weight w by min(w,t), where t is the positive anchor demand.
If the anchor is selected and a selected weight is at least t, that term
alone satisfies either row. Otherwise every selected weight is unchanged.
The new-row export retains the original weighted rows.

## Independent check and preserved correction

The producer reconstructs every eligible domain from the literal core and
signature data. A separate standard-library verifier reconstructs all
domains again using bit masks, then recomputes all 11,520 demand attempts
and all 18,372 neighbor coefficients in the positive-demand cases. It
checks the complete row list, origins, primitive normalization and capped
rows. It does not import the producer.

The first saved census used all 24 potentials correctly but copied a
metadata count of 12 from the earlier source. That source and result are
preserved. Version 2 changes only the count field to the bank length. The
corrected artifact and separate exact replay are the accepted pair.

The corrected certificate is
`f0-local-packing-new-bank-reanchoring02.json.gz`, SHA-256
`3eaf4ceae4a3c7489cbcc1479b2ce732922ce00bdc923ceb1624bf7465b67715`.
The independent replay is `f0-local-packing-new-bank-reanchoring02-cold.json`,
SHA-256 `d3db8b43f7f3b52fc3c65fcd7c2da0bc12e762a8c425a6a3b929504ba9d9a948`.
Its `new_rows_upper_zero_vs_frozen157` field contains the 48 weighted rows,
each with RHS 0. Producer and replay completed in 1.4278 and 1.5981 seconds.

A separate exact comparison against the later registry file with SHA-256
`b19c520815cb657184625ee8c7cd57b794364a71eff9fcfb57f0e7429604a11b`
found all 48 rows still new. That comparison is arithmetic on the saved
rows; acceptance of the parent master outcome remains a separate receipt.
Adding all 48 would produce a 301-row prefix and requires an explicit
change to the previous 256-row registry limit before another query.

These are necessary rows in the stated F0 domain. They do not exclude the
whole F0 case or the unrestricted 99-vertex problem.
