# Complete eight-root projector scan at the integer count point

The bounded run constructed and scanned all 3,664 specified projector
blocks, covering all 916 eight-vertex roots. It found no exact separator
and no unconfirmed numerical negative direction at the integer count
witness with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.

This is a complete numerical separation scan for these two projector
families at that exact input. It is not an exact PSD certificate, a
certificate for the full order-ten PSD cone, or a graph construction.
The previous 2,405 blocks were not rescanned by this driver.

## Coverage and exact gates

Each root has four blocks: spectral and per-embedding Schur, for each
of the two projectors. Every allowed neighborhood mask is retained.
The reusable cache contains zero-count roots and all masks of degrees
zero, one and two. Its construction is independent of the point.

All 3,664 contractions use Python integers. All nine universal kernel
equations pass exactly in each matrix, before the nine pivot
coordinates are removed. The separator removes additional rows only
after proving that every entry in the row is zero at this point.
Numerical eigensystems then propose possible directions. An accepted
direction would need an exact negative integer quadratic value and an
exact induced-count form.

No such direction was found. The smallest reported numerical
eigenvalue is approximately −5.5×10⁻¹⁶, and no value crossed the
separator's −10⁻⁸ threshold. This numerical tolerance is not used as
an exact PSD acceptance test. There is no unsupported promotion of a
numerical pass to a theorem.

Independent literal reconstruction of supported entries is a separate
gate for any resulting cut. This run produced no cuts, so it did not
invoke that reconstruction stage or load the dense count reduction.

## Complete cache and resource use

The cache has 13,735,344 lower entries and 16,613,124 nonzero tensor
coefficients. Its CSR arrays occupy 254,313,520 bytes. It is stored in
29 immutable chunks with 32 complete roots per chunk, except the final
20-root chunk. The compressed chunks total 57,623,454 bytes.

A root is committed only after all four of its complete blocks have
been scanned. Chunk writes are idempotent, and a timer interruption
would preserve the completed prefix. No interruption occurred.

The build-and-scan stage, including periodic checkpoints, took
135.710 seconds within the 180-second budget. Total wall time was
136.799 seconds. Peak RSS was 252,584 KiB. Product construction took
45.357 seconds; the exact matrix/kernel work and quotient separation
took 28.052 seconds. The remainder includes compression and checkpoint
writes. One numerical thread was used. No optimizer was called.

## Frozen files

Driver:
`experiments/workspace/grid_free_order10_projector_full_scan.py`

Driver SHA256:
`943bd7d44aec5d00e5f55355747d0b8df07ac824c1a6eb21569a61eeacb5366f`

Preparation:
`experiments/logs/moments-and-counts/order10-eight-root-projector-full01-preparation.json`

Preparation SHA256:
`b624ac75271018323fb9c5fb16613b7211a79617c84ffeeb7ceddc532e4f580c`

Result:
`experiments/logs/moments-and-counts/order10-eight-root-projector-full01.json`

Result SHA256:
`f56fb300b440d660a5a542b181fd44e7f6c2f331bb8f28a85e16f2fcca44c0d9`

Complete cache manifest:
`experiments/logs/moments-and-counts/order10-eight-root-projector-full01-cache/manifest.json`

Cache-manifest SHA256:
`434454d319468262ca384e00b3a251a672262c5e73f2bd7f655bfccad23794ce`

The preparation also binds the
[complete domain/inverse package](grid_free_order10_projector_domains.md),
the [four-root controls](grid_free_order10_projector_probe.md), and the
coordinator's source reviews. The publication manifest lists all 29
chunks explicitly.
