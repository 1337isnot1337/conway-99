"""No-import controls for the narrow joint-PSD/clique native adapters."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
WORK = ROOT / "experiments/workspace"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def functions(source):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(source).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def check():
    results = []
    for name in ("query", "replay", "native-audit"):
        record_path = LOGS / ("f0-joint-psd-clique-"+name+"-substitutions.json")
        record = json.loads(record_path.read_text())
        parent, new = ROOT / record["parent_path"], ROOT / record["new_path"]
        assert digest(parent) == record["parent_sha256"] and digest(new) == record["new_sha256"]
        source = parent.read_text()
        counts = []
        for before, after in record["exact_text_substitutions"]:
            count = source.count(before)
            assert count > 0
            counts.append(count)
            source = source.replace(before, after)
        assert source == new.read_text()
        assert ast.dump(ast.parse(source), include_attributes=False) == ast.dump(ast.parse(new.read_text()), include_attributes=False)
        results.append({"adapter": name, "parent_sha256": digest(parent), "new_sha256": digest(new),
                        "substitution_record_sha256": digest(record_path), "replacement_occurrences": counts,
                        "entire_source_equals_explicit_substitutions": True,
                        "complete_AST_equals_explicit_substitutions": True,
                        "functions_covered": sorted(functions(source))})
    old_exact = WORK / "root_prism_free_f0_schur_path_exact_v3.py"
    new_exact = WORK / "root_prism_free_f0_joint_psd_clique_exact.py"
    assert digest(old_exact) == "e039d525a93ab2972ac53538060feb7b6e16dd9f671bb051d29c543b6008b794"
    assert digest(new_exact) == "f16d9648a396a4c2c78b68262ce4c767351bfd69bdf66237b49b35e0fb8752fc"
    assert functions(old_exact.read_text().replace("len(ray_hex) == 27764", "len(ray_hex) == 28043"))["exact_phase"] == functions(new_exact.read_text())["exact_phase"]
    old_replay = functions((WORK / "root_prism_free_f0_schur_path_replay_v3.py").read_text())
    new_replay = functions((WORK / "root_prism_free_f0_joint_psd_clique_replay.py").read_text())
    for name in ("digest", "canonical", "number", "check_integer_certificate", "controls"):
        assert old_replay[name] == new_replay[name]
    return {"status": "PASS: complete narrow-adapter text/AST controls",
            "source_sha256": digest(Path(__file__)), "adapters": results,
            "exact_helper_sha256": digest(new_exact),
            "exact_phase_identical_except_ray_dimension": True,
            "independent_integer_certificate_arithmetic_identical": True,
            "new_model_loader_review_required": True,
            "subject_modules_imported": False, "model_builds": 0,
            "optimizer_calls": 0, "eigendecompositions": 0}


if __name__ == "__main__":
    output = LOGS / "f0-joint-psd-clique-reuse-controls.json"
    assert not output.exists()
    result = check()
    output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
