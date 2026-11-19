# Exact prism-zero count witness through order ten

## Result and scope

The rounded point from the
[prism-zero IPM probe](grid_free_order10_prism_zero.md) has an exact repair:
increase ordinary core coordinate 549 from 5 to 6. No other coordinate
changes.

The repaired point gives 48,965 nonnegative integer induced counts through
order ten. It satisfies all 180,445 original extension equations, every
level total, the prism/rook/broken-rook zero conditions, all exact ordinary
count upper bounds, and the fourteen certified linear cuts used by the
probe. The saved witness contains the complete 550-coordinate vector and
all 48,965 induced counts.

This is a finite count witness. It is not a graph. It shows that these
count equations and fourteen inequalities do not exclude the global
prism-free case. Exact PSD feasibility of all cached moment blocks is not
asserted in this checkpoint.

## The single correction

The two negative rounded induced counts, catalogue types 48301 and 48915,
have the same exact reduced form:

\[
c_{48301}=c_{48915}
  =2x_{54}-x_{538}-2x_{544}+10x_{549}.
\]

Both forms equal -1 at the rounded point. The change

\[
x_{549}:5\longmapsto6
\]

raises both counts to 9. Every other induced count remains nonnegative,
as checked by a complete exact evaluation after the change.

Coordinate 549 is the ordinary count of catalogue type 48964. Its graph
has adjacency bit rows

```text
[664, 240, 864, 449, 771, 390, 526, 43, 60, 85]
```

Its automorphism order is 10 and the previously certified ordinary-count
upper bound is 7,761. The repaired value 6 respects that bound.

Coordinates 0 through 57 are unchanged. All count forms of order at most
nine use only those coordinates; this absence of new-coordinate
coefficients is checked explicitly. Consequently every order-nine count,
the thirteen moment cuts, the universal old-coordinate count cut, and
all 1,416 cached moment matrices are unchanged by the repair.

## Exact verification

The search first represents the rounded point losslessly for a scan of
the existing 1,416 PSD blocks. That scan finds no exact negative
integer-vector direction. Its smallest numerical eigenvalue is about
`-2.43e-15`; this is only a numerical observation.

The repair then loads the existing order-ten reduction and checks that
every induced-form coefficient is divisible by the common scale
3,628,800. It recomputes all initial counts with Python integers and
confirms that the only negative values are the two counts above.

For trial updates, the maximum absolute coefficient of a new coordinate
is 4,800. The maximum absolute initial count is 459,981,793,571. The
search permits total absolute change at most four, so every intermediate
integer evaluation is bounded in magnitude by

\[
459981793571+4\cdot4800=459981812771<2^{63}.
\]

This explicit bound justifies the fixed-width integer trial evaluation.
Every trial evaluates all 48,965 counts. The fourteen cut values are
unchanged because the allowed changes have support only in coordinates
58 through 549.

The first trial passes. The source then recomputes the candidate using
the original scaled coefficient forms and Python integers. It verifies
nonnegativity, divisibility, all 180,445 original equations, level totals,
zeroed graph counts, the ordinary-count bounds, and all fourteen cuts.
The final cached-block scan and certificate-binding replay also complete
with no exact negative direction. They do not establish PSD.

The complete computation takes 19.128 seconds. No optimizer is called.
The general sparse-search fallback is not reached. Failure of that
fallback would have been reported as unresolved, not infeasible.

## Artifacts and reproduction

The frozen source is
`experiments/workspace/grid_free_order10_prism_zero_repair.py`, SHA-256

```text
b3e7bb85990c68561505b55b90476b81e0bd5c8ed7fd2bc7400b0e39e8544c19
```

The complete witness is
`experiments/logs/moments-and-counts/prism-zero-repair-witness.json`,
SHA-256

```text
62faca107e3f5a7f560c009133e2da563aa16619382b7778f7ff53aa1cd75db7
```

The same directory contains the `prism-zero-repair` result, computation
log, initial rounded-point proposal and separation, final proposal and
separation, and a manifest binding the package. The original IPM proposal,
rounded point, drivers, and logs remain unchanged.

The original command was:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_prism_zero_repair.py \
  --cache /tmp/conway99-order10-reduced.pickle \
  --rounded experiments/logs/moments-and-counts/grid-free-order10-prism-zero-v2-rounded-counts.json \
  --preparation experiments/logs/moments-and-counts/grid-free-order10-scaled-preparation.json \
  --loop-result experiments/logs/moments-and-counts/grid-free-order10-moments-loop.json \
  --initial-psd experiments/logs/moments-and-counts/prism-zero-repair-rounded-separation.json \
  --prefix experiments/logs/moments-and-counts/prism-zero-repair \
  --seconds 240
```

The mathematical witness is the saved integer point and count vector;
its validity does not depend on repeating the numerical IPM solve or the
local search.
