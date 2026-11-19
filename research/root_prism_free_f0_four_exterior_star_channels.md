# Exact star channels for the retained four-exterior rows

This is an encoding proposal for the accepted 23,010 retained four-exterior inequalities. Their current literal block has 401,874 terms in the accepted 68,934-variable, 257,594-row model. No model has been changed and no inventory or solver has been run for this proposal.

The accepted family and its exact retained IDs are bound by [the four-exterior root acceptance](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-root-acceptance01.json), SHA256 74341c2db1458b35a8b932bb7fbde28824b9eadf09cbe404e1d5bbf5a69150a9. The actual model is bound by [the strengthened native acceptance](../experiments/logs/root-prism-free/f0-strengthened-native-root-acceptance01.json), SHA256 1c09b33189f337c90759a6339716fee001efe0b7b6c3727f8a0ec41e8a141116; its raw protobuf SHA256 is 4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2.

## Definition and exact equivalence

Write one retained row as

\[
y_{bc}+L_b+L_c-x_b-x_c\leq0.
\]

Here \(L_b\) is the sum of the original live edges from \(b\) to signatures containing the two core sites of that row; \(L_c\) is the corresponding sum at \(c\). The central edge is outside both stars. Keep exactly the star edge sets used by the accepted row, including its original removal of the 1,884 literal zero edges. Later spectral zeros need not be substituted.

For each distinct pair consisting of a center \(b\) and an exact star edge set \(E_b\), introduce

\[
p_b=x_b-L_b,\qquad
p_b+\sum_{e\in E_b}y_e-x_b=0.
\tag{1}
\]

A saved origin supplies a core site \(i\in h_b\) with \(q_{bi}=1\). The original mixed equation is

\[
\sum_{\substack{a:\,ab\text{ eligible}\\i\in h_a}}y_{ab}=x_b.
\]

Every star edge occurs once with coefficient one in that mixed support. Nonnegativity of the other edge variables gives \(0\leq L_b\leq x_b\). Thus (1) determines a unique value satisfying

\[
0\leq p_b\leq x_b\leq1.
\tag{2}
\]

When the original selector and edge variables are Boolean, \(p_b\) is an integer and hence automatically Boolean. Declaring the new variable Boolean imposes no extra restriction on an original Boolean solution.

Substitution gives the exact identity

\[
y_{bc}+L_b+L_c-x_b-x_c
=y_{bc}-p_b-p_c.
\tag{3}
\]

The replacement is therefore the three-term row

\[
y_{bc}-p_b-p_c\leq0,
\tag{4}
\]

or, on Boolean assignments, the clause

\[
\neg y_{bc}\ \lor\ p_b\ \lor\ p_c.
\]

Every original feasible Boolean assignment has exactly one extension through (1). Every extended feasible Boolean assignment projects to an original feasible assignment by (3). All constraints outside the retained four-exterior block remain in place.

The real relaxation has the same projection if all new channels are relaxed to \(0\leq p_b\leq1\) and (4) is kept as its linear clause inequality. This follows from the same unique extension and (2). Declaring channels integer while relaxing original variables to real values is a different mixed formulation; no equality with that mixed projection is asserted. An explicit native Boolean clause has the stated integer semantics; its standard linear relaxation is (4).

This is an alternative representation of the retained constraints. It does not prove those constraints redundant and does not strengthen their projected real feasible region.

## Deduplication and proof records

A channel key is

\[
(\text{center selector ID},\ \text{sorted original edge IDs in the star}).
\]

A core-pair name alone is not the final key. Equal edge sets at the same center define the same expression, even when several core-pair origins describe it. Different centers retain different channels. Retain every origin and every quota-one witness attached to a merged channel.

The prepared inventory will:

1. Bind the accepted complete compact four-family report, retained-ID replay, finalizations and root acceptance, plus the original domain and literal-zero overlay.
2. Reconstruct the complete 68,394-edge namespace from the literal signatures and mixed quotas. This is namespace verification, not another four-exterior case census.
3. Read the accepted retained rows in their accepted order and recover every saved case origin.
4. Partition each row into its central edge and the two endpoint stars. Check both stars against the full original neighbor lists and the original literal-zero set.
5. Check the actual coefficient-one inclusion in an original quota-one mixed support. Record its native row index \(154430+18b+i\), complete positive edge support, selector coefficient \(-1\), and the original case ID.
6. Sort distinct channel keys deterministically, preserve all origins, and emit the complete map from every old retained row to its central edge and two channel IDs.

