# Independent audit of the rook-interface model

This note checks the mathematical necessity and clause logic of
`experiments/workspace/seven_red_interfaces.py`. The independent program
`experiments/workspace/seven_red_interfaces_independent_audit.py` uses a
different graph representation and a second SAT solver. It reproduces the
six-base and seven-base UNSAT results. The production DRAT certificate and
its replay provide the separately checkable solver proof.

The conclusion concerns all-red grids. A partial interface satisfying the
constraints is not a 99-vertex strongly regular graph.

## Necessary finite model

Let `R_0,...,R_(b-1)` be distinct all-red grids in a hypothetical
`srg(99,14,1,2)`. The [preliminary grid results](red_grid_limit.md) give:

- The grids are pairwise disjoint.
- Each pair of grids is joined by a perfect matching.
- Every such matching is a rook-graph isomorphism.

Choose coordinates on `R_0`, and transport them along its matchings to all
other grids. All matchings from `R_0` become the identity. Every remaining
matching is an automorphism of the same nine-point rook graph. This change
of coordinates does not restrict the possible configurations.

No remaining matching permutation `p` can send a point `x` to a rook
neighbor `p(x)`. If it did, the nonadjacent pair `(R_0,x),(R_j,p(x))` would
have the following three common neighbors:

- `(R_0,p(x))`;
- `(R_j,x)`;
- `(R_i,x)`, where the matching from `R_i` to `R_j` sends `x` to `p(x)`.

They are distinct because the grids are disjoint. This contradicts `mu=2`.
Exactly eleven of the 72 rook automorphisms satisfy the required condition.
The independent audit obtains all 72 by testing all `9!` permutations of
the nine points, then applies the no-neighbor-move test. Its ordered list
of eleven permutations agrees with the production list.

The same argument can use any grid as reference. Therefore a triangle of
matching labels has allowed holonomy. If its three increasing-index
oriented labels are `a=p_(i,j)`, `b=p_(j,k)`, and `c=p_(i,k)`, the map on
`R_i` is

    c^(-1) b a.

This is the product used in the production table. Exactly 581 of the
`11^3` label triples have allowed holonomy.

Finally let `H` be the adjacency matrix on the union of the grids. For
distinct vertices `u,v`, every extension to the full graph must satisfy

    (H^2)_(u,v) + H_(u,v) <= 2.

The bound is one common neighbor for an adjacent pair and two for a
nonadjacent pair. Only cross-grid pairs need encoding: a pair in one grid
already has its exact required common-neighbor count there, and a matching
from an external grid cannot add a common neighbor to two distinct points.

These conditions alone define the weak production model. It uses neither
the complement's vertex types nor spectral inequalities nor exact face
counts. Six such bases are already solver-UNSAT.

## Audit of the production clauses

Each nonreference grid pair has eleven label variables, constrained to
have exactly one true variable. The adjacency of any two points in these
grids is the disjunction of precisely the labels matching those points.
Both directions of this disjunction are encoded. The matrix is symmetric.
Within-grid adjacency and reference matchings are fixed Boolean values.

For a nonreference triple, eleven face variables choose exactly one
holonomy. A forbidden label triple gives a clause rejecting that triple.
An allowed triple implies its unique face variable. Under the exactly-one
constraints this describes the table exactly. A face containing the
reference grid uses its opposite matching label directly.

The common-neighbor gate for two nonconstant edge literals is an exact
conjunction, with all three defining clauses. Fixed true and false inputs
are simplified before gates are introduced. The code distinguishes Boolean
constants by object identity, so integer variable number one is not
mistaken for the constant `True`.

For every cross-grid point pair the cardinality terms are its adjacency
indicator and one conjunction for each potential common neighbor. Fixed
true terms reduce the bound; fixed false terms disappear. Repeated
indicators retain their multiplicity in the sum. This is the required
entry of `H^2+H`, without dropping paths or counting a false path.

## Additional optional clauses

These checks are not needed for the six-base exclusion, because its run
disables both options.

In diagonal coordinates `u=x+y`, `v=x-y` over `F_3`, every allowed map fixes
one coordinate pointwise. Apart from the identity, five maps act on `u`
and five on `v`. If every edge label fixes the same coordinate, the
two-dimensional space of zero-sum functions of that coordinate gives a
rook-minus-two space on each grid. Equal copies on all `b` grids have
eigenvalue `b-3` in the induced red graph. They are orthogonal to the global
constant vector. For `b>=7`, their Rayleigh quotient exceeds the permitted
upper bound three. Thus the optional requirement that both coordinate
families occur is necessary in its stated range.

For seven bases with `y` type-two complement vertices, the
[cubic trace count](red_grid_cubic_trace.md) gives exactly

    t_R = 27 + y/3

triangles meeting three red bases. Each unordered base triple contributes
the number of fixed points of its holonomy. The eleven allowed maps have
zero, three, or nine fixed points. Dividing by three gives the encoded
weight `9+y/9`, with weights zero, one, and three respectively. The two
extra identity-copy variables are each equivalent to the original face
indicator, so the unit-weight cardinality encoder counts an identity face
three times exactly.

## Exhaustive four-base control

Four bases have three free matching labels. The audit tests all 1,331
assignments. It builds their 36-point adjacency as integer bitsets and
counts common neighbors by intersections. Independently, it asks whether
the production CNF is satisfiable with those three labels fixed.

The answers agree for every assignment: exactly 136 are accepted. This
checks the complete four-base behavior, including rejected cases, instead
of relying on a single positive witness. The saved JSON records the
production source hash used for this test.

## Independent full-pair search

The second encoding has only the original matching-label variables. It
uses no adjacency variables, conjunction variables, face variables, or
cardinality auxiliaries. Plain clauses first impose exactly one label,
allowed triangle products, and common-neighbor caps for pairs involving
the reference grid.

The reference-pair caps and triangle products alone remain satisfiable at
five, six, and seven bases. Thus the remaining pair constraints matter.

CaDiCaL produces an assignment of matching labels. The audit builds the
entire adjacency as bitsets and examines every unordered pair. If a pair
violates the cap, three positive terms from its entry of `H^2+H` suffice
to witness failure. A term is either the pair's edge or a two-edge path.
The audit collects the selected matching labels forcing these edges and
adds the clause forbidding their simultaneous selection.

Every such clause is necessary. Internal rook edges and reference
matchings are constants. Each other used edge follows from one of the
listed label variables. Therefore an assignment satisfying all listed
labels contains the same three offending terms regardless of its other
matching choices. No invalid assignment is excluded on an unverified
spectral or geometric assumption.

The deterministic run recorded in
`experiments/logs/grids-and-triangles/seven-red-interfaces-independent-audit.json`
returned:

| Bases | Result | Candidate assignments | Direct pair cuts |
| --- | --- | ---: | ---: |
| 5 | Valid partial interface | 4 | 81 |
| 6 | Solver UNSAT | 853 | 20,229 |
| 7 | Solver UNSAT | 371 | 32,595 |

The five-base witness is saved as six explicit matching labels and passes
every pair cap. It is a positive control for the local interface model.
The two UNSAT searches use CaDiCaL195, whereas the production model uses
Glucose4. This cross-check is separate from the production DRAT replay.

Reproduce the audit with:

```sh
.venv/bin/python experiments/workspace/seven_red_interfaces_independent_audit.py \
  --lazy-full-model --seconds 45 \
  --output experiments/logs/grids-and-triangles/seven-red-interfaces-independent-audit.json
```
