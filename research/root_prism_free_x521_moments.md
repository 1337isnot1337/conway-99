# Moment scans of the exact x521-zero count witness

The exact integer count witness on `x521=0` produced no new separator
from either existing moment family. Both scans completed, with no exact
negative block and no unconfirmed numerical negative. This is a scan
result, not an exact PSD certificate.

The count witness itself was proved feasible for the finite count model
in [`root_prism_free_x521_face.md`](root_prism_free_x521_face.md). These
scans do not modify that witness, its model, or its one-call LP outcome.
No LP is called by this package.

## Input and exact conversion

The input is the saved rounded integer witness, SHA-256
`ee8e22f070e0529be5be8bf14c853c6ad9ed97127570223abf6e1529ab8857f9`.
It is not the unrounded IPM proposal. Its independent full-model replay
checked all 48,965 induced counts, all 180,445 extension equations,
59 required core zeros, the original DP bounds, and all 25 retained cuts.

The frozen scanner interfaces accept floating-point ordinary core
coordinates. The adapter first checks every one of the 550 integers is
nonnegative and strictly smaller than `2^53`. It then requires
`float(value).as_integer_ratio() == (value,1)` for every coordinate.
After writing the scanner input, it invokes both scanners' exact input
parsers and checks that they recover precisely the original integer
vector, with denominator one. The old scanner reads the first 58
coordinates; the new scanner reads all 550.

The adapter binds both scanner source hashes, all twelve old-family
cache hashes, the old count-form cache, and the complete new cache.
The new scanner also reproduces all 48,965 stored integer induced counts
from the supplied core coordinates before scanning.

## Results

| Family | Blocks scanned | Exact negative blocks | New cuts | Unconfirmed numerical negatives | Scan seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing ordinary/induced order-nine families | 1,416 | 0 | 0 | 0 | 0.913 |
| Complete order-ten `r=8,s=1` family | 916 | 0 | 0 | 0 | 4.074 |

The complete new-family cache contains every required eight-vertex root
and its flags. It was prepared independently of this point. No block or
flag was omitted because its count vanishes at the witness. During the
scan, 868 row occurrences were removed only after checking every entry
of each row was exactly zero.

The combined run, including cache checks and exact replay stages, took
13.929 seconds and reached peak resident memory 853,736 KiB. The new
scan completed before its 180-second bound. No timeout occurred.

## Exact gates and remaining limit

Numerical eigensystems only propose integer vectors. Both frozen
scanners contract each proposed vector against the appropriate moment
form with integer arithmetic and accept it only when the resulting
integer value is negative. The adapter replays every accepted vector
and combines its necessary inequality into a 550-coordinate row. A row
already among the 25 satisfied seeds would trigger an error, since it
cannot be negative at this exact witness.

There were no accepted vectors in this run. The saved replay therefore
checks source/cache/input provenance, exact integer conversion, the
stored count vector, and consistency of the empty cut lists. It does
not prove that all passing moment matrices are PSD. Numerical scans can
fail to produce a certificate even when a matrix has a small negative
eigenvalue; exact PSD certificates would require a separate calculation.

This package supplies no graph, no new graph exclusion, and no new
constraint for the count model. It records that these two frozen
separator families did not reject this exact count witness.

## Files and replay

Source:

`experiments/workspace/root_prism_free_x521_moments.py`

Source SHA-256:

`f35d60d5583fa974bef00577724ef16b54dc858c5517e33bef8dd14f11a6712f`

Artifacts use the prefix
`experiments/logs/moments-and-counts/prism-zero-order10-x521-integer-moments`:

- `-input.json` stores the exact integer witness through the scanner interface;
- `-old1416.json` and `-old1416-replay.json` record the old-family scan;
- `-r8s1.json` and `-r8s1-replay.json` record the complete new-family scan;
- `-result.json` records the combined outcome and exact input controls;
- `-scan.log` and `-replay.log` record the two processes;
- `-manifest.json` binds the package.

The replay does not recompute numerical eigensystems or call an optimizer:

```bash
.venv/bin/python experiments/workspace/root_prism_free_x521_moments.py replay
```

Add `--rebuild` to reconstruct the bound parent count model instead of
reading the locally generated, hash-bound face cache. That reconstruction
requires the existing reduction cache and approximately 1.2 GiB of memory.
