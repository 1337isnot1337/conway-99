# Five-variable Boolean extensions from order-ten counts

This package prepares a necessary count test. It has not scanned a graph count
point. It constructs no new flag products and uses no order-eleven catalogue.

The domain contains all 4,543,737 five-subsets of allowed high-mask classes at
all 62 six-vertex roots. The fifth joint moment is absent from the current
catalogue. Eliminating that single unknown produces exact inequalities using
only moments through degree four.

## The extension interval

Fix a labelled embedding of a six-vertex root. A mask with at least three root
neighbors has at most one outside vertex: two such vertices would have at
least three common neighbors. Its class count is therefore a Boolean
variable. Select five distinct allowed masks and call their indicators
\(X_0,\ldots,X_4\).

For \(T\subseteq\{0,\ldots,4\}\), write

\[
m_T=\sum_{\text{labelled root embeddings}}\prod_{i\in T}X_i.
\]

These are unnormalized moments. In particular, \(m_\varnothing\) is the number
of labelled root embeddings. The existing six-root, two-free-vertex tensor
contains every \(m_T\) with \(|T|\le4\).

Let \(S\) be the set of variables that equal one in a complete five-variable
assignment. Its atom count is

\[
a_S=\sum_{T\supseteq S}(-1)^{|T|-|S|}m_T
   =b_S+(-1)^{5-|S|}x,
\qquad x=m_{\{0,\ldots,4\}},
\]

where \(b_S\) omits the term with \(T=\{0,\ldots,4\}\). Thus all 32 atom
counts are nonnegative exactly when

\[
L:=\max_{|S|\text{ odd}}(-b_S)
\ \le\
U:=\min_{|S|\text{ even}}b_S.
\]

The sign depends on the number of **present** variables. Odd present
cardinality gives a lower bound; even present cardinality gives an upper
bound. The all-present atom is \(x\), so \(L\ge0\).

This condition is sufficient for a nonnegative distribution on these five
variables with the prescribed lower moments. Choose any \(x\in[L,U]\) and
use the 32 values \(a_S\) as masses. Möbius inversion recovers all prescribed
moments and the masses sum to \(m_\varnothing\). If the known moments are
integers, \(L\) and \(U\) are integers. A nonempty real interval therefore
also contains an integer fifth moment. This does not construct a joint
distribution across different five-subsets or a graph.

## Exact cuts when the interval is empty

Suppose an odd state \(S\) attains \(L\), an even state \(T\) attains \(U\),
and \(L>U\). The sum of the two exact-assignment indicators is nonnegative
on every Boolean assignment, but its candidate expectation is

\[
a_S+a_T=b_S+b_T=U-L<0.
\]

The degree-five terms cancel. The cancellation is performed before graph
form conversion; no unavailable order-eleven coefficient is used. The
remaining squarefree polynomial has degree at most four, coefficients in
\(\{-1,0,1\}\), and at most 31 nonzero monomials. Consequently it is a
necessary linear inequality on induced graph counts through order ten.

There are 256 pairs of opposite-parity states. Their classification is:

| Hamming distance | Pairs per five-subset | Relation to the previous atom test |
|---|---:|---|
| 1 | 80 | Sum over one free Boolean variable; an existing four-variable atom |
| 3 | 160 | Additional five-variable extension inequality |
| 5 | 16 | Additional five-variable extension inequality |

The code checks every pair polynomial on all 32 literal Boolean assignments.
It also checks that every distance-one polynomial is independent of the
coordinate in which its two states differ.

Two synthetic moment systems show that the extension family can add
information beyond nonnegative four-variable atoms alone. Assign signed
mass \(+1\) to every five-bit state, then change states \(0\) and \(7\) to
mass \(-1\). Alternatively, change states \(0\) and \(31\) to mass \(-1\).
The negative states have Hamming distance three or five. Every four-variable
atom is a sum over two adjacent cube states, so its mass is zero or two.
All four-variable marginals are nonnegative. The sum of the two negative
full atoms is \(-2\), however, and the five-variable extension interval is
empty by exactly two. These examples are Boolean moment controls, not SRG
count vectors. They do not establish independence from every other graph
constraint in the repository.

## Catalogue normalization and complete coverage

The preparation binds the frozen four-Boolean domain ledger and the full
six-root/two-free cache index. For each of the 62 roots it independently
checks the allowed high masks using visible pair caps. It checks both
possible mutual-edge values for every pair of high masks against the saved
pair-flag domain.

