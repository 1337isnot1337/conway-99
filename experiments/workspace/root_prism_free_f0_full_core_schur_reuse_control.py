"""Source-only reuse controls for the full21-core Schur cut adapter."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT/"experiments/workspace/root_prism_free_f0_graph_schur_cuts.py"
SUBJECT = ROOT/"experiments/workspace/root_prism_free_f0_full_core_schur_cuts.py"
PARENT_SHA256 = "45ce5c3cd1dffa1eaef611b4aa31964244d87e2f2c5078b99b417aa4ffb8edb5"
SUBJECT_SHA256 = "c5489561a99de14cc0c68a3d05dbc8eb1eb3fc17e4a759b4c3d63f8d771f7d8e"
CHANGED_FUNCTIONS = ["bindings", "load_state", "preparation"]
CHANGED_CONSTANTS = {"KERNEL_SOURCE_SHA256", "KERNEL_FILE", "KERNEL_FILE_SHA256", "KERNEL_RAW_SHA256"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(tree):
    return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}


def common_top_level(tree):
    result = []
    for index, node in enumerate(tree.body):
        if isinstance(node, ast.FunctionDef):
            continue
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            assert isinstance(node.value.value, str)
            continue
        if isinstance(node, ast.Import) and len(node.names) == 1:
            alias = node.names[0]
            if alias.name == "root_prism_free_f0_full_core_schur_kernels":
                assert alias.asname == "full_core"
                continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in CHANGED_CONSTANTS:
                continue
        result.append(ast.dump(node, include_attributes=False))
    return result


def run():
    parent_raw, subject_raw = PARENT.read_bytes(), SUBJECT.read_bytes()
    assert sha(parent_raw) == PARENT_SHA256 and sha(subject_raw) == SUBJECT_SHA256
    parent, subject = ast.parse(parent_raw), ast.parse(subject_raw)
    a, b = functions(parent), functions(subject)
    assert a.keys() == b.keys()
    changed = [name for name in a if a[name] != b[name]]
    assert changed == CHANGED_FUNCTIONS
    assert common_top_level(parent) == common_top_level(subject)
    assert all(name in a and a[name] == b[name] for name in
               ("raw_quotient", "cut", "exact_violation", "limits", "floating_matrix", "scan", "replay", "main"))
    return {"status": "PASS: source-only full21 adapter reuse",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "parent_sha256": PARENT_SHA256, "subject_sha256": SUBJECT_SHA256,
            "unchanged_functions": [name for name in a if a[name] == b[name]],
            "changed_functions_for_direct_review": changed,
            "only_additional_import": "root_prism_free_f0_full_core_schur_kernels as full_core",
            "changed_top_level_constants": sorted(CHANGED_CONSTANTS),
            "all_other_top_level_AST_equal": True,
            "kernel_geometry_or_new_binding_mathematics_audited_by_this_control": False,
            "subject_imports": 0, "model_rebuilds": 0, "optimizer_calls": 0, "eigendecompositions": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    assert not args.output.exists()
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
