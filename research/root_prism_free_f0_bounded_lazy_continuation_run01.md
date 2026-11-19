# Terminal UNKNOWN from the bounded-fallback continuation

The single authorized continuation ended at its time boundary without a
component exclusion or graph construction. It checked 81 SAT candidates,
completed 62 sixty-row passes, and retained 2,916 proved inequalities.
The last candidate reached the shared-edge stage with about 3.47 seconds
remaining. That stage supplied no exact certificate before the budget
expired.

The terminal status is
`UNKNOWN: no exact shared certificate before shared budget; unresolved`.
Elapsed time was 182.690646 seconds, including a recorded cooperative
overrun of 2.690646 seconds. There was no incremental UNSAT answer and no
fresh proof query.

## Exact progress

All 480 first-incidence selectors remained free. The conditional scope
is component zero in the globally prism-free, F-free split $18+18$
shell, with every second component and alignment unrestricted.

| Checked result | Count |
|---|---:|
| SAT candidates checked against their actual prefix | 81 |
| Registry-only refinements, without a row LP | 19 |
| Complete sixty-row passes | 62 |
| New exact individual-row obstructions | 121 |
| Exact rational individual-row boxes | 3,599 |
| Shared-feasibility calls | 9 |
| New exact shared-edge obstructions | 8 |
| Bounded-potential fallback calls | 0 |
| Exact shared-box feasibility witnesses | 0 |
| New individual inequalities, including transports | 1,452 |
| New signed inequalities, including transports | 96 |
| Final individual inequalities | 2,640 |
| Final signed inequalities | 276 |

The first eight shared calls produced checked integer rays from the
original feasibility model. Each was lifted to the full 480-selector
domain and transported under all twelve verified core relabelings.
The bounded fallback was available but did not run in this transcript.

The terminal incidence satisfies all 2,916 registered inequalities and
has sixty exact individual-row boxes. No cut or clause was added from
its uncertified final shared-edge answer.

## Why the terminal shared call stopped

The final selected domain has 1,226 eligible edges and 1,140 mixed/degree
equations. The shared helper received 3.472806 seconds. Its original
feasibility phase received 3.453711 seconds and returned a numerical
infeasibility status after 0.597065 seconds.

That phase did not save a numerical dual ray. Its total elapsed time,
including the dual-ray attempt and exact bookkeeping, was 3.468397
seconds. After the wrapper's replay, the remaining shared budget was
negative. The helper therefore made no bounded-potential call and
preserved UNKNOWN.

There is no saved ray, basis or bounded potential for arithmetic-only
reconstruction of this final answer. A later bounded-potential-only
query would be a separately prepared computation. This transcript does
not repeat the expired original feasibility call.

## Formula and cold replay

The formula grew from 59,466 to 62,334 clauses, keeping 28,308 variables.
Its 5,340 explanation clauses use no new auxiliary variables. The final
CNF has 582,612 literal occurrences and 2,715,748 bytes.

The final CNF SHA256 is
`27e32a5d17bbad0b8101262b026d82fb8da82bed1ba13eb01b94fe64ebc42c1e`.
Peak process RSS was 211,152 KiB.

The cold replay passed. It reconstructed the complete initial exact
registry, retained prefix and new seed clauses; checked every candidate
and actual clause prefix; replayed all row obstructions, rational boxes,
shared rays and full-domain lifts; verified every explanation's exact
falsifying-assignment bound; and matched the final CNF hash. It also
replayed the final numerical record without accepting it as a proof.

## Durable transcript

All 253 JSON or gzipped-JSON records are preserved in one deterministic
lossless archive. They include the nine explicit shared-feasibility
phase records as well as their wrapper records. Their uncompressed size
is 31,531,257 bytes; the archive is 4,413,940 bytes. The rebuildable final
CNF is omitted.

The bundle checks every member hash and restores only under this
transcript's fixed path prefix. It preserves equal existing files and
refuses to overwrite unequal files. Missing-file, equal-file and
mismatch controls passed. Restoration replay matched all 253 records.

| Artifact | SHA256 prefix |
|---|---|
| Terminal result | `88c4858aa36aaf3a` |
| Cold replay | `95996661c85ce21a` |
| Transcript archive | `17ab4829c18b94ce` |
| Transcript manifest | `6b7fdea075bd2f8a` |

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_bounded_lazy_transcript_bundle.py cold-replay \
  --output /tmp/f0-bounded-lazy-continuation-run01-replay.json
```

The earlier parent UNKNOWN and the separate gap-33 certificate remain
unchanged. The new terminal UNKNOWN is also frozen. No numerical status
is used as a component exclusion.
