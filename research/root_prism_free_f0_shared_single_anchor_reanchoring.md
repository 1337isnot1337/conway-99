# Reanchoring the fresh single-anchor shared certificates

## Result and scope

The sixteen cold-accepted shared certificates from direct-master runs 01 and 02 contain ten certificates with exactly one nonzero anchor potential. Their core transports give 114 distinct primitive integer site potentials. The complete 114 by 480 census gives 12,204 positive-demand pairs and 12,204 distinct necessary selector rows. Exactly 36 rows already occur in the planned 301-row prefix. The remaining 12,168 rows are new by exact normalized row equality.

The planned prefix consists of the 253 accepted run 02 rows and 48 independently replayed packing reanchorings. Every one of those 301 rows is retained. All 4,416 original literal rows also remain in the base model.

After exact Boolean coefficient capping, none of the 12,168 new rows is removed by the sufficient coordinatewise dominance criterion, either against the 4,248 usable single-anchor authoritative rows or against another new row. The full additional family has 53–210 terms per row, maximum absolute coefficient 58, maximum coefficient bit length 6, and maximum absolute activity 1,672. Seven new rows violate at least one of the sixteen accepted candidates. This is a finite family of necessary inequalities, not a graph construction or a component exclusion.

The complete new registry would contain 12,469 additional rows:253+48+12,168. Its next native query requires a new explicit registry cap and a fresh source/configuration gate. No master controller or native model was changed by this census.

## Local inequality

Let h_b be the three-element site incidence vector of signature b. For a selected anchor a, let q_a be its required site-neighbor count vector. Every permitted exterior neighbor b lies in the reconstructed full domain N(a). For a genuine completion, exterior edge indicators z_ab satisfy

    sum_b h_b z_ab = q_a,    0 <= z_ab <= x_b.

Consequently every integer site vector w gives the necessary inequality

    (w dot q_a) x_a <= sum_{b in N(a)} max(w dot h_b, 0) x_b

when its demand w dot q_a is positive. The inequality is automatic when x_a=0. When x_a=1, multiply the mixed equations by w, omit negative edge contributions, and use z_ab<=x_b. No automorphism is needed to reuse w at a different anchor. All 480 domains and targets are reconstructed from the frozen 21-vertex core before enumeration.

The shared separator has one degree row followed by 18 mixed rows per selected anchor, with degree RHS 8. Its saved effective site vector is already

    w_i = -ray_degree - 3 ray_mixed_i.

Writing delta=-ray_degree and v_i=-ray_mixed_i gives w=3v+delta*1. Each signature has weight 3 and each q_a sums to 24, so this absorbs the degree potential and multiplies the original local weight and demand by 3. The producer verifies this conversion against the saved integer rays; it does not apply the conversion twice. It also verifies the complete internal edge order, exact weighted demand, positive capacity and strict gap for all sixteen source certificates.

Each single-anchor vector is divided by its positive coefficient gcd. The twelve actual core automorphisms are checked on the core, signatures and targets. Their transported vectors are deduplicated before the 114 by 480 census. All 54,720 attempts, including 42,516 nonpositive demands, are preserved.

## Capping and the reduction criterion

A local row has the form t*x_a <= sum_b w_b*x_b with t>0 and w_b>=0. For Boolean selectors, replacing each weight by min(w_b,t) gives an equivalent constraint. Divide the resulting row by its positive coefficient gcd.

For two capped rows A and B at the same anchor, A implies B whenever

    w_A(b)*t_B <= w_B(b)*t_A

for every coordinate b, with missing weights treated as zero. This is a sufficient criterion. The retained family is not asserted to be minimal under all Boolean implications. For example, some implications require reasoning about several coordinates together and are not detected by this test.

The baseline contains all 4,416 literal rows plus the planned 301 rows. Of these,4,248 have the required one-positive-coefficient sign form and zero RHS. The remaining 469 rows are preserved but are not used by this particular comparison. Every fresh raw row has a direct coverage witness to a retained or authoritative capped row. In this result all 12,168 witnesses point to the retained row's own capped key: there are no dominance deletions.

## Execution record

The initial producer is `experiments/workspace/root_prism_free_f0_shared_single_anchor_reanchoring.py`, SHA-256 `878e7058cd6aab4761adf56e2ca90e0cbc199d463a1824d26da0171632793676`. Its configuration is `experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring-configuration01.json`, SHA-256 `42b6a6651435adbfb81d33819917f870df2d69f7205878d01899ea9a2ef8ba53`.

The first attempt saved the complete bank and raw census, then its 65-second outer timeout ended it during reduction. It produced no accepted terminal report. The original source, partial directory, stdout and stderr are preserved. The resume ledger records that outcome explicitly.

The separate exact reduction wrapper is `experiments/workspace/root_prism_free_f0_shared_single_anchor_reduction.py`, SHA-256 `b25311bbc83bd81015b25f0063596ee7d2259f99732ec0498489ffd48464c441`. It reads the saved artifacts by hash and does not repeat enumeration. It leaves the original helper source unchanged and uses an equivalent local predicate with cached immutable weight dictionaries and an early support-inclusion rejection. The 120-second internal/125-second outer bound is explicit. It completed in 49.467252 seconds with exit 0.

The generic helper is `experiments/workspace/root_prism_free_f0_local_row_dominance.py`, SHA-256 `d91591788e7f97742736df8bb6cdafaddb46939668054fb7450e351a2d276566`. Its separate source review and finite Boolean controls are recorded in `f0-local-row-dominance-independent-review01.json`. The caller enforces exact integers or canonical decimal strings before using the helper.

No optimizer, native model, or historical 3,948-potential bank was used. The separate independent replay passed in 44.725852 seconds. It reconstructs the complete fresh bank, all 54,720 attempts,12,204 rows and 12,168 direct coverage witnesses without importing these producers or the dominance helper. It also binds the 253-row prefix to the accepted run 02 cold registry. Its source SHA-256 is `76df109a6d68bb16b7ddf90f9de3dd9240ec3699f363c88fa58f0965b3070629`; its full report SHA-256 is `4d5b7a4a10bc1deed16509b0ed2dfbcc2d4794178054846a4c3f5768f967f05f`.

The compact certified export is `experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring02/certified-selector-cuts.json.gz`, SHA-256 `26e0883d145b13593b2a005b1b5bc6fc86fe423bf3dd18452561e64f803efcde`. It contains every final row in exactly the independently checked order, with parallel raw-row-key provenance. The source `root_prism_free_f0_shared_single_anchor_export.py`, SHA-256 `b79cb59d0bc4e57129d425a0d1d1d1fd058f80c3eb4d27bd99a43181f1eb0b52`, verifies exact equality to the accepted cold report before writing it. Export removed no rows.

The large dominance and original export JSON records are preserved as lossless xz archives. The independent cold report is preserved as a lossless gzip archive. `publication-restoration-checks.json` records exact original-byte reconstruction, including deterministic gzip recompression for the originally compressed dominance record. No JSON reserialization is used to restore an acceptance input.
