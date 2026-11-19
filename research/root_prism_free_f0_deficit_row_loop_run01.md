# Exact-deficit continuation: terminal clause limit

The single prepared continuation stopped at the fixed two-million
clause limit after 45.878523 seconds. It generated fourteen valid
incidence selections. Exact individual or shared-row certificates
rejected every selection. It did not return UNSAT and does not
exclude the component.

The hypothesis remains component zero in a globally prism-free
and $F$-free split $18+18$ shell. All 480 incidence selectors were
free. No first design, second component, or alignment was fixed.

## Exact outcomes

The fourteen complete individual-row passes produced 26 integer
obstructions and 814 rational row boxes. Each accepted object was
replayed in exact arithmetic. The obstructions produced 312
transported inequalities, of which 299 entered the formula.

Iterations nine, ten, and eleven had sixty exact individual row
boxes and proceeded to the shared-edge stage. All three shared
tests produced complete exact integer Farkas certificates under
the new deficit reconstruction.

| Iteration | Eligible shared edges | Nonzero ray entries | Largest absolute entry | Rounding scale | Exact RHS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 9 | 1,217 | 22 | 6 | 1 | -1 |
| 10 | 1,220 | 53 | 7 | 2 | -1 |
| 11 | 1,220 | 21 | 3 | 1 | -1 |

Each ray was lifted over the complete 68,394-edge signature domain.
Each lift has normalized gap one at its generating selection.
All twelve verified core transports were inserted for each lift,
giving 36 new signed inequalities. No numerical-only inference
or unproved visitation block was used.

The final individual-row pass produced five exact obstructions and
sixty transported inequalities. Forty-seven fitted within the fixed
clause limit; the next inequality was refused before any partial
encoding was returned. The thirteen unencoded inequalities remain
proved and stored in the full row transcript. Their normalized
predicates are distinct from the 647 retained individual predicates.

The complete proved registry therefore has 660 individual weighted
inequalities and 72 signed shared inequalities. The terminal CNF
contains 647 of those individual inequalities and all 72 signed
inequalities, plus the twelve earliest direct row cuts.

## Terminal formula and verification

The final formula has 276,792 variables and 1,999,803 clauses.
Its 54,794,644 DIMACS bytes have SHA256
`e1de52b6da658d07265bbbbbda0898fcdaef1a53a2a0823778a7a7df484944a3`.
The terminal result SHA256 is
`13b47be2d896887c3b23c435499bc6b4ba75c541469a3de229cebeb98b14a8fe`.
Peak recorded memory was 550,084 KiB. There was no overall time
overrun and no second query.

The cold replay reconstructed the exact starting provenance,
all fourteen actual candidate prefixes, all 26 integer row
obstructions, 814 rational boxes, three complete shared rays,
their full-domain lifts, and the exact terminal CNF hash. It called
no solver or optimizer. The result remains
`STOP: encoding resource limit; unresolved`.

The thirteen additional predicates are available to a later
encoding. Their proof does not depend on having fitted in this
formula. Any later encoding or clause representation must preserve
their exact mathematical meaning or prove each weaker clause
from the corresponding inequality.

## Compressed transcript

The 39 immutable JSON records occupy 17,703,591 uncompressed bytes.
The deterministic archive
`experiments/logs/root-prism-free/f0-deficit-row-loop-run01-transcript.tar.gz`
contains their exact bytes in 1,214,414 bytes. Its SHA256 is
`ee4a0753cce1094475c758da901b330def95dc1c5beb27b12b059d35bd4e590b`.
The adjacent `f0-deficit-row-loop-run01-transcript-bundle.json`
records every member hash, byte count, and the archive hash.

The frozen source
`experiments/workspace/root_prism_free_f0_deficit_transcript_bundle.py`
checks every archive member before restoration. It only writes
missing JSON records beneath the one fixed transcript directory.
An equal existing file is preserved; an unequal file causes refusal.
Archive paths, regular-file types, symlink-resolved containment,
member ordering, sizes, and hashes are all checked. The positive
restore, equal-file reuse, and mismatch-refusal controls use a
disposable directory.

The `restore` mode restores only missing records. The `cold-replay`
mode first restores them and then invokes the frozen mathematical
and CNF replayer. Both require a new `--output` path. The final raw
CNF is omitted from the archive because its exact source rebuild
has already passed.

No full graph, completed exterior graph, component exclusion,
or unrestricted Conway99 resolution was obtained in this run.
