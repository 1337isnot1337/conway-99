# Twelve additional integer zeros in case 4

The single bounded query of the complete 99-zero-face LP with the two proved
parity covers found twelve further forced-zero coordinates:

\[
1062,1063,1064,1065,1066,1067,
1125,1126,1127,1128,1129,1130.
\]

They are distinct from the prior 99 zeros, giving 111 proved zeros in total.
Case 4 is not excluded. No binary incidence or new exact feasible real point
was produced by this run.

## Direct integer proof

Let \(Z\) be the twelve-column set above and let \(H_2\) be the second
42-column cover in the frozen parity certificate. A signed sum of 42 original
Gram equations gives, after substituting only the prior 99 zeros,

\[
\sum_{a\in H_2}x_a+2\sum_{a\in Z}x_a=1.
\]

The verifier `rook_case4_face99_parity_face.py` checks this identity on every
one of the 1,214 original columns. It exports all 42 original row IDs,
integer multipliers, core-pair quotas, full coefficients, and the removed
known-zero terms. It independently replays the 99-zero seed and both original
odd-cover proofs. No LP, modular elimination, or numerical point is used in
this verification.

The identity already forces the twelve zeros for nonnegative integer
incidences: each doubled coordinate satisfies \(2x_a\leq1\), hence
\(x_a=0\). It also gives \(\sum_{a\in H_2}x_a=1\). This is stronger than
describing the conclusion solely as a consequence of the newly added real-LP
cover. The cover exposed this integer consequence to the real relaxation.

For the strengthened real LP, the same deduction follows from
\(\sum_{a\in H_2}x_a\geq1\) and nonnegativity. The first cover remains a
valid active constraint even though this particular proof uses only the
second cover.

The direct certificate is
`rook-case4-face99-parity-face-certificate.json`, SHA256
`717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e`.
Its separate replay passed in 2.213 seconds.

## Query and complete replay

The numerical phase used two native calls and 1.814475 seconds of total
solver/existing-ray time. The complete run took 5.500328 seconds. It began
with 3,083 active rows, then added the two violated frozen coordinate-cover
rows 154,836 and 154,842. The second proposal had no unprocessed cover
violation at the recorded numerical tolerance.

The accepted exact output is a zero-face certificate, not a primal point or
an infeasibility certificate. Its 50 nonzero multipliers use 42 retained Gram
equalities, the second parity cover, and seven max-min extension rows. Its
exact bound is \(14t\leq0\). Eliminating those seven auxiliary extension
rows yields the displayed original-coordinate identity. The two dynamically
added coordinate covers do not enter this certificate.

The terminal record is
`rook-case4-face99-parity-generation-run01/result.json`, SHA256
`87c1e83d0a70f21b17e8a3b1c81b771768b87fd926ed4a898683317251e7b9c0`.
Every numerical prefix and available basis is retained in its adjacent
iteration records.

Cold replay rebuilt all 167,937 base rows, all 1,115 max-min extensions, the
entire 165,969-coordinate-cover pool, both integer-cover proofs, and all
earlier zero premises. It checked the exact finite-box certificate and the
bounded prefix transcript. Replay passed in 38.285 seconds. Its SHA256 is
`ca9e2cbf2b4034a596db226658ca8a98349cee7d9413c0e7909ae6acf8a21d42`.

No second query was run. The next prepared task is exact original-row and
cover propagation from the 111 proved zeros, retaining both parity covers.
That closure is a separate package and is not an outcome of this run.

## Replay commands

Run from the repository root, choosing new output paths:

```sh
python experiments/workspace/rook_case4_face99_parity_cover_generation.py replay \
  --model experiments/logs/grids-and-triangles/rook-case4-face99-parity-model01/model.json \
  --arrays experiments/logs/grids-and-triangles/rook-case4-face99-parity-model01/arrays.npz \
  --preparation experiments/logs/grids-and-triangles/rook-case4-face99-parity-generation-preparation.json \
  --result experiments/logs/grids-and-triangles/rook-case4-face99-parity-generation-run01/result.json \
  --output /tmp/rook-case4-two-cover-cold.json

python experiments/workspace/rook_case4_face99_parity_face.py replay \
  --certificate experiments/logs/grids-and-triangles/rook-case4-face99-parity-face-certificate.json \
  --output /tmp/rook-case4-integer-twelve-zero-cold.json
```

Both commands are optimizer-free. The standalone identity is the compact
mathematical certificate; the complete model replay also verifies how the
bounded query found it.
