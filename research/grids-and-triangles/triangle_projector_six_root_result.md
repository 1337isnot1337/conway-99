# Six-root conditioned triangle result

The unchanged integer count point with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`
passes all 30 prepared six-root conditioned triangle blocks. Every full matrix
was contracted with Python integers. Every coefficient of det(tI+M) was
nonnegative. For a real symmetric matrix this certifies positive
semidefiniteness: a negative eigenvalue would give a positive real zero of a
monic polynomial with nonnegative coefficients.

The single authorized query took 5.214 seconds. A cold
replay took 4.627 seconds and reproduced all matrices,
characteristic polynomials, 38 core-triangle zero rows and 180 point-star
kernel equations. The replay did not regenerate the product tensors.
No negative vector or new inequality was found.

| Root type | Full order | Rank | Nullity |
| --- | ---: | ---: | ---: |
| 50 | 220 | 213 | 7 |
| 51 | 176 | 160 | 16 |
| 52 | 110 | 97 | 13 |
| 53 | 52 | 42 | 10 |
| 60 | 139 | 120 | 19 |
| 62 | 86 | 72 | 14 |
| 67 | 150 | 143 | 7 |
| 68 | 122 | 112 | 10 |
| 69 | 114 | 98 | 16 |
| 70 | 77 | 66 | 11 |
| 71 | 78 | 58 | 20 |
| 72 | 43 | 29 | 14 |
| 76 | 75 | 61 | 14 |
| 77 | 91 | 77 | 14 |
| 79 | 50 | 38 | 12 |
| 80 | 109 | 90 | 19 |
| 83 | 92 | 85 | 7 |
| 84 | 75 | 65 | 10 |
| 85 | 44 | 35 | 9 |
| 86 | 74 | 66 | 8 |
| 87 | 57 | 40 | 17 |
| 88 | 47 | 37 | 10 |
| 90 | 53 | 38 | 15 |
| 93 | 60 | 49 | 11 |
| 94 | 36 | 20 | 16 |
| 95 | 24 | 17 | 7 |
| 96 | 44 | 36 | 8 |
| 97 | 39 | 29 | 10 |
| 98 | 26 | 18 | 8 |
| 99 | 11 | 0 | 11 |

The zero matrix for root 99 is retained. No root, class or row was removed
because its current count was zero.

This is an exact certificate for this finite family at one count point.
It does not prove that a graph exists or that all possible order-ten
inequalities hold.

The tensor preparation and its literal host controls are described in
[the preparation note](triangle_projector_six_root_conditioning.md).
The full result has SHA256
`56ad9814ced15ed84758bad6f7eba15f532333e8412d6450ce3b57ac5b5562f8`.
The repository stores its exact bytes under the same filename with
`.gz` appended; decompress that archive before passing it to the replay
driver. The uncompressed result is unchanged.

Run the saved arithmetic replay after decompression:

```sh
python experiments/workspace/triangle_projector_six_root_query.py replay \
  --directory experiments/logs/moments-and-counts/triangle-projector-six-root-preparation01 \
  --point experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json \
  --result /tmp/order10-six-root-triangle-query01.json \
  --output /tmp/order10-six-root-triangle-query01-replay.json
```
