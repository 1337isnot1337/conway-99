# A triple-capacity saturation in case4

The second bounded row-generation run forces six further columns to zero. Its
certificate reduces to two Gram equations and one triple-capacity bound on the
original 1,214-column domain. It does not need the earlier 81 zero columns.

Write `C_ij` for the sum of weights of columns containing core sites `i,j`,
and `C_ijk` for the corresponding triple sum. The literal Gram data give

\[
C_{9,27}=1,\qquad C_{5,27}=2.
\]

The triple-capacity constraint is `C_(5,15,27) <= 1`. It is necessary because
two actual remaining vertices in that support would share three core
neighbors. It is one of the twelve triple bounds that were not already
dominated by a quota-one pair in the original CNF.

Every admitted column containing sites 5 and 27 contains exactly one of sites
9 and 15. Thus

\[
C_{5,27}=C_{5,9,27}+C_{5,15,27}.
\]

Both terms are at most one: the first is bounded by `C_(9,27)=1`, and the
second by its triple capacity. Their sum is two, so both are exactly one.
Consequently every column containing sites 9 and 27 but not site 5 has weight
zero.

The standalone verifier checks the equivalent coefficient identity on every
original column:

\[
C_{9,27}-C_{5,27}+C_{5,15,27}
  =\sum_{a\in P}x_a\leq 1-2+1=0,
\]

where

```text
P = {302,309,315,329,335,342,809,816,822,828,841,848,
     1021,1027,1034,1041,1054,1061}.
```

All weights are nonnegative, so all eighteen columns vanish. Twelve were
already known to vanish; the six new columns are 1021, 1027, 1034, 1041, 1054
and 1061. The union with the previous proved zeros therefore has 87 columns.
The conclusion uses a triple bound and is not claimed as a Gram-only deduction.
It is valid for nonnegative real weights; no rounding or weight integrality
is used.

The numerical run made two calls, added four original covers after the first
call, and spent 3.54 seconds in the solver. None of those four covers occurs in
the final certificate. The original retained proof had 37 Gram rows, one
triple row and six max-min extension rows. The direct identity above removes
the extension variable and all unnecessary Gram rows.

This is a conditional restriction on the case4 attachment model. It does not
exclude that model or resolve the full Conway99 problem. It also motivates
exact transportation tests: the Gram rows give margins, and triple bounds
give cell capacities. A projected transportation table need not lift to a
full attachment incidence.
