# Relabeling the checked signed cuts

The eight replayed cuts from the first incidence-master pilot give
1,152 distinct clauses after removing unused assumption units and
applying the 144 verified core relabelings. No clause in that set is
strictly subsumed by another. This is a static consequence of the saved
proofs. It does not use a new SAT call or modify the completed pilot.

The eight tested designs also lie in eight distinct relabeling orbits,
each of size 144. On their union of 1,152 labelled designs, the original
eight clauses block only eight designs. The closed set blocks all
1,152. This finite control shows the additional pruning from relabeling.
It is not a count of all possible incidence designs or a search-time
prediction.

## Removing unused assumption units

For one pilot case, let `F` be the frozen necessary joint formula, `C`
its signed assumption core, and `H` the retained input clauses. The
completed replay has established

\[
H\subseteq F\cup\{\{\ell\}:\ell\in C\},\qquad H\text{ is UNSAT}.
\]

Let `D` contain exactly those literals of `C` whose singleton clauses
occur in `H`. Every removed singleton is absent from `H`. Therefore

\[
H\subseteq F\cup\{\{\ell\}:\ell\in D\}.
\]

The same retained proof excludes `D`. This inference needs no new
solver call and makes no minimality claim about `D`.

Three cases shrink:

| Case | Original size | Refined size | Unused signed units |
| --- | ---: | ---: | --- |
| 3 | 42 | 40 | -9, -37 |
| 4 | 41 | 39 | -9, -85 |
| 5 | 42 | 40 | -38, -115 |

The other five cases keep their original sizes. The refined sizes,
in pilot order, are `40,35,29,40,39,40,41,39`.

These unit numbers are the existing selector variables `1,...,252`.
Literal `u>0` selects signature index `u-1`; literal `-u` requires that
signature to be absent. The proof signs are preserved throughout.

## Why all images are necessary

The complementary-rook core is preserved by simultaneous row and
column permutations, optional coordinate transposition, and optional
interchange of its first two bases. These give 144 distinct
permutations of the signature domain.

For an action `g` on signature indices, transport a signed literal by

\[
g(\ell)=\operatorname{sgn}(\ell)
\bigl(g(|\ell|-1)+1\bigr).
\]

Every completed graph with the fixed core can be relabeled by `g`.
Its incidence selectors, exterior edges, and all necessary constraints
are transported together. If it realized the pattern `g(D)`, applying
`g^{-1}` would give a completion realizing `D`, contrary to the retained
proof. Thus every image yields the valid clause

\[
\bigvee_{\ell\in D}\neg g(\ell).
\]

No completed graph is assumed to have an automorphism. The operation
changes its labeling. All 144 clauses are consequences; this imposes
no equality between graph variables and chooses no symmetric graph.

The program checks the primary mathematical domain directly. For every
action it reconstructs the core-coordinate map from signature
incidence families, then checks:

- All 729 adjacency and Gram matrix entries.
- All 252 transported incidence signatures.
- All `252*27` mixed demands.
- The complete set of 20,934 eligible edges.

Core-pair packing is preserved because signature containment, the core
pair, and every incident edge are transported together. Activation,
the total selector count, and exterior degree 11 are also preserved.

This is an action on the mathematical primary-variable model. No
permutation of the auxiliary sequential-counter variables is asserted.
The counters encode the transported cardinality constraints; a new
auxiliary extension can be chosen after the primary variables are
relabeled. A literal permutation of the serialized CNF is unnecessary.

## Exact coverage

Each refined cut has an orbit of size 144. The eight orbits are
disjoint, giving 1,152 image clauses. The certificate stores every
image, its originating replayed case, and an explicit action index.
The source reconstructs every action deterministically and binds the
complete action table by hash.

Strict clause subsumption is checked by signed-literal containment.
There are no subsumed clauses among these 1,152. The full set can be
added to a future master without adding auxiliary variables. Its
2,520 original clauses would become 3,672 clauses.

This future addition was not made during the baseline pilot. No
master formula with these image clauses has been solved here, and
there is no exhaustion or whole-core exclusion claim.

## Files and exact replay

Files:

- `experiments/workspace/complement_rook_incidence_master_cut_orbits.py`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-cut-orbits.json`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-cut-orbits-generation.log`
- `experiments/logs/grids-and-triangles/complement-rook-incidence-master-cut-orbits-replay.log`

The standard-library program requires the completed eight-case
full-replay report. It checks the pilot, proof, retained-input, and
replay-log bindings before using any cut.

```sh
python experiments/workspace/complement_rook_incidence_master_cut_orbits.py \
  --pilot experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.json \
  --replay experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-full-replay.json \
  --certificate experiments/logs/grids-and-triangles/complement-rook-incidence-master-cut-orbits.json
```

The pilot and its generation-time certificates remain unchanged. This
certificate records only proof-supported refinement and relabeling.
