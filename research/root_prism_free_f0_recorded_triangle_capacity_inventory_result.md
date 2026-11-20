# Recorded triangle capacity inventory: complete proposal, timed out finalization

The one source-bound extraction produced the complete saved-incidence
table and every proposed row, then exceeded its declared ten-second
limit during final serialization and hashing. Its original finalization
and owner remain explicitly unaccepted. No retry was performed.

This is a read-only metadata extraction from the already accepted
5,364 triangle indicators. It did not construct a native model, enumerate
a new signature or triangle domain, or call an optimizer.

## Preserved outcome

| Item | Observed result |
| --- | --- |
| Inventory phase | 8,374 milliseconds |
| Source through final serialization/hash | 12,196 milliseconds |
| Outer owned call and receipt binding | 17,209 milliseconds |
| Declared bound | 10,000 milliseconds |
| Source finalization | UNACCEPTED_METADATA_FINALIZATION_BUDGET_OVERRUN |
| Owner | UNACCEPTED_TRIANGLE_CAPACITY_METADATA_EXECUTION |
| Owner report_accepted | false |
| Complete report | 2,879,184 exact bytes |

The report's internal construction status is
PASS_COMPLETE_SAVED_TRIANGLE_INCIDENCE_AND_SUFFICIENT_IMPLICATION_AUDIT.
That status is subordinate to the failed finalization and owner. It does
not constitute acceptance of this run or of a native model.

All three exact outputs were preserved and uploaded before any next
work. Their identities are:

- Report: experiments/logs/root-prism-free/f0-recorded-triangle-capacity-inventory01.json,
  Git 8201fa6b57efd6be545a4465fdf80aa8c69bf30c,
  SHA-256 2f8eea3f1bb67c796ca8bc1deb06606d0e0c2f1948838128fbc30ed05b6eb09c.
- Finalization: experiments/logs/root-prism-free/f0-recorded-triangle-capacity-inventory01-finalization.json,
  Git 0efb7ed6e15f5cc153c0dbaa27b9e9575637f308,
  SHA-256 aa3eb24fa0b711cc751b31f299ccaf5f50302b134486b15a7f1cde9fb0ecc27c.
- Owner: experiments/logs/root-prism-free/f0-recorded-triangle-capacity-inventory01-owner.json,
  Git 647c89b1901188ecf2fa4ea609d2115f6a4553ae,
  SHA-256 958f6ac9c21c103bfa663be687bbfde492858e7b4a62532886ca6daeb0e663d3.

## Exact saved proposal

The report contains all 6,300 nonempty edge-incidence lists. These split
into 84 existing target equalities, 3,312 existing singleton AND upper
bounds, and 2,904 proposed non-target side capacities. The complete
vertex-incidence list gives 420 nonempty local proposals and sixty
tautologies.

The saved proposal has 3,324 rows and 26,832 terms, with no new variables.
Its sufficient Boolean implication audit certifies 1,548 side rows from
pairwise original Gram/mixed conflicts and another 48 from the installed
forest extensions. The other 1,308 are unresolved by those sufficient
checks. Every row is retained. Neither continuous redundancy nor full
model nonredundancy is inferred from this classification.

The exact digest descriptor is
experiments/logs/root-prism-free/f0-recorded-triangle-capacity-row-keys01.json,
Git 91b8c95924a9936760136b93d39df89e2f2d1d8f,
SHA-256 0599b49e238d17186ffc112cc8f8d581880a13c2c5407bd7a52ad566433368e1.
It was obtained by projection and hashing of the preserved report,
without rerunning the extractor.

| Ordered row-key array | SHA-256 |
| --- | --- |
| All 3,324 rows | 9e7d7387a389e31232799697b7228976dfb4ae22980bf0a6ecc3885456e93b43 |
| Side-edge rows | b8c8e2967bbebae3036e30e142a34b1969b560609cfcf83802bcfb8cb636356e |
| Local-selector rows | 0204d653b732885307d617f5099955dab71af0de4103ea9e81f743c9d874b175 |

These are hashes of compact JSON arrays without a trailing newline.
Their order is ascending original edge ID for side rows, then ascending
selector ID for local rows.

## Authority for any future use

The report is an untrusted proposal table. Its failed time bound is not
waived or relabelled. Any later acceptance of mathematical rows must
cite an independent reconstruction of every incidence and row from the
previously accepted indicator/domain/native metadata, followed by the
separate native construction and replay required for a model change.

The mathematical inequalities themselves are proved in
[root_prism_free_f0_recorded_triangle_capacities.md](root_prism_free_f0_recorded_triangle_capacities.md).
Their source/theorem review is Git
aeff91a3a8f7f23c3684a7f80e2fd6d1b1d332b7,
SHA-256 ebc4e422b5283d3070425f70875fd59f49ed57ef50800fcc5a24f57d954cae1b.
That review explicitly did not execute the extraction.

The distinct continuous bound of eighteen for the 84 target edges has
its own complete independent coefficient/orientation check, Git
4fdaa03c481c57af8b55922be9b8f17d6658fd4c,
SHA-256 84572d32b842a905db9b08efe91be0fbf3fb8c1185ead6b782d9f6555f4eed3d.
Its proof does not depend on this failed metadata run.

The current native model and current solver query were not modified.
No graph, first-component exclusion, or complete SRG result is claimed.
