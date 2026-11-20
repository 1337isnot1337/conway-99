# The bounded case4 binary query remains unresolved

The single prepared CaDiCaL300 query on the complete case4 CNF with 85
additional proved zero units reached its 180-second owned-child wall
limit. The parent saved UNKNOWN before terminating and reaping the child.
There is no accepted binary incidence, UNSAT proof, or case exclusion.

The query used the frozen formula with SHA-256
`f3467d02ca6763391668c0cdac0a395dab23688d831b25107fcf04ea1c94ac22`:
134,852 variables and 439,689 clauses. All 439,604 previous clauses were
preserved, with precisely 85 negative primary units appended. Together
with the 14 existing units, these impose the independently proved
99-coordinate zero face. All original incidence choices outside that
face remain available. No value or active-basis assumption from the real
selector point was imposed.

The child completed clause streaming and bootstrap in 6.835819 seconds
and recorded entry into its one solver call. It did not return a solver
answer before the deadline. The total parent operation took 180.090988
seconds. The saved log contains no final solver statistics, so it does
not identify how the remaining time was divided among internal solver
phases. No memory or proof-size refusal was observed. No retry was run.

The separate cold replay passed in 28.002218 seconds. It rebuilt the
complete original formula and every added unit implication, reproduced
the exact full CNF hash, and checked the unresolved terminal bindings and
the owned child's termination record. It called neither a solver nor a
proof checker: there was no completed proof to verify.

The terminal result is
`experiments/logs/grids-and-triangles/rook-case4-face99-boolean-run01/result.json`,
SHA-256
`b17958a2e0544391cc9699d08cda417924d3c18f9224e2ed15e233c82e65bf45`.
The cold report is
`experiments/logs/grids-and-triangles/rook-case4-face99-boolean-run01-replay.json`,
SHA-256
`5f642dd8e62081766960d16a10bbfe860894b01efffcb8f8142937c62eb417ae`.
The child log and its bootstrap record are retained alongside the result.

The exact rational point previously recovered on the full real selector
relaxation remains valid. Its positivity on all 1,115 unforced coordinates
prevents further coordinate-zero deductions from that real relaxation
alone. The Boolean timeout does not strengthen or refute that statement;
it leaves the integral incidence question open.

The preparation, limits, exact unit provenance, and candidate/proof
acceptance rules are documented separately in
`rook_case4_face99_boolean_preparation.md`. The terminal manifest binds
those files, the independent source review, and the actual query and replay
records.
