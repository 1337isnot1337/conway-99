# CaDiCaL case4 run: hard-timeout UNKNOWN

## Terminal result

The single prepared CaDiCaL300 production attempt reached the 180-second
child wall deadline. The parent saved UNKNOWN before sending SIGKILL and
reaped the child with return code minus9. The measured child-process interval
was 180.076 seconds; the parent wrapper completed in 180.082 seconds.

No terminal child result was written. No partial incidence, raw proof or
partial proof was accepted. There was no retry. Case4 remains open.

The deadline included child imports, loading and solving. Because the child
was killed before its terminal record, this result does not supply separate
bootstrap or solver-search timings. The parent peak RSS was 79,380 KiB;
that figure does not measure the child's peak memory.

The formula was unchanged from the previous Glucose4 run: 134,852 variables,
439,604 clauses, and SHA-256
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.
No assumption, symmetry constraint or new clause was added.

## Verification and scope

A separate cold replay reconstructed the complete original formula, thirty
Gram pair conflicts, sixty exact integer row inequalities and their
threshold encodings, the full coordinate-cover ledger and the streamed CNF.
The complete hash matched. The replay also bound the recorded hard timeout,
child reaping and refusal to use a partial proof. It passed in 29.590 seconds
with peak RSS 353,336 KiB.

No DRAT checker is called for this production UNKNOWN result, because no
completed UNSAT proof exists. The previously verified tiny CaDiCaL proof
remains a backend control only.

The separate non-author source review checked the complete process wrapper,
inherited parser and retained-input paths, source/runtime/control bindings,
unchanged CNF hash, tiny truth tables, SAT assignment and saved watchdog and
DRAT artifact bindings. That review did not rebuild the CNF or rerun a
solver, watchdog or proof checker.

This result supplies no new mathematical exclusion. The fourteen intrinsic
unit exclusions, complete coordinate-cover family and no-new-unit capacity
closure remain exact independent results. No inference about another local
matching or the whole graph follows from the timeout.

## Bindings

| Artifact | SHA-256 |
| --- | --- |
| Production result | `95ffa7e41a06e98d58439f768107f33ab37dcd11a3eb8aac8822f7cb5c4a7c77` |
| Cold full-formula/result replay | `38612dbb984514f381a25fcbf2d3c494225f34cda11f6f7a067cf8265163e108` |
| Coordinator source/model gate | `9e57f359b5187b973522d48b41737e4622d49e9f217c842de44af184a1cf810d` |
| Independent process/proof-binding review | `a61b0e07632d876b051198e50b3d156127b5bf13757b908439d52e51ea055f04` |

The result directory is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-run01`.
The cold replay report and log are adjacent to that directory.
The preparation source, exact commands, runtime bindings and tiny controls
are documented in `complement_rook_35core_case0004_coordinate_cover_cadical.md`.
