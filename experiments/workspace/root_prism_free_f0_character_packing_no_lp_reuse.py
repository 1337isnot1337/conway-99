"""No-import complete-source and AST audit of the no-LP tactic delta."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = "experiments/logs/root-prism-free/f0-character-packing-no-lp-substitutions01.json"
LEDGER_SHA = "db440f4b0f80fce0c4800b90e9b2e3d2ccb6c41ac95d28f9733c2b19d6934c29"

def audit():
    raw = (ROOT / LEDGER).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == LEDGER_SHA
    ledger = json.loads(raw)
    reports = {}
    for kind in ("query", "replay"):
        item = ledger[kind]
        old_raw, new_raw = (ROOT/item["parent_path"]).read_bytes(), (ROOT/item["new_path"]).read_bytes()
        assert hashlib.sha256(old_raw).hexdigest() == item["parent_sha256"]
        assert hashlib.sha256(new_raw).hexdigest() == item["new_sha256"]
        expected = old_raw.decode()
        for sub in item["substitutions"]:
            assert expected.count(sub["old"]) == sub["occurrences"]
            expected = expected.replace(sub["old"], sub["new"])
        assert expected.encode() == new_raw
        assert ast.dump(ast.parse(expected), include_attributes=False) == ast.dump(ast.parse(new_raw), include_attributes=False)
        old = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(old_raw).body if isinstance(n, ast.FunctionDef)}
        new = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(new_raw).body if isinstance(n, ast.FunctionDef)}
        changed = sorted(k for k in old if old[k] != new[k])
        added = sorted(set(new)-set(old))
        assert set(old) <= set(new)
        if kind == "query":
            assert changed == ["check_preparation", "configuration", "native_parameters", "reuse_controls"]
            assert added == ["native_parameter_controls"]
        else:
            assert changed == ["replay"] and added == []
        reports[kind] = {"whole_text_transformation_passed":True,"whole_AST_transformation_passed":True,
                         "changed_functions":changed,"added_functions":added,
                         "AST_identical_functions":sorted(k for k in old if old[k] == new[k]),
                         "source_sha256":item["new_sha256"]}
    return {"status":"PASS: complete no-LP parameter/provenance source delta",
            "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "ledger_sha256":LEDGER_SHA,"checks":reports,
            "subject_imports":False,"model_reconstruction":False,"optimizer_calls":0}

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    result=audit();args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
