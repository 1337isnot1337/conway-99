# Direct moments for induced high-vertex graph patterns

All **200** rooted induced-pattern orbits now have exact moment right
sides at the frozen count point. Literal normalization checks recover all
200 full automorphism orders, and the decorated right sides aggregate
exactly to all 73 presence-only equations. No optimizer or product tensor
was used.

## The fixed-pattern moment

Fix a labelled independent six-root \(H\). A high neighborhood class has
at least three root neighbors, so it contains at most one outside vertex.
Let \(T\) specify distinct high masks and every edge and nonedge among
their vertices. It has at most four free vertices. Let \(F_T\) be the
resulting induced graph on the six roots and those free vertices.

For a fixed labelled root embedding, the high masks determine every free
vertex uniquely. The pattern indicator is therefore Boolean. Its sum over
all labelled root embeddings is exactly the number of labelled induced
embeddings of \(F_T\):

\[
m_T=|\operatorname{Aut}(F_T)|\,n(F_T),
\]

where \(n(F_T)\) is its unlabelled induced count. This includes
automorphisms that move the chosen root set. Dividing by the root
stabilizer would give the wrong normalization.

If \(R\) is the orbit of \(T\) under relabelling the six roots, every
pattern in \(R\) has the same unrooted graph type. The quotient right side
is

\[
b_R=|R|\,|\operatorname{Aut}(F_T)|\,n(F_T).
\]

No free-label or root-stabilizer divisor is applied.

## Complete checks

The independent source rebuilds all adjacency matrices from masks and
mutual-edge bits. It checks all 720 root-label images of each pattern,
their orbit sizes and stabilizers, and their disjointness. It checks every
edge prescription on the 73 presence representatives, including forbidden
prescriptions. The complete domain contains 279 valid decorations on
those representatives and 200 pattern orbits.

For each pattern graph, the source enumerates every independent six-set
and every ordering of that root set. It counts exactly the root embeddings
whose uniquely determined free vertices realize the specified pattern.
Since the host in this test is the pattern graph itself, this count is its
full automorphism order. All 200 counts agree with the catalogue. The
checks cover 144,720 ordered root embeddings.

Three additional hosts append an isolated vertex to a pattern graph.
The source separately counts induced copies and literal pattern
indicators. In each case the latter equals the full automorphism order
times the induced-copy count, testing nontrivial copy multiplicities.

The pattern graphs occupy 200 distinct catalogue types. They have 73,263
distinct root-labelled pattern representatives in total.

## One required multiplicity of two

For 199 rows, the pattern graph has exactly one independent six-set.
Its coefficient in the quotient right side is 720.

Row 4 is different. Its four high masks are
\(7,11,13,14\), the four triples on four root sites, and there are no
high-high edges. The graph is \(K_{4,4}\) with a perfect matching removed,
plus two isolated vertices. It has two independent six-sets.

Its root-label orbit has size 15, its root stabilizer has size 48, and
its full automorphism group has order 96. Thus its right side is

\[
15\cdot96\,n(F)=1440\,n(F),
\]

not \(720\,n(F)\). The graph is catalogue type 13,864. At the bound point
its induced count is 41,030 and its quotient right side is 59,083,200.

## Aggregation and point scope

For each fixed presence mask set, summing over all valid mutual-edge
patterns recovers its presence indicator. The exact preparation checks
this identity at the bound point in two forms:

1. Graph-pattern moments, weighted by their orbit sizes inside the
   presence stabilizer, sum to the fixed-mask presence moment.
2. Full root-orbit right sides sum to the old presence-orbit right side.

All 73 comparisons pass exactly. All 200 decorated right sides are
positive at this point; no row is removed.

Each right side is a single induced-count coordinate with its exact
integer coefficient. A later linear combination of these rows therefore
has a direct induced-count form. This preparation does not construct or
check the full graph-domain feature matrix; that coefficient aggregation
is a separate artifact.

The count point is the unchanged 48-cut prism-zero, \(x_{521}=0\) integer
witness, SHA256
0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.
Neither the moment preparation nor its replay makes a feasibility or
graph-existence claim.

## Frozen artifacts

Source: experiments/workspace/grid_free_order10_high_mask_graph_moments.py,
SHA256
e5a3cd963baa17aa755e04cae36fb33725cd7b03e40df4ca00b4014d81c899f7.

Exact moments: experiments/logs/moments-and-counts/order10-high-mask-graph-moments01.json,
SHA256
43bde72fa777410a73732d418530a6a853a39740a1b7bcfc591d78977ad4cc3d.

Cold replay: experiments/logs/moments-and-counts/order10-high-mask-graph-moments01-replay.json,
SHA256
002e643769789b4505288dd815ccf65436d2cc1135aa349b8276e6dbf5658d96.

Preparation took 2.91 seconds with peak RSS 167,684 KiB. The fresh replay
took 3.75 seconds. The independent source and saved-arithmetic review is
bound separately.
