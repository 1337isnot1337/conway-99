# Integer-point scan of the remaining complement matrices

The run completed all 737 complement matrices left by the quota-one
reduction and separately screened all 916 existing scalar child
matrices at the integer witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
It found no exact separator and no unconfirmed numerical negative
direction. No cut was added to an optimizer.

This is a numerical separation result with exact acceptance gates,
not an exact PSD certificate. The 4,478 quota-one cases were not
directly scanned: their implication from child PSD is the separate
theorem in the [domain note](grid_free_order10_complement_domains.md).
The child scans here are at the integer point, rather than the earlier
unrounded proposal, but they still do not certify exact child PSD.

## Exact construction and separation

Each matrix is assembled as

\[
L_a=M_7-B_aM_8B_a^T
\]

from the existing complete scalar caches and the frozen sparse lifts.
All contractions and additions use Python integers. Every selected
X_a row is checked to vanish exactly before it is deleted; all 737
checks pass. Other rows are removed only when every entry is proved
zero at this count point.

The numerical routine proposes possible integer directions. A proposed
negative direction would be lifted to the complete parent coordinates
and checked exactly. Its induced-count form is the parent quadratic
minus the quadratic of the lifted child vector. The driver records
that supported-product reconstruction and core reduction are required
before optimizer use. No negative direction occurred, so these later
stages were not invoked.

The smallest reported complement quotient eigenvalue is approximately
0.01838 after diagonal normalization. The scalar child minimum is
zero, including exact zero rows. These numerical observations are not
substituted for exact PSD proofs.

## Coverage and runtime

All 916 scalar child domains and all 737 designated complement domains
were retained. No point-dependent cache pruning was used. The run
used one numerical thread and completed without a timeout or error.

The scan stage took 11.679 seconds within its 120-second budget. Total
wall time, including shared-environment setup and loading, was
53.463 seconds. Peak RSS was 207,596 KiB. No new product tensors,
dense reduced count matrix, or optimizer were used.

## Frozen artifacts

Source:
`experiments/workspace/grid_free_order10_complement_scan.py`

Source SHA256:
`806aea35eedde9f09eda5c5b0b5113b62e0c37e218a46c6ad727ea6950ca74a7`

Preparation:
`experiments/logs/moments-and-counts/order10-complement-scan01-preparation.json`

Preparation SHA256:
`7716b04a73af3a2a37b56ebeff54cbc3663d94e2c01f003f57cd8932dba02fbd`

Result:
`experiments/logs/moments-and-counts/order10-complement-scan01.json`

Result SHA256:
`72bbe6bf45832ef2cd6a76f3ac25227c1f334c32f1cb358401b544b740df563c`

The matching manifest binds the source, preparation, result, logs and
this note. The complete domain theorem and its replay remain unchanged.
