"""No-import complete-source audit for the bounded native preparation v2."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
OLD = ROOT / "experiments/workspace/root_prism_free_f0_full_fourier_native.py"
NEW = ROOT / "experiments/workspace/root_prism_free_f0_full_fourier_native_v2.py"
OLD_SHA = "a1bde1aa30b0154223d2f94fe1ee1744274792f5f993bf60ca210f2939fdf703"
NEW_SHA = "ce21cabaa26e28e69f84380736adb28b7e193037a67a83d0ec79df84230b77ad"
SUBSTITUTIONS = [
    ["SECONDS = 60\n", "SECONDS = 180\n"],
    ["    deadline = started + SECONDS\n    definition(config_path)\n    supervisor = source_module(\"supervisor\")\n",
     "    deadline = started + SECONDS\n    supervisor = source_module(\"supervisor\")\n"],
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def binding(path, expected):
    raw = path.read_bytes()
    assert sha(raw) == expected
    return {"path": str(path.relative_to(ROOT)), "sha256": expected, "bytes": len(raw)}


def run():
    old_binding, new_binding = binding(OLD, OLD_SHA), binding(NEW, NEW_SHA)
    old, new = OLD.read_text(), NEW.read_text()
    transformed = old
    for before, after in SUBSTITUTIONS:
        assert transformed.count(before) == 1
        transformed = transformed.replace(before, after, 1)
    assert transformed == new
    assert ast.dump(ast.parse(transformed), include_attributes=False) == ast.dump(ast.parse(new), include_attributes=False)
    trees = [ast.parse(text) for text in (old, new)]
    functions = [{node.name: ast.dump(node, include_attributes=False)
                  for node in tree.body if isinstance(node, ast.FunctionDef)} for tree in trees]
    assert functions[0].keys() == functions[1].keys()
    changed = sorted(name for name in functions[0] if functions[0][name] != functions[1][name])
    assert changed == ["owned"]
    owned_nodes = [next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "owned") for tree in trees]
    call_ast = ast.dump(ast.parse("definition(config_path)").body[0], include_attributes=False)
    positions = [i for i, node in enumerate(owned_nodes[0].body) if ast.dump(node, include_attributes=False) == call_ast]
    assert positions == [2]
    owned_nodes[0].body.pop(positions[0])
    assert ast.dump(owned_nodes[0], include_attributes=False) == ast.dump(owned_nodes[1], include_attributes=False)
    worker = next(n for n in trees[1].body if isinstance(n, ast.FunctionDef) and n.name == "worker")
    assert "definition(config_path)" in ast.unparse(worker)
    failure_dir = LOGS / "f0-full-fourier-literal-native01"
    owner_path, stage_path = failure_dir / "owner-result.json", failure_dir / "stages.json"
    failure_bindings = {
        "owner": binding(owner_path, "a232de888a1d370a9b999a05ce54657257419eed0bdd7ddce4ca1da00c97d4cf"),
        "stages": binding(stage_path, "80d47d6d095c9e875e0dc5b7dff9401c6406ebd2af6189c1b534fb395c8651f7"),
    }
    owner, stages = json.loads(owner_path.read_bytes()), json.loads(stage_path.read_bytes())["stages"]
    assert owner["status"] == "UNKNOWN_HARD_DEADLINE" and not owner["report_accepted"]
    assert owner["supervision"]["child_reaped"] and owner["optimizer_calls"] == 0
    assert stages[-1]["stage"] == "passed_Fourier_specification_and_owned_cold_bound"
    import_stage = next(s for s in stages if s["stage"] == "native_import_complete")
    return {
        "schema": "conway99.f0.full-Fourier-native-v2-complete-delta.v1",
        "status": "PASS: two explicit source substitutions; no model or optimizer",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "old_source": old_binding, "new_source": new_binding,
        "substitutions": SUBSTITUTIONS,
        "complete_text_identity_after_substitutions": True,
        "complete_AST_identity_after_substitutions": True,
        "changed_function_AST": changed,
        "unchanged_function_AST": sorted(name for name in functions[0] if name not in changed),
        "owner_only_delta": "Remove the duplicate owner definition(config_path) call; the worker retains the complete hash and definition checks before construction.",
        "owned_seconds": {"old": 60, "new": 180},
        "mathematical_inputs_and_operations_unchanged": True,
        "protobuf_construction_and_full_parent_restoration_unchanged": True,
        "native_validation_and_acceptance_unchanged": True,
        "cold_comparison_unchanged": True,
        "preserved_failed_attempt": failure_bindings,
        "observed_failed_owner_seconds": owner["owner_seconds"],
        "observed_failed_supervision_seconds": owner["supervision"]["seconds"],
        "observed_owner_time_outside_supervision_seconds": owner["owner_seconds"] - owner["supervision"]["seconds"],
        "observed_child_import_complete_seconds": import_stage["elapsed_seconds"],
        "observed_child_last_stage_seconds": stages[-1]["elapsed_seconds"],
        "timing_attribution_limit": "The v1 owner did not log individual hash durations. Time outside supervision is measured by subtraction; filesystem or scheduling causes are unconfirmed.",
        "source_imports": 0, "model_builds": 0, "optimizer_calls": 0,
        "production_query_authorized": False,
    }


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    result = run()
    path = LOGS / "f0-full-fourier-native-v2-reuse-controls.json"
    assert not path.exists()
    path.write_bytes(canonical(result) + b"\n")
    print(json.dumps({"status": result["status"], "path": str(path.relative_to(ROOT)),
                      "sha256": sha(path.read_bytes()), "source_sha256": result["source_sha256"],
                      "unchanged_functions": len(result["unchanged_function_AST"])}, sort_keys=True))
