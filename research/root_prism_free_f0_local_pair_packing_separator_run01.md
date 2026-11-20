# Anchor178: an exact mixed-plus-packing cut

The single authorized local LP produced an exact selector inequality. Its separate cold replay passed. No model was changed and no second query ran.

The source is `root_prism_free_f0_local_pair_packing_separator.py`, SHA750c7959439b28f4ec5c33939b84b17886037a6585de80a148f708a0287e2ee5. The preparation is bound by report SHAee348676e6455c6f1893be7e65afa26d1cdb963edad1f9bf038cff84ec151862 and root gate SHA921cfd4109957c0f61f3e82e6fa7d04c8f156e59f19b5fb131cb76bb26a70188. The general derivation and prior-work distinction are in `root_prism_free_f0_local_pair_packing_separator.md`.

## Exact arithmetic

The anchor is178, with core signature `{2,8,13}`. The integer site potential, in core-site order0 through17, is

```
[2,-5,-6,-1,6,2,-6,2,-6,-1,-1,2,-1,-5,-5,-5,-1,6]
```

There are only two nonzero pair multipliers:

\[
\mu_{\{0,5\}}=4,\qquad \mu_{\{0,17\}}=7.
\]

The site-potential demand is12. Subtracting the pair-multiplier total11 gives `t=1`. For each of the244 complete eligible neighbors, the source computes

\[
w_b=\max\bigl(v\cdot h_b-4\mathbf1[\{0,5\}\subseteq h_b]
-7\mathbf1[\{0,17\}\subseteq h_b],0\bigr).
\]

Exactly69 weights are positive. Their histogram is

| Weight | Number of neighbors |
|---:|---:|
|2|1|
|3|28|
|4|18|
|6|1|
|7|19|
|10|2|

Every one of the31 eligible neighbors in the frozen selected set has weight0. The universal row

\[
x_{178}\le\sum_b w_bx_b
\]

therefore has left-minus-right value1 at that incidence. Its coefficients have already been contracted against every full neighbor; no point-zero pruning enters the row. Dividing the integer potentials by6 gives an exact feasible point of the advertised bounded dual with objective `-1/6`. The numerical optimality status is not needed for this conclusion.

There is also a short contradiction using only this selected local domain. All31 adjusted coefficients are nonpositive. Multiplying the mixed equations by `v` therefore gives

\[
12\le 4\sum_{b:\{0,5\}\subseteq h_b}y_{178,b}
+7\sum_{b:\{0,17\}\subseteq h_b}y_{178,b}
\le4+7=11.
\]

The first inequality uses the full selected-neighbor coefficient check; the second uses the two core-pair packing bounds. This explains the local impossibility without using a numerical optimality claim.

The row has70 nonzero coefficients. All12 actual core relabelings give distinct normalized rows, each with70 terms. Their anchors are178,284,36,326,110,235,172,263,48,318,131,240 in the saved action order. All transported site/pair potentials and literal full-neighbor contractions are retained. Exactly one of the12 rows is violated by the original frozen selection; the other transports are valid inequalities without a claim that this same selection violates them.

For binary selectors, the base inequality is also equivalent to the positive-support cover

\[
x_{178}\le\sum_{b:w_b>0}x_b.
\]

If `x178=1`, the weighted inequality requires at least one positive-support selector; conversely one such selector supplies weight at least1. This consequence does not require a further LP. The accepted machine-readable file retains the original weighted rows; no capped-row native overlay has been built in this package.

## Query and replay

The one HiGHS call took0.001880720 seconds under its30-second bound. Its owner finished and reaped the child in1.998505973 seconds under the60-second wall limit. Exact acceptance used demand1, selected capacity0, and strict gap1.

The separate cold owner finished and reaped its child in1.757807463 seconds. It reloaded the frozen inputs, independently contracted the saved pair coefficients from literal core pairs, checked3172 full-neighbor weights across the base and12 transports, and reproduced the integer reconstruction from the saved hexadecimal float proposal. Both owner overruns are0.

The accepted outputs are:

- `f0-local-pair-packing-separator-run01-cold/certified-selector-cuts.json`, SHA26b6e829be88927d88f6a23208bca675a322e999e92678a07408411c40dbb2f5. Field `rows_upper_zero` contains12 sorted lists of `[original selector ID, integer coefficient]`, each with upper bound0.
- Cold report SHA73982595edfb2141c6d096c9d1a897ef824b43ccde023fca8e4f6461f7ee3c2c.
- Accepted cold owner SHA3cfadfe885a608587788af6d47ef2ada950bfe18d02da432165881736633ed19.
- The full replayed multiplier and transport certificate has SHAc880aa365a871b99b26be70bba8641b0318d50d41ccd21de17ab91d3064d2672.

This is an arithmetic explanation of why the specified first incidence cannot extend. It rejects that incidence by a universal selector row with only69 positive-support neighbors. It does not exclude the whole F0 component, construct the second incidence, or prove any global model infeasible. Root and the controller agent received the exact row and cold bindings before any possible future model change.
