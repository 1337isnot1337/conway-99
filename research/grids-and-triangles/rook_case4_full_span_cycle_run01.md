# Case4 full-span continuation: one new cover and a new exact point

The single prepared continuation completed two LP rounds and two full-span parity calls. It found one new necessary 27-column cover and reconstructed two exact positive points. The second parity call stopped with native UNKNOWN, so the terminal result is unresolved. It proves neither exhaustion of the parity span nor exclusion of case4.

The original 167,115 extended rows remain unchanged. The run started with four certified appended cuts. The first LP point was checked against that prefix, the new cut was checked directly against the original Gram equations and its source point, and the second LP point was checked against all five appended cuts. The final accepted prefix therefore has 167,120 rows. No later rejecting cut is pending.

## The new cover

Let H27 be the sum of selectors with original IDs

```
23 45 123 259 261 262 339 401 402 405 539
730 731 732 733 764 780 781 782 800 801 802
1175 1176 1177 1180 1183
```

Original Gram rows 214, 344 and 582 have total right-hand side 3. Their full integer coefficient sum, after the already proved zero substitutions, is H27 + 2Q for a nonnegative integer linear form Q. Thus an integral incidence satisfies H27 in {1,3}; the retained inequality is H27 >= 1. Its exact deficit at the first point is 4,246,645,930 / 26,500,111,260. The direct proof and the complete original-coordinate coefficient vector are retained in separation-00/cut.json and separation-00/proof.json.

No claim is made here that H27 = 1. A separate native-capacity triple census is a later task and is not part of this terminal package.

## Exact points and scope

The first reconstructed point has denominator 26,500,111,260 and common floor 288,147,941 / 26,500,111,260. It satisfies the four-cut prefix. The second point has denominator 3,461,944,222 and common floor 37,621,464 / 3,461,944,222. It satisfies the five-cut prefix.

Both points passed the full exact matrix checks and the original 1,214-coordinate inspector, including the original native rows and the complete coordinate-cover obligations. Their cold checks are saved separately. They are fractional selector witnesses, not graph constructions or binary incidence solutions.

The run used 4.816503022 cumulative native LP seconds. The two native separation calls used 66.111999991 seconds in total. The second call ended UNKNOWN after approximately 60.09 native seconds. The owner exited normally after 192.361842442 seconds, without a retry. The prescribed bindings-only verification then passed in 1.032347803 seconds, checking 70 artifact references.

## Reproduction and preserved evidence

The preparation and preflight remain the previously frozen files rook-case4-full-span-cycle-preparation01.json and rook-case4-full-span-cycle-preflight01.json. The controller source is rook_case4_full_span_cycle.py, SHA256 ddf52b6807e9759337e14c0baff94bbaa9be5c599eaa8bb287277330eab4ec15. This package includes the complete terminal directory, both numerical prefixes, saved basis proposals, exact candidates and cold records, separator models and outputs, all per-stage states, supervisor result, and the separate bindings report.

The H42 upper-five theorem, conditional H5 branch work and the 44-term strengthening are separate proof packages. None was silently inserted into this frozen run.
