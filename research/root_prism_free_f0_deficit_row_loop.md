# Free-incidence continuation with exact-deficit ray reconstruction

This separate preparation retains the complete compact-run cut
registry and adds the twelve subsequently proved repaired-ray
transports. It preserves the compact run's recorded UNKNOWN status.
No earlier source, formula, cut, or solver result is changed.

The domain is still all 480 first-component incidence selectors for
component zero in the globally prism-free and $F$-free split $18+18$
case. No first incidence, second component, or alignment is fixed.

## Complete starting formula

The preparation first cold-replays the preceding compact formula,
all nine actual candidate prefixes, fifteen exact individual-row
obstructions, and 525 exact rational row boxes. That replay includes
its own complete inherited provenance. It then regenerates the
separate repaired-ray certificate and all twelve new transports.

The starting registry contains 348 individual weighted inequalities
and 36 signed shared-row inequalities. The twelve earliest direct
row cuts remain in the unchanged baseline. Every weighted predicate
uses the already audited full-Tseitin binary-adder encoder.

| Part | Auxiliary variables added | Clauses |
| --- | ---: | ---: |
| Original incidence and twelve direct row cuts | 27,828 above the 480 selectors | 56,994 |
| 348 individual weighted inequalities | 77,112 | 596,580 |
| 36 signed shared inequalities | 103,416 | 822,876 |
| Complete formula | 208,836 total variables | 1,476,450 |

The complete formula has 5,816,352 literal occurrences and 39,946,715
DIMACS bytes. Its SHA256 is
`2c528bfce40ea18b82949fbb45dcb05f683096c8c9ab2dd94583e238ab458cb3`.
The compressed preparation is
`experiments/logs/root-prism-free/f0-deficit-row-loop-preparation.json.gz`,
SHA256
`8884d196447a51e6104e473794a402cd2c0ab54465207355face9f20041faa08`.

The twelve repaired inequalities account for 65,856 new auxiliary
variables and 524,820 clauses. Their insertion remains below the
unchanged resource limits. All nine prior candidates violate a
proved inequality in the starting registry; none is blocked by
an arbitrary visitation clause.

## Revised numerical proposal stage

The shared-edge LP itself is unchanged: one undirected variable per
eligible selected pair, all mixed and degree equations, and bounds
from zero to one. A numerical point still requires exact rational
reconstruction before it is accepted. A numerical infeasibility
answer only proposes equality multipliers.

For each proposed integer equality vector $\lambda$, the new helper
sets

$$
u_e=\max\{0,-(A^T\lambda)_e\}.
$$

This guarantees the required nonnegative primary and upper-slack
coefficients. It still accepts the ray only if the complete exact
verifier proves $b^T\lambda+\sum_eu_e<0$. This is the same
certificate theorem as `root_prism_free_f0_shared_ray_repair.md`.

The helper tries a fixed list of small integer rounding scales in
both orientations. Its final proposal uses the common denominator
of the exact dyadic representations of the saved floating-point
equality multipliers. Because these denominators are powers of two,
their maximum is a common multiple. The common scaling preserves
those proposed equality values exactly. Acceptance still depends
only on the subsequent integer sign and strict-gap checks.

Every accepted report stores its numerical values and the precise
orientation and scale. Replay recomputes the rounded equality
multipliers and exact upper deficits before checking the complete
ray. The helper never accepts a numerical sign or status as a proof.
If all exact reconstructions fail, it records UNKNOWN.

The preparation directly tests this helper against the frozen
1,228-edge example. It reproduces the same integer ray with right
side $-26$, the same potential gap 78, and all twelve normalized
selector transports with gap 26. This control calls no optimizer.

## Unchanged bounds and proof gate

The runner retains the same limits: at most twenty incidence
queries, ten seconds per SAT query, sixty seconds per individual-row
pass or shared LP, and 180 seconds overall. It keeps the ceilings of
one million variables, two million clauses, and 250,000 gate states
per inequality. No weaker cut representation is added in this model.

Each SAT selection receives the complete exact incidence and cut
inspection. Individual-row separation runs first; shared-edge
separation requires a complete pass of sixty exact individual
boxes. Only exact necessary inequalities receive core transports
and enter the free-selector formula.

An exact shared box, UNKNOWN, an error, a resource or time limit,
or incremental UNSAT stops the loop. A shared box is a rational
relaxation point, not an exterior graph. Incremental UNSAT remains
uncertified until a fresh full-formula proof passes DRAT and a
separate cold retained-input/proof replay.

## Sources and scope

The new files under `experiments/workspace/` are:

- `root_prism_free_f0_shared_deficit_separator.py`, SHA256
  `6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf`.
- `root_prism_free_f0_deficit_row_loop.py`, SHA256
  `27b10330125ca5586512e2a4d3f8a297cf203dbb05e246bda4820240d03e940e`.
- `root_prism_free_f0_deficit_row_loop_certificate.py`, SHA256
  `f023da2322053bd15c844f6c8c3c63d54feb3e5ed8ed51b1df0f6cb18319d419`.

The preparation and its cold replay call no incidence solver or
optimizer. A further bounded query requires its separate source
and model review. This package reports no component exclusion,
completed exterior graph, or unrestricted Conway99 result.
