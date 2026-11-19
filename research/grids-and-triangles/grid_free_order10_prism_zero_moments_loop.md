# Prism-zero order-ten counts after the new moment cuts

## Result and limits

The bounded loop stopped after one LP call because neither separator
produced a fresh exact cut. The LP returned a numerical point after
14.230 seconds. Separately, rounding its core coordinates gave an exact
integral order-ten count witness that satisfies all 25 retained cuts.

This is a witness for the finite count system. It is not a graph. PSD
of the rounded witness is not certified. The moment scans below concern
the unrounded numerical point, and their absence of an exact separator
does not prove PSD.

The source was permitted at most six sequential calls, with 120 solver
seconds per call and 180 seconds per new-family scan. Its recorded stop
condition ended the run after the first call. It did not perform a second
LP, a dual extraction, or an additional optimization.

## Prepared model

The source reconstructs the earlier prism-zero baseline and first checks
its exact numerical matrix/bounds hash. It then fixes the 58 ordinary
core coordinates proved zero by prism containment and appends the eleven
new order-ten moment cuts. The original positive DP bounds and row
scalings remain unchanged.

| Property | Value |
| --- | ---: |
| Baseline rows | 47,634 |
| New seed moment cuts | 11 |
| Initial total rows | 47,645 |
| Stored numerical columns | 547 |
| Free columns after zero closure | 491 |
| Matrix nonzeros | 5,430,251 |
| Retained exact cuts | 25 |
| Old moment blocks scanned | 1,416 |
| New complete-cache blocks scanned | 916 |

The 25 retained cuts consist of one universal order-ten count cut,
thirteen previously certified moment cuts, and eleven new order-ten
moment cuts. The preparation embeds each of the eleven saved directions
into its complete, unpruned flag block and rechecks its exact count form
and reduced core form. It also reproduces all 48,965 induced counts of
the earlier seed witness from that witness's ordinary core coordinates.

All 916 new blocks come from the point-independent cache. No root or
flag was omitted because it happened to have zero count at the seed
point. During each scan a row may be removed only after every entry in
that row is exactly zero at the current dyadic point.

Preparation took 14.809 seconds and called no optimizer. Its peak
resident set was 1,198,296 KiB. The run's peak was 1,198,548 KiB.

## Numerical point and separator outcome

The only LP call used HiGHS IPM, one thread, pure feasibility, presolve,
and no crossover. It returned `kOptimal` after 13 IPM iterations. The
reported 58 fixed core coordinates were exactly zero in the stored
floating-point proposal.

The old-family scan found no exact negative integer direction. It did
record one numerical negative without an exact certificate:
`induced-schur-7.pickle`, block 409, approximately
`-2.384185793238964e-7`. This remains an unresolved numerical indication
in that scan; it is not reported as a proved violation.

The full new-family scan processed all 916 roots in 3.816 seconds. It
found no exact negative direction and no unconfirmed numerical negative.
It removed 868 rows only after exact zero-row checks. Its exact dyadic
evaluation also found no negative induced-count form at the numerical
point.

No new cut was available from either scan, so the loop stopped. The
sources retain all raw solver values, validity flags, proposal values,
model hashes, and scan results.

## Exact rounded count witness

The rounded core vector has 550 entries including the constant. The
checker imposes all 58 prism-containing core zeros exactly, then checks
every reduced count with Python integer arithmetic.

The witness passes:

- nonnegative integral counts for all 48,965 catalogue types;
- all 180,445 original extension equations;
- every level total and both nine-vertex zero-pattern checks;
- every original ordinary-core DP bound;
- all 25 retained exact cuts.

The smallest retained-cut value is 629,575. The edge-component coordinate
`x521` equals 116. Its numerical precursor was approximately 116.4510.
No extra edge-component inequality or partition face was included in
this run.

The first 58 coordinates of the new rounded witness are:

```text
1, 0, 237, 170, 428, 859, 2513, 8114, 681, 0, 5487, 263,
285, 1233, 13623, 50959, 1072, 26565, 1448, 951, 1694, 4060,
365, 679, 9861, 982, 1065, 9381, 1617, 273, 19, 2, 570,
13909, 627, 30596, 35830, 1569, 1761, 20262, 3151, 0, 0,
0, 0, 628, 0, 274, 73, 15, 1818, 280, 0, 0, 48, 97, 0, 0
```

They differ from the earlier repaired witness. Its earlier exact PSD
certificate therefore does not transfer to this new point. The saved
rounded-count file explicitly keeps `PSD_feasibility_certified: false`.

## Frozen files

Sources:

- `experiments/workspace/grid_free_order10_prism_zero_moments_loop.py`
- `experiments/workspace/grid_free_order10_r8s1_scan.py`

Their SHA-256 hashes are, respectively:

```text
a65dc6b31ebebe7bcd14398f685537f642081a7517c2e0ec94eb96246ad6e473
71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887
```

Artifacts use the prefix
`experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure`:

- `-preparation.json` and `-preparation.log` bind the model and inputs;
- `-controls.json` records exact small separator/sign controls;
- `-loop.json` and `-run.log` record the terminal one-round outcome;
- `-round0-solver-data.json.gz` preserves the solver arrays;
- `-round0-proposal.json` preserves the numerical point;
- `-round0-old-separation.json` records the old-family scan;
- `-round0-r8s1-separation.json` and `-round0-r8s1-replay.json`
  record the complete new-family scan and exact certificate replay;
- `-round0-rounded-counts.json` contains all 550 integer core entries and
  all 48,965 integer induced counts;
- `-manifest.json` binds this package.

The preparation SHA-256 is
`fce82618e5beef610d70fadbf7b0e5d955a43496c05c3621b78ee270ff87c820`.
The terminal result SHA-256 is
`1087850a3cdb2d8d9a349c1a0bb4c67c60a2a74e3688081f2aa063b2be987d46`.
The exact rounded-count witness SHA-256 is
`3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326`.

The numerical model hash is
`62664e9c7d7fd5abe9ca61585e10f0d3714bbd72509dca0e7a54d725cbd5943e`.
All earlier preparations, count witnesses, certificates, and caches
remain unchanged.
