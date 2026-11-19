# Exact five-variable extensions at the 48-cut count point

The complete five-Boolean extension scan passed at the frozen integer count
point `0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
Every tested five-variable marginal has a nonnegative integer extension.
The extensions are separate local distributions. This result does not
construct a joint distribution across all mask classes or a graph.

The derivation, domain, and synthetic controls are in
`grid_free_order10_five_boolean_extension.md`. The scan uses the same 62
six-vertex root domains and the existing complete six-root/two-free-vertex
product cache. No new graph products or reduced-count matrix were built.

## Complete result

| Quantity | Exact result |
|---|---:|
| Roots retained and completed | 62 |
| Roots with five-subsets | 48 |
| Five-subsets tested | 4,543,737 |
| Empty extension intervals | 0 |
| Tight extension intervals | 4,459,591 |
| Positive-width extension intervals | 84,146 |
| Completed batches | 132 |
| Saved negative forms | 0 |

For each five-subset, the test computes the two integer endpoints

\[
L=\max_{|S|\text{ odd}}(-b_S),\qquad
U=\min_{|S|\text{ even}}b_S.
\]

All intervals satisfy \(L\le U\). A tight interval fixes the missing fifth
moment. A positive-width interval permits more than one integer value.
There are 29 roots with at least one positive-width interval. The other
completed domains have only tight intervals or have fewer than five high
masks. No zero-count root or class was removed from the prepared domain.

Each root's enumerated subset stream matches the complete domain hash.
The exact counts of infeasible, tight, and positive-width intervals sum to
the expected number of five-subsets, both per root and globally.

## Exact arithmetic and scope

Cached tensor coefficients were contracted with labelled embedding counts,
equal to induced counts times automorphism orders. The source checked the
complete frozen product-row references before constructing the moment
arrays. Integer bounds were checked before every fixed-width contraction
and Boolean transform.

The largest proper moment encountered was 72,926,995,680. The largest
transform and row-sum guard was

\[
1024M=74,677,243,576,320<2^{63}-1.
\]

The interval decisions therefore used exact integer arithmetic. They were
not based on floating-point tolerances or an eigensystem. The scan found
no negative direction, so no fresh product reconstruction or optimizer
call was needed.

This is stronger than a numerical no-separator report for this stated
family: it verifies every local extension interval exactly. Its scope
remains finite and explicit. Compatibility among the different five-set
extensions is untested. Complete order-ten PSD feasibility, graph
realizability, and the Conway 99 problem remain unresolved.

## Execution and bindings

The coordinator reviewed the complete source and preparation before the
single query. The driver used a 60-second alarm and one thread. It completed
in 20.5902 seconds, with peak RSS 267,300 KiB. No retry was launched.

The source retains complete batch counts on interruption and caps saved
negative forms. Those paths were not needed in this completed run. The
negative extractor has six synthetic cached-form controls, including
automorphism multipliers one, two, and seventeen. Any future exported
negative still requires a fresh literal-product replay before optimizer
use.

The source is
`experiments/workspace/grid_free_order10_five_boolean_extension_scan.py`.
The following files are under `experiments/logs/moments-and-counts/`:

- Preparation: `order10-five-boolean-extension-scan01-preparation.json`.
- Coordinator gate: `order10-five-boolean-extension-scan-coordinator-review.json`.
- Result and log: `order10-five-boolean-extension-scan01.json` and
  `order10-five-boolean-extension-scan01.log`.
- Complete frozen whitelist: `order10-five-boolean-extension-terminal-manifest.json`.

Source SHA-256:
`c7d48bcda5c0cd284676eb940664d90373827322ea6ec17464a7d6f52a93aa50`.

Result SHA-256:
`080114b551d6f398bbe33367a86c88c3c763bc78aef609abe139a7c94ee48350`.
