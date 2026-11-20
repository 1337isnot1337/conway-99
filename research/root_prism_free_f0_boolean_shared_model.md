# Complete literal Boolean shared-edge model

The new model keeps the complete accepted F0 selector parent and appends
one Boolean variable for each of the 68,394 eligible exterior edges. It
retains all 480 signature choices and all original edge variables. The
selector parent has 540 variables and 17,162 rows, including its complete
12,481-row additional registry.

The model adds both endpoint activations for each edge, all exterior degree
equations, and all mixed core/exterior equations. It also includes the
previously certified prism edge zeros and every retained literal core-pair
clique row. No completed-graph symmetry, selector fixing, objective,
assumption, or solution hint is imposed.

| Row family | Count |
| --- | ---: |
| Complete parent | 17,162 |
| Both endpoint activations | 136,788 |
| Exterior degree equations | 480 |
| Mixed equations, including 756 empty equations | 8,640 |
| Witnessed prism edge zeros | 1,884 |
| Literal core-pair cliques | 3,096 |
| Total | 168,050 |

There are 68,934 variables: the original 540 and the 68,394 new Boolean
edges. Edge variables use the original complete lexicographic edge order.
The original parent is recovered byte for byte by removing the appended
variables and rows.

## Meaning of the appended constraints

For each eligible pair `a,b`, the edge variable satisfies `y_ab <= x_a`
and `y_ab <= x_b`. For every signature `a`, its incident edge sum is
`8*x_a`. The 18 mixed equations have right-hand sides `q_ai*x_a`, using
the independently reconstructed targets. Their target sum is 24 and every
neighbor signature has size three, consistent with degree eight.

Each zero row has an explicit six-site induced triangular prism witness
inside the fixed 21-vertex core plus the two joined exterior signatures.
The producer and independent checker each validate all 1,884 witnesses.
These rows use the existing prism-free F0 premise.

For a center `b` and two distinct core sites `i,j`, two exterior neighbors
of `b` containing both sites would have three common neighbors. The
common-neighbor cap therefore gives at most one such edge. Endpoint
activation strengthens this to a live edge sum at most `x_b`. Removing
only the already proved zero terms gives the saved literal clique rows.
All 73,440 center/core-pair buckets were reconstructed; all 258 original
representative rows and their twelve transports were compared. Native
rows use literal variable IDs throughout.

The older proof records are described in
[the edge-motif note](root_prism_free_f0_edge_motifs.md) and
[the core-pair clique note](root_prism_free_f0_core_pair_edge_cliques.md).
Their complete hashes and transport mappings are bound by configuration02
and the saved overlay proof.

## Native preparation and independent replay

Small actual native controls checked Boolean and signed domains, an empty
linear equation, an integer coefficient above the binary64 exact range,
and rejection of an invalid variable index. Public native text parsing
and export preserved the complete control bytes.

The full preparation then constructed the expected standard protobuf,
parsed it through the public native interface, validated it, and compared
the complete exported bytes. The model phase took 17.557 seconds; its
owner completed in 19.505 seconds. Peak resident memory was 551,624 KiB.
No `CpSolver` was constructed and no optimizer was called.

The model has 33,451,907 raw bytes, SHA-256
`4505234d13039159c3191918f7db729819ad6ed25f46e538d91975466d660e83`.
Its lossless gzip has 4,960,256 bytes, SHA-256
`5d2e705f10f5a04f593a486ca271f0a6e06dc981c95ffc977054c6fdce906036`.

The independent checker imports neither builder and constructs neither
`CpModel` nor `CpSolver`. It reconstructs the domain, all appended
variables and 150,888 appended rows, every prism witness, every bucket,
and every transport. It also compares the complete original parent
bytes. Replay took 6.394 seconds; its owner completed in 6.574 seconds.
Both owners exited successfully with all children reaped.

The accepted preparation report has SHA-256
`ecdc3405f803d8e5815dba2555f4c9884018de69aff0b756a132e26c0a0a8471`.
The independent cold report has SHA-256
`a907d1c0f51f893166f32b1aab136d885b412cf0aecbdfed2a938fdaaf373efb`.
The cold owner inventory includes a historical initial owner snapshot.
Its separate preserved snapshot and resolution record distinguish it
from the final accepted owner; neither original receipt was rewritten.

## Exact restoration

The publication keeps the lossless gzip and a checked restoration
manifest. A fresh clone can materialize the raw model before replay:

```bash
python experiments/workspace/exact_prefix_suffix_artifacts.py restore \
  --manifest experiments/logs/root-prism-free/f0-boolean-shared-native-preparation01-publication01/manifest.json
```

The helper checks the compressed and complete raw hashes. It accepts an
existing raw file only if every byte matches. The manifest uses the full
decoded gzip as its prefix and an empty suffix, so the raw 33 MB file
need not be stored twice in Git.

This package establishes the model construction and exact transport.
It contains no solver query and establishes neither a full graph nor
infeasibility. General outside-pair common-neighbor constraints remain
outside this model; any returned assignment needs further inspection.
