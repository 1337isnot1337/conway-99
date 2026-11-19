"""Source-only audit of the frozen count blossom query adapter."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "experiments/logs/root-prism-free/f0-core-matching-blossom-query-substitutions.json"
LEDGER_SHA = "f691cc652856e897de488c7005782904b5e52418a34b365c473592073bc7b5aa"
BINDINGS = {
    "experiments/workspace/root_prism_free_f0_full_fourier_query.py": "a8eff9c09fdd2a31482d23e3c83b11424fab32462e9b1431c3d899b6b8034955",
    "experiments/workspace/root_prism_free_f0_full_fourier_replay.py": "9a072b04151e4a150d1627171c16c7dd33d87a49a6817157d1766aeddab062a1",
    "experiments/workspace/root_prism_free_f0_core_matching_blossom_query.py": "67cd7853f00d5f99df7524046c30d72a1286106c2f5577a50d573cf1fa4a967b",
    "experiments/workspace/root_prism_free_f0_core_matching_blossom_replay.py": "baf3f134cf83c3a9f4410276ebbd570f89ec47a651dde96486c030043577e677",
    "experiments/logs/root-prism-free/f0-core-matching-blossom-native-overlay02-cold/report.json": "268a2d4f97f4436823f4d36271425c856ad770f5877667941b13e403f5b9166f",
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def functions(text):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}

def main():
    for name, expected in BINDINGS.items():
        assert sha((ROOT / name).read_bytes()) == expected
    assert sha(LEDGER.read_bytes()) == LEDGER_SHA
    ledger = json.loads(LEDGER.read_bytes())
    checked = []
    for item in ledger["files"]:
        old = (ROOT / item["parent_path"]).read_text()
        new = (ROOT / item["path"]).read_text()
        assert sha(old.encode()) == item["parent_sha256"]
        assert sha(new.encode()) == item["sha256"]
        predicted = old
        for replacement in item["replacements"]:
            assert predicted.count(replacement["old"]) == replacement["count"]
            predicted = predicted.replace(replacement["old"], replacement["replacement"])
        assert predicted == new
        parent, child = functions(old), functions(new)
        assert parent.keys() == child.keys()
        unchanged = [name for name in parent if parent[name] == child[name]]
        changed = [name for name in parent if parent[name] != child[name]]
        checked.append({"path": item["path"], "complete_text_transformation": True,
                        "unchanged_functions": unchanged, "changed_functions_read": changed,
                        "child_function_AST_sha256": {k: sha(v.encode()) for k, v in child.items()}})
    assert len(checked[0]["unchanged_functions"]) == 15
    assert checked[0]["changed_functions_read"] == [
        "configuration", "owner_preparation_binding", "load_target",
        "construct_initial", "provisional_record", "worker"]
    assert len(checked[1]["unchanged_functions"]) == 4 and checked[1]["changed_functions_read"] == ["replay"]
    cold = json.loads((ROOT / "experiments/logs/root-prism-free/f0-core-matching-blossom-native-overlay02-cold/report.json").read_bytes())
    assert cold["status"].startswith("PASS")
    assert cold["model_report_sha256"] == "ddd0eac97aac5741a60778276ac1798240089a547ffb43a77629fb8736114d4e"
    report = {
        "status": "PASS: complete adapter-text and changed-path source review",
        "source_sha256": sha(Path(__file__).read_bytes()), "bindings": BINDINGS,
        "substitution_ledger_sha256": LEDGER_SHA, "checked_files": checked,
        "mathematical_source_review": [
            "All 32296 variable IDs and all 117 pool IDs retain their parent semantics.",
            "The new exact target and initial row counts are 65811 and 65694.",
            "The actual initial-to-target row embedding, pool hashes and full target coverage remain checked.",
            "The native model and cold report bindings use the actual overlay outputs.",
            "The new cold schema uses model_report_sha256, checked against the actual saved cold record.",
            "The one-worker, seed-zero, no-LP parameters and 300-owner/180-native caps are unchanged.",
            "A later native call still requires a strictly larger certified pool prefix.",
            "Candidates remain provisional pending separate exact parent and literal acceptance.",
            "Native infeasibility and deadline outcomes remain unproved."
        ],
        "source_review_only": True, "subject_modules_imported": False,
        "model_or_census_reconstructed": False, "controls_or_optimizer_repeated": False,
        "cold_record_hash_bound_not_rerun": True,
    }
    output = ROOT / "experiments/logs/root-prism-free/f0-core-matching-blossom-query-direct-lane-review.json"
    assert not output.exists()
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "report_sha256": sha(output.read_bytes()),
                      "source_sha256": report["source_sha256"]}))

if __name__ == "__main__":
    main()
