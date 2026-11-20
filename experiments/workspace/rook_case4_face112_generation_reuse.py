"""Read-only exact substitution/AST control for the 112-face LP driver."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "experiments/logs/grids-and-triangles/rook-case4-face112-generation-substitutions.json"
SCOPE_LABELS = {"preparation_scope", "certificate_scope", "replay_scope"}
CHANGED_FUNCTIONS = {"source_bindings", "load_inputs", "definition", "cold_arrays", "preflight_replay"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(source):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}


def assigned(source, name):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.dump(node.value, include_attributes=False)
    raise AssertionError(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    ledger = json.loads(LEDGER.read_bytes())
    old = (ROOT / ledger["parent_path"]).read_bytes()
    new = (ROOT / ledger["child_path"]).read_bytes()
    assert sha(old) == ledger["parent_sha256"]
    transformed = old.decode()
    normalized_scope = old.decode()
    labels = []
    for item in ledger["substitutions"]:
        assert item["occurrences"] == 1 and transformed.count(item["before"]) == 1
        transformed = transformed.replace(item["before"], item["after"])
        labels.append(item["label"])
        if item["label"] in SCOPE_LABELS:
            assert normalized_scope.count(item["before"]) == 1
            normalized_scope = normalized_scope.replace(item["before"], item["after"])
    assert transformed == new.decode()
    assert len(labels) == len(set(labels)) == 18
    old_functions = functions(normalized_scope)
    new_functions = functions(new.decode())
    assert set(old_functions) == set(new_functions)
    unchanged = sorted(k for k in old_functions if old_functions[k] == new_functions[k])
    changed = set(old_functions) - set(unchanged)
    assert changed == CHANGED_FUNCTIONS
    for name in ("run", "replay", "reconstruct_bound", "reconstruct_primal", "expanded_numeric",
                 "extend", "full_float_matrix", "inspect_numeric_point", "initial_row_ids", "controls"):
        assert name in unchanged
    for name in ("LIMITS", "OPTIONS", "native_once"):
        assert assigned(old.decode(), name) == assigned(new.decode(), name), name
    report = {
        "status": "PASS: complete exact substitution ledger and AST reuse checked without subject imports",
        "control_source_sha256": sha(Path(__file__).read_bytes()),
        "parent_driver_sha256": sha(old), "child_driver_sha256": sha(new),
        "substitution_ledger_sha256": sha(LEDGER.read_bytes()),
        "exact_text_substitutions": len(labels),
        "AST_identical_functions_after_three_scope_string_updates": unchanged,
        "functions_requiring_fresh_read": sorted(changed),
        "native_calls_run_loop_exact_bound_primal_and_terminal_replay_algorithms_unchanged": True,
        "limits_options_and_native_helper_alias_unchanged": True,
        "preflight_change": ledger["preflight_change"],
        "subject_sources_imported": False, "model_or_CNF_rebuilt": False, "optimizer_calls": 0,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
