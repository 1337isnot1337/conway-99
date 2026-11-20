"""Read-only delta and acceptance review of the face112 exact basis wrapper."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "experiments/workspace/rook_case4_face112_basis_reconstruction.py"
SOURCE_SHA = "6e8ac4d29fa14bf9c1ba2793a3f86c1e53854995cecb4bd30ae7e193352f3ee4"
LEDGER = "experiments/logs/grids-and-triangles/rook-case4-face112-basis-reuse-controls.json"
LEDGER_SHA = "0141115ab384080268289544db58d25b0a29637cb9513f7d4909afe4dcfbb93f"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(text):
    return {n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    raw = (ROOT / SOURCE).read_bytes()
    ledger_raw = (ROOT / LEDGER).read_bytes()
    assert sha(raw) == SOURCE_SHA and sha(ledger_raw) == LEDGER_SHA
    ledger = json.loads(ledger_raw)
    old_raw = (ROOT / ledger["parent_path"]).read_bytes()
    assert sha(old_raw) == ledger["parent_sha256"] == "1cbeb11b23e0033fa23d10ce24aedf1585ad0119d0433f296febf722231a67b6"
    transformed = old_raw.decode()
    for item in ledger["substitutions"]:
        assert transformed.count(item["old"]) == item["count"]
        transformed = transformed.replace(item["old"], item["new"])
    assert transformed == raw.decode()
    old, new = functions(old_raw.decode()), functions(raw.decode())
    assert set(old) == set(new)
    changed = [k for k in old if old[k] != new[k]]
    assert changed == ["proposal", "inspect"]
    unchanged = [k for k in old if old[k] == new[k]]
    assert unchanged == ledger["unchanged_functions"]
    report = {
        "status": "PASS: full source read and independent complete basis-wrapper delta review",
        "review_source_sha256": sha(Path(__file__).read_bytes()),
        "subject_source": {"path": SOURCE, "sha256": SOURCE_SHA},
        "parent_source": {"path": ledger["parent_path"], "sha256": ledger["parent_sha256"]},
        "substitution_ledger": {"path": LEDGER, "sha256": LEDGER_SHA},
        "all_text_substitutions_independently_checked": len(ledger["substitutions"]),
        "fresh_functions_completely_read": changed,
        "AST_unchanged_functions": unchanged,
        "mathematical_findings": [
            "The816 saved nonbasic lower extension rows impose x_j=t only as candidate reconstruction assumptions. No universal selector restriction or exclusion follows from failure of this face.",
            "The287 remaining active rows use their actual lower/upper endpoints. Allowing the recorded H1 equality alongside original native rows is valid for this proposal; all other binding and alias checks remain exact.",
            "Folding aliases sums coefficients at t, and the remaining variable list includes t last. Restoration fills aliases from the exact t coordinate and checks every candidate square equation.",
            "Acceptance requires all166010 base face rows plus1102 extension inequalities, all2271 original native rows, all178533 original covers, both unit sums, allfour pair bounds,112 zeros and original1214 unit bounds.",
            "The inspector demands positive t, exact population64 and rational integer arithmetic. Numerical basis validity merely proposes the square system; only full exact acceptance can promote its point.",
            "The single Dixon solve, one owned60-second child,4096-bit output cap and full cold replay are AST-identical. Singular, timed-out or rejected reconstructions remain UNKNOWN; no optimizer is called."
        ],
        "source_entirely_read": True,
        "subject_imported": False, "controls_repeated": False,
        "matrix_or_native_model_rebuilt": False, "exact_linear_solves": 0, "optimizer_calls": 0,
        "terminal_point_or_cold_arithmetic_independently_repeated": False,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
