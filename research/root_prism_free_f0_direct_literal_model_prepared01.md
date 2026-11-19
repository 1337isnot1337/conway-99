# Direct540 preparation and cold replay

The direct literal model has 540 variables and 4,681 linear constraints with
454,152 coefficient terms. It has no products, tables, external row pool,
Fourier variables, or edge variables. All 4,416 certified literal cuts are
encoded, including the 12 large cuts through the existing exact radix rows.

The single 60-second preparation owner ended
`UNKNOWN_HARD_DEADLINE`. It killed and reaped its child at 60.88 seconds.
That result and `report_accepted=false` remain unchanged.

The child had already written a complete preparation report at 55.98 seconds.
It had checked every original equation, motif and zero-pair implication,
constructed the exact protobuf, passed the public native validator, and
compared the complete native export byte-for-byte. Those raw artifacts were
preserved. The record establishes that the checks completed; it does not
change the owner's timeout.

The separately authorized cold replay then completed within its own limit.
Its owner exited and reaped the child after 13.79 seconds, with zero overrun.
The cold phase reconstructed the complete mathematical plan and protobuf and
compared every byte with the preserved artifacts. It did not repeat native
model construction or invoke a solver.

| Record | SHA-256 |
| --- | --- |
| Original preparation owner | c5a7826dcd4260830730801ea9457dca2766c5cc1a643adf7a06951e4532b156 |
| Completed raw child report | 36521e821a363281d2792f115dce6577fb4f27dd40309a08f27160a527f73a62 |
| Separate cold report | 2c67cbf7eaae08cad0bfd6d47c32de0606b91486a2731f452806de0c3add8254 |
| Separate cold owner | 2da83ed1808634d2bf02e7ef44465ad38c4f198fde9202d719d4b2596c22e863 |
| Exact compressed plan | bd921d7d8f16c64bd866e0ec319b1cc3db37450cf5a6c884a37a9f40044c48d7 |
| Exact compressed model | 34724b46df693d930de465d2d3b7473ae8742a322aa7006e21e0aa780f1c1bd6 |

The mathematical plan completed at child time 12.20 seconds and the exact
protobuf at 14.25 seconds. The next recorded stage, at 55.98 seconds, covers
archive writes, native construction, validation and export comparison.
The log does not isolate their individual costs. Peak recorded RSS was
318,484 KiB. No causal performance conclusion follows from these timings.

The largest absolute row box activity is 783,727,900,923, within the checked
signed-integer native bounds. The 4,681 rows comprise 4,404 direct cut rows,
36 radix equalities, 151 nonempty Gram/population equations, and 90 motif
conflicts. All 172 original equations remain in the exact candidate
obligations, including the 21 literal zero equations. All 4,410 known
zero-pair consequences have explicit original-row or motif witnesses.

The raw `native-model.pb` file is retained locally. Its 5,327,821 bytes have
SHA-256 de9e9f0f9deb2e7dc1c41866c959c5264de2b7fef7d11d3c9c0d8772aa0bbe3e.
Publication uses the complete `model.pb.gz` archive instead of a second
copy of the raw bytes. Full decompression equality was separately checked
and is recorded in the publication summary.

The source-only package and original preparation gate remain unchanged.
No production query has run. There is no candidate, exclusion, or
exterior-graph claim. Query source and preflight require their own gate.
