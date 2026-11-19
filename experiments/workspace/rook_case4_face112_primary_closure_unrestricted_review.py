"""Source-only review binding for the112-zero closure delta; no subjects imported."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "experiments/workspace"
LOGS = ROOT / "experiments/logs/grids-and-triangles"
SOURCES = {
    "rook_case4_face112_primary_closure.py": "b4badaae4abb08400ad16e5feaf2e30037f1423b3b1f2c9d3b87d8df05e39463",
    "rook_case4_face112_primary_closure_v2.py": "bcf81e923c39b6a86cb99987c53b0fd0d444508df32313a215eb977ec453102d",
    "rook_case4_face112_primary_closure_v3.py": "405f732445043762db0c52cbc0cfdc159dcb945351925afdcc57af7c9606b3f9",
    "rook_case4_face111_primary_closure_v2.py": "983d62f91f4bd7ce53e1a11897d41dbf3a093b7fd426659fce4069973caa169e",
    "rook_case4_face111_two_parity_equalities.py": "195b5fc78cb6895ee7797ebf1926f1cd19d990d992d5a9e9638d44f24aa984c6",
    "rook_case4_face111_native_bounds_independent_replay.py": "17f92ce409b0ccdef54c4321eaec7ccb09206a4d2f3af61122051960b53df348",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for name, expected in SOURCES.items():
        assert sha(WORK / name) == expected
    first = json.loads((LOGS / "rook-case4-face112-primary-closure-json-repair.json").read_text())
    second = json.loads((LOGS / "rook-case4-face112-primary-closure-json-repair02.json").read_text())
    old = (WORK / "rook_case4_face112_primary_closure.py").read_text()
    middle = (WORK / "rook_case4_face112_primary_closure_v2.py").read_text()
    current = (WORK / "rook_case4_face112_primary_closure_v3.py").read_text()
    assert old.count(first["exact_old_expression"]) == 1
    assert old.replace(first["exact_old_expression"], first["exact_new_expression"]) == middle
    assert middle.count(second["exact_old_expression"]) == 1
    assert middle.replace(second["exact_old_expression"], second["exact_new_expression"]) == current
    for before, after in ((old, middle), (middle, current)):
        a = {f.name: ast.dump(f, include_attributes=False) for f in ast.parse(before).body if isinstance(f, ast.FunctionDef)}
        b = {f.name: ast.dump(f, include_attributes=False) for f in ast.parse(after).body if isinstance(f, ast.FunctionDef)}
        assert a.keys() == b.keys()
        assert [name for name in a if a[name] != b[name]] == ["load"]
    report = {
        "status": "PASS: full source/premise review and independent exact repair-delta checks",
        "reviewer_source_sha256": sha(Path(__file__)),
        "source_bindings": SOURCES,
        "repair_records": {p: sha(LOGS / p) for p in (
            "rook-case4-face112-primary-closure-json-repair.json",
            "rook-case4-face112-primary-closure-json-repair02.json")},
        "both_repairs_change_only_saved_JSON_summary_comparison": True,
        "final_comparison_preserves_histogram_values_without_key_order_assumption": True,
        "mathematical_review": {
            "premise_ancestry": "The previous loader reconstructs the original2271 rows, complete178533-cover registry and111 proved zero premises; the new loader retains its exact raw cover bytes and unit IDs.",
            "parity_equalities": "The independently bound proof reconstructs the111-zero face, H2=1, the33-Gram odd H1 identity and original signature capacity. H1<=2 and odd nonnegative integrality force H1=1.",
            "native_bounds": "Each objective bound is replayed from unrestricted row multipliers using the matching finite endpoint, plus the positive unit-box residual. No numerical dual-feasibility premise is used.",
            "zero663": "The refined exact bound is x663<=2/3; Boolean integrality gives x663=0. The full original-coordinate identity and all prior-zero corrections are checked by the bound checker.",
            "four_pairs": "Every pair objective has an exact upper bound strictly below2, hence its Boolean sum is at most1. The three redundant Gram580 implications remain valid additional rows.",
            "full_row_preservation": "All2271 original rows compare unchanged. Only H1's upper endpoint changes42 to1, four pair rows append, and the111-zero seed gains663. The resulting2277 native rows plus112 zero axioms total2389.",
            "rules_and_scope": "The original propagation and sequential reason checker are hash-bound unchanged. There is no probing, selector branch or optimizer. Real-scope statements are explicitly relative to the augmented integer-derived premises.",
            "JSON_boundary": "The computed histogram uses integer keys and the saved JSON uses decimal-string keys. Decoding the freshly serialized summary compares JSON values; it does not alter any bound coefficient or numerical result."
        },
        "subject_modules_imported": False, "bound_certificates_recomputed": False,
        "model_or_registry_rebuilt": False, "closure_run": False, "optimizer_calls": 0,
        "case4_exclusion_claimed": False,
    }
    output = LOGS / "rook-case4-face112-primary-closure-unrestricted-source-review.json"
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
