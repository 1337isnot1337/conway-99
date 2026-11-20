"""Inventory only: six-root triangle vertex-projector preparation scope."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import time

import triangle_incidence_projector_moments as base
import triangle_projector_six_root_conditioning as products

BINDINGS = {
    "products_source": "3a01408b78323129146d0856fe81231d867461eaee422536bc7e87a8c8a9fdd5",
    "old_preparation": "9fa1e50db6e809de53639ee3382b8803a94df85798898d243258d61c6c137a8b",
    "old_model_raw": "3474f83d65a7fd4ffbc84b124b147f8cafc6ab4b0fcd2ed3ba3c39eed58d1550",
    "old_model_gzip": "45bdb52816da961cb3a64764ee1bdd9238fbf1a3e0b33a2a22ea8a48698ba777",
}
FAMILIES = ["minus", "plus", "scalar", "Q", "minus_schur", "plus_schur"]


def inventory(scope, old_directory):
    started = time.monotonic()
    assert base.digest(Path(products.__file__).read_bytes()) == BINDINGS["products_source"]
    domains = products.load_scope(scope)
    raw = (old_directory / "preparation.json").read_bytes()
    assert base.digest(raw) == BINDINGS["old_preparation"]
    prep = json.loads(raw)
    assert prep["complete_thirty_block_coverage"]
    packed = (old_directory / "model.json.gz").read_bytes()
    assert base.digest(packed) == BINDINGS["old_model_gzip"]
    raw = gzip.decompress(packed)
    assert base.digest(raw) == BINDINGS["old_model_raw"]
    old = json.loads(raw)
    assert old["domains"] == domains
    rows = []
    for domain, block in zip(domains, old["blocks"]):
        rid = domain["root_type"]
        assert rid == block["root_type"]
        assert domain["root_order"] == 6 and domain["core_triangles"]
        assert len(domain["root_rows"]) == 6 and domain["largest_pair_union_order"] == 10
        for c in domain["classes"]:
            assert c["root_intersection_mask"] > 0 and len(c["outside_masks"]) <= 2
            assert base.cap_valid(c["literal_rows"])
        rows.append({
            "root_type": rid, "classes": len(domain["classes"]),
            "lower_entries": domain["lower_entries"],
            "candidate_union_bound": domain["partial_injection_and_free_edge_candidate_bound"],
            "core_triangles": len(domain["core_triangles"]),
            "outside_vertex_profile": dict(Counter(len(c["outside_masks"]) for c in domain["classes"])),
            "stabilizer_profile": dict(Counter(products.stabilizer(c) for c in domain["classes"])),
            "old_Q_nonzero_terms": len(block["terms"]),
            "old_scalar_support_count_from_positive_union_enumeration":
                block["census"]["exact_stabilizer_divisions"],
        })
    by_id = {r["root_type"]: r for r in rows}
    chunks = [
        {"chunk": i, "root_types": ids,
         "classes": sum(by_id[r]["classes"] for r in ids),
         "lower_entries": sum(by_id[r]["lower_entries"] for r in ids),
         "candidate_union_bound": sum(by_id[r]["candidate_union_bound"] for r in ids),
         "old_control_seconds": prep["chunks"][i]["seconds"]}
        for i, ids in enumerate(products.CHUNKS)
    ]
    assert sum(r["classes"] for r in rows) == 2374
    assert sum(r["lower_entries"] for r in rows) == 127647
    assert sum(r["candidate_union_bound"] for r in rows) == 2967175
    assert sum(r["old_scalar_support_count_from_positive_union_enumeration"] for r in rows) == 239743
    return {
        "status": "COMPLETE_POINT_INDEPENDENT_SIX_ROOT_VERTEX_PROJECTOR_INVENTORY",
        "source_sha256": base.digest(Path(__file__).read_bytes()),
        "bindings": BINDINGS, "scope_sha256": products.SCOPE_SHA,
        "scope_source_sha256": products.SCOPE_SOURCE_SHA,
        "roots": rows, "chunks": chunks,
        "root_count": 30, "classes": 2374,
        "only_triangle_containing_roots": True, "all_62_roots_covered": False,
        "all_existing_class_domains_unchanged": True,
        "families": FAMILIES, "prospective_blocks": 180,
        "lower_entries_per_family": 127647, "candidate_union_bound": 2967175,
        "expected_scalar_support": 239743,
        "root_Gram_positive_leading_minor_checks": 360,
        "root_Gram_inverse_identity_entries": 2160,
        "root_to_class_cross_entries": 28488,
        "root_to_class_correction_lower_entries": 255294,
        "core_triangle_rows_in_each_Schur_family": 38,
        "new_information_order": 10,
        "no_existing_separate_scalar_cache_assumed": True,
        "reuse": "Use the exact old domains and product enumerator. Reconstruct every old conditioned-Q coefficient from the new Q and N tensors.",
        "builder_changes": [
            "Root size five becomes six; use only the thirty old triangle-containing domains.",
            "Retain all one or two core triangles and every old class without zero-point pruning.",
            "Use the frozen six-root overlap enumerator and its five fixed chunks.",
            "Construct Kminus, Kplus, N and unconditioned Q in one pass over each old union domain.",
            "Check the coefficientwise projector partition and all thirty old conditioned-Q tensors.",
            "Check each six-root vertex Gram before inversion, then form both per-embedding Schur tensors.",
            "Retain all root/chunk checkpoints and direct ordered-pair host controls through order ten.",
        ],
        "proposed_limits": {"overall_seconds": 180, "per_chunk_seconds": 60, "workers": 1},
        "estimated_raw_model_bytes": [18000000, 28000000],
        "estimated_compressed_model_bytes": [4000000, 7000000],
        "estimates_are_not_measured_outcomes": True,
        "tensor_generation_performed": False, "count_point_loaded": False,
        "optimizer_called": False, "seconds": time.monotonic() - started,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--old-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = inventory(args.scope, args.old_directory)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("roots", "builder_changes")}, indent=2))


if __name__ == "__main__":
    main()

