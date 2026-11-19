# One full-span parity cut for rook case4

The single authorized separation query produced an exact violated cover. The
native call took 6.661 seconds; the complete owned process took 8.433 seconds.
The separate artifact-only replay passed in 0.156 seconds. No second call was
made. The case4 incidence problem remains open.

## Certified inequality

Let

```
H = {
  28, 47, 48, 50, 80, 127, 129, 130, 131, 179, 180, 182,
  230, 266, 344, 407, 466, 545, 597, 598, 602, 605, 664,
  665, 668, 669, 670, 736, 769, 807, 851, 918, 919, 967,
  971, 972, 974, 976, 978, 980, 1016, 1017
}.
```

Every Boolean incidence satisfying the original Gram equations and the
previously proved zero coordinates satisfies

\[
\sum_{a\in H}x_a\ge1.
\]

At the accepted point with denominator 67,336,409,858, the exact deficit is

\[
1-\sum_{a\in H}x_a
=\frac{7,303,459,804}{67,336,409,858}>0.
\]

The proof adds original Gram rows with IDs

```
93, 102, 117, 118, 119, 121, 122, 123, 124, 156,
186, 215, 224, 235, 236, 237, 238, 239, 240, 241,
296, 301, 321, 326, 330, 337, 338, 340, 341, 342,
343, 344, 350, 373, 377, 382, 385, 387, 388, 389,
411, 416, 436, 455, 473, 521, 535, 548, 560, 571.
```

Their RHS sum is 81. Write their full nonnegative integer coefficient vector
as \(c\). After substituting the proved zeros, its odd support is exactly
\(H\). The removed odd coordinates are 126, 465, 966, 970, 973 and 977. Hence

\[
\sum_{a\in H}x_a
+2\sum_{a\notin Z}\left\lfloor\frac{c_a}{2}\right\rfloor x_a=81,
\]

where \(Z\) is the frozen set of 112 proved zeros. Nonnegative integrality
makes the first sum a positive odd integer. This proves the cover. Under the
same equalities it is equivalent to the rounded capacity

\[
\sum_{a\notin Z}\left\lfloor\frac{c_a}{2}\right\rfloor x_a\le40.
\]

The saved certificate retains all 1,214 original coefficients. The proof uses
only the original Gram equations, the stated proved-zero premises and
integrality. It does not use a numerical dual or assume that the proposing
point is a Boolean incidence.

## What was checked

The prepared native model represents the complete 286-dimensional Gram
parity span. It used 2,491 Boolean variables and 2,208 constraints, with no
objective, hint or assumption. The native complete vector was persisted
before its mathematical inspection. The native status was OPTIMAL for this
satisfaction problem; acceptance rests on the exact cut proof.

The separate replay checked every Boolean constraint in the frozen protobuf,
reconstructed the selected original-row witness from the saved choice bits,
checked all 1,214 integer coefficients and the proved-zero substitutions, and
recomputed the exact point deficit. It performed no optimizer call, model
reconstruction or parity search.

The query stops after one feasible separating assignment. It neither
enumerates the full set of cuts nor proves that a later strengthened
relaxation is infeasible. This cut rejects the saved fractional point. It
does not exclude the case4 core or solve the Conway99 problem.

## Artifact bindings

- Query preparation: `3200a0fbfbe6f2212a65515a68431459bf76717226f089451b1ad707035c8360`.
- Native model: `8b8f94b7b1e700c6b71744d5e6d94a814aa84638f7e412c588918a0fd497180f`.
- Source point: `23de7244e4e4efb1ef82ff649008b1236bb389888ffbb923edf4017cfe1bc2e3`.
- Cut certificate: `f9080c52f570d3a9eabf461eabd6ef4dde6ac2fc2454ecc75367fe658d9e3fd7`.
- Native vector: `efa476b2e0fd9c1f32cf9eb64b93e29fe81bd0fc2249c49490336bc95853fed5`.
- Terminal result: `2e1db8a9aba8fd991bdfeaa050e9d4099a6c83cc8a78842fcc8c4567a573f395`.
- Direct replay: `28cc396064b7e6ae5e7ad0ac401de0929aa3ea25b20d88483a1020abc79d620c`.
