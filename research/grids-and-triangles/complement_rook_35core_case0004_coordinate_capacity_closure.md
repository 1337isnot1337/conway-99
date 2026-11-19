# Original-demand capacity closure for case4

## Result

The complete absence closure adds no unit beyond the fourteen proved
intrinsic exclusions. After removing those fourteen columns, all 1,200
remaining targets pass all 470,982 positive coordinate-difference capacity
tests at their original demands, and all 1,200 exterior-degree capacity
tests. One complete pass reaches a fixed point.

This is an exact negative result for this strengthening rule. It is not an
incidence witness or a graph completion. Case4 remains open.

The census took 3.808 seconds with peak RSS 45,448 KiB. A separate cold replay
passed. The certificate contains the original fourteen unit proofs and the
complete final target inventory. There are no new exclusion proofs.

## Capacity rule

Use the frozen full 35-core domain and the augmented vectors

\[
w_b=(h_b,1),\qquad
t_a=(2\mathbf1-h_a-Bh_a,\ 14-|h_a|).
\]

For an actual exterior vertex a, every positive coordinate difference
delta=t_a(i)-t_a(j) requires at least delta actual neighbors from

\[
C_{a,i,j}=\{b\in E(a):w_b(i)>w_b(j)\}.
\]

Let U be a set of attachment columns already proved absent. If

\[
|C_{a,i,j}\setminus U|<\delta,
\]

then a cannot occur. This uses the original positive demand, including
demands greater than one. The augmented degree coordinate is included in
every ordered comparison. Independently,

\[
|E(a)\setminus U|<14-|h_a|
\]

also excludes a.

The upper bounds count every still-possible candidate as available. Some
candidates may be mutually incompatible in a whole incidence, so these
upper bounds are necessary and can be loose. A passing target is not
declared feasible.

## Coverage and provenance

The initial set is

\[
352,353,354,355,439,552,553,645,869,873,957,1080,1081,1167.
\]

Each seed is independently rechecked as an empty original positive support.
The new source reconstructs all target vectors and all 551,156 directed
eligible-neighbor entries. There are 476,766 original positive coordinate
differences across the full 1,214-target domain.

Stages are synchronous. A new target proof may use only absences proved in
earlier stages. Every proof format records the target, coordinate pair or
degree rule, original demand, complete original cover, removed columns,
the earlier proof ID for every removal, remaining columns and strict
capacity deficit. No demand is weakened to one.

The terminal verifier uses a separate counting implementation. For each
active neighborhood, it counts coordinate incidences s_i and ordered
cooccurrences c_ij. The positive-support capacity is s_i-c_ij. This checks
all final capacities without using the census's bitset-difference operation.

Only target488 has a zero minimum coordinate-capacity margin. Its saved
minimizer compares coordinates17 and0, with demand1 and capacity1. Target487
has minimum margin1, with the same coordinates and demand1 versus capacity2.
Thus the sole zero-margin condition at the fixed point already has demand
one; the complete original-demand closure contributes no additional unit.

## Controls

A three-target synthetic control separates the original demand from its
weakened Boolean cover. One target requires two neighbors from a nonempty
support of size one, so it is removed. That removal then creates an
exterior-degree deficit at a second target. The two synchronous stages and
the earlier-proof provenance are checked exactly.

A separate genuine nine-vertex rook graph supplies four actual exterior
rows. The complete eligible domains contain every actual neighbor, the
mixed and degree identities hold, and the closure removes none of those
four targets. Neither control calls a solver or optimizer.

## Bindings and replay

Source:
`experiments/workspace/complement_rook_35core_case0004_coordinate_capacity_closure.py`

SHA-256:
`3e6522c8e191b371d9493278fe3b368eea093c0a5d5bd8e81c10ad9c5dd8cd52`

Compressed certificate:
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-capacity-closure.json.gz`

SHA-256:
`566e0598594330c406ede41d827c1eb02e9cd43c198ba1c05d82acd74d04fa65`

Cold replay report SHA-256:
`b2f77f3a913ff8de7b7b84222787d5b51afce6109baf104b4c162364f897f725`

From the repository root, replay to a fresh path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_capacity_closure.py \
  --replay experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-capacity-closure.json.gz \
  --output /tmp/conway99-case4-coordinate-capacity-closure-replay.json \
  --seconds 60
```

## Static backend inventory

The separately saved
`complement-rook-35core-case0004-sat-backend-inventory.json` records local
Python-SAT version1.9.dev23, native factory symbols, source hashes and the
relevant method bodies. It creates no solver instance, performs no query,
and installs nothing. No standalone SAT executable was found among the
ten recorded executable names on PATH.

The installed Python interfaces for CaDiCaL300 and CaDiCaL195 expose proof
retrieval but reject Python interrupt calls. MapleChrono and Maplesat expose
both interrupt and proof retrieval. Kissat404 rejects both interrupt and
proof retrieval. These are source observations, not runtime or proof-validity
controls. Any later backend query requires its own concrete preparation and
controls.
