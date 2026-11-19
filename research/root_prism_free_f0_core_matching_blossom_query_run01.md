# F0 blossom-strengthened count query: bounded UNKNOWN

The single authorized query of the blossom-strengthened count model ended with `UNKNOWN_NATIVE_BUDGET_OVERRUN`. It returned no integer candidate and appended no external-pool row. It establishes neither count feasibility nor an F0 exclusion.

## Exact frozen model

The model retains all 32,296 variable IDs, 16,280 product constraints, 44 tables and 117 external-pool rows from the complete Fourier/literal model. It adds the 6,854 core-matching blossom inequalities not already implied by the explicit boxes. The full target has 65,811 constraints; the initial solve contains 65,694 constraints. The separate overlay build and cold replay verify every new row and recover the parent model exactly after removing the suffix.

The query source is SHA-256 67cd7853f00d5f99df7524046c30d72a1286106c2f5577a50d573cf1fa4a967b. Its preparation is 711705d98feaf8d3a9a361335d81b6a49e5ee1cf1408168af11969b8aef943b1. Root gate 43d1235b238612965f5f763bfd1b4a81c22d0ec9b224a21a96f5c35238f53adb authorized this one query and its separate terminal cold replay after the direct literal lane released the execution slot.

## Terminal outcome

The first native call requested 180 seconds. Measured call wall time was 180.19452018599986 seconds, exceeding the cumulative native budget by 0.19452018599986332 seconds. The driver preserved this as `UNKNOWN_NATIVE_BUDGET_OVERRUN`. The native response itself was `UNKNOWN`, with no solution vector.

The owner completed and reaped its child in 188.0800421840031 seconds, below its 300-second hard deadline. There was one native call, no later prefix, no appended row and no retry. Initial construction and validation took 6.167413706003572 seconds. The terminal process record reports a 702,904 KiB peak resident set.

The owner result is:

- Path: experiments/logs/root-prism-free/f0-core-matching-blossom-query-run01/result.json
- SHA-256: c7eebf3e0f2a64dbf6d9c69bfc6fccebdb063e9586327572506a74d2ce58d0f2

The per-call model, prefix, parameters, response and exact native timing record are retained. The terminal package does not describe the small native overrun as a successful bounded acceptance.

## Separate cold replay

The prescribed optimizer-free cold replay passed. Its owner completed and reaped its child in 5.388631346999318 seconds, below the 60-second cap. It loaded the frozen target and initial archives, checked all domains and the exact initial-to-target embedding, checked the 117 external row identities, and verified the saved call's complete prefix, parameters, response and time-accounting chronology.

It preserved the terminal UNKNOWN status. It found no pending saved candidate and no provisional full-target witness. No parent acceptance or literal decoding was attempted because there was no vector.

The cold report is:

- Path: experiments/logs/root-prism-free/f0-core-matching-blossom-query-run01-cold/report.json
- SHA-256: 4f02b48c97b52186b96ab0181a7b7aa1cc6169cf1d2431ec0e43e8b13dd4e433

The cold owner receipt is SHA-256 5aec6bbf0b125de5598ef572b36f6433aca6903c3796fd3ddbad68962d21f8a5.

## Lossless publication

The first call's raw model is exactly the already-published successful overlay's initial protobuf:

- Raw bytes: 16,955,261
- Raw SHA-256: 940e34316ed30532aee8c192947a7d69e54ccd7e9ebf8d85a3c4ada912a7331a
- Archive: experiments/logs/root-prism-free/f0-core-matching-blossom-native-overlay02/initial.pb.gz
- Archive SHA-256: 1f633c70a669badb8d151a7696d744c194b8ed649b4a6f90a0ea7b8142efb7ee

The raw call file remains local. The terminal map records its lossless restoration from that archive instead of uploading a duplicate 16.96 MB blob. Before replaying from a fresh checkout, decompress this archive to the saved call000/model.pb path and check the raw hash. All other query and cold records are included directly in the terminal map. The immutable preparation map is Git blob 6d6178c827531edada635939d99d41430391bb1c.
