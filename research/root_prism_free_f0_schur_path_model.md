# Full fractional model with two-edge prism constraints

This preparation adds the complete 5,124-row two-edge prism family to the
prepared graph-Schur and one-edge prism model. The earlier model remains
unrun. This package prepares one subsequent numerical call on the larger
model; preparation and transport checks call no optimizer.

The scope remains the globally prism-free and F-free split 18+18 shell with
component zero. All 480 first-component signatures remain available. The
second component and its incidence are free. There is no graph-automorphism
assumption, fixed first design, or new selector restriction.

## Necessary two-edge inequality

Let x-y-z be an induced path in the fixed core. Let three distinct exterior
signatures a,b,c have the following intersections with these three sites:

| Signature | Core sites present | Core sites absent |
| --- | --- | --- |
| a | x,z | y |
| b | x | y,z |
| c | y,z | x |

If exterior edges ab and bc both occur, the triangles {a,b,x} and {c,y,z}
have matching edges a-z, b-c, x-y. The potential edge ac is absent: its
endpoints already have distinct common neighbors b and z. Hence these six
vertices induce a prism. Global prism-freeness therefore implies

\[
y_{ab}+y_{bc}\le z_b.
\]

Taking expectations and averaging through the twelve verified core actions
gives the quotient inequality Y_ab+Y_bc<=x_b. If both literal edges have the
same quotient coordinate, their coefficients add to two. They cannot be
deduplicated as repeated terms.

The frozen census checks 107,520 literal configurations and records every
disposition. After implications from already certified zero edges and
quota-one mixed equations, 61,512 configurations remain. Their complete
quotient gives 5,122 three-coordinate rows and two two-coordinate rows with
coefficient two. Every quotient row has twelve checked literal transports.

## Exact assembly

The versioned builder binds the frozen parent, the complete path census,
and both existing cold-replay records. It does not repeat either earlier
census. It independently checks all twelve actual core actions, their 144
compositions, the selector and edge orbits, all 5,124 appended literal
inequalities, and all 61,488 row transports. Each literal check constructs
the six-vertex prism from its prescribed core and exterior incidences.

The original matrix and scale prefixes are preserved exactly. The only
new rows are the 5,124 path inequalities, with zero right-hand sides and
15,370 nonzero terms. No variable is removed or added.

| Quantity | Prepared parent | Path overlay |
| --- | ---: | ---: |
| Variables | 15,200 | 15,200 |
| Equalities | 6,135 | 6,135 |
| Inequalities | 16,505 | 21,629 |
| Total rows | 22,640 | 27,764 |
| Nonzero matrix entries | 889,906 | 905,276 |

The inherited rows include all 4,416 normalized selector predicates, the
original RLT system, 32 selector-PSD directions, 39 graph-Schur directions,
162 visible-prism edge-zero equalities, and 715 one-edge prism inequalities.
The whole PSD cone is not imposed. The later core-pair clique family is
outside this preparation.

All mathematical coefficients remain integers. New path-row scales are
positive powers of two. Every inherited scale remains unchanged. The native
transport check constructs exactly the query's CSC matrix and calls
passModel, getLp, and getNumNz without run. It checks every coefficient,
index, bound, and cost against the supplied matrix.

## Bounded numerical and exact phases

The new query and replay are explicit narrow substitutions of the reviewed
parent sources. A source-only control compares their complete text and AST
against those substitutions. The new exact loader checks the entire parent
prefix and every appended row certificate.

The planned production query permits one IPM call with crossover disabled,
one thread, and a 180-second numerical child bound including setup. It saves
available numerical coordinates without treating them as an exact point.
It neither requests a basis nor attempts active-face reconstruction.

If the backend reports infeasibility, getDualRay is called only after
getDualRayExist confirms that a ray already exists. A saved ray permits one
separate 60-second exact phase. Dyadic row scales are pulled back with exact
rational arithmetic. A certificate is accepted only when integer row
multipliers give a strict contradiction over the complete unit box. The
standalone cold replay verifies the certified parent bindings, reconstructs
every appended row from its witnesses, and checks that certificate against
the complete assembled matrix. A numerical status without this certificate
remains UNKNOWN.

The first path preparation's direct Python-object comparison failed before
its model was written; complete canonical bytes nevertheless matched. A
second analogous parent-comparison issue was found in source review before
cold execution. An attempted repeated census then exceeded its existing
30-second preparation limit. These records are preserved. The final adapter
uses the already certified parent records and checks only the newly appended
mathematical content. Every earlier prepared model remains unqueried.
