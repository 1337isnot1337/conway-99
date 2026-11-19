# Exact empty-root packing moment witness

The frozen 48-cut integer count point has an **exact nonnegative rational
extension** to the complete empty-root high-mask packing domain. This
settles this finite model in the feasible direction. It does not construct
a Conway graph.

## What was solved and checked

The complete structural domain has 90,776 atoms. Its degree-at-most-four
moment model has 124,314 listed monomials, of which 17,903 have nonzero
support. The exact root-label quotient has 73 equations and 249 variables.

One normalized primal query solved

\[
Cw=b/g,\qquad w\ge0,
\]

where \(g=72{,}926{,}995{,}680\). The constant equation is
\(\sum_Ow_O=1\). No finite upper bounds were imposed.

The numerical query returned an optimal status after 0.0156 seconds.
That status was only a proposal. Exact rational elimination then solved
the proposed 73-column support against the original integer right side
\(b\). The resulting 73 total labelled orbit masses are positive. Their
common denominator is **1,443,221**.

The exact checker verifies all 73 quotient equations and the total mass.
It assigns each orbit mass uniformly to that orbit's atoms, using the
previously verified literal incidence counts. It checks all 500 row-orbit
lifts and then all 124,314 individual moments. A separate process replayed
the saved rational weights without calling an optimizer.

The complete query and exact reconstruction took 0.457 seconds, with peak
RSS 46,256 KiB. No dual query ran. No separator was produced.

## Exact consequence and limits

Let \(p\) be any squarefree polynomial of degree at most four in the 42
empty-root high-class indicators. If \(p(S)\ge0\) for every atom in the
complete structural packing domain, the exact measure gives

\[
\mathbb E[p]=\sum_{S\in\Omega}\mu_Sp(S)\ge0.
\]

Thus no degree-at-most-four polynomial depending only on these high-class
presence variables and nonnegative on this domain can separate the bound
count point. This conclusion covers arbitrary coefficients and supports,
not only a preselected list of inequalities.

The domain enforces the root pair capacities, the Boolean nature of high
classes, and the outside-pair common-neighbor restriction. It does not
record the graph induced by the selected outside vertices. Other roots,
edge-sensitive moments, stronger graph constraints, and consistency across
root embeddings remain separate questions.

The masses are rational finite-model weights. No integer incidence
structure or host graph is asserted. The result also does not certify a
complete order-ten moment cone beyond this stated local domain.

## Frozen artifacts

The input point has SHA256
0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.

Source: experiments/workspace/grid_free_order10_high_mask_packing_query.py,
SHA256
8aa977d91ed3bd5407974e9e704fe7d48eb07f798795ccd2b614c40ba2717e57.

Preparation: experiments/logs/moments-and-counts/order10-high-mask-packing-query-preparation.json,
SHA256
b1040a602346df4a47109911b02d8402cf942b91719c3533ed6cdf1b9e48496d.

Exact model binding:
054d1bb69e8e9c993762712fc5cd5f1b4f0eeeadbcad8c7b30a91c1bc29935fc.

Witness: experiments/logs/moments-and-counts/order10-high-mask-packing-query01-primal.json,
SHA256
10451057f18327167f6df07901631acd4c2dde479c9dd92be6550223bd50eadd.
The rational weight-list hash is
18f3bac9c03e4a3ad8d05f279dd4379b103d0e2ed6efafff8d9a07778e06ca50.

Exact replay: experiments/logs/moments-and-counts/order10-high-mask-packing-query01-primal-replay.json,
SHA256
1726341f2a3060a37099a074082a0de25f64395c2dd90e2c430a0cc59f0aa1b8.

Preparation also includes four exact support controls, three tiny backend
controls, and an explicit unitriangular minor proving exact row rank 73.
The query coordinator review is bound separately. All earlier domains,
matrix files, and preserved preparation failures remain unchanged.
