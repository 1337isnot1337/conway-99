"""No-import complete text/AST gate for the six-observable query adapter."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = "experiments/logs/root-prism-free/f0-small-gram-query-substitutions01.json"
LEDGER_SHA = "d71e8c19b8d2e74321e25da5dd6c27c3db2832d314a8fc5aa016247d5eca6c01"


def audit():
    raw = (ROOT / LEDGER).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == LEDGER_SHA
    ledger = json.loads(raw)
    checks = {}
    for kind in ("query", "replay"):
        record = ledger[kind]
        old_raw = (ROOT / record["parent_path"]).read_bytes()
        new_raw = (ROOT / record["new_path"]).read_bytes()
        assert hashlib.sha256(old_raw).hexdigest() == record["parent_sha256"]
        assert hashlib.sha256(new_raw).hexdigest() == record["new_sha256"]
        expected = old_raw.decode()
        for substitution in record["substitutions"]:
            assert expected.count(substitution["old"]) == substitution["occurrences"]
            expected = expected.replace(substitution["old"], substitution["new"])
        assert expected.encode() == new_raw
        assert ast.dump(ast.parse(expected), include_attributes=False) == ast.dump(ast.parse(new_raw), include_attributes=False)
        old = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(old_raw).body if isinstance(n, ast.FunctionDef)}
        new = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(new_raw).body if isinstance(n, ast.FunctionDef)}
        assert set(old) == set(new)
        changed = sorted(k for k in old if old[k] != new[k])
        if kind == "query":
            assert changed == ["check_preparation", "configuration", "construct_initial", "load_target", "provisional_record", "worker"]
            # After changing only the three dimension literals, all algorithmic
            # functions, including worker and target checks, match the parent.
            normalized = old_raw.decode().replace("18444", "18450").replace("34398", "34405").replace("34281", "34288")
            normalized_functions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(normalized).body if isinstance(n, ast.FunctionDef)}
            algorithmic = ["construct_initial", "load_target", "provisional_record", "worker", "run",
                           "native_parameters", "evaluate_proto", "pool_scan", "choose_rows"]
            assert all(normalized_functions[k] == new[k] for k in algorithmic)
        else:
            assert changed == ["replay"]
            normalized = old_raw.decode().replace("18444", "18450").replace("34398", "34405").replace("34281", "34288")
            normalized_functions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(normalized).body if isinstance(n, ast.FunctionDef)}
            assert all(normalized_functions[k] == new[k] for k in old)
        checks[kind] = {
            "source_sha256": record["new_sha256"], "whole_text_delta_checked": True,
            "whole_AST_delta_checked": True, "changed_functions": changed,
            "unchanged_functions": sorted(k for k in old if old[k] == new[k]),
            "new_functions": [], "algorithmic_delta_only_dimension_literals": True,
        }
    return {
        "status": "PASS: complete six-observable query binding/dimension delta",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "ledger_sha256": LEDGER_SHA, "checks": checks,
        "source_modules_imported": False, "native_libraries_imported": False,
        "model_reconstructed": False, "optimizer_calls": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = audit()
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
