# The 47-cut repair and the 48-cut zero face

The latest saved point has nonnegative integral induced counts through
order ten, satisfies all 180,445 original equations, and satisfies 48
retained inequalities. It also has `x1=x521=0`. This is a finite count
witness. It is not a graph or a certificate for every moment condition.

## From 44 to 47 inequalities

The six-root loop starts with the previous 25 inequalities, eighteen
six-root inequalities, and the edge-component inequality
`4158-3*x1-2*x521>=0`. It fixes all 58 ordinary prism-containing cores.
The prepared model has 47,664 rows, 547 columns, and 5,438,205 nonzeros.

The first numerical solution gives three new six-root separators, with
root catalogue indices 96, 76, and 81. A separate constructor reproduces
all 15,979 supported product entries. It then reconstructs the induced
forms and all 550 reduced coefficients using Python integers. Each
primitive form has a strictly negative exact value at the saved dyadic
proposal. The replay uses no eigensystem or optimizer.

The second numerical solution satisfies the 47 retained inequalities.
All 2,394 selected blocks are scanned completely without another exact
separator. Rounding produces one negative induced count: type 48,668
has value minus four. Changing only `x525` from 119 to 118 makes that
count zero. Every count remains a nonnegative integer, and every bound
and held inequality remains satisfied.
The saved witness has `x521=88` and minimum held-cut value 3,193.

An independent audit checks all 48,965 induced counts, all original
equations, all eleven level totals, 549 ordinary upper bounds, the
1,443 prism-containing induced zeros, and all 47 inequalities. A separate
scan of the integer point completes all 2,394 blocks with no exact or
unconfirmed numerical negative. That scan does not certify exact PSD.

## A four-cycle flag rejects that point

The [additional flag families](grid_free_order10_higher_flags_results.md)
contain nine four-root blocks with up to three free vertices and two
two-root blocks with up to four free vertices. Their complete product
cache has eleven blocks and 90,256 lower-triangle entries. Flags count
labelled free-vertex assignments; stabilizer multiplicities are retained.

The four-cycle root gives a 39-term induced-count inequality with value
`-101639192` at the repaired 47-cut point. An independent direct graph
constructor reproduces its 78 supported products. Reduction through the
previously audited count matrix gives the following primitive inequality:

```text
277887456 - 200496*x1 - 107305*x2 - 66832*x12
 + 66832*x21 - 200496*x44 - 66832*x86 + 34184*x381
 - 25376*x384 - 49612*x395 + 49612*x414 - 34184*x425
 - 17485*x449 - 73658*x537 >= 0.
```

This inequality excludes the saved point, not the entire prism-free
count face. The earlier count audit and its narrower scan remain valid
within their stated families. A separate
[four-cycle decomposition](grid_free_order10_higher_flags_c4_structure.md)
also gives a simpler 18-term variance inequality, reconstructed from
three products. Its primitive value at that point is minus 2,800.

## A new point with both motif counts zero

The next model retains all 48 inequalities and also fixes `x521=0`.
It has 47,668 rows, 547 columns, 490 free columns, and 5,439,078 nonzeros.
Its numerical model SHA256 is
`dd90c9323bc4ae6672b70020dd2902696116404fb1fe7abe54489466691c64ad`.
The cut-coefficient SHA256 is
`f240480eb4c6b5ac084d79aedfc143506c0e03cf5202359b8a3434cc61eeece4`.

The first IPM call returns an optimum in 20.224 seconds. Rounding this
proposal directly gives an exact count witness. No repair is needed.
Its SHA256 is
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
The smallest held-cut value is 3,182. All 59 required ordinary zeros
hold: the 58 prism-containing cores and coordinate 521.

The separate face auditor checks all original equations, level totals,
ordinary bounds, required zeros, and 48 inequalities using Python
integers. It also evaluates all 48,965 induced rows and 549 ordinary
rows of the frozen, coefficientwise-audited reduction and matches the
saved counts. It does not derive that reduction again. The audit passes
in 16.518 seconds. A non-author source review also passes.

All 2,405 selected blocks are scanned at the **unrounded numerical
proposal**, with no exact separator. This statement does not transfer
that scan to the rounded point. At the rounded point, a separate exact
congruence proves that the entire 15-flag four-cycle block is PSD of
rank thirteen. It checks all 44 principal minors of the four distinct
blocks in the decomposition. Its simpler variance has value 3,568.
No exact PSD certificate is claimed for the other 2,404 blocks.

The selected family does not include the new eight-root spectral
projector and per-embedding Schur blocks. Those are a separate test.
The unrestricted existence problem remains open in this repository.

## Replay

Commands run from the repository root. The catalogue and reduced cache
are the same hash-bound caches used by the earlier order-ten audits.
Use a new output path if a report already exists.

```sh
.venv/bin/python experiments/workspace/grid_free_order10_r6s2_new_cuts_replay.py \
  --reduced-cache /tmp/conway99-order10-reduced.pickle \
  --output /tmp/conway99-r6s2-three-cuts-replay.json --seconds 120

.venv/bin/python experiments/workspace/grid_free_order10_higher_flags_fresh_replay.py run \
  --preparation experiments/logs/moments-and-counts/order10-higher-flags-r4s3-fresh-preparation.json \
  --output /tmp/conway99-r4s3-cut-replay.json --seconds 60

.venv/bin/python experiments/workspace/audit_prism_zero_held_count_face_witness.py \
  --witness experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json \
  --sha256 0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df \
  --catalogue /tmp/conway99-order10-catalogue.pickle \
  --cuts experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01.json \
  --cuts-sha256 9230f3b8b4f9fa47bd587b9e58bedf57b3710d689e96ae8db11592c88423f07e \
  --expected-cut-count 48 --reduction /tmp/conway99-order10-reduced.pickle \
  --output /tmp/conway99-48cut-face-audit.json
```

The discovery records retain raw proposals, solver metadata, every
separator scan, exact cut replays, and the failed pre-repair rounding.
The publication manifest lists their hashes. Neither a timeout nor the
absence of a numerical separator is used as an exclusion certificate.
