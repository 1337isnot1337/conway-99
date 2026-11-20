# Exact coverage of the eleven unrestricted root-matching cases

## Result and scope

The mandatory root neighborhood of an SRG(99,14,1,2) gives an
unrestricted 15-vertex core: one root and its 14 neighbors, whose
induced graph is seven disjoint edges. After fixing one near vertex,
the possible matching on its 12 outside neighbors has exactly eleven
orbits under the remaining signed permutation group `C_2 wr S_6`.

The audit independently enumerates all 10,395 perfect matchings,
provides an explicit transport of every matching to its canonical
representative, and separately computes all eleven orbits by a
generator-based graph traversal. Both counts agree with the exact
orbit-size formula. No SAT model is built or solved here.

This establishes coverage of the eleven matching cases. It does not
establish that any case has or lacks a graph completion. No grid,
graph automorphism, or additional local configuration is assumed.

## Why the root core and the 84 outside signatures are mandatory

Choose any vertex `v`. Every vertex in `N(v)` has exactly one
neighbor within `N(v)`, because each edge has exactly one common
neighbor. Therefore `N(v)` induces `7K_2`.

Label the near vertices `0,...,13`, with mate involution `i -> i^1`.
The root has no neighbors among the remaining 84 vertices. Every
outside vertex has exactly two near neighbors, since it and the root
are nonadjacent and have two common neighbors.

Its two labels cannot be mates: a near mate-pair already has the
root as its unique common neighbor. Conversely, two non-mate near
vertices already share the root and require exactly one additional
common neighbor. No other near vertex can supply it, because the
near induced graph is a matching. Thus there is exactly one outside
vertex for each unordered non-mate pair of labels. There are

\[
\binom{14}{2}-7=84
\]

such pairs. This derives the entire core-to-outside incidence without
choosing a special root.

Fix near label 0. Its twelve outside neighbors have signatures
`{0,j}` for `j=2,...,13`. Its other two neighbors are the root and
near label 1, which are adjacent. Since the full neighborhood of
near 0 is again seven disjoint edges, those twelve outside neighbors
must induce a perfect matching `P`.

Use local labels `0,...,11` for the twelve outside vertices, where
local label `i` denotes signature `{0,i+2}`. The remaining six near
mate-pairs induce a fixed reference pairing

\[
M=\{\{0,1\},\{2,3\},\ldots,\{10,11\}\}.
\]

`M` is a reference pairing of labels; it is not an additional
adjacency assumption on these outside vertices.

## The group and the complete invariant

Any permutation of the six remaining near mate-pairs, followed by
independent swaps of their endpoints, preserves the root core and
its full outside-incidence description. It fixes near labels 0 and
1. The resulting group on the twelve local labels is

\[
W=C_2\wr S_6,\qquad |W|=2^6\cdot6!=46,080.
\]

Using this action to choose a labeled representative does not assert
that a completed graph has a nontrivial automorphism.

The union of `M` and any perfect matching `P`, with their edges
distinguished by color, splits into alternating cycles. A common
edge of `M` and `P` is regarded as a two-edge component. A component
with `r` reference pairs has `2r` vertices. The component values `r`
therefore form a partition of six.

This partition is invariant under `W`. It is also complete: the
explicit construction below maps every matching with that partition
to the same canonical matching. Hence there are exactly `p(6)=11`
orbits.

## Canonical representatives and explicit transports

Write the partition in nondecreasing order. Allocate consecutive
blocks of reference pairs to its parts. For a part `r` beginning
with reference-pair index `k`, the canonical matching has edges

\[
\{2(k+j)+1,\ 2(k+(j+1\bmod r))\},
\qquad j=0,\ldots,r-1.
\]

For `r=1`, this is the reference edge itself.

For an input component, choose its least local vertex `u_0` and
define

\[
u_{j+1}=P(M(u_j)),\qquad j=0,\ldots,r-1.
\]

These are one endpoint from each reference pair of the component,
and `u_r=u_0`. Define the transport by

\[
g(u_j)=2(k+j),\qquad g(M(u_j))=2(k+j)+1.
\]

Process components by increasing size, breaking ties by their least
vertex. The resulting `g` is a permutation of the twelve points and
satisfies

\[
g(M(u))=M(g(u)),\qquad gPg^{-1}=P_{\mathrm{canonical}}.
\]

Thus `g` belongs to `W` and maps the input matching **to** its
canonical representative. This direction is explicit in the source
and certificate. The compressed certificate stores all 10,395 such
transports, not merely one example per orbit.

## Orbit sizes

Let a partition have `m_r` parts equal to `r` and let
`c=sum_r m_r` be its number of parts. A component of size `r` has
`2r` automorphisms preserving the two edge colors, including the
`r=1` case. Components of equal size can also be permuted. Thus the
stabilizer has order

\[
\prod_r(2r)^{m_r}m_r!,
\]

and the orbit size is

\[
\boxed{\frac{2^{6-c}\,6!}{\prod_r r^{m_r}m_r!}.}
\]

The independent enumeration and generator traversal give:

| Canonical partition | Orbit size |
| --- | ---: |
| `1+1+1+1+1+1` | 1 |
| `1+1+1+1+2` | 30 |
| `1+1+1+3` | 160 |
| `1+1+2+2` | 180 |
| `1+1+4` | 720 |
| `1+2+3` | 960 |
| `1+5` | 2,304 |
| `2+2+2` | 120 |
| `2+4` | 1,440 |
| `3+3` | 640 |
| `6` | 3,840 |
| Total | 10,395 |

The total also equals `11!!`, the number of perfect matchings on
twelve labeled points.

## Independent computations and certificate representation

The first enumeration repeatedly pairs the least remaining point
with every other remaining point. It checks that all 10,395 partner
vectors are distinct. Each is classified by connected components of
the union with `M`, and its explicit transport is constructed and
verified.

The second computation does not use the alternating-cycle
classification to decide orbit membership. It traverses the action
of eleven generators: the six individual mate swaps and the five
swaps of adjacent reference pairs. These generate `C_2 wr S_6`.
Starting from the eleven canonical matchings, it obtains disjoint
orbits whose union is exactly the first enumeration's set. Each
orbit size agrees with the formula above.

For compact storage, a twelve-entry partner vector or transport
permutation is encoded as `sum_i value[i]*12^i`. Every certificate
record contains the matching code, orbit index, and transport code.
Replay decodes each record, checks the permutation and mate relation,
and applies the transport directly to the matching. The JSON is
compressed with deterministic gzip settings.

## Files and replay

- Source: `experiments/workspace/root_full_caps_matching_audit.py`.
- Certificate: `experiments/logs/moments-and-counts/root-full-caps-matching-audit-certificate.json.gz`.
- Generation and replay logs use the same stem.

Replay requires only the Python standard library:

```sh
python experiments/workspace/root_full_caps_matching_audit.py \
  --certificate experiments/logs/moments-and-counts/root-full-caps-matching-audit-certificate.json.gz
```

Add `--write` to regenerate the certificate. Generation and replay
both enumerate all matchings, recompute all generator orbits, and
check every explicit transport. Neither command builds or solves a
SAT instance.
