# Triangle-incidence append: source preparation

The prepared producer retains all 80,730 variables and all 297,470 rows of the accepted combined model. It appends 3,325 linear rows with 26,916 terms. The resulting model would have 300,795 rows and 3,337,296 terms. No native model has been built from this source.

The append has three families in this order:

| Family | Rows | Terms | First native row |
| --- | ---: | ---: | ---: |
| Side-edge capacities | 2,904 | 10,320 | 297,470 |
| Local-selector capacities | 420 | 16,512 | 300,374 |
| Global target total | 1 | 84 | 300,794 |

## Necessary inequalities

The accepted parent already defines 5,364 Boolean triangle indicators as the exact AND of their three original edge variables. It also has 84 target equalities. Original edge variables retain index 540 + edge_id; triangle indicators retain index 71,382 + triangle_index.

For a non-target edge e that occurs in at least two recorded triangles, the new row is

\[
\sum_{T\ni e}\tau_T\le y_e.
\]

An adjacent pair in the intended graph has exactly one common neighbor. Thus an active edge belongs to at most one actual triangle. The 84 existing target equalities and the existing AND upper bounds for 3,312 singleton side edges already cover the other two cases in the complete 6,300-edge incidence list.

For each of the 420 selectors a with nonempty recorded incidence, let k0(a) be the number of fixed-component edges inside its three-site signature. Here k0 is zero or one. The local row is

\[
\sum_{T\ni a}\tau_T\le(2+k0(a))x_a.
\]

The original mixed rows give overlap-one degree (3-2k0)x_a. Subtracting from exterior degree 8x_a gives overlap-zero degree (5+2k0)x_a. Summing the edge capacities around a counts every recorded triangle twice. For Boolean x_a and integral indicators, rounding 2T_a <= (5+2k0)x_a gives the stated row. Empty local incidences are recorded explicitly and contribute only tautologies.

The final row is

\[
0\le\sum_{e\in E_{\mathrm{target}}}y_e\le12,
\]

over all 84 target edges. Its separate accepted structural certificate uses twelve original quota-one Gram rows. The selected private target graph decomposes into stars, edges, and singletons; each such component has at most one shared attachment edge. Each component therefore contributes at most its number of private vertices to the target-edge total. The twelve private color quotas bound that number by twelve. The producer binds the accepted proof and complete certificate, reconstructs the target row, and checks the twelve private Gram messages in the parent. The independent native checker reconstructs all structural conditions again.

These are necessary graph constraints. The certificate's attaining witness concerns only the restricted color/activation relaxation. It is not a feasible witness for the full parent model, and no full-model nonredundancy claim is made.

## Exact input and output contract

The parent is the root-accepted raw model with SHA256
2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6
and 39,306,083 bytes.

The producer reads 23 exact input artifacts and six bound sources. The configuration contract contains every descriptor, all successful status authorities, and 60 explicit cross-reference links. Root owns the actual native configuration and execution gates.

The earlier capacity extractor completed its table but exceeded its finalization bound: 12,196 ms against 10,000 ms, with outer elapsed 17,209 ms. Its report, finalization, owner, and digest descriptor remain unaccepted proposal data. The new producer requires the separate accepted literal replay and its 30,000/45,000 ms receipts. It reconstructs the rows before comparing the proposal table. It does not waive or retry the failed extraction.

The first two families retain all seven accepted literal digests, including complete incidence/origin projections and the 60 empty local selectors. The new global row has its own exact single-key digest. Full append and per-family digests are separately recorded.

All new constraints are unnamed, linear-only ConstraintProto messages with sorted unique terms and no enforcement or other metadata. The entire parent raw byte string is retained as the exact prefix. A separate constraint-only suffix reconstructs the full output by concatenation. Removing the suffix constraints must recover the original parent bytes. Every old variable and constraint message is compared in full.

The lossless artifacts are model.pb, model.pb.gz, suffix.pb.gz, append-rows.json.gz, and restoration-manifest.json. The row ledger contains all complete keys and origins. The independent checker compares complete canonical ledger and manifest bytes, rather than accepting selected fields alone.

## Prepared execution limits and current status

The producer exposes only controls and prepare. Its established supervisor owns a ten-second control worker under a fifteen-second owner, and a 120-second native preparation worker under a 135-second owner. Preparation constructs and validates one CpModel through the pinned public transport. It never constructs CpSolver or runs an optimizer.

The separate checker uses ten-second controls and a 120-second replay under external fifteen- and 135-second owners. It imports protobuf definitions only, reconstructs the rows independently, verifies all old and new messages, and checks the entire raw-prefix restoration. Future model use requires both successful owners and a separate root acceptance.

Seventeen inherited functions are text-identical to the accepted combined producer. The owned supervisor wrapper has only three namespace substitutions. The remaining append, receipt, and control functions are new and are listed in the exact source-reuse record.

Source preparation and interface comparisons are complete. Python import, syntax compilation, toy controls, actual model decoding, native construction, and solver execution remain unrun for this new producer and checker. The source package does not authorize a build or query.
