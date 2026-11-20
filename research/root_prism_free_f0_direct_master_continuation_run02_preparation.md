# Second direct-master preparation

The new master starts with 157 additional necessary selector rows. It retains
all 133 rows from the accepted first continuation and adds all 24 rows from
the accepted local pair-packing batch. Exact normalized deduplication found
no overlap between those 24 rows and the inherited registry.

The last first-run call queried 121 additional rows. Its final certificate
grew the registry to 133. Thus neither that final prefix nor the new 157-row
prefix repeats the last queried model.

## Receipt binding

Registry v4 imports the arithmetic, normalization, native append functions,
range checks, and matching/shared cut conversions from hash-pinned registry
v3. It changes none of those functions. The 256-row limit remains. Any later
batch beyond that limit is saved and refused as a complete batch.

The wrapper binds the first run and its accepted cold owner. It compares the
saved and replayed 133-row registries, checks that the original 37-row prefix
is unchanged, and reconstructs the 96 later additions with their original
provenance. Those additions contain every core action for each of the eight
exact shared-row refutations.

The wrapper separately binds the pair-packing run, cold report, accepted
owner, source, root gate, and exported 24 rows. It appends every new row and
checks that the entire 133-row prefix is unchanged.

## Native preparation

Preparation 03 constructed 540 variables and 4,838 native linear rows. The
actual public-builder protobuf matched the expected complete original
prefix plus all 157 rows. Its raw SHA256 is
`7417a7d0a9bb2ec639f90814118dc06eade159039503cd38315fa30555be5b8f`.
The initial registry canonical SHA256 is
`066908e53d96b3b706923ef1939711939e35ee15f9cd3d09fa043a6fb96b7fe8`.

The preparation owner accepted the report after 7.440258 seconds. It
constructed no solver and invoked no optimizer. The child was reaped and
the owner recorded no deadline overrun.

Controller v4 changes only its helper binding, a descriptive initialization
stage, and preparation authority. A fresh preparation now binds the current
source directly. The complete production and cold-replay function ASTs are
identical to v3. The canonical matching-witness comparison is retained.

All query bounds remain unchanged: eight calls, 60 seconds per CP call,
180 cumulative CP seconds, a 300-second owner, and a separate 60-second cold
owner. Any new production run requires the separate source review and root
gate. This preparation alone makes no feasibility or exclusion claim.

## Evidence

- [Accepted-prefix adaptation](../experiments/logs/root-prism-free/f0-direct-master-accepted-prefix-adaptation02.json)
- [Frozen seed configuration](../experiments/logs/root-prism-free/f0-direct-master-seed-configuration03.json)
- [Native preparation](../experiments/logs/root-prism-free/f0-direct-master-preparation03/report.json)
- [Preparation owner](../experiments/logs/root-prism-free/f0-direct-master-preparation03/owner.json)
- [Native restoration records](../experiments/logs/root-prism-free/f0-direct-master-preparation03-native-restoration.json)
