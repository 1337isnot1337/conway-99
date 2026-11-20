# Exact direct literal incidence, run 01

The direct540 query returned a 60-signature selection satisfying the complete
frozen selector system. Exact Python-integer inspection passed every original
equation, motif conflict and certified selector cut. A separate owned cold
replay checked the saved vector and the terminal transcript again.

This is a literal first-incidence witness. This package does not assign
exterior edges or certify a complete graph.

## Exact conditions checked

| Obligation | Checked |
| --- | ---: |
| Native variables and domains | 540 |
| Native linear rows | 4,681 |
| Original Gram/population equations | 172 |
| Original motif conflicts | 90 |
| Original certified selector cuts | 4,416 |
| Known zero-pair consequences | 4,410 |

The inspector evaluated the original cut coefficients with Python integers,
including the 12 large inequalities. The native limb system was not used as
a substitute for that check. All 60 selected signature IDs are distinct.
The profile counts are 24 of type \((1,1,1)\) and 36 of the other permitted
types; each fiber has the derived \(12,36,12\) distribution.

The selected IDs, in the frozen 480-signature ordering, are:

~~~text
2, 14, 17, 26, 36, 48, 58, 60, 61, 71, 74, 87, 90, 97, 106,
117, 124, 133, 136, 139, 145, 152, 171, 178, 190, 191, 194, 197,
205, 212, 219, 220, 225, 230, 239, 240, 257, 261, 273, 286, 289,
295, 301, 309, 310, 318, 325, 328, 341, 352, 366, 375, 392, 406,
410, 414, 433, 443, 447, 450
~~~

## Execution and separate replay

Exactly one native solve was called. The native status was OPTIMAL for a
feasibility model with no objective. Actual native call wall time was
16.212 seconds. The complete owner exited and reaped its child in
19.802 seconds, below its 300-second limit and the separate 180-second
native cap. The driver saved all 540 returned integers before exact
inspection.

The native response reports 612 Booleans after processing, 58 conflicts,
31,560 branches and 3,026,592 integer propagations. Peak recorded RSS was
286,336 KiB. These are measurements for this target and run. They do not
establish a matched-input speed comparison with the preceding count model.

The separate terminal cold owner completed and reaped its child in
1.909 seconds. It checked the exact model hash, parameters, response,
candidate vector, timing records and all direct obligations. Both owners
had zero overrun. No optimizer ran during the cold phase.

| Artifact | SHA-256 |
| --- | --- |
| Query result | ba8cfb827f1f0ec86dfe6693a9095bfa1f0bddd658d816d7656d4bc3478bf9ae |
| Query owner | 3b5959d8bd4dc3912acd2d7fdda2050f4593282d2f21a05e9afefeb4525e3217 |
| Full 540-integer candidate | b08b82804031b4310333d3f37e71e02f3790eb420bdedc97016a0c65df7015e8 |
| 60-signature selection | 6c1434b1dbb5a28f19707a3048cb43d64f14370856d03ef7496a3a58fabf4aaa |
| Direct exact check | 6bd0650b1d9552f75fb7e7847170b0ba634e43faddb960eaa3908198f9b8280c |
| Cold report | d9a3cd90320752b08690a761e649210fccc3cef63487f0c72f52f9670226288a |
| Cold owner | 23036aaca985fe751ebfcd0af2f688959c7d7fb49eeed3781bc6263a5b2c8c22 |

The query files are in
`experiments/logs/root-prism-free/f0-direct-literal-query-run01/`.
The separate replay files are in
`experiments/logs/root-prism-free/f0-direct-literal-query-run01-cold/`.

The terminal summary is
`f0-direct-literal-query-run01-terminal-summary.json`,
SHA-256 ea66e6bb208c10a30d84ad5855ab63ed6397c2aa3f0564bdedcb79acb76b7339.

## Mathematical consequence and remaining scope

The original 172 equations, 90 motif conflicts and full 4,416-cut registry
cannot by themselves exclude the F0 incidence slice: this saved Boolean
selection satisfies all of them. This is stronger evidence for that
specific limitation than a fractional point or an unfinished search.

It does not imply that the selected vertices have a compatible exterior
graph. The full count/Fourier target contains additional edge and moment
conditions which this direct model does not impose. Core matchings and a
fixed-selection exterior completion therefore remain separate checks.

The selection was sent to the parent for those checks. Their outcomes are
not included in this immutable query package. No arbitrary visitation
clause or candidate-dependent constraint was added to this run.

## Publication restoration

The raw query `actual-model.pb` remains local. Its 5,327,821 bytes have
SHA-256 de9e9f0f9deb2e7dc1c41866c959c5264de2b7fef7d11d3c9c0d8772aa0bbe3e.
The terminal package binds exact recovery from the already published
`f0-direct-literal-model01/model.pb.gz`, SHA-256
34724b46df693d930de465d2d3b7473ae8742a322aa7006e21e0aa780f1c1bd6,
rather than uploading another identical raw copy. Full decompression-byte
equality was checked.