For distinct high masks, the sum of the allowed edge and nonedge pair flags
equals the product of the two class indicators. A degree-three monomial is
represented by a pair flag times a single flag. A degree-four monomial is
represented by the product of two pair flags. The masks are distinct, so
their unique outside vertices fix the free labels. No free-label
automorphism divisor is introduced. The existing labelled tensor entries
retain their original normalization.

Every saved product-row reference through degree four is recomputed and
hashed against the old ledger. The preparation does not reload the product
tensors. Sparse coefficient-read counts are explicitly inherited from that
frozen ledger. A future exact induced-count form multiplies each labelled
embedding coefficient by the corresponding graph automorphism order.

All roots and all high masks remain in the domain. There is no zero-count
or point-dependent pruning. Forty-eight roots have at least five high
masks; the other fourteen have no five-subset and remain in the ledger.
Each of the 4,543,737 five-subsets is explicitly enumerated in lexicographic
mask order and included in a per-root streaming hash.

The dense lookup arrays use colexicographic ranks

\[
\operatorname{rank}(i_0<\cdots<i_{k-1})
=\sum_{j=0}^{k-1}\binom{i_j}{j+1}.
\]

For every root and each degree zero through four, the preparation checks
that the ranks cover exactly \(0,\ldots,\binom hk-1\), without duplicates.
The domain contains 774,546 known monomial slots, 327,655 cached product-row
references, and 229,779 inherited sparse coefficient reads. The largest
root has 42 high masks, 124,314 monomial slots, and 850,668 five-subsets.

## Batched arithmetic and workload

A future scan needs no array of the 1,163,196,672 opposing-atom constraints.
For each batch of at most 50,000 five-subsets, it gathers 31 known moments,
sets the top-moment slot to zero, performs the five-bit upper Möbius
transform, and compares the two interval endpoints.

Across the complete domain this means 140,855,847 proper-moment lookups,
145,399,584 affine atom constants, and 363,498,960 integer subtractions.
There are 132 nonempty batches when each root is processed separately.
The distance-three and distance-five pairs account for 799,697,712 implicit
additional inequalities.

The primary per-batch int64 buffers are 12.8 MB for the known moments,
12.8 MB for the transformed constants, and 2 MB for the five indices.
The largest per-root dense moment arrays occupy 994,512 bytes. These figures
exclude NumPy temporaries, Python tuples, and the frozen cache load. The
preparation itself used 132,600 KiB peak RSS and completed in 5.83 seconds.
It loaded the small catalogue, not the product cache or count point.

Tensor contraction must first pass the existing positive-coefficient and
used-column integer bounds. Let \(A\) be the maximum exact cached product
entry. A proper moment is a sum of at most four entries, so its maximum
\(M\) satisfies \(M\le4A\). Each transform intermediate has absolute value
at most \(32M\), an interval gap at most \(64M\), and an atom-row sum has
absolute partial sums at most \(1024M\). The vectorized helper requires

\[
1024M\le2^{63}-1
\]

using Python integer arithmetic before any subtraction. This guard also
protects the row-sum identity and sign reversal. Failure of an arithmetic
bound must stop the future scan; it is not evidence of infeasibility.
Zero root count does not authorize skipping any interval unless all of
its required expressions are separately verified.

## Controls and reproduction

The frozen preparation checks:

- All 256 opposing-parity polynomials on all 32 assignments: 8,192 literal
  polynomial evaluations.
- 567 nonnegative integer distributions, including every pure atom at
  weights one and three, every two-atom support, zero, uniform, parity,
  and nonuniform examples.
- Exact reconstruction from both endpoints of every tested feasible
  interval. Uniform even- and odd-parity distributions have identical
  lower moments and interval \([0,1]\); their weight-three versions have
  interval \([0,3]\).
- The two strict examples described above, including all 80 four-variable
  atoms in each example.
- 84 synthetic colex-gather and batched-transform cases, checked against
  direct inclusion-exclusion with Python integers.

Source:
`experiments/workspace/grid_free_order10_five_boolean_extension_domains.py`

Certificate:
`experiments/logs/moments-and-counts/order10-five-boolean-extension-domains.json.gz`

The source exposes preparation and cold replay only. An unused output path
is required. To replay the complete domain and controls:

```bash
.venv/bin/python experiments/workspace/grid_free_order10_five_boolean_extension_domains.py \
  --replay experiments/logs/moments-and-counts/order10-five-boolean-extension-domains.json.gz \
  --output /tmp/order10-five-boolean-extension-replay.json \
  --seconds 60
```

Any future negative direction must save its two states, exact interval,
signed proper monomials, cached references, and induced-count form. A fresh
literal product reconstruction must pass before optimizer use. This
preparation claims no result about the current count witness or the
existence of a Conway 99 graph.
