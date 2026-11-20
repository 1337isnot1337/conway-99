# Three type-\(33\) edges need not give a split shell

The [split-component reduction](root_prism_free_f0_components.md) proves
that a prism-free, \(F\)-free triangle shell has either one connected
component of size 36 or two components of size eighteen. The converse
of its type-\(33\) implication does not hold locally: all three central
edges can have partition \(33\) in a connected shell.

Label each twelve-vertex fiber by \((b,i)\in\{0,1\}\times\mathbb Z_6\).
Normalize the first two cross matchings to identity. In each block take
the first internal matching to be
\((01)(23)(45)\), and the other two internal matchings to be
\((12)(34)(50)\). Set the remaining cross permutation to
\[
Q(b,i)=(1-b,i+1).
\]

Each pair of internal matchings, after the appropriate cross pullback,
has two alternating six-cycles. Thus every central edge has partition
\(33\). Within either block the first two fibers already form a
connected twelve-cycle, and the first and third fibers join all
eighteen block vertices. The permutation \(Q\) joins the two blocks.
The full shell is therefore connected.

The [exact control source](../experiments/workspace/root_prism_free_f0_connected_control.py)
checks all visible common-neighbor caps, enumerates the triangles and
confirms that no two form a prism, and checks the three edge
partitions directly. It also excludes an internal \(F\): every
noncentral vertex has degree four in the partial core, whereas both
centers of \(F\) have degree five. Both centers would have to be
central, and none of their partitions has a part of size two.

This is a thirty-nine-vertex partial graph. It is not a full graph
construction or evidence that its exterior can be completed.

The [certificate](../experiments/logs/root-prism-free/f0-connected-all33-control.json)
contains all adjacency rows and source hashes. Standard-library replay:

    .venv/bin/python experiments/workspace/root_prism_free_f0_connected_control.py \
      --certificate experiments/logs/root-prism-free/f0-connected-all33-control.json \
      --replay
