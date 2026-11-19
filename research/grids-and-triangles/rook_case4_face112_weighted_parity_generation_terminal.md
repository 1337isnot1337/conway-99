# Two-cut LP numerical terminal

The single authorized generation run stopped after one native call. The
numerical optimizer reported an optimum with `t` approximately
0.010916374589735645. Its 1,103-variable basis is saved. The full scan of
167,115 rows detected no violation above the declared tolerance; the
largest residual was approximately 4.62e-14. None of the 164,044 pooled
coordinate covers needed to be added.

This numerical point has not been accepted as a rational point by the
generation driver. Its generic rounding attempts did not produce an
exact point or a finite-box certificate. The immutable result therefore
remains `UNRESOLVED: retained numerical proposals give no accepted exact
outcome`. It excludes neither the case nor any coordinate.

| Recorded quantity | Value |
| --- | ---: |
| Native calls | 1 |
| Native/existing-ray time | 2.621498 seconds |
| Simplex iterations | 7,040 |
| Added original cover rows | 0 |
| Numerical phase time | 3.627063 seconds |
| Generic exact stage time | 0.384397 seconds |
| Total recorded run time | 9.416766 seconds |
| Exact bound accepted | None |
| Exact point accepted by this driver | None |

The result hash is
`c6537ce8337084ab131991b2608e59fa37fa38ae59f9c9f478e01dd2e5c6892d`.
The complete numeric record has gzip hash
`b024197a41afb7412b5010deafcf136cbf1bf3ca1b08aed2ffd1965e4cb9ee00`
and decompressed hash
`d73d5d8463b194c057c8f9c96d2cb0dd3e1d4cc9acc40f76701440bad0805831`.

The prescribed cold replay passed in 13.955463 seconds, hash
`00591861439cf247245dbba5c16b7e5e10d8528a3d2139d6cce5c27a1c4e6866`.
It checked the unchanged cached H3 array prefix, both direct Gram-derived
parity rows, the extended matrix and the complete saved numerical
transcript. It made no optimizer call and retained the unresolved
mathematical outcome.

A later exact solve of the saved basis is a separate artifact-only task.
It does not alter this record, reuse numerical tolerance as a proof, or
rerun the optimizer. Its preparation and any outcome are excluded from
this package.
