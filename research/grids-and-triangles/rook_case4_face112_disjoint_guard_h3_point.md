# Grouped guard cuts at the exact H3 point

All 227 previously certified grouped guard inequalities pass at the new
exact H3 selector point. Every inequality is strict.

The point is
[the H3 basis candidate](../../experiments/logs/grids-and-triangles/rook-case4-face112-h3-basis-run01/candidate.json),
with SHA256 cecacaaa1cb6974dd898f1d2b69be32a06e44e9b89a1b45e35717bc347d3b4e8
and common denominator 27,131,679,103. Its original constraints and H3
were independently checked in report
f20cb9ffe3768591cd255dd9b148881d7c3df8df80fb881a7c59a75c6758395c.

The [separate contraction record](../../experiments/logs/grids-and-triangles/rook-case4-face112-disjoint-guard-h3-point01.json)
has SHA256 a7c09c90ca241e23385b4469ebbcf942c086707ce063c56b9ff169d734691e9b.
It checks all 1,681 coefficient occurrences with Python integers after
canonical decimal-string parsing. Every value is also checked through
the corresponding guard-and-target formula.

The smallest slack is
1,930,960,324 / 27,131,679,103. The inequality
x74 + x75 + x76 + x77 + x176 + x177 + x178 <= x535
has slack 12,971,644,484 / 27,131,679,103.

No optimizer or propagation runs in this check. No old point contraction
is repeated. Passing this finite family does not establish a Boolean
incidence or a completed graph.
