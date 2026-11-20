# The rook graph cannot be covered by nine disjoint triangles in a 99-graph

Suppose nine disjoint triangles are arranged in a three-by-three array. Assume that two in the same row or column are joined by a perfect matching, and that two in different rows and columns are anticomplete. This configuration of 27 points is impossible in a Conway 99-graph. The proof includes an exhaustive Boolean calculation with independently checked DRAT refutations.

Every row and column is a grid by the [three-triangle observation](full-triangle-components.md). Thus each of its three matchings composes flatly around the triangle of cells. Within each row, label the three points of every cell so that all horizontal matchings preserve labels. Independent permutations of each row's labels now set both vertical matchings from the top cell of column zero to the identity. On each other column, choose how its middle and bottom labels transport to the top cell. The remaining vertical edges are determined, giving $6^4=1296$ labeled cores. The [checker](../../experiments/workspace/rook_nine_covers.py) finds 18 isomorphism classes of ordinary graphs. An isomorphism carries any extension of one core to an extension of the other. The representative's six grids are induced in every such extension.

## Attaching the 72 exterior points

Every exterior point sees exactly one vertex in each row and column grid. Its neighbors in the core therefore form three signed cells on a permutation of the rows and columns. A triple of core neighbors occurs at most once, since two points have at most two common neighbors. Write $A$ for the 27-point adjacency matrix. The required matrix of exterior common-neighbor counts is $Q=12I+2J-A-A^2$.

For a fixed permutation the 27 possible triples form a binary three-by-three-by-three table. Every two distinct cells on the permutation determine its third cell. Thus each two-coordinate margin is prescribed by the corresponding entries of $Q$. For every pair of symbols at the first two positions, enumerate the subsets of the three remaining symbols of precisely the required size. Subtract these choices from the other two margins and require both margins to vanish at completion. Combining the tables for the six permutations gives 484 assignments, on just five ordinary cores. At every leaf the checker verifies directly that the $72\times27$ exterior incidence matrix $B$ satisfies $B^{\mathsf T}B=Q$. Up to isomorphism keeping the 27-point set distinguished, the five cores have respectively 2, 21, 51, 6, and 6 attachments.

## Exterior adjacency

For a fixed attachment let $E$ denote the unknown symmetric adjacency matrix on the 72 points. The equations for exterior-to-core pairs require
$$
EB=2J-B-BA.
$$
A possible edge $xy$ is omitted if the two rows of $B$ already overlap in two points, or if adding either incidence row to the other's equations would exceed an entry of the right side. Every remaining row equation is encoded as an exact cardinality. For exterior pairs, overlap two prohibits any common exterior neighbor. With overlap one, an edge and an exterior common neighbor cannot occur together. These necessary clauses suffice on the first four cores. On the last core the verifier also imposes the full upper bound of two minus the overlap on the edge indicator plus the number of common exterior neighbors.

CaDiCaL generated an UNSAT proof for each of the 86 attachments, and DRAT-trim verified all 86 against their generated CNFs. The same adjacency encoder accepts the actual exterior edges for all 510 nonempty proper choices of the marked set in the nine-point rook graph. Run `make verify-nine-triangle-cover` for the control, enumeration and complete proof replay. The checker generates proofs in temporary directories. The default structural suite only enumerates the attachments.
