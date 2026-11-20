# Two more excluded matchings for the first local eight-set

The indexed 35-vertex cores **9 and 10 are excluded**. Each result has a
checked retained DRAT proof, full cold reconstruction of its original
incidence formula, and exact certificates for the additional Gram clauses
used by the retained proof.

These are two local-core exclusions. They do not exclude the first local
eight-set, the complementary-rook 27-core, or a Conway99 graph. The checked
exclusions among the first set's 28 possible matchings are now

\[
\{0,1,2,3,8,9,10,21\}.
\]

The other 20 matchings remain unresolved. Earlier ten-second UNKNOWN
records are unchanged; the two new runs and their proofs form a separate
checkpoint.

## The fixed cores and complete incidence domains

Use the complementary-rook 27-core and signature ordering from
[`complement_rook_35core_domains.md`](complement_rook_35core_domains.md).
The first local eight-set has original signature indices

\[
L=(0,1,9,10,18,20,26,27).
\]

Matching endpoints below are positions in this ordered list. Case 9 uses
\((0,5),(1,4),(2,6),(3,7)\). Case 10 uses
\((0,5),(1,4),(2,7),(3,6)\).

For either 35-core with adjacency matrix \(B\), the remaining 64 vertices
must have attachment columns \(h_v\) satisfying

\[
G=12I+2J-B^2-B=\sum_v h_vh_v^{\mathsf T}.
\]

The frozen original formula contains the complete admissible attachment
domain, all Gram equalities, at most one column for each original
three-point signature, and all required core-triple packing conditions.
See [`complement_rook_35core_incidence.md`](complement_rook_35core_incidence.md)
for the model and its scope. No full exterior graph is assumed or fixed.

The new formulas preserve every original clause and variable. They append
only the binary exclusions certified in the bounded
[`downdate preparation`](complement_rook_35core_downdate_preparation.md).

| Case | Attachment columns | Variables | Original clauses | Appended binary clauses | Solve time, including bootstrap | Retained input clauses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 1,284 | 114,173 | 233,228 | 839 | 7.336 s | 21,217 |
| 10 | 1,160 | 102,301 | 208,762 | 490 | 5.135 s | 19,528 |

Each query was fresh, proof-enabled, and limited to 60 seconds including
bootstrap. The direct proof check and the cold proof check each had a
separate 60-second limit. Both queries returned UNSAT, and all checks
passed. There were no additional cases or retries.

## Only five extra inequalities are needed by the retained proofs

If columns \(h\) and \(k\) are both selected, then

\[
G-hh^{\mathsf T}-kk^{\mathsf T}
=\sum_{v\ne h,k}h_vh_v^{\mathsf T}\succeq0.
\]

Thus any integer vector \(w\) for which

\[
w^{\mathsf T}Gw-(w^{\mathsf T}h)^2-(w^{\mathsf T}k)^2<0
\]

certifies the binary clause forbidding that pair. This uses the exact Gram
identity and nonnegative summands; it introduces no additional graph
assumption. The vectors need not be eigenvectors or involve an inverse.

The retained case-9 proof uses two clauses outside its original formula;
the retained case-10 proof uses three. Their large discovery vectors were
rounded to small integer vectors and then checked again against the full
35-by-35 matrix. The certificate records every vector and column.

| Case | Forbidden primary selectors | \(\|w\|_\infty\) | \(w^{\mathsf T}Gw\) | \((w^{\mathsf T}h,w^{\mathsf T}k)\) | Residual value |
| --- | --- | ---: | ---: | --- | ---: |
| 9 | 976, 989 | 8 | 443 | \((-18,-11)\) | \(-2\) |
| 9 | 298, 308 | 14 | 1,452 | \((-25,-29)\) | \(-14\) |
| 10 | 827, 1,135 | 10 | 540 | \((-18,15)\) | \(-9\) |
| 10 | 286, 1,135 | 9 | 544 | \((-16,-17)\) | \(-1\) |
| 10 | 642, 764 | 9 | 648 | \((-20,-16)\) | \(-8\) |

Both case-9 conflicts use two signatures with the same first two core
neighbors. The case-10 conflicts have other forms. No general exclusion
of duplicate signatures or wider class follows from these five examples.

Unlike the earlier case-2 retained proof, these retained proofs are not
original-only DRAT proofs: their input sets include the two or three
explicitly certified Gram clauses. The combined mathematical and DRAT
certificates establish the local exclusions.

## Verification and bindings

Before solving, the coordinator read the complete overlay wrapper and
direct auditor. The coordinator also ran both direct audits independently.
Those audits reconstructed the attachment domains and all 1,225 Gram
entries, checked all 839 or 490 integer negative witnesses, and checked
the unchanged original CNF bodies and exact binary suffixes.

After solving, the overlay replay rebuilt the complete original and
augmented formulas, checked their hashes, checked inclusion of every
retained input, and verified DRAT. The compact replay repeated the cold
original-formula binding and retained-proof checks using only the five
small vectors. It imports the original incidence builder and does not
import the downdate census, inverse computation, or overlay builder.

A second researcher reviewed the compact wrapper's bindings, direct
quadratic test, selector indexing, exact coverage of non-original inputs,
and DRAT gate. That read-only review found no issue. It did not recompute
the five numerical values or rerun the proofs; those checks belong to the
saved exact replay described above.

The original and augmented CNF hashes are:

| Case | Original SHA256 | Augmented SHA256 |
| --- | --- | --- |
| 9 | `3d0abc9c9427793eb5d6ec03a40bd2fed0b77c022d7dbf51eb85f19b595e2db7` | `43edea2c63786b036a6de7b75d372078431ad5dcec07211ff3f7f134155d534b` |
| 10 | `31af8937967a87f2220600674d250e7861bd7d606b26ea02308a2263440b4187` | `3f4ee7d59cb223dcd5cbb8ffdb0548290bc36cf55196d47952a0a35edc0f71bd` |

The compact certificate is
[`complement-rook-35core-cases09-10-compact-certificate.json`](../../experiments/logs/grids-and-triangles/complement-rook-35core-cases09-10-compact-certificate.json),
SHA256 `591fb8967425ed29686c3d76a5d9e7720854a239f86f38c3c1508dc7e977b861`.
Its replay source is
[`complement_rook_35core_cases09_10_retained_certificate.py`](../../experiments/workspace/complement_rook_35core_cases09_10_retained_certificate.py).

From the repository root, use a new output directory:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_cases09_10_retained_certificate.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-35core-cases09-10-compact-certificate.json \
  --replay \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-cases09-10-compact-replay-new \
  --checker-seconds 60
```

The terminal artifact manifest binds the preparation and coordinator
audits, both run records, compact retained CNFs/proofs, cold replays, the
compact certificate and replay, and this note. Large raw discovery proofs
are omitted from that publication list; their hashes and byte counts are
preserved. Reproduction uses the retained input sets and checked proofs.
