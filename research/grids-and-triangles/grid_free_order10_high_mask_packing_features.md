# Complete empty-root packing moment matrix

The preparation stores a complete finite moment model for the empty
six-vertex root. Its supported matrix has **17,903 rows, 90,776 columns, and
4,463,060 entries equal to one**. No optimizer has been called, so no
feasibility or infeasibility conclusion is made.

## Variables and exact normalization

Let \(\Omega\) be the complete structurally allowed packing domain in
[the domain note](grid_free_order10_high_mask_packing_domains.md).
There are 42 high neighborhood classes. An atom \(S\in\Omega\) specifies
which of their Boolean indicators are one.

For every subset \(T\) of classes of size at most four, define

\[
m_T=\sum_{\phi:H\hookrightarrow G}
       \prod_{h\in T}X_h(\phi).
\]

The sum runs over labelled induced embeddings of the empty six-root.
The proposed finite model has one nonnegative weight \(w_S\) per atom and
the equations

\[
\sum_{S\in\Omega:\,T\subseteq S}w_S=m_T.
\]

The constant row is \(T=\varnothing\). It fixes the total weight to the
labelled root count. No individual weight upper bound is required.
Actual graph embeddings give integer weights; a real nonnegative solution
would certify only this finite moment extension.

The moments use the frozen complete six-root/two-free tensors. A singleton
class is its one-free flag. A product of two distinct high classes is the
sum of its allowed mutual-edge and mutual-nonedge flags. Three- and
four-class products use the corresponding cached flag products.
Distinct masks fix the free labels, so no additional free-label divisor
occurs. A cached catalogue term is evaluated as

\[
|\operatorname{Aut}(F)|\times
       \#\{\text{unlabelled induced copies of }F\}.
\]

The complete product-reference digest is checked against the frozen
four-Boolean domain ledger. All moments and their individual cached row
references are saved.

## Matrix coverage

The baseline retains all 132,062 pair-capacity atoms, before the additional
outside-pair intersection filter. Rows are grouped by degree and then by
combinatorial colex rank. Their counts are

\[
1,\quad42,\quad861,\quad11{,}480,\quad111{,}930.
\]

Every column contains exactly its monomials of degree at most four.
The preparation checks containment for every stored entry, strict row
ordering within every column, and the exact required column cardinality.
These checks establish complete coverage without an unchecked row
selection. Separate literal controls cover all 511 Boolean columns on
zero through eight classes.

| Stage | Rows | Columns | Entries equal to one |
|---|---:|---:|---:|
| Complete pair-capacity baseline | 124,314 | 132,062 | 5,804,664 |
| Outside-pair intersection filter | 124,314 | 90,776 | 4,463,060 |
| Remove unsupported rows | 17,903 | 90,776 | 4,463,060 |

The saved CSC matrix stores int32 row indices and column pointers, with an
implicit coefficient one at each entry. The baseline is preserved even
though the subsequent model can use the smaller structural domain.

## Bound count point and zero rows

The point is the frozen 48-cut prism-zero, \(x_{521}=0\) integer count witness,
SHA256
0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.
The labelled empty-root mass is 72,926,995,680.

Exactly 106,411 monomial moments are zero. They coincide with the rows
unsupported by every structurally allowed atom. Consequently, filtering
atoms by these zero moments removes exactly the same 41,286 baseline atoms
already rejected by the outside-pair intersection condition. It removes
**no additional structurally allowed column**.

Every zero-based removal has a saved monomial witness. Every remaining
positive moment has at least one supporting column. This finds no immediate
support contradiction.

The source treats zero filtering as a fixed-point operation. A later
certificate must be checked on the complete structural domain. Here the
zero rows are identically unsupported on that domain, so their removal
does not narrow it. The separate exact certificate helper can perform
full-domain constant-shift repair or zero-feature penalty recovery when
needed. Any graph-count cut still needs fresh literal product replay.

## Arithmetic and saved scope

Tensor contractions use int64 only after Python-integer bounds establish
safety. The largest coefficient row sum is 15; the contraction bound is
1,093,904,935,200. Zero-feature counts use int64 rather than uint8.
All matrix indices and pointers are below \(2^{31}\).

Preparation completed in 7.64 seconds, with peak RSS 298,200 KiB. It loaded
the small catalogue and only the seven-root cache part containing root 38.
It loaded no reduced count matrix and generated no product tensors.

The completed source is
experiments/workspace/grid_free_order10_high_mask_packing_features_v2.py,
SHA256
8e0ceb67d345456058ae2adac42326214f9386914bfb08b8df90f223a7c9cb04.
The result is
experiments/logs/moments-and-counts/order10-high-mask-packing-features02.json,
SHA256
d4df7b082b71cc25b2f2b4710c034e43a75bafeaa4d4cf4e913422bf3787fe0f.
It binds the matrix, moment, and filter NPZ files.

The first source and features01 result are preserved. That invocation
stopped at the certificate-helper hash gate before loading matrix or tensor
data. Version two changes only the recorded helper hash following its
control-report bit-count correction. The helper is not called by this
preparation. All matrix and filter logic is unchanged.
