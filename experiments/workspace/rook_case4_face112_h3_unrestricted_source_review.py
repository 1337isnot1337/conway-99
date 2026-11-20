"""Read-only independent H3 append and driver-delta review; no subject imports."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "experiments/workspace"
L = ROOT / "experiments/logs/grids-and-triangles"
SOURCES = {
    "parent": ("rook_case4_face112_cover_generation.py", "e0e245f1cfc20ff4e5eef7f148ee57b7a97af5829094bf57a0ff9247784942bc"),
    "builder": ("rook_case4_face112_h3_model_v2.py", "d06dfcadee54deeb81c244c9e11c80bd8687fdc682dcd01e274130fab1a0e2b7"),
    "driver": ("rook_case4_face112_h3_cover_generation.py", "655696089ce7f4b4fac3aabccbe1492f5f55c8c4670d3942b6b2cc251734e900"),
    "proof": ("rook_case4_face112_third_parity_cover.py", "9da8c7edc60429b6a7bee6cd15da447e08a6ae1656a4be5b77b1dd2f5ba5bdb3"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    text = {}
    for key, (name, expected) in SOURCES.items():
        raw = (W / name).read_bytes()
        assert sha(raw) == expected
        text[key] = raw.decode()
        ast.parse(text[key])
    ledger_path = L / "rook-case4-face112-h3-generation-reuse-controls.json"
    raw = ledger_path.read_bytes()
    assert sha(raw) == "33235226370f246569a012ed6c629b38141d8b1dea5a69a6354fb5810a273954"
    ledger = json.loads(raw)
    changed = text["parent"]
    for step in ledger["explicit_substitutions"]:
        assert changed.count(step["before"]) == step["occurrences"]
        changed = changed.replace(step["before"], step["after"])
    assert changed == text["driver"]
    old = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(text["parent"]).body if isinstance(n, ast.FunctionDef)}
    new = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(text["driver"]).body if isinstance(n, ast.FunctionDef)}
    assert set(old) == set(new)
    same = sorted(k for k in old if old[k] == new[k])
    assert same == sorted(ledger["AST_identical_functions"])
    report = {
        "status": "PASS: complete H3 necessity/append source and narrow driver delta reviewed",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "subjects": {k: {"path": str((W/n).relative_to(ROOT)), "sha256": h} for k, (n,h) in SOURCES.items()},
        "substitution_ledger_sha256": sha(raw),
        "complete_text_substitutions_independently_checked": len(ledger["explicit_substitutions"]),
        "unchanged_function_ASTs_independently_checked": same,
        "mathematical_checks": [
            "The five original quota-one Gram rows have odd total; deleting only proved-zero odd coefficients gives H3>=1 for nonnegative integer selectors.",
            "The reexpanded identity H3=1+2*(U-x803), together with U<=1 and x803>=0, proves H3<=3. No zero663 premise is used in that theorem.",
            "The complete112 parent implies the theorem's prior111 zeros and both unit sums. The new model does not fix a candidate or branch.",
            "All166010 parent row/array prefixes remain byte-identical; the sole new row has exactly27 unit coefficients and range[1,3].",
            "The original164044-cover pool remains1960..166003. H3 is always active at166010; max-min rows begin166011.",
            "The unchanged bounded query and exact acceptance use the new full167113-row definition. The solver result is not accepted without the inherited exact gates."
        ],
        "subject_imported": False, "model_or_control_rebuilt": False,
        "cold_replay_repeated": False, "optimizer_calls": 0,
        "scope": "Source and mathematical review only; no matrix reconstruction, point evaluation or solver execution repeated."
    }
    output = L / "rook-case4-face112-h3-unrestricted-source-review.json"
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output.read_bytes()), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
