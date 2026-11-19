"""Read-only source/AST gate for the complete 112-face LP and its driver.

This imports neither subject, rebuilds no matrix, repeats no numerical or
control query, and records the accompanying complete mathematical source read.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
FILES = {
    "builder": ("experiments/workspace/rook_case4_face112_model.py", "8cfae2fc990e293f47029da2dc5a4d66b864e2547777d6a142de424133361da7"),
    "driver": ("experiments/workspace/rook_case4_face112_cover_generation.py", "e0e245f1cfc20ff4e5eef7f148ee57b7a97af5829094bf57a0ff9247784942bc"),
    "parent_driver": ("experiments/workspace/rook_case4_face99_parity_cover_generation.py", "c7459874bed464e062caee2fe23be9221cfde03ae979a33f8d54e1a305fb07fd"),
    "premise_loader": ("experiments/workspace/rook_case4_face112_primary_closure_v3.py", "405f732445043762db0c52cbc0cfdc159dcb945351925afdcc57af7c9606b3f9"),
    "premise_review": (BASE + "rook-case4-face112-primary-closure-unrestricted-source-review.json", "1719ecbda683e4f0b2aa1d3b6c18ee9db9c0ae79acff1f2618022e60be10ccc4"),
    "model": (BASE + "rook-case4-face112-model01/model.json", "018882c8cea2a8cb9c2fc73a433d40973d20588bc5accb0fb8b0165fddc4337f"),
    "cold": (BASE + "rook-case4-face112-model01-cold-replay.json", "26f063161cbf9c0beb139b392f0b46007254176c522308d3ed2d5e3ee3c2e703"),
    "preparation": (BASE + "rook-case4-face112-generation-preparation.json", "a9ae876612b63682f24fe4141916339be8650fed4d9737a93b9a8991e14ab31e"),
    "preflight": (BASE + "rook-case4-face112-generation-preflight.json", "4c424e42710ddfee32e9d8ca0f46b7cd2e3a47ce30de52a73be7dbbd7d319601"),
    "ledger": (BASE + "rook-case4-face112-generation-substitutions.json", "834d5e2af57ec8963845c6ace76cc3f6d008bb67c0cfa113dd92c7096dbc17b0"),
    "author_reuse_record": (BASE + "rook-case4-face112-generation-reuse-controls.json", "894d56b7bff5ae7e1751368c25a6229cdadbb131a1c2e56d16fe512994d2bf7c"),
}
FRESH = {"source_bindings", "load_inputs", "definition", "cold_arrays", "preflight_replay"}
SCOPE = {"preparation_scope", "certificate_scope", "replay_scope"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(source):
    return {n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}


def assignment(source, name):
    for n in ast.parse(source).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name
                for target in n.targets for t in ast.walk(target)):
            return ast.dump(n.value, include_attributes=False)
    raise AssertionError(name)


def review():
    raw = {}
    for key, (path, expected) in FILES.items():
        raw[key] = (ROOT / path).read_bytes()
        assert sha(raw[key]) == expected, key
    ledger = json.loads(raw["ledger"])
    old, new = raw["parent_driver"].decode(), raw["driver"].decode()
    transformed, scope_only = old, old
    labels = []
    for item in ledger["substitutions"]:
        assert item["occurrences"] == 1 and transformed.count(item["before"]) == 1
        transformed = transformed.replace(item["before"], item["after"])
        labels.append(item["label"])
        if item["label"] in SCOPE:
            assert scope_only.count(item["before"]) == 1
            scope_only = scope_only.replace(item["before"], item["after"])
    assert transformed == new and len(labels) == len(set(labels)) == 18
    f0, f1 = functions(scope_only), functions(new)
    assert set(f0) == set(f1)
    changed = {k for k in f0 if f0[k] != f1[k]}
    assert changed == FRESH
    unchanged = sorted(set(f0) - changed)
    assert len(unchanged) == 18
    for name in ("LIMITS", "OPTIONS", "native_once", "set_model"):
        assert assignment(old, name) == assignment(new, name), name
    model, cold, prep, flight = (json.loads(raw[k]) for k in ("model", "cold", "preparation", "preflight"))
    assert (model["columns"], model["rows"], model["nonzeros"]) == (1102, 166010, 10767167)
    assert model["source_bindings"]["builder_sha256"] == FILES["builder"][1]
    assert cold["model_sha256"] == FILES["model"][1]
    assert cold["source_bindings"] == model["source_bindings"]
    assert cold["all_omission_witnesses_replayed"] and cold["all_row_column_transports_checked"]
    assert model["retained_original_primary_rows"] == 1960
    assert model["retained_coordinate_covers"] == 164044
    assert model["integer_cover_ranges"] == [[1, 1], [1, 1]]
    assert model["added_pair_rows"] == [[259, 590], [259, 591], [259, 593], [259, 732]]
    assert len(model["fixed_zero_columns"]) == 112 and not model["fixed_one_columns"]
    assert model["parent_real_feasible_set_preservation_claimed"] is False
    assert prep["source_bindings"] == flight["source_bindings"]
    assert flight["preparation_sha256"] == FILES["preparation"][1]
    assert flight["prior_complete_cold_replay_sha256"] == FILES["cold"][1]
    assert flight["definition_sha256"] == prep["definition_sha256"]
    assert not flight["duplicate_base_rebuild_performed"]
    assert flight["terminal_exact_acceptance_still_rebuilds_all_inputs"]
    definition = prep["definition"]
    math = definition["complete_original_maxmin_model"]
    assert (math["variables_including_t"], math["rows"], math["nonzeros"]) == (1103, 167112, 10769371)
    assert definition["initial_rows"] == 3068 and definition["initial_nonzeros"] == 27942
    assert definition["initial_row_ranges"] == [[0, 1960], [166004, 167112]]
    assert definition["retained_cover_pool_count"] == 164044
    assert definition["always_active_proved_parity_equalities"] == [166004, 166005]
    assert definition["always_active_certified_pair_rows"] == [166006, 166007, 166008, 166009]
    assert definition["all_original_rows_required_for_rational_primal_acceptance"] == 167112
    assert definition["only_original_rows_may_be_added"]
    return {
        "status": "PASS: complete builder/driver source read and independent exact reuse/binding review",
        "review_source_sha256": sha(Path(__file__).read_bytes()),
        "bindings": {k: {"path": p, "sha256": h} for k, (p, h) in FILES.items()},
        "independent_complete_text_substitutions_checked": len(labels),
        "AST_identical_functions_after_only_scope_updates": unchanged,
        "fresh_functions_read_completely": sorted(FRESH),
        "complete_builder_and_driver_read": True,
        "mathematical_review": [
            "The premise loader rederives the 112 zeros, both integer unit sums and four pair capacities; no numerical selector or saved witness is fixed.",
            "All 2271 original native rows and 178533 original coordinate covers are reconstructed. Only proved-zero substitution and real unit-box tautologies remove obligations.",
            "For a zero cover target the remaining positive sum is nonnegative. For a live target, the projected cover has the same lower bound and a box-valid finite upper bound.",
            "The two unit sums and four pair capacities are retained explicitly; integer validity is distinguished from preservation of the older real relaxation.",
            "The native prefix, complete cover pool and always-active suffix partition all 167112 extended rows. The extension 0 <= x_j-t <= 1 with unit boxes preserves original feasibility at t=0.",
            "Prefix row-duals/rays are expanded by original row ID with zeros elsewhere. An exact subset finite-box certificate applies to every full-model feasible point.",
            "Rational primal acceptance checks every extended row and restores all original 1214 coordinates with proved zeros; numerical status alone proves neither feasibility nor exclusion.",
            "Preflight binds the already completed exact model replay; terminal replay still reconstructs all original arrays and validates every appended-cover prefix and certificate.",
            "Run, bound/primal reconstruction and terminal replay are unchanged after the explicit scope strings. No optimizer call is introduced by the new preparation or cold-record reuse."
        ],
        "limits": definition["limits"],
        "scope_limits": [
            "This is a source and mathematical review, not an independent matrix rebuild or native execution.",
            "Author preparation/cold/control results are hash-bound and not repeated.",
            "No query outcome or case exclusion is asserted by this review."
        ],
        "subject_sources_imported": False,
        "author_controls_repeated": False,
        "model_or_CNF_rebuilt": False,
        "optimizer_calls": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    result = review()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
