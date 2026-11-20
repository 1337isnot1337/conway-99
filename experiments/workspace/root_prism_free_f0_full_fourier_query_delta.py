"""Construct and audit the explicit full-Fourier query/replay source delta.

This module imports no subject and constructs no model or solver. Its exact
text ledger includes every binding, dimension, status and budget change.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from pprint import pformat
import re

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "experiments/workspace"
LOGS = ROOT / "experiments/logs/root-prism-free"
OLD_QUERY = WORK / "root_prism_free_f0_character_packing_no_lp_query.py"
OLD_REPLAY = WORK / "root_prism_free_f0_character_packing_no_lp_replay.py"
QUERY = WORK / "root_prism_free_f0_full_fourier_query.py"
REPLAY = WORK / "root_prism_free_f0_full_fourier_replay.py"
OLD_QUERY_SHA = "f3f704371307da14ab035eed1b2a7345bb1725babf0f01cc8e06d5b7e26475e7"
OLD_REPLAY_SHA = "9aad245010f752f26f57566eaa2e3730200898f5f32e242c1ca32b4a98c023e7"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class Delta:
    def __init__(self, text):
        self.text, self.changes = text, []

    def change(self, before, after, count=1):
        assert before != after and self.text.count(before) == count, before[:120]
        self.text = self.text.replace(before, after)
        self.changes.append({"before": before, "after": after, "occurrences": count})

    def all(self, before, after):
        self.change(before, after, self.text.count(before))

    def assignment(self, name, value):
        node = next(n for n in ast.parse(self.text).body if isinstance(n, ast.Assign)
                    and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name)
        old = ast.get_source_segment(self.text, node)
        self.change(old, name + " = " + pformat(value, width=118, sort_dicts=False))


OWNER_BINDING = '''def owner_preparation_binding(path):
    """Bind the small preparation in the owner; full archive checks stay in the worker."""
    raw = path.read_bytes()
    prepared = json.loads(raw)
    assert prepared["status"] == "PASS: full-Fourier literal no-LP query preparation; no optimizer"
    bound = prepared["definition"]
    assert bound["runner_source_sha256"] == file_sha(Path(__file__))
    assert bound["target_proto_sha256"] == TARGET_SHA and bound["initial_proto_sha256"] == INITIAL_SHA
    assert bound["variables"] == VARIABLES and bound["target_constraints"] == 58957
    assert bound["initial_constraints"] == 58840 and bound["external_rows"] == 117
    assert bound["maximum_owned_child_seconds"] == SECONDS
    assert bound["maximum_cumulative_native_solve_seconds"] == NATIVE_SECONDS
    assert prepared["reuse_controls"]["status"] == "PASS"
    assert prepared["optimizer_calls"] == 0 and not prepared["CpSolver_constructed"]
    return prepared, sha(raw)


'''


BUDGET_HELPERS = '''def native_time_budget(deadline, now, used):
    assert all(isfinite(v) for v in (deadline, now, used)) and used >= 0
    return max(0.0, min(NATIVE_SECONDS - used, deadline - now - FINALIZATION_RESERVE))


def native_budget_controls():
    cases = [(1000, 800, 0, 180), (1000, 990, 0, 2),
             (1000, 990, 179.25, 0.75), (1000, 992, 0, 0),
             (1000, 1001, 0, 0), (1000, 100, 180, 0),
             (1000, 100, 181, 0), (1000, 990, 170, 2),
             (1000, 900, 170, 10)]
    for deadline, now, used, expected in cases:
        assert native_time_budget(deadline, now, used) == expected
    rejected = 0
    for used in (-1.0, float("inf"), float("nan")):
        try:
            native_time_budget(1000, 900, used)
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError("invalid cumulative native time accepted")
    return {"status": "PASS", "explicit_deadline_and_cumulative_cases": len(cases),
            "invalid_time_inputs_rejected": rejected, "owned_seconds": SECONDS,
            "cumulative_native_seconds": NATIVE_SECONDS, "optimizer_calls": 0}


'''


def build_query():
    raw = OLD_QUERY.read_bytes()
    assert sha(raw) == OLD_QUERY_SHA
    d = Delta(raw.decode())
    for old, new in [("18444", "32296"), ("34398", "58957"), ("34281", "58840")]:
        assert not any(old in h for h in re.findall(r'"([0-9a-f]{64})"', d.text))
        d.all(old, new)
    d.change("No-LP lightweight exact external-row search on the final Z+Y domain target.",
             "No-LP external-row search on the complete Fourier and literal target.")
    d.change("arithmetic check. One owned180-second budget, at most12 native calls and\n16 exact violated rows per returned vector; no unchanged-prefix retry.",
             "arithmetic check and literal decoder. One owned300-second budget, at most\n180 cumulative native seconds, 12 calls and16 exact violated rows per returned\nvector; no unchanged-prefix retry.")
    d.change("import json\nfrom pathlib import Path", "import json\nfrom math import isfinite\nfrom pathlib import Path")
    tree = ast.parse(d.text)
    old_sources = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
                                       and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "SOURCES"))
    sources = {"prior_no_lp_query": (OLD_QUERY.name, OLD_QUERY_SHA), **old_sources}
    sources["model"] = ("root_prism_free_f0_full_fourier_native_v2.py", "ce21cabaa26e28e69f84380736adb28b7e193037a67a83d0ec79df84230b77ad")
    d.assignment("SOURCES", sources)
    inputs = {
        "prior_no_lp_query_root_review": ("f0-character-packing-no-lp-root-source-review.json", "760b83c211d696d1b22eeb222952696cddf9bb87af2d3ffb19fb8d8765423275"),
        "model_preparation": ("f0-full-fourier-literal-native02/report.json", "d2cc38f284420c461fd191ce4ebfb9dbc16cf6cfd03f8ca1d2e00842bb92e9c4"),
        "model_cold": ("f0-full-fourier-literal-native02-cold/report.json", "5433cc1765e164f6c9df603cb0bfff6c62b5c6779c8f7e5391fff3c8e68a654c"),
        "native_owner": ("f0-full-fourier-literal-native02/owner-result.json", "4e7e66ad3a6b850388076bba218790f3a00f951a8d7a91d82c6a3c5f414ee8f7"),
        "cold_owner": ("f0-full-fourier-literal-native02-cold/owner-result.json", "e08ca2605d0eca0ee8adb12b4b31dabc2c14901b4360f482d4040e93588e162d"),
        "native_v2_root_review": ("f0-full-fourier-native-v2-root-source-review.json", "0ef8d80ba79376fd3fd179857fcade823f2bf5c61f579d3b5a4cb24540191196"),
        "native_root_review": ("f0-full-fourier-native-root-source-review01.json", "2741de4261e7fd3be287eae22dabc3e2a2f1261314043680471c1f13e3746f70"),
        "native_peer_review": ("f0-full-fourier-native-independent-source-review.json", "05c99a3d72b3c5de376dca1ce110e96cbafa443d151318c78046371e9d154329"),
        "plan": ("f0-full-fourier-literal-native02/plan.json.gz", "b7914f80201dc0803faecb5ec1b5e3a405daee6621e2a44021929571573576b9"),
        "target_archive": ("f0-full-fourier-literal-native02/target.pb.gz", "277449dc6d999207fbc77d452d1f351011791b1093cdda7875fc309d972381dd"),
        "initial_archive": ("f0-full-fourier-literal-native02/initial.pb.gz", "3f8833a098695b058a70841757ffb7e20bcb86531027eeef3c55c586ecd5d6ac"),
        "prior_query_controls": ("f0-character-pool-query-preparation01/preparation.json", "6e0812462e4ddb9b1b331d0652edc92d14da75dd4c975eb8dbc5c8cefcd95ba1"),
        "prior_no_lp_preparation": ("f0-character-packing-no-lp-query-preparation01/preparation.json", "123c940a34b590c944316a2fd606e5febcf1cedbdea3ec0f828d41b115068f37"),
    }
    d.assignment("INPUTS", inputs)
    d.assignment("TARGET_SHA", "4e0ec33cb363299a9e199ce33a30a937a85d2f96969965f54833ed38464a911b")
    d.assignment("INITIAL_SHA", "cf4c7cf7cb21087f443f5bdd6f2781a02e13091b7329d7f05fe78820182e179d")
    d.change("SECONDS, MAX_CALLS, MAX_APPEND, FINALIZATION_RESERVE = 180, 12, 16, 8",
             "SECONDS, NATIVE_SECONDS, MAX_CALLS, MAX_APPEND, FINALIZATION_RESERVE = 300, 180, 12, 16, 8")
    d.all("conway99.f0-packing-no-lp-query.v1", "conway99.f0-full-Fourier-literal-no-lp-query.v1")
    d.all("PASS: no-LP lightweight packing-query preparation; no optimizer",
          "PASS: full-Fourier literal no-LP query preparation; no optimizer")
    d.change('"external_rows": 117, "maximum_owned_child_seconds": SECONDS,',
             '"external_rows": 117, "maximum_owned_child_seconds": SECONDS,\n            "maximum_cumulative_native_solve_seconds": NATIVE_SECONDS,')
    d.change('"separate_full_restored_parent_arithmetic_receipt_required": True,',
             '"separate_full_restored_parent_arithmetic_receipt_required": True,\n            "independent_Fourier_literal_decoder_required_before_acceptance": True,\n            "native_budget_overrun_preserves_vector_without_acceptance": True,\n            "owner_avoids_duplicate_archive_hashing_worker_checks_complete_configuration": True,')
    d.change("def reuse_controls():\n", OWNER_BINDING + "def reuse_controls():\n")
    d.change('    native = functions["native_parameters"]\n',
             '    native = functions["native_parameters"]\n    cap_names = [n for n in ast.walk(native) if isinstance(n, ast.Name) and n.id == "NATIVE_SECONDS"]\n    assert len(cap_names) == 1\n    cap_names[0].id = "SECONDS"\n')
    d.change('"native_parameter_delta": "Only explicit linearization_level=0; all old fields unchanged.",',
             '"native_parameter_delta": "No-LP fields unchanged; calls are clipped to the remaining180 native seconds and300 owner seconds.",\n            "native_budget_controls": native_budget_controls(),')
    d.change("    assert 0 < seconds <= SECONDS\n", "    assert 0 < seconds <= NATIVE_SECONDS\n")
    d.change("def worker(preparation_path, directory, deadline):\n", BUDGET_HELPERS + "def worker(preparation_path, directory, deadline):\n")
    d.change('"production_solve_calls": 0, "iterations": [], "added_pool_ids": [],',
             '"production_solve_calls": 0, "iterations": [], "added_pool_ids": [],\n              "maximum_cumulative_native_solve_seconds": NATIVE_SECONDS,\n              "native_solve_wall_seconds": 0.0, "native_budget_overrun_seconds": 0.0,')
    d.change('        added = []\n        result["construction_seconds"]',
             '        added = []\n        native_used = 0.0\n        result["construction_seconds"]')
    d.change('                result["status"] = "UNKNOWN_TOTAL_LIMIT_BEFORE_NEXT_CALL"\n                break\n            step_directory',
             '                result["status"] = "UNKNOWN_TOTAL_LIMIT_BEFORE_NEXT_CALL"\n                break\n            if native_used >= NATIVE_SECONDS:\n                result["status"] = "UNKNOWN_NATIVE_BUDGET_BEFORE_NEXT_CALL"\n                break\n            step_directory')
    d.change("            remaining = deadline - time.monotonic() - FINALIZATION_RESERVE\n",
             "            remaining = native_time_budget(deadline, time.monotonic(), native_used)\n")
    d.change("params = native_parameters(cp_model.cmh, min(SECONDS, remaining))", "params = native_parameters(cp_model.cmh, remaining)")
    d.change('"native_max_time_seconds": min(SECONDS, remaining), "appended_pool_ids": []}',
             '"native_max_time_seconds": remaining, "appended_pool_ids": [],\n                    "native_solve_wall_seconds_before": native_used,\n                    "native_seconds_remaining_before": NATIVE_SECONDS - native_used}')
    d.change('            step["solve_wall_seconds"] = time.monotonic() - call_started\n',
             '            step["solve_wall_seconds"] = time.monotonic() - call_started\n            native_used += step["solve_wall_seconds"]\n            step.update(cumulative_native_solve_wall_seconds=native_used,\n                        native_budget_overrun_seconds=max(0.0, native_used - NATIVE_SECONDS))\n            result.update(native_solve_wall_seconds=native_used,\n                          native_budget_overrun_seconds=step["native_budget_overrun_seconds"])\n')
    d.change('            stage("native_return_and_integer_vector_saved", call_index=call, integer_values=len(point))\n',
             '            save(step_directory / "record.json", step)\n            save(directory / "progress.json", result)\n            stage("native_return_and_integer_vector_saved", call_index=call, integer_values=len(point))\n')
    d.change('            if status.name in ("FEASIBLE", "OPTIMAL"):\n',
             '            if native_used > NATIVE_SECONDS:\n                step["status"] = result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"\n            elif status.name in ("FEASIBLE", "OPTIMAL"):\n')
    d.change('                    elif deadline - time.monotonic() <= FINALIZATION_RESERVE:\n',
             '                    elif native_used >= NATIVE_SECONDS:\n                        step["status"] = result["status"] = "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE"\n                    elif deadline - time.monotonic() <= FINALIZATION_RESERVE:\n')
    d.change('    _, preparation_sha = check_preparation(preparation_path)\n',
             '    _, preparation_sha = owner_preparation_binding(preparation_path)\n')
    d.change('"maximum_owned_child_seconds": SECONDS, "count_feasibility_claimed": False,',
             '"maximum_owned_child_seconds": SECONDS, "maximum_cumulative_native_solve_seconds": NATIVE_SECONDS,\n              "count_feasibility_claimed": False,')
    d.change('                      final_added_pool_ids=child["added_pool_ids"])',
             '                      final_added_pool_ids=child["added_pool_ids"],\n                      native_solve_wall_seconds=child["native_solve_wall_seconds"],\n                      native_budget_overrun_seconds=child["native_budget_overrun_seconds"])')
    d.change('        assert not child["count_feasibility_claimed"]\n',
             '        assert not child["count_feasibility_claimed"]\n        assert child["maximum_cumulative_native_solve_seconds"] == NATIVE_SECONDS\n        if provisional:\n            assert child["native_solve_wall_seconds"] <= NATIVE_SECONDS\n            assert child["native_budget_overrun_seconds"] == 0\n')
    d.change('if __name__ == "__main__":\n    parser',
             'if __name__ == "__main__":\n    if not __debug__:\n        raise RuntimeError("assertions are required")\n    parser')
    compile(d.text, str(QUERY), "exec")
    return d


def build_replay(query_sha):
    raw = OLD_REPLAY.read_bytes()
    assert sha(raw) == OLD_REPLAY_SHA
    d = Delta(raw.decode())
    d.change("import json\nfrom pathlib import Path", "import json\nfrom math import isfinite\nfrom pathlib import Path")
    d.change("import root_prism_free_f0_character_packing_no_lp_query as query", "import root_prism_free_f0_full_fourier_query as query")
    d.assignment("QUERY_SHA", query_sha)
    for old, new in [("18444", "32296"), ("34398", "58957"), ("34281", "58840")]:
        assert not any(old in h for h in re.findall(r'["\']([0-9a-f]{64})["\']', d.text))
        d.all(old, new)
    d.change('    "UNPROVED_NATIVE_INFEASIBLE", "ERROR_NATIVE_MODEL_INVALID", "UNKNOWN_NATIVE_LIMIT",',
             '    "UNPROVED_NATIVE_INFEASIBLE", "ERROR_NATIVE_MODEL_INVALID", "UNKNOWN_NATIVE_LIMIT",\n    "UNKNOWN_NATIVE_BUDGET_OVERRUN", "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE",')
    d.change('assert result["maximum_owned_child_seconds"] == 180 and not result["automatic_retry"]',
             'assert result["maximum_owned_child_seconds"] == 300 and not result["automatic_retry"]\n    assert result["maximum_cumulative_native_solve_seconds"] == query.NATIVE_SECONDS == 180')
    d.change('    prefix_complete = True\n', '    prefix_complete = True\n    native_used = 0.0\n')
    d.change('        assert parameters.max_time_in_seconds == step["native_max_time_seconds"]\n',
             '        assert parameters.max_time_in_seconds == step["native_max_time_seconds"]\n        assert step["native_solve_wall_seconds_before"] == native_used\n        assert step["native_seconds_remaining_before"] == query.NATIVE_SECONDS - native_used\n        assert 0 < parameters.max_time_in_seconds <= query.NATIVE_SECONDS - native_used\n        if "solve_wall_seconds" in step:\n            assert isfinite(step["solve_wall_seconds"]) and step["solve_wall_seconds"] >= 0\n            native_used += step["solve_wall_seconds"]\n            assert step["cumulative_native_solve_wall_seconds"] == native_used\n            assert step["native_budget_overrun_seconds"] == max(0.0, native_used - query.NATIVE_SECONDS)\n')
    d.change('        if response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL):\n',
             '        if step["status"] == "UNKNOWN_NATIVE_BUDGET_OVERRUN":\n            assert native_used > query.NATIVE_SECONDS and call == len(directories) - 1\n            assert not step["appended_pool_ids"]\n            entry["native_budget_overrun_acceptance_not_inferred"] = True\n            if point is not None:\n                pending.append({"call_index": call, "candidate_sha256": files["candidate.json"]["sha256"],\n                                "stage": "native_budget_overrun_saved_only"})\n        elif response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL):\n            assert native_used <= query.NATIVE_SECONDS\n')
    d.change('assert step["status"] in ("UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE", "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE")',
             'assert step["status"] in ("UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE", "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE",\n                                                "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE")\n                    if step["status"] == "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE":\n                        assert native_used >= query.NATIVE_SECONDS')
    d.change('        assert len(child["iterations"]) == child["production_solve_calls"]\n',
             '        assert len(child["iterations"]) == child["production_solve_calls"]\n        assert child["maximum_cumulative_native_solve_seconds"] == query.NATIVE_SECONDS\n        assert child["native_solve_wall_seconds"] == result["native_solve_wall_seconds"] == native_used\n        assert child["native_budget_overrun_seconds"] == result["native_budget_overrun_seconds"] == max(0.0, native_used - query.NATIVE_SECONDS)\n')
    d.change('                  original_parent_acceptance_performed=False,\n',
             '                  original_parent_acceptance_performed=False,\n                  completed_record_native_solve_wall_seconds=native_used,\n                  maximum_cumulative_native_solve_seconds=query.NATIVE_SECONDS,\n                  native_budget_chronology_checked=True,\n                  independent_literal_decoder_performed=False,\n')
    d.change('    _, preparation_sha = query.check_preparation(preparation_path)\n',
             '    _, preparation_sha = query.owner_preparation_binding(preparation_path)\n')
    d.change('if __name__ == "__main__":\n    parser',
             'if __name__ == "__main__":\n    if not __debug__:\n        raise RuntimeError("assertions are required")\n    parser')
    compile(d.text, str(REPLAY), "exec")
    return d


def function_inventory(old, new):
    def functions(text):
        return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
    a, b = functions(old), functions(new)
    return {"unchanged": sorted(k for k in a.keys() & b.keys() if a[k] == b[k]),
            "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
            "added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys())}


def main(write):
    query = build_query()
    query_sha = sha(query.text.encode())
    replay = build_replay(query_sha)
    if write:
        assert not QUERY.exists() and not REPLAY.exists()
        QUERY.write_text(query.text)
        REPLAY.write_text(replay.text)
    else:
        assert QUERY.read_text() == query.text and REPLAY.read_text() == replay.text
    query_inventory = function_inventory(OLD_QUERY.read_text(), query.text)
    replay_inventory = function_inventory(OLD_REPLAY.read_text(), replay.text)
    for name in ("evaluate_proto", "pool_scan", "choose_rows", "native_parameter_controls"):
        assert name in query_inventory["unchanged"]
    report = {"schema": "conway99.f0.full-Fourier-query-complete-delta.v1",
              "status": "PASS: complete text/AST transformation; no subject import or optimizer",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "old_query_sha256": OLD_QUERY_SHA, "query_sha256": query_sha,
              "old_replay_sha256": OLD_REPLAY_SHA, "replay_sha256": sha(replay.text.encode()),
              "query_substitutions": query.changes, "replay_substitutions": replay.changes,
              "query_function_inventory": query_inventory, "replay_function_inventory": replay_inventory,
              "complete_source_bytes_checked": True, "complete_AST_checked": True,
              "actual_native_preparation_and_cold_bound": True,
              "original_117_pool_math_and_integer_evaluators_unchanged": True,
              "owner_seconds": 300, "cumulative_native_seconds": 180,
              "maximum_calls": 12, "maximum_appended_rows_per_candidate": 16,
              "terminal_replay_owner_seconds": 60,
              "new_algorithm_scope": "Cumulative native wall-time clipping and durable accounting; overrun vectors remain saved and unaccepted. Small owner binding replaces duplicate full archive hashing, which remains in the worker.",
              "subject_imports": 0, "native_models_built": 0, "optimizer_calls": 0}
    path = LOGS / "f0-full-fourier-query-reuse-controls.json"
    if write:
        assert not path.exists()
        path.write_bytes(canonical(report) + b"\n")
    else:
        assert json.loads(path.read_bytes()) == report
    print(json.dumps({"status": report["status"], "query_sha256": report["query_sha256"],
                      "replay_sha256": report["replay_sha256"], "control_source_sha256": report["source_sha256"],
                      "report_sha256": sha(path.read_bytes()), "query_inventory": query_inventory,
                      "replay_inventory": replay_inventory}, sort_keys=True))


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    main(parser.parse_args().write)
