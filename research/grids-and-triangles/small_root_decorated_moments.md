# Complete high-graph distributions over the 33 small roots

## Scope

This preparation strengthens the published presence distributions for all 33 six-vertex roots whose complete high-class domain has population at most four. It retains the induced graph among the high vertices.

The finite domain contains 1,275 decorated states over 1,115 presence atoms. Only nine roots permit a high-high edge. Root 49 has 80 presence atoms and no possible high-high edge, so its decorated distribution coincides with the previous presence distribution.

No count point was loaded or evaluated during preparation. No optimizer was used. The preparation neither constructs a graph nor excludes one.

## Literal pattern moments

Fix a labelled six-vertex root H. A high class is a root-neighborhood mask with at least three root vertices. Each high class contains at most one vertex: two distinct vertices in the same class would have at least three common neighbors.

Write a decorated partial state as s=(A,E), where A is a set of high masks and E specifies every edge and nonedge among their vertices. Let F_s be the graph formed by the root and these high vertices, with all root incidences and all high-high adjacencies fixed.

For a fixed labelled root embedding, there is at most one extension realizing this literal pattern because its masks identify all the free vertices. Therefore the aggregate partial-pattern moment is

    m_s = Aut(F_s) N_{F_s},

where N_F is the number of induced vertex subsets of type F. There is no division by a rooted or free-label stabilizer. If distinct literal decorations have isomorphic unrooted graphs, they have equal individual moments; each literal decoration remains a separate state.

The frozen 32-root preparation has 294 singleton catalogue fingerprints across all 2,450 selected product rows. The new source checks those complete rows against the singleton class-to-type map. Root 49 contributes its frozen literal type anchors. The resulting table has 313 distinct types. The source independently recounts each automorphism factor and checks an explicit isomorphism for every one of the 1,275 states.

Summing m_(A,E) over every admitted decoration E of one presence set A exactly reproduces its frozen presence-moment form. All 1,115 such identities are checked before a count point can enter the program.

## Complete state domain

The source independently enumerates the high-mask universe, every presence set of size at most four, and every internal edge assignment on each cap-compatible presence set. It tests the necessary cap

    A_ij + |N(i) intersect N(j)| <= 2

on the full literal graph.

It also checks every five-mask subset with no high-high edges. Each such graph already violates a cap. Adding high-high edges cannot repair a cap violation, so no actual root embedding can have five or more high vertices.

This gives a complete necessary domain for every actual full high graph at these roots. It may retain states that fail other ambient constraints. That makes the subsequent nonnegativity conditions necessary, without asserting that every retained state extends to a 99-vertex graph.

For every state t=(T,D) and every subset A of T, the program finds exactly one restriction

    t|A = (A, D[A])

in the state domain. The preparation checks all 8,011 restrictions.

## Exact inversion

Let w_s count labelled root embeddings whose entire high graph is exactly state s. For a partial state s,

    m_s = sum_{t restricting to s} w_t.

If s=(A,E) is a restriction of t=(T,D), the interval between them consists of the unique restrictions of t to the subsets B satisfying A subset B subset T. It is a Boolean interval. Its Mobius coefficient is therefore

    mu(s,t) = (-1)^(|T|-|A|).

Consequently,

    w_(A,E)
      = sum_{(T,D): (T,D)|A=(A,E)}
          (-1)^(|T|-|A|) m_(T,D).

The edge-restriction condition is essential. A larger decoration contributes only to the unique decoration it induces on A.

Every actual graph has nonnegative integer w_s. A negative value therefore gives a necessary induced-count inequality that the saved point violates. Conversely, nonnegative values certify only this finite decorated-moment distribution; they do not certify ambient graph existence.

The source tests the complete inversion matrix on every atomic distribution, covering 114,847 state/atom equalities. Each recovered distribution is also checked against every decorated partial-pattern moment.

## Coarsening to the published presence distributions

For a presence set A,

    presence_moment(A) = sum_E m_(A,E),
    presence_weight(A) = sum_E w_(A,E).

Each larger decorated state restricts to exactly one decoration on A. Thus summing the decorated inversion over E gives precisely the original presence inversion.

The source checks these identities on every atomic distribution. The future point query will check them again using exact BigInt arithmetic, together with every frozen presence-moment form. This prevents a negative decoration from being confused with a change in the earlier presence model.

A synthetic control has all decorated partial moments nonnegative and all exact presence weights nonnegative, while one exact decorated weight is negative. It demonstrates the algebraic distinction between the two models. It is explicitly not claimed to arise from a catalogue-consistent count point.

## Root symmetries and divisibility

The complete root automorphism groups act on the decorated state domains. The preparation checks 5,175 state transports and obtains 589 decorated orbits.

For a state s, its stabilizer acts freely by precomposition on injective labelled root embeddings whose exact high graph is s. Therefore w_s is divisible by the stabilizer order. The source verifies coefficientwise that every derived induced-count form has this divisor. This check is a normalization control; no additional count-point restriction was evaluated during preparation.

## Frozen artifacts

- Source: experiments/workspace/small_root_decorated_moment_recovery.js
- Preparation: experiments/logs/moments-and-counts/small-root-decorated-moment-preparation.json
- Cold preparation replay: experiments/logs/moments-and-counts/small-root-decorated-moment-preparation-replay.json
- Manifest: experiments/logs/moments-and-counts/small-root-decorated-moment-manifest.json

The source's prepare mode checks the two frozen input-preparation Git blobs and the frozen isomorphism dependency. Query mode additionally requires the existing count-point Git blob, reruns the point-independent preparation, and uses only BigInt count arithmetic.

At this checkpoint only preparation and its byte-identical cold replay have run. The count query awaits a separate coordinator gate.
