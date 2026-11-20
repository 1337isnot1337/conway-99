# Complete recovery of the case-four selector LP

The complete case-four selector relaxation has been rebuilt from published inputs.
Preparation and a fresh reconstruction both pass. No optimizer has run on this recovered model yet.
Case four remains unresolved.

## Scope and exact reconstruction

The input consists of the published native model, its lazy-model metadata, and the complete packed coordinate-cover registry.
The builder imports no unavailable checkpoint-43 file and no ancestor model builder.

It reconstructs all 630 Gram supports from the diagonal memberships.
The nonnegative row combination G(3,27)+G(4,27)-G(17,27) proves 46 zero columns.
The complete cover registry supplies fourteen empty-cover units.
Their overlap has size two, so the union fixes 58 of the original 1,214 selectors to zero.

Every other selector remains free in [0,1].
The builder substitutes only those proved zeros.
It omits an original row only when its complete finite box lies inside the row bounds.
A cover is omitted only when its guarded selector is already zero.

| Quantity | Exact count |
| --- | ---: |
| Remaining variables | 1,156 |
| Original native rows accounted for | 2,271 |
| Original coordinate covers accounted for | 178,533 |
| Retained native rows | 1,992 |
| Retained covers | 172,216 |
| Total retained rows | 174,208 |
| Nonzero integer coefficients | 11,868,882 |
| Original native box tautologies omitted | 279 |
| Covers with fixed-zero guards omitted | 6,317 |

The retained rows include every original signature and triple capacity, every remaining Gram no-good, and all sixty exterior-row cuts after exact substitution.
Two exterior-row cuts become box tautologies; the other 58 remain explicit.

## Independent recovery checks

The canonical row stream has SHA256

`444835c4d3c466dc9bb5c71646da13bf98e6eefdb3a492c51bcf54185b8919d5`.

Its record format preserves each row's original source and index, both finite bounds, and every reduced column/coefficient pair.
This hash agrees exactly with the captured pre-outage record.

The regenerated compressed array archive also has the same pre-outage hash:

`fb9ba6b1185f7796e39ac2904f077ad58238e89b0445305a22238c0374dd158f`.

It contains 5,312,569 compressed bytes and 147,480,936 uncompressed array bytes.
The new builder has different source bytes from the unavailable old builder; no recovery of that old source is claimed.

The [native run](https://github.com/1337isnot1337/conway-99/actions/runs/44504861314) prepared the model in 11.639 seconds, with peak reported RSS 307,948 KiB.
A separate full reconstruction took 10.541 seconds and checked every omission witness and typed array.
The builder also passed 6,216 exact box controls and 626 complete small cover-linearization controls.

The full new model JSON has SHA256

`9373396621ff2a713200c9832d9da82801b51f1c674233eaa81a1587a9f29b42`.

Its exact bytes, preparation record and cold replay record are preserved in the repository.
The compressed array archive can be regenerated from the public inputs without an optimizer.

## Subsequent query

The next proposed model adds t in [0,1] and all 1,156 inequalities x_j-t>=0, then maximizes t.
The finite-box certificate note proves how an exact zero upper bound exposes forced selectors, or how a strict negative bound certifies infeasibility.
A verified point with t>0 would show that no remaining selector is identically zero in this complete real relaxation.

That optimizer call is a separate step with its own source review, native controls and exact acceptance rules.
The recovered matrix and this preparation result do not settle binary incidence feasibility or graph completion.
