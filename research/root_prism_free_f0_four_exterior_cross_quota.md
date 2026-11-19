# Four-exterior rows and existing mixed equations

For the original F0 four-exterior family, let b,c be the two centers and i,j the two core sites. Its premises include i in h_b, j not in h_b, j in h_c, i not in h_c, q_bi=q_cj=1, and an eligible central edge bc. Let T be the signatures containing both i and j. With the original proved-zero edges omitted, put

\[
L=\sum_{a\in T}y_{ab},\qquad R=\sum_{a\in T}y_{ac}.
\]

The proposed prism row is

\[
y_{bc}+L+R\le x_b+x_c.
\]

## A sufficient linear implication

The accepted mixed equations have the form

\[
\sum_{a:\,s\in h_a}y_{va}=q_{vs}x_v.
\]

All edge variables are nonnegative. If q_bj=1, the mixed row at (b,j) contains y_bc and every term of L, so y_bc+L<=x_b. The original mixed row at (c,j) gives R<=x_c. Adding proves the complete proposed row. The certificate uses native rows 154430+18b+j and 154430+18c+j.

If q_ci=1, the symmetric proof uses mixed rows at (c,i) and (b,i). It gives y_bc+R<=x_c and L<=x_b. This proof uses no integrality and is valid in the continuous relaxation. Removing extra nonnegative terms only weakens the summed mixed equations.

Eligibility of the central edge implies that both cross quotas are at least one. Thus only cases with cross quotas (2,2) can survive this particular sufficient test. The test does not prove that all such cases are necessary. A quota-one equation does not make an individual eligible edge zero; no empty-support shortcut is used.

The [independent source review](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-v8-independent-source-review01.json) checks both certificates, row offsets and the original-family reconstruction requirements. Small activated-assignment controls include a counterexample when the additional quota premise is removed.

## Preserved failed computation

The first forward reconstruction was bound to the exact committed domain and literal-zero overlay. Its source requires all original counts: 73,404 cases, 936 central-zero cases, no empty-side case, 72,468 distinct rows and 1,250,496 terms. It also requires the complete ordered row-key SHA256 2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c, previously accepted by the pre-outage independent replay.

The source returned, so those assertions passed. The wrapper then serialized and hashed its verbose report, but exceeded its 60-second total bound. Its final deadline exception prevented return of the report. No quota histogram, row disposition or deletion count was retained or accepted. The [failure record](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-v8-failure01.json), frozen source, configuration and runner are preserved unchanged.

A separate independent compact reconstruction is in preparation. It must check actual mixed-term support certificates and preserve complete row keys and origins with smaller arrays. No unchanged automatic retry or native-model modification follows this failed attempt. Rebuilding the same row-key family will not recover the original compressed inventory or rewrite the earlier metadata failure.

No native model, optimizer query, entire-component exclusion or Conway99 solution is obtained here.
