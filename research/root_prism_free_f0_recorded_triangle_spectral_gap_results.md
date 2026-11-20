# Recorded triangle spectral-gap test: 3,156 rejected triples

One gated exact call tested all 5,364 recorded exterior triangles against
the spectral-gap matrix. It rejected 3,156 through a negative three-by-three
determinant while every proper principal minor was nonnegative. The other
2,208 passed all seven principal-minor tests. None of the passing matrices
had zero determinant.

The complete separate independent literal replay now passes and is
[root accepted](../experiments/logs/root-prism-free/f0-recorded-triangle-spectral-gap-literal-root-acceptance01.json).
It confirms every record, all 37,548 minors, all origins and both row-key
families. The rows are certified for the next native append; the actual
new native preparation and complete protobuf replay remain separate.

| Recorded outcome | Triangles |
| --- | ---: |
| Negative diagonal | 0 |
| Negative pair minor, with no negative diagonal | 0 |
| Negative determinant, all proper minors nonnegative | 3,156 |
| All seven principal minors nonnegative | 2,208 |
| Total | 5,364 |

The complete report retains all 37,548 tested minors, all six independent
entries per matrix, each original triangle and edge ID, its unique target
origin and native indicator variable. It includes every rejected zero-row
and triangle-cover proposal in exact triangle-index order.

## One exact rejected triangle

The first record has vertices 0,91,325 and original edge IDs
16,170,25269. Its indicator is native variable 71382. The matrix is
\[
\begin{pmatrix}
1174&-392&-256\\
-392&1174&-1066\\
-256&-1066&1306
\end{pmatrix}.
\]
Its pair minors are 1,224,612; 1,467,708; and 396,888. Its determinant
is -25,628,400. These values are quoted from the saved exact report.

The accepted spectral-gap theorem requires this block to be positive
semidefinite in an actual completion. For a triangle, lambda=1 forces
the residual second-incidence Gram block to be 3I, so the block above is
completely determined by the accepted first-component kernel and fiber
profiles. No choice of second component can change this calculation.

The record therefore proposes t_0=0, or the equivalent Boolean edge
cover y_16+y_170+y_25269<=2. Here the y subscripts are original edge IDs,
so their native indices are 556,710,25809.

For later model use, one zero row per rejected existing indicator is
sufficient. The accepted AND lower row
t-y_ab-y_ac-y_bc>=-2 then already implies the corresponding edge cover
continuously. There is no need to add both representations merely to
obtain that cover.

## Effect on the recorded supports

A projection of the completed report groups the original records by
their already bound target-edge origins. Each of the 84 targets retains
between two and 39 compatible recorded triangles. None loses every
recorded support. Thus these results alone do not yield an immediate
target-edge zero through support exhaustion.

This projection performs no new matrix arithmetic. It preserves all
84 target counts and one rejected and one compatible example, bound
to the full report's exact hash. Compatibility here means only that
the seven tested minors are nonnegative. It does not establish that
a triangle extends to a graph or satisfies every native constraint.

The scope is only the recorded 5,364 triangles in the fixed F0,
globally prism-free/F-free split18+18 branch. No complete eligible-triple
census, other-component classification, graph construction or component
exclusion is claimed. A rejected triangle may also be excluded by other
existing constraints; no full-model independence claim is made.

## Execution and preservation

The mandatory controls passed: all seven minors of 729 symmetric
matrices with entries in {-1,0,1} were compared with independent
permutation expansion, followed by six explicit positive, singular,
negative and large-integer examples. There were 5,145 exact oracle
comparisons, including integers above 2^53.

The worker used 12.145 seconds through complete report hashing, within
30 seconds. The outer owner used 12.173 seconds, within 45 seconds.
Both exact returned texts were preserved before publication. There was
one call, no retry, no native import and no optimizer. The V8 owner is
an elapsed receipt; it does not claim OS-process preemption.

The full report is 2,569,247 bytes, below the 8 MiB cap:
experiments/logs/root-prism-free/f0-recorded-triangle-spectral-gap-minors01.json,
Git 2f0d27b2c2bd2d9e61ddcb4c11ae41168a206ee5,
SHA256 31789e7cb6012e8d0f3545170bfa19daec752027b4cd1c7a6bc013749cc146f1.

The exact finalization is
f0-recorded-triangle-spectral-gap-minors01-finalization.json,
Git c0e1c25f5c16bbda5adfa68b96dbdf36f96b6c3d,
SHA256 0a44fae4471eee8cad8b04c7ae63459f375a4b8cc98d26d557f7b1dd01fbc2fb.

The outer owner is
f0-recorded-triangle-spectral-gap-minors01-owner.json,
Git 2b287234122d73a90c93457e8ddb3224b0468d3a,
SHA256 00e16300139b6272e003ebd0f521d98976f8f965e7dbe8a4b67b95357daa0776.

Canonical JSON hashes without a trailing newline are:

- All complete records:
  c23d30fa880e5868e596755231ee61667863455211879a63904a29ed18827181.
- The 3,156 proposed indicator-zero row keys:
  68cbeeb785a7d68e7141464bd3c9c9274bebddcd33875ea4c843494f2da44b4c.
- The 3,156 proposed triangle-cover row keys:
  960262ba78c15d40fd557b340ec0b2d1248a8532eb5fdfdae0e5b7839e897812.

The complete source, method, configuration, independent source review,
root gate, terminal artifacts and this note are listed in
f0-recorded-triangle-spectral-gap-terminal-git-blobs01.json. The earlier
preparation map remains preserved as the historical unrun preparation.


## Separate independent replay

The independent worker visits the accepted triangle list in reverse
order and computes each principal determinant by signed permutation
expansion using BigInt. It reconstructs the saved edge namespace,
fiber profiles, kernel offsets, all target-incidence tables and every
complete original record. Its seven exact controls include values
above 2^53.

The complete replay takes 13.516 seconds through report hashing under
30 seconds. The elapsed owner takes 13.725 seconds under 45 seconds.
The original 24,136-byte report, 457-byte finalization and 3,576-byte
owner are retained. The report SHA256 is
6fbf1ab7cac847439e6e21e7a4df40c070e9a0e89aad5a55267f86da566a1bee.
The sorted failed-index array SHA256 is
cb049b7390dfd13617d01675b0cce593377ba5bebfc6084767a49033f7ad4dbe.

The [native preparation](root_prism_free_f0_triangle_gap_native_preparation.md)
appends only the 3,156 unit-zero indicators after this independent
acceptance. All 84 target edges still have nonempty recorded support;
the replay does not change the scope or turn passing minors into
feasibility certificates.
