# Root 42 exact interval result

The immutable 48-cut count point has a nonnegative integer distribution on the complete root-42 high-mask presence domain, including every stabilizer divisibility condition.

The exact feasible scalar interval is
\[
0\le u\le 9794,\qquad u\in2\mathbb Z.
\]
The frozen query chooses \(u=0\). All 241 atoms of population at most four then have positive weight; all twelve population-five atoms have weight zero. The total labelled-root mass is 55,883,520. After normalization and cancellation, the common probability denominator is 27,941,760.

The single optimizer-free query completed in 0.659 seconds. A separate verifier completed in 0.044 seconds without importing the query or its interval helper.

## Exact checks

The saved result contains all 253 integer atom weights. The independent replay reconstructs the 241 supplied moments from their direct induced-count forms, all 253 affine constants and slopes, both exact interval endpoints, all 253 individual moment equations, all 23 quotient equations, and all 253 root-stabilizer divisibilities.

The upper endpoint is attained by the four-class state
\[
\{A_{02},A_{12},A_{13},B_0\}.
\]
It has exactly one population-five extension. Its exact-state weight is
\[
w_A=N_{\mathrm{ind}}(37894)+N_{\mathrm{ind}}(38120)-u=9794-u.
\]
The two catalogue types are its two permitted high-edge variants. The lower endpoint comes from a population-five atom, whose mass is \(u\).

Thus every even value between 0 and 9,794 gives a nonnegative integer distribution satisfying the prepared presence equations and stabilizer conditions. The deterministic certificate uses the least such value, zero.

This result closes the prepared presence-only root-42 test at this count point. It does not determine a consistent joint induced high-edge distribution, a low-neighborhood exterior completion, or a 99-vertex graph.

## Frozen artifacts

| Artifact | Git blob |
| --- | --- |
| Point-independent package manifest | 5e7cc8be064a8fc7a82524e136d88411b747b798 |
| Interval preparation | 7f6b7952f81dc6c1ee0f25e12379e3dcd3656979 |
| Complete query result and weights | 233ed73fae5f80b3dc23b126c1528db64a8b6f31 |
| Independent artifact verifier | 6017c3a8b7e91ccf348de3bcd78ff33802bb8f56 |
| Independent replay result | 369ea5b53e5d05a56d956216cb6415fa7cad75e4 |
| Immutable count point | c881dae3be05cf289fcc45a99d72c405ac863c46 |

The count point has SHA-256
0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.

Replay:

~~~sh
node experiments/workspace/root42_packing_moment_interval_replay.js \
  experiments/logs/moments-and-counts/order10-root42-packing-moment-interval-preparation.json \
  experiments/logs/moments-and-counts/order10-root42-packing-moment-interval-result.json \
  experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json
~~~

The entry point checks each input's exact Git blob before computing. No optimizer is called.
