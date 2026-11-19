# F0 direct master: third continuation result

The strengthened 12,469-row registry produced one exact candidate and one new
multi-anchor support certificate. Twelve transported universal rows increased
the registry to 12,481 rows. The next query reached its time limit without a
candidate. The terminal status is `UNKNOWN_MASTER_NATIVE`.

| Call | Additional rows queried | Native seconds | Outcome |
| --- | ---: | ---: | --- |
| 0 | 12,469 | 55.781855 | Exact candidate; exact support refutation; 12 new rows |
| 1 | 12,481 | 59.805618 | `UNKNOWN`; no candidate |

The first candidate passed the complete original constraints, all 12,469
additional rows, and all 18 matching checks. Its selection SHA-256 is
`cc1c3f2aee567601e9afe29c4a1db17cd0b3f92ce26777de39ce4cb5e278fd37`.
The original shared-feasibility phase returned without an exact decision.
The reserved bounded-potential phase then found an exact integer separator
with demand 176, capacity 172, and gap 4. The potential has 60 nonzero anchors,
997 nonzero entries, and maximum absolute entry 6. This is a shared
multi-anchor certificate; the previous single-anchor census does not apply
to it directly.

Both native calls used different certified prefixes. Total CP time was
115.587473 seconds. The owner accepted the terminal report after 272.647305
seconds, with no deadline overrun and all children reaped. Two shared
optimizer calls were made: one original feasibility call and one bounded
potential call. The full numerical outputs, exact certificate, twelve
transports, registry transition, and both native responses are preserved.

The separate cold replay passed after 52.266056 owner seconds. It constructed
no `CpSolver` and made no optimizer call. It checked both complete called
prefixes, the candidate, all matching checks, the support certificate, all
transports, the registry transition, and the terminal status. The saved and
replayed final registries are byte identical.

The final registry has canonical value SHA-256
`85bc3f6a4748b85e110bc37c783da269cb5b735a2bca0484e9ba11e7f9c98f4d`
and file SHA-256
`c8873283cd403b6d85fe63f0073d3ec51f4d3e9047aa5ec5310d7a5402869797`.
This 12,481-row prefix has already been queried. A later continuation requires
a new certified constraint or a separately justified change to the search;
the completed run does not authorize another identical query.

## Evidence and restoration

The run result is
`experiments/logs/root-prism-free/f0-direct-master-continuation-run03/result.json`.
Its SHA-256 is
`5192b4cf6a3149522f1c9f771e19a0571cf9ea50169eb151a343f7913e197e25`.
The accepted cold report is
`experiments/logs/root-prism-free/f0-direct-master-continuation-run03-cold/report.json`,
SHA-256
`5f6edb6d7d7927f2094b55aa99cdff55e7358c3adffa09163809e192cf48f70e`.

Large files use the exact bases from the preparation package and the suffixes
in the terminal publication package. From a fresh clone, restore them with:

```sh
python experiments/workspace/exact_prefix_suffix_artifacts.py restore --manifest experiments/logs/root-prism-free/f0-direct-master-continuation-run03-publication02/manifest.json
```

The command verifies complete gzip and raw protobuf hashes, all complete
registry hashes, and exact equality for any existing target. The manifest
contains dependency order for snapshots restored from earlier entries.
The original run and cold files remain unchanged.

This result rules out the one saved candidate. It does not rule out the whole
F0 component and does not construct a strongly regular graph.