The planned source does not import the old producer and does not decode or construct a native model. The already accepted parent mixed equations and complete preserved-parent cold are its authority for the native meaning of those mixed-row receipts.

## Native ordering

Keep original variable indices \(0,\ldots,68933\). Append channel \(k\) at variable index \(68934+k\), with domain \([0,1]\).

For the all-linear encoding, each channel equality has coefficient \(-1\) on its center selector and coefficient \(+1\) on its star edges and channel. Its domain is \([0,0]\). The replacement row has coefficient \(+1\) on the central edge and coefficient \(-1\) on both channels, with domain \([-2,0]\). The lower endpoint is valid from their Boolean box bounds and adds no restriction.

The old retained block starts at zero-based native row 227270: 168050 complete parent rows, then 1224 one-edge rows and 57996 path rows. A future builder can preserve the order and full protobuf contents of all other rows, put the channel equalities at this block boundary, follow them with the replacement rows in accepted retained-ID order, and shift subsequent row indices by the number of channels.

For an explicit native Boolean clause, the literal indices are

\[
[-(540+e_{bc})-1,\ 68934+k_b,\ 68934+k_c].
\]

The current all-linear terminal checker would require a separate reviewed extension before that clause form could be used. The linear three-term form already has the exact same Boolean meaning.

## Size formulas and bounds

Let \(C\) be the number of distinct channels, and let \(S\) be the sum of their star sizes, counting each distinct star once. Neither number has been computed for this proposal.

The known accepted counts give

\[
\sum_{\text{row occurrences}}(|E_b|+|E_c|)
=401874-3(23010)=332844.
\]

| Quantity | Exact formula |
|---|---:|
| New Boolean variables | \(C\) |
| Channel equalities | \(C\) |
| Three-term rows | \(23010\) |
| Terms in channel equalities | \(S+2C\) |
| Terms in three-term rows | \(69030\) |
| Total replacement-block terms | \(69030+S+2C\) |
| Change in term count | \(S+2C-332844\) |
| New total variables | \(68934+C\) |
| New total rows, using either one row or one clause per old row | \(257594+C\) |

Term count decreases exactly when \(S+2C<332844\). No decrease or solver improvement is claimed before the inventory and a separately authorized experiment.

There are at most \(480\cdot3\cdot15=21600\) distinct center/core-pair stars: a center signature has three included core sites and fifteen excluded sites, and each origin uses one of each. A fixed center and unordered core pair have a fixed original live-star set. Deduplicating exact channel keys can only lower this count. The accepted family uses only 48 core pairs and further quota restrictions, so 21600 is a conservative upper bound, not an observed channel count.

It follows that the proposed model has at most 90,534 variables and 279,194 rows. The prepared inventory stops explicitly if the proved channel bound fails; it never truncates a family.

Short clauses may interact differently with native presolve and propagation. Presolve may also eliminate channel variables. Exact equivalence alone supplies no runtime guarantee.

## Prepared, unrun inventory

Source: [root_prism_free_f0_four_exterior_star_channel_inventory_v8.js](../experiments/workspace/root_prism_free_f0_four_exterior_star_channel_inventory_v8.js).

Configuration: [f0-four-exterior-star-channel-inventory-configuration01.json](../experiments/logs/root-prism-free/f0-four-exterior-star-channel-inventory-configuration01.json).

The proposal is one finite identity-and-size inventory, with a 30-second inventory phase, a 60-second total bound through serialization, and a 16 MiB report bound. The exact complete keys, all row mappings, origins and mixed witnesses are retained. A complete report also needs a passing within-bounds finalization.

Only JavaScript syntax parsing has been performed. The factory, main inventory and controls have not been executed. There is no native build, solver call, new accepted row, or change to the frozen query model. Root authorization and source review are required before the inventory; a later model variant also requires a new builder and independent complete native replay.
