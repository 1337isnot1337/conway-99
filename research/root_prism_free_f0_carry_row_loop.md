# Compact free-incidence continuation

This preparation retains every inequality proved in the first
individual/shared-row continuation. It uses the separate exact
binary-adder encoder for all weighted inequalities. The mathematical
domain remains all 480 first-component selectors for component zero
in the globally prism-free and $F$-free split $18+18$ case.
No incidence, second component, or alignment is fixed.

## Complete cut provenance

Before building the compact formula, the preparation cold-rebuilds
the complete preceding formula and checks each of its five candidates
against the actual cut prefix at that point. It verifies eleven
integer individual-row obstructions, 289 rational row boxes, and the
shared-edge Farkas certificate. It also reconstructs all twelve
transports of the last shared-edge cut.

The preceding run encoded only eight of those twelve transports
before reaching its variable limit. The new preparation includes
the remaining four. Their inequalities were already proved in the
frozen terminal transcript; they are not extra search assumptions.
The complete registry is 168 individual-row weighted inequalities
and 24 signed shared-row inequalities. The twelve earliest direct
row cuts remain in the unchanged baseline.

All five preceding candidates violate at least one proved inequality
in this complete registry. No clause is added merely to prevent
revisiting a candidate.

## Exact formula

| Part | Auxiliary variables added | Clauses |
| --- | ---: | ---: |
| Original incidence and twelve direct row cuts | 27,828 above the 480 selectors | 56,994 |
| 168 individual weighted inequalities | 34,428 | 265,320 |
| 24 signed shared inequalities | 37,560 | 298,056 |
| Complete formula | 100,296 total variables | 620,370 |

The complete formula has 2,404,476 literal occurrences and 15,424,105
DIMACS bytes. Its SHA256 is
`46e5cda7906d7ed409e825a5baabad0e27380fdfeffa609612c689b4a1f930ef`.
The compressed preparation is
`experiments/logs/root-prism-free/f0-carry-row-loop-preparation.json.gz`,
SHA256
`b43aedd6dda33b3b0415865831fb48e87610815f4f3659d7a59f8c5c84b0eb9e`.

For each last shared inequality, the previous decision-graph encoder
used 104,489 auxiliary variables and 187,219 clauses. The binary
adder uses 2,683 auxiliary variables and 21,331 clauses for the same
454-term predicate. The proof of the encoding and its exhaustive
Boolean controls are in `root_prism_free_f0_carry_threshold.md`.

The new clauses keep the exact integer coefficients. The encoder
does not replace them with weaker cover clauses. Every gate has a
full Tseitin equivalence, and every auxiliary ID is fresh.

## Continuation and stop rules

The prepared runner keeps the preceding limits: at most twenty
incidences, ten seconds per SAT query, sixty seconds per complete
individual-row pass, sixty seconds per shared LP, and 180 seconds
overall. Formula limits remain one million variables and two million
clauses. The per-cut gate limit remains 250,000.

A SAT selection must pass the original exact incidence checks and
every retained weighted inequality. Each selected signature then
receives its exact individual-row test. An accepted integer
obstruction produces a universal row inequality and its twelve core
transports. Only a complete sixty-row pass with sixty exact rational
boxes and no obstruction reaches the shared-edge LP.

A shared-edge infeasibility result is retained only after exact
integer Farkas verification. Its potentials are extended to all
480 signatures and its edge weights allocated over all 68,394
eligible signature pairs. The resulting universal signed inequality
and its twelve transports use the same compact encoder. An exact
feasible shared box stops the loop; it is not an exterior graph.

The runner stops on UNKNOWN, uncertified numerical output, error,
resource or time limits, an exact shared box, or incremental UNSAT.
Incremental UNSAT remains uncertified. A separate fresh proof query
must rebuild the complete necessary formula and pass direct DRAT
verification. A second cold rebuild must check retained-input
inclusion and the proof again before any conditional component
exclusion is reported.

## Frozen implementation

The new sources are:

- `experiments/workspace/root_prism_free_f0_carry_threshold.py`.
- `experiments/workspace/root_prism_free_f0_carry_row_loop.py`.
- `experiments/workspace/root_prism_free_f0_carry_row_loop_certificate.py`.

The continuation preserves the frozen individual-row and shared-row
mathematical helpers. Its source SHA256 is
`ec85c752a5d3c5538250e0099286dcbad674e23ef9572f72bbd3ca72fb5ef403`.
The fresh/cold proof wrapper SHA256 is
`6ed58e8656b5a46a8dd14e6064495dbfe2960d8916bdabc85b54ec22cd3d557a`.

This is a preparation package. Its build and cold replay call no
incidence solver or optimizer. A later query requires its separate
source and model gate. No result here excludes the component,
connected shell cases, or the unrestricted Conway99 problem.
