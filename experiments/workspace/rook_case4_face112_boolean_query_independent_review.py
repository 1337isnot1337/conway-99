"""Source-only audit of the frozen 112-face proof-capable query adapter."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/"experiments/logs/grids-and-triangles"
LEDGER = LOG/"rook-case4-face112-boolean-query-substitutions.json"
LEDGER_SHA = "daafb4894e3ce4e2e4053914527e8bbb255fb6abfcab1e75d58a70bad9ed0bbc"
PREP = LOG/"rook-case4-face112-boolean-query-preparation.json"
PREP_SHA = "7039ecf70eb0ec50d21f537c9979cf157223a3214dc7b82fb6bd11f4c00b9c7c"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def functions(text):
    return {n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def literal(node):
    if isinstance(node, ast.Constant):
        assert type(node.value) in (str, int)
        return node.value
    if isinstance(node, ast.Dict):
        return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.LShift):
        left, right = literal(node.left), literal(node.right)
        assert type(left) is type(right) is int and 0 <= right <= 63
        return left << right
    raise AssertionError(ast.dump(node))


def constant(text, name):
    for n in ast.parse(text).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return literal(n.value)
    raise AssertionError(name)


def main():
    assert sha(LEDGER.read_bytes()) == LEDGER_SHA
    ledger = json.loads(LEDGER.read_bytes())
    old_raw = (ROOT/ledger["parent_path"]).read_bytes()
    new_raw = (ROOT/ledger["new_path"]).read_bytes()
    assert sha(old_raw) == ledger["parent_sha256"]
    assert sha(new_raw) == ledger["new_sha256"] == "c79ff548abf28ee4300b974e3f4a4e864647a4690b5ab3c8b8b0efa920c7f4b9"
    old, new = old_raw.decode(), new_raw.decode()
    transformed = old
    counts = []
    for item in ledger["exact_text_substitutions"]:
        assert transformed.count(item["old"]) == item["occurrences"]
        counts.append(item["occurrences"])
        transformed = transformed.replace(item["old"], item["new"])
    assert transformed == new
    assert ast.dump(ast.parse(transformed), include_attributes=False) == ast.dump(ast.parse(new), include_attributes=False)
    before, after = functions(old), functions(new)
    assert set(before) == set(after)
    changed = [name for name in before if before[name] != after[name]]
    assert changed == ledger["changed_function_ASTs"] == ["retained_inclusion", "prepare", "inspect_selected", "solve", "replay"]
    protected = ["resource_caps", "checker_binding", "run_checker", "checked", "child"]
    assert all(before[name] == after[name] for name in protected)
    limits = constant(new, "LIMITS")
    assert limits == constant(old, "LIMITS")
    assert limits["production_queries"] == 1 and limits["automatic_retries"] == 0
    assert limits["owned_child_wall_seconds_including_imports_bootstrap_solve_and_export"] == 180
    assert limits["direct_DRAT_seconds"] == limits["cold_DRAT_seconds"] == 60
    assert sha(PREP.read_bytes()) == PREP_SHA
    prep = json.loads(PREP.read_bytes())
    assert prep["complete"] and prep["production_solver_calls"] == 0
    assert prep["limits"] == limits and prep["assumptions"] == []
    assert prep["backend"] == "cadical300"
    assert prep["current_checker_on_existing_tiny_proof"]["passed"]
    assert prep["tiny_solver_queries_repeated"] == 0
    assert prep["source_hashes"]["rook_case4_face112_boolean_query.py"] == ledger["new_sha256"]
    assert prep["source_hashes"]["rook_case4_face112_boolean_overlay.py"] == "6e96e8712b1af1bf355de8b69ac2dac358b73e27f8e68c9d500037ab7117d150"
    cold_path = Path(prep["model_cold"])
    if not cold_path.is_absolute():
        cold_path = ROOT/cold_path
    assert sha(cold_path.read_bytes()) == prep["model_cold_sha256"] == "485cf967289bbabd728f7648d8b84cd2bd7fbdfd0492628b9c0ddb9734629fc1"
    cold = json.loads(cold_path.read_bytes())
    assert cold["CNF_sha256"] == prep["CNF_sha256"] == "aa4a35139c75ecb857ed55af73bd20411d267fd20fa6b2593ef16a7485c528ef"
    assert cold["model_sha256"] == prep["model_sha256"]
    overlay_review = LOG/"rook-case4-face112-boolean-independent-review.json"
    assert sha(overlay_review.read_bytes()) == "740a45f4996bb1ff7b8589309856e6f7e9e553697ba44cda3830496c47f607bc"
    report = {
        "status": "PASS: complete query source and proof-acceptance review",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "parent_source": {"path": ledger["parent_path"], "sha256": ledger["parent_sha256"]},
        "subject_source": {"path": ledger["new_path"], "sha256": ledger["new_sha256"]},
        "substitution_ledger_sha256": LEDGER_SHA,
        "query_preparation_sha256": PREP_SHA,
        "overlay_review_sha256": sha(overlay_review.read_bytes()),
        "complete_text_and_AST_substitution_match": True,
        "replacement_occurrences": counts,
        "changed_function_ASTs": changed,
        "unchanged_protected_function_ASTs": protected,
        "limits": limits,
        "review": {
            "scope": "One query of the complete indexed case 4 incidence formula; no candidate, symmetry or positive-pattern assumption is added.",
            "SAT": "The prior full native inspector remains. The selected set must avoid all 112 zeros, meet both parity supports once, meet the 86-column support twice, and use at most one member of pair (259,590).",
            "attribution": "The six boundaries split the exact original, conflict, weighted, cover, prior-unit and new-constraint suffixes. Duplicate input clauses are assigned to their first available family.",
            "timeout": "The unchanged parent watchdog owns the child deadline, persists UNKNOWN and reaps the child. A failed or timed-out child cannot exclude the case.",
            "proof": "Appending a terminal empty clause does not bypass checking. Direct DRAT, exact retained-input inclusion, cold full-formula reconstruction and a second DRAT check are required before exclusion.",
            "resource_bounds": "The unchanged proof-export, memory and file limits refuse oversized results. No fallback solve or automatic retry is present.",
            "cold_scope": "The full original encoder is bound to its published cold certificate; the new cold replay reconstructs the overlay and every new premise.",
        },
        "preparation_and_tiny_checker_records_hash_bound_not_rerun": True,
        "subject_imports": 0,
        "CNF_rebuilds": 0,
        "native_or_domain_censuses": 0,
        "solver_calls": 0,
        "DRAT_calls": 0,
        "case4_excluded": False,
    }
    output = LOG/"rook-case4-face112-boolean-query-independent-review.json"
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
