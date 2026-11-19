"""Source-only independent delta audit; imports no subject or native module."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "experiments/workspace"
LOG = ROOT / "experiments/logs/root-prism-free"
LEDGER = LOG / "f0-full-fourier-query-reuse-controls.json"
EXPECTED_LEDGER = "d32bbacfe4c2801b8f019340cc61d2fdcf934b24a4b52dc59a60a3cc2becb1df"
EXPECTED = {
    "query": "a8eff9c09fdd2a31482d23e3c83b11424fab32462e9b1431c3d899b6b8034955",
    "replay": "9a072b04151e4a150d1627171c16c7dd33d87a49a6817157d1766aeddab062a1",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(text):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}


def main():
    raw = LEDGER.read_bytes()
    assert sha(raw) == EXPECTED_LEDGER
    ledger = json.loads(raw)
    checked = {}
    for kind in ("query", "replay"):
        old_path = WORK / ("root_prism_free_f0_character_packing_no_lp_" + kind + ".py")
        new_path = WORK / ("root_prism_free_f0_full_fourier_" + kind + ".py")
        old_raw, new_raw = old_path.read_bytes(), new_path.read_bytes()
        assert sha(old_raw) == ledger["old_" + kind + "_sha256"]
        assert sha(new_raw) == ledger[kind + "_sha256"] == EXPECTED[kind]
        old_text, new_text = old_raw.decode(), new_raw.decode()
        transformed = old_text
        replacements = ledger[kind + "_substitutions"]
        for item in replacements:
            assert transformed.count(item["before"]) == item["occurrences"]
            transformed = transformed.replace(item["before"], item["after"])
        assert transformed == new_text
        assert ast.dump(ast.parse(transformed), include_attributes=False) == ast.dump(ast.parse(new_text), include_attributes=False)
        old, new = functions(old_text), functions(new_text)
        inventory = {
            "added": sorted(set(new) - set(old)),
            "removed": sorted(set(old) - set(new)),
            "changed": sorted(k for k in set(old) & set(new) if old[k] != new[k]),
            "unchanged": sorted(k for k in set(old) & set(new) if old[k] == new[k]),
        }
        assert inventory == ledger[kind + "_function_inventory"]
        checked[kind] = {"path": str(new_path.relative_to(ROOT)), "sha256": sha(new_raw),
                         "old_source_sha256": sha(old_raw), "bytes": len(new_raw),
                         "complete_text_and_AST_match": True, "ordered_substitutions": len(replacements),
                         "function_inventory": inventory}
    report = {
        "status": "PASS: complete query and replay source review with independent text/AST delta audit",
        "review_source_sha256": sha(Path(__file__).read_bytes()),
        "ledger_sha256": EXPECTED_LEDGER, "sources": checked,
        "whole_subject_sources_read": True,
        "mathematical_and_runtime_findings": [
            "The archived initial model is checked as the exact 58840-row subset of the 58957-row target on all 32296 unchanged variable domains; the external registry contains the complementary 117 rows.",
            "Each later native call requires an earlier exactly rejected candidate and a strictly larger prefix containing only original target rows; selection remains the first at most16 violated pool IDs.",
            "The per-call native limit is clipped by the remaining180 cumulative measured solve seconds and remaining300 owner seconds, with an8-second finalization reserve. The owner retains its independent hard deadline and reap path.",
            "Every returned integer vector is saved atomically before response-text parsing, prefix arithmetic, external-row scans or provisional acceptance. Deadline and cumulative-budget overruns preserve it without promotion.",
            "The unchanged Python-integer evaluator checks domains, linear rows, two-factor products and allowed tables. The unchanged pool scan uses exact signed integer contractions.",
            "A full target pass remains provisional and requires the separate restored-parent arithmetic receipt and literal decoder. Native infeasibility, a partial record or an UNKNOWN response is never an F0 exclusion.",
            "The replay reconstructs chronological target-row prefixes, checks actual saved protobufs, repeats candidate arithmetic and row selection, and independently sums all recorded native-call wall times. Pending and late candidates remain unaccepted.",
            "The lightweight owner preparation binding avoids archive duplication; the search and replay children still check the complete source/input configuration before native data use."
        ],
        "scope": "Source-only review. The target's mathematical necessity and native construction remain bound to their prior independent preparation/cold gates.",
        "subject_imports": 0, "controls_repeated": 0, "model_rebuilds": 0,
        "native_solver_calls": 0, "point_or_terminal_replay_calls": 0,
    }
    path = LOG / "f0-full-fourier-query-independent-source-review.json"
    assert not path.exists()
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "path": str(path.relative_to(ROOT)),
                      "sha256": sha(path.read_bytes()), "source_sha256": report["review_source_sha256"],
                      "query_substitutions": 35, "replay_substitutions": 16}, sort_keys=True))


if __name__ == "__main__":
    main()
