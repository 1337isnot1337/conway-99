# A limit of the complementary-rook linear relaxation

The joint real incidence/edge relaxation below permits `a=36`. An exact
rational point and a rational dual certificate give an optimum of 36.
Thus these linear constraints do not strengthen the elementary upper
bound on `a`. This is a statement about a finite real relaxation, not a
binary incidence design or a graph.

## Full domain before averaging

The core is the complementary-rook 27-point matrix

\[
B=\begin{pmatrix}R&I&I\\I&R&I\\I&I&J-I-R\end{pmatrix}.
\]

All 252 possible exterior signatures `(p,q,t)` are retained. They satisfy
`p!=q`, `R[p,q]=0`, and `t` distinct from both `p` and `q`. A selector
`x_s` records whether signature `s` is present. For every eligible pair
`s,w`, an edge variable `y_sw` records its possible adjacency. There are
20,934 eligible pairs before averaging. The eligibility conditions use
only core overlap and nonnegative mixed demands.

The real relaxation contains:

- `0<=x_s<=1`, nonnegative edges, and `y_sw<=x_s,x_w`;
- every core incidence Gram equation and the population 72;
- every mixed equation and exterior degree equation, with right side
  multiplied by the source selector;
- for each source and pair of core points, at most one selected neighbor
  containing that core pair.

The last family is necessary because two such neighbors would already
have two common core neighbors. They cannot also share the source.
Its conditional right side is the source selector. The relaxation
omits binary restrictions and the remaining exterior common-neighbor
products.

## Averaging is legitimate only for this real relaxation

The 72 simultaneous rook relabelings and the swap of the first two
grids form 144 automorphisms of the fixed core and complete domain.
Each acts on selectors and possible edges. Every feasible binary graph
would give a feasible point of the real system, and averaging its
relabelings preserves all linear equalities and inequalities.

The objective `a` is invariant under these relabelings. Therefore an
upper bound from the averaged real system would be necessary for every
graph. Equalities between orbit variables are used only after this
convex averaging argument. No automorphism of a binary completion is
assumed.

The selector orbits have sizes 72, 144, and 36. They correspond to two
rook-near relations to the tip, one near and one far relation, and two
far relations. The edge domain has 179 orbits. After removing duplicate
rows, the model has 182 variables, 54 equalities, and 517 inequalities.

## Exact result

The 36 both-far candidates immediately give `a<=36`, because the Gram
margins make the selected both-near and both-far counts equal. The
computed exact point attains this bound in the real relaxation. Its
182 orbit values are nonnegative; 16 are fractional, and every
denominator divides four.

The replay checks every equality and inequality with rational arithmetic.
It also checks a rational combination of the equality and inequality
rows. Inequality multipliers are nonnegative, and the resulting
coefficient vector dominates the objective coefficient vector. Its
right side is 36. The feasible objective value and dual bound agree
exactly.

An independent audit imports neither the model builder nor an optimizer.
It reconstructs the full labeled domain and lifts the saved orbit point.
It checks all 729 Gram entries, 41,868 activations, 6,804 mixed equations,
252 degree equations, and 88,452 packing inequalities with exact integer
arithmetic after scaling by four. It separately verifies the 144 group
actions and the elementary upper bound.

This negative result leaves the checked binary bound `a>=3` unchanged.
It directs subsequent tests toward binary incidence choices and local
neighborhood constraints.

## Replay

```sh
.venv/bin/python experiments/workspace/complement_rook_joint_projection.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-joint-projection.json
```

The replay reconstructs the full domain, checks the core group actions,
rebuilds the averaged model, verifies source and model hashes, and
checks the saved primal and dual witnesses exactly. It starts no solver.
