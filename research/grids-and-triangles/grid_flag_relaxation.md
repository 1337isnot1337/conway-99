# A limit of aggregate grid-line constraints

This note records the earlier relaxation with at most seven all-red grids.
The [later exact certificate](grid_count_119.md) proves `29g-4b<=3465` from
the same flag inequalities. Combined with the improved all-red restriction,
it gives at most 119 grids. The saved 120-grid assignment below is therefore
a witness only for the earlier relaxation, not for the current conditions.

`global_grid_flags.py` couples the seven-axis graph at each vertex to the
six triangle multiplicities in each grid. It retains the signless-incidence
support criterion, the pointwise fifteen-grid bound, the excluded sole
six-cycle support, and the crossing-square inequality. It also requires
integer triangle populations and at most seven all-red grids.

For a grid corner p, let a,b be the multiplicities of its two lines. If the
four other lines include a red line in each direction, the edge of D_p
corresponding to this grid cannot have a disjoint edge. Otherwise the two
opposite four-cycles would produce a crossing nongrid square using a red
edge. A corner with no disjoint edge therefore consumes the corresponding
two-vertex-cover flag in its root graph. The model records this compatibility
for each unordered pair (a,b).

The resulting relaxation has 509 root types and 1,596 possible grid-line
types. It does not reconstruct intersections between actual grids. Its
real optimum is approximately 120.448, so it gives no improvement on the
existing integer bound of 120. More strongly, its integer version has an
exactly checked count assignment with 120 grids. This count assignment is
not a graph, and does not prove that 120 grids are attainable.

The saved integer assignment passes every equality and inequality by Python
integer arithmetic, including the added all-red bound. Replay it without
running an optimizer:

```sh
.venv/bin/python experiments/workspace/global_grid_flags.py --verify experiments/logs/session-ab2f/global-grid-flags-integral.json
```

Improving this earlier relaxation requires a stronger restriction. The
later all-red bound supplies one without changing its aggregate flags.
