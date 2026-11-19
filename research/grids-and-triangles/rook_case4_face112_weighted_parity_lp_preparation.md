# Complete rook case4 LP with the two weighted parity cuts

This preparation adds two exact integer consequences to the frozen H3
selector relaxation. It contains no production optimizer result.

## Matrix and proof domain

The parent has 1,102 free selector coordinates, 112 proved zeros, 166,011
rows and 10,767,194 nonzero coefficients. Its complete original-domain
cold verification is retained under hash
`56864810924bacb6b331db728a4ce32810d8e6f2dfe7c196e0a73e0b2f583a97`.

The new builder reads that exact parent model and its arrays. It checks
every inherited array prefix and row/column transport, then appends only
the two rows from the direct weighted-parity certificate:

| New row | Original-coordinate form | Lower | Upper | Terms |
| --- | --- | ---: | ---: | ---: |
| 166,011 | Rounded capacity equivalent to the 70-column odd cover | 0 | 4 | 48 |
| 166,012 | 50-column odd cover | 1 | 17 | 50 |

Both rows have unit coefficients. The capacity/cover equivalence is the
exact Gram identity `H+2F=b`; every coordinate and proved-zero substitution
is checked in the separate direct proof. The new rows require only the
older 99-zero premises. They neither add a zero assumption nor constrain
a selector to a value proposed by a numerical point.

The new base has 166,013 rows and 10,767,292 terms. Its model hash is
`c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3`;
its arrays hash is
`59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e`.
The integer row-stream hash is
`461e17bf688f21c831928b528e334cb5f80f0a8f9075df0dee740f76fae1db55`.
The arrays archive has 5,347,974 bytes.

The original cover supports are not enumerated again. The new cold pass
binds the earlier full-domain verification, checks the cached complete
prefix, reconstructs both new proof rows, and compares every new array.
It passed in 9.884 seconds under hash
`567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156`.
Its metadata states explicitly that the inherited omission proofs were
bound rather than rerun in this pass.

## Unchanged bounded query method

The driver adds a max-min coordinate `t`, with `0<=x_j-t<=1` for each of
the 1,102 surviving selectors and unit bounds on every variable. Every
base point extends with `t=0`. Thus the extra coordinate does not remove
an original feasible point.

The extended model has 1,103 variables, 167,115 rows and 10,769,496 terms.
The initial active system has 3,071 rows and 28,067 terms: all 1,960
retained native rows, both unit sums, four pair capacities, H3, both new
parity rows and every max-min extension row. All 164,044 retained original
coordinate covers remain in the complete external pool.

The source transformation from the reviewed H3 driver has 25 recorded
text substitutions. Sixteen functions are AST-identical, including the
numerical run, row-pool inspection, exact primal acceptance and saved
prefix replay logic. The changes concern bindings, two extra row IDs,
dimensions and the explicit cached-prefix proof contract.

The proposed single production run keeps the previous limits:

- At most 30 native calls and 120 cumulative optimizer/existing-ray seconds.
- At most 180 seconds in the numerical phase, including bootstrap and scans.
- At most 512 newly violated original covers appended after one call and
  14,848 covers over the entire run.
- One solver thread, no hints, no selector assumptions and no symmetry
  restriction.
- A separate 60-second exact reconstruction stage and 60-second exact
  terminal acceptance check.
- Stop on a nonoptimal or invalid numerical result; no automatic retry.

After each numerical point, the driver scans every row in the complete
extended model. Rows are selected by decreasing numerical violation,
then increasing original row ID. Numerical feasibility is a proposal
only. A rational point is accepted only after exact finite-bound checks
on every one of the 167,115 rows and restoration of all 1,214 original
coordinates. An exact bound from an active row subset remains valid for
the complete model. Numerical infeasibility without an exact certificate
does not exclude case4.

Preparation and the native assembly controls made no optimizer calls.
The final preflight hash is
`66352ced7b8d35052d0e45c0b8d7c3bc00902c4699a9347b3b5981ac6069e840`.
The preparation hash is
`d33f414489ca4f3e734b4011c4582668bf469f8192a659d8200ff440edb8543c`;
the mathematical definition hash is
`35ce7bca9fafb01d289d2896bd58382815f4abdc1882b65e5c80af74fe1938f1`.

The scope remains one specified 35-vertex core and internal matching. A
real point is not a binary incidence. A binary incidence would still be
only a partial graph specification. The complete Conway99 problem is not
settled by this preparation.
