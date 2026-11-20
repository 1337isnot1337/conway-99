# Bounded order-ten count and moment-cut loop

## Result and scope

This run added nine exact necessary moment inequalities and then stopped at
its prescribed time limit. It did not produce a count witness or an
infeasibility certificate.

The first LP round returned a numerical proposal. Exact integer quadratic
forms reject that proposal in nine of the 1,416 cached moment blocks. The
second round, with all nine new inequalities present, reached its
30-second limit. No later round ran. No dual extraction ran.

The resulting fourteen inequalities consist of thirteen moment inequalities
and the previously proved universal order-ten count inequality. These are
necessary inequalities, not an exhaustive description of the moment cone.
In particular, the 1,416 cached blocks do not comprise every conceivable
order-nine PSD inequality.

## Model

The model uses the frozen order-ten reduction and the complete subset-DP
ordinary-count upper bounds from
[the scaled count search](grid_free_order10_scaled.md). It fixes only the
constant coordinate to one and the rook and broken-rook coordinates to
zero. The remaining 547 ordinary core coordinates are free. Each coordinate
is divided by its exact upper bound, giving numerical bounds from zero to
one. The objective is zero.

The base model has 47,620 induced-count inequalities and 5,427,663 nonzero
coefficients. Initially it adds the four exact cuts from
[the previous moment separation](grid_free_order10_moments.md) and the
universal order-ten count cut. The initial model therefore has 47,625 rows
and 5,427,792 nonzeros.

The independently saved `order10-reduction-audit.json` checks all 180,445
original extension equations after exact reduction. Every equation reduces
identically to zero. The induced-count coefficient forms are integral, and
the ordinary embedding forms have the required automorphism divisibility.
There are no additional reduced equalities or congruences to append. The
loop result binds that audit by SHA-256.

The loop uses one single-thread HiGHS simplex instance. New rows are
appended to that instance, allowing the solver to reuse its basis. Each
round has both a 30-second cancellation timer and the corresponding
cumulative HiGHS time limit. The source permits at most six rounds and
stops on any nonoptimal numerical status or on failure to find a fresh
exact separator. This run stopped after two rounds.

## Recorded rounds

Round numbers below are zero-based, as in the saved artifacts.

| Round | Rows | Held cuts | Numerical status | Solver seconds | Simplex iterations | Fresh exact cuts |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 0 | 47,625 | 5 | Optimal | 12.925 | 294 | 9 |
| 1 | 47,634 | 14 | Interrupted at time limit | 30.042 | 2,917 | None tested |

Only round zero produced a proposal. Its full 547-coordinate proposal is
preserved, including the exact floating-point values used by the scanner.
Those values are interpreted as dyadic rationals for exact separation.
No rounding of that proposal is accepted as a count witness.

## Nine additional exact separators

For each negative block, the scanner saves an integer vector, the exact
quadratic-form contraction, and the resulting primitive integer linear
form in the 58 order-nine coordinates. Each form is strictly negative at
the saved proposal and nonnegative at the previously published order-nine
positive control. The positive control checks the implementation; it does
not prove that the control extends to order ten.

| Cache | Block | Root type | Matrix order |
| --- | ---: | ---: | ---: |
| `moments-5-2-512.pickle` | 15 | 32 | 19 |
| `induced-moments-3-3-512.pickle` | 0 | 4 | 18 |
| `induced-moments-3-3-512.pickle` | 1 | 5 | 9 |
| `induced-moments-5-2-512.pickle` | 12 | 29 | 41 |
| `induced-moments-5-2-512.pickle` | 15 | 32 | 19 |
| `induced-moments-5-2-512.pickle` | 16 | 33 | 19 |
| `induced-moments-5-2-512.pickle` | 17 | 34 | 13 |
| `induced-moments-5-2-512.pickle` | 19 | 36 | 26 |
| `induced-moments-7-1-512.pickle` | 177 | 281 | 14 |

The cached forms are contracted with Python integers. Off-diagonal terms
receive the factor two. Dividing by a positive coefficient gcd preserves
the inequality. The saved dyadic numerator is strictly negative in every
case. Replaying these nine certificates requires no LP solve and no
numerical eigensystem.

No negative integer-vector certificate was found in the two additional
projector caches. This is a limit of the scan, not a proof that those
matrices are PSD at the proposal. The proposal is already excluded by the
nine exact inequalities listed above.

## Reproduction and bindings

The frozen driver is
`experiments/workspace/grid_free_order10_moments_loop.py`, SHA-256
`549233611473b1c3558bb19a26d6dbeb532463123684e023963f05dab58ed4f4`.
It reuses the frozen scaled finder, moment separator, and universal-cut
exporter. Their hashes and all input hashes appear in the preparation
artifact.

Artifacts use the prefix
`experiments/logs/moments-and-counts/grid-free-order10-moments-loop`:

- `-preparation.json` and `-preparation.log` record the reviewed model.
- `.json` and `.log` record the bounded run and its exact stop status.
- `-round0-proposal.json` preserves the numerical proposal.
- `-round0-separation.json` contains all nine integer-vector certificates
  and their complete linear coefficient vectors.
- `-round0-replay.log` records exact replay of those nine certificates.
- `-manifest.json` binds the frozen files and summarizes the result.

Run the inexpensive certificate replay from the repository root:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_moments.py replay \
  experiments/logs/moments-and-counts/grid-free-order10-moments-loop-round0-separation.json
```

The saved source also exposes `prepare` and `run` commands. The recorded
run used `--rounds 6 --seconds 30` and bound
`experiments/logs/moments-and-counts/order10-reduction-audit.json` through
`--extension-audit`. Replaying the exact certificates does not require
rerunning the bounded optimization.
