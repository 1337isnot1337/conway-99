"""Reproduce and audit the narrow six-cut LP adapter without importing it."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "experiments/workspace/rook_case4_parity_cycle_v4.py"
OLD_SHA = "345e091ef71dde96b3423773d5315b8733c275f0af142ab0f88ac03570ca263e"
PROOF = ROOT / "experiments/workspace/rook_case4_box_cut_lp_proof.py"
PROOF_SHA = "091946b8444aa1c3b49f2955b076e00f7241a96926a9b9d2a4afb210fe4067c3"
TARGET = ROOT / "experiments/workspace/rook_case4_box_cut_lp_adapter.py"
REPORT = ROOT / "experiments/logs/grids-and-triangles/rook-case4-box-cut-lp-adapter-reuse.json"
NAMES = ["save", "save_gzip", "read_record", "record_ref", "checked_ref", "source_bindings",
         "read_input", "point_data", "domain", "with_point", "validate_registry", "load_matrix",
         "checked_state", "numerical_scan", "float_matrix", "initial_rows", "numeric_stage",
         "numeric_records", "expanded_numeric", "finite_bound", "inspect_point", "exact_stage",
         "replay_numeric", "exact_cold", "state_payload"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main(create):
    raw = OLD.read_bytes()
    assert sha(raw) == OLD_SHA and sha(PROOF.read_bytes()) == PROOF_SHA
    old = raw.decode()
    tree = ast.parse(old)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    bodies = {name: ast.get_source_segment(old, functions[name]) for name in NAMES}
    header = old[:old.index("def save(path, value):")]
    old_doc = ast.get_source_segment(old, tree.body[0])
    new_doc = '"""Single-round LP kernels with a distinct exact branch-box proof kind.\n\nThe numerical, basis, finite-box and cold functions are source-identical to\nthe reviewed v4 implementations, apart from registry proof dispatch and\naccurate acceptance metadata. No old module is modified. This module has\nno scan, multi-round cycle, or CLI production entry point.\n"""'
    changes = [
        ["module_docstring", old_doc, new_doc],
        ["proof_import", "import rook_case4_face112_h3_weighted_parity as weighted\n",
         "import rook_case4_face112_h3_weighted_parity as weighted\nimport rook_case4_box_cut_lp_proof as box_proof\n"],
        ["proof_source_binding", "SOURCES = {\n", "SOURCES = {\n    \"box_proof\": (\"experiments/workspace/rook_case4_box_cut_lp_proof.py\", \"" + PROOF_SHA + "\"),\n"],
    ]
    for label, before, after in changes:
        assert header.count(before) == 1, label
        header = header.replace(before, after, 1)
    validator_changes = [
        ["fixed_registry", '    assert len(registry) <= LIMITS["maximum_new_cuts"]\n',
         '    assert len(registry) <= LIMITS["maximum_new_cuts"]\n    assert registry == box_proof.frozen_registry() and len(registry) == 6\n'],
        ["distinct_proof_dispatch",
         '        nums, den = point_data(entry["source_point"])\n        checked = exact.verify_cut(entry["certificate"], data["gram"], data["zeros"], nums, den, deadline)\n',
         '        if entry.get("proof_kind") == box_proof.PROOF_KIND:\n            checked = box_proof.verify_entry(entry, data["gram"], data["zeros"], deadline)\n        else:\n            assert "proof_kind" not in entry\n            nums, den = point_data(entry["source_point"])\n            checked = exact.verify_cut(entry["certificate"], data["gram"], data["zeros"], nums, den, deadline)\n'],
    ]
    for label, before, after in validator_changes:
        assert bodies["validate_registry"].count(before) == 1, label
        bodies["validate_registry"] = bodies["validate_registry"].replace(before, after, 1)
    before = '            "appended_signed_parity_rows_checked": len(registry),\n'
    after = ('            "appended_signed_parity_rows_checked": sum("proof_kind" not in e for e in registry),\n'
             '            "appended_box_cover_rows_checked": sum(e.get("proof_kind") == box_proof.PROOF_KIND for e in registry),\n'
             '            "appended_proved_rows_checked": len(registry),\n')
    assert bodies["inspect_point"].count(before) == 1
    bodies["inspect_point"] = bodies["inspect_point"].replace(before, after, 1)
    generated = (header + "\n\n".join(bodies[name] for name in NAMES) + "\n").encode()
    ast.parse(generated)
    if create:
        with TARGET.open("xb") as stream:
            stream.write(generated)
    else:
        assert TARGET.read_bytes() == generated
    new_tree = ast.parse(generated)
    new_functions = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
    assert list(new_functions) == NAMES
    function_checks = []
    for name in NAMES:
        original_body = ast.get_source_segment(old, functions[name])
        new_body = ast.get_source_segment(generated.decode(), new_functions[name])
        same_ast = ast.dump(functions[name], include_attributes=False) == ast.dump(new_functions[name], include_attributes=False)
        same_text = original_body == new_body
        assert same_ast == same_text == (name not in ("validate_registry", "inspect_point"))
        function_checks.append({"name": name, "identical_text": same_text, "identical_ast": same_ast,
                                "old_sha256": sha(original_body.encode()), "new_sha256": sha(new_body.encode())})
    report = {"status": "PASS_COMPLETE_SOURCE_EXTRACTION_AND_EXPLICIT_TWO_FUNCTION_DELTA",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "old": {"path": str(OLD.relative_to(ROOT)), "sha256": OLD_SHA},
              "proof": {"path": str(PROOF.relative_to(ROOT)), "sha256": PROOF_SHA},
              "adapter": {"path": str(TARGET.relative_to(ROOT)), "sha256": sha(generated), "bytes": len(generated)},
              "header_substitutions": changes, "validator_substitutions": validator_changes,
              "inspection_metadata_substitution": [before, after], "function_checks": function_checks,
              "identical_functions": 23, "changed_functions": ["validate_registry", "inspect_point"],
              "old_arithmetic_kernel_still_imported_by_hash": True,
              "subject_imports": 0, "native_calls": 0, "old_files_modified": False}
    if create:
        with REPORT.open("x") as stream:
            json.dump(report, stream, sort_keys=True, indent=2); stream.write("\n")
    else:
        assert json.loads(REPORT.read_bytes()) == report
    print(json.dumps({"status": report["status"], "adapter": report["adapter"], "report_sha256": sha(REPORT.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    main(parser.parse_args().create)
