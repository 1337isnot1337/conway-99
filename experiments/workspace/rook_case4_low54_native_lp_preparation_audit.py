"""Independent small-domain preparation audit and certificate tamper controls."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import time

import rook_case4_low54_native_lp as exact
import rook_case4_low54_native_lp_query as query
import rook_case4_low54_native_lp_replay as cold

ROOT = exact.ROOT
SOURCES = {
    "helper": (Path(exact.__file__), "174c084dc9df3e3e0eed5e028ad18b6c89957c51b4ddfe7c0e4bbeaaa70d5380"),
    "query": (Path(query.__file__), "7f3f3db6422932def93ef9b9efa52415a1499d8d0675c48c776d3318f74bfa13"),
    "cold": (Path(cold.__file__), "12906b10154ea48871ee659fb4553a7aa9c5d28846d2a5e124c152d557dfb144"),
}
PREPARATION = ROOT/exact.LOGS/"rook-case4-low54-native-lp-preparation02/preparation.json"
PREPARATION_SHA = "a2b840b62891ff7f562e21138bcbd60b589677bc106db77e49b90be23f60eee4"


def run(output):
    started = time.monotonic()
    for path, digest in SOURCES.values():
        assert exact.sha(path.read_bytes()) == digest
    assert exact.sha(PREPARATION.read_bytes()) == PREPARATION_SHA
    prep, spec = exact.load(PREPARATION)
    config = {
        "source_bindings": query.bindings(), "preparation": exact.reference(PREPARATION),
        "specification": prep["specification"], "limits": exact.LIMITS,
        "selected_whole_cover_indices": [b["index"] for b in spec["selected54_boxes"]],
    }
    independently_rebuilt, rows = cold.domain(config)
    assert independently_rebuilt == spec and len(rows) == 2288
    old_path = ROOT/"experiments/workspace/rook_case4_complete_lp_recovery.py"
    old_tree, new_tree = ast.parse(old_path.read_text()), ast.parse(Path(exact.__file__).read_text())
    reuse = {}
    for name in ("normalize_row", "original_rows"):
        old = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        new = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        a, b = ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False)
        assert a == b
        reuse[name] = exact.sha(a.encode())
    accepted, rejected, gaps = 0, 0, []
    controls = [
        ([[0, 1], [1150, 1]], 0, 0, 1),
        ([[0, 2], [1150, -3]], 3, 4, -1),
        ([[0, 2], [1, -1], [2, 1], [1150, 3]], -2, 0, 1),
    ]
    for full_terms, lower, upper, multiplier in controls:
        state = "1"+"?"*1101
        branch = {"pilot_index": 0, "index": 0, "prior_branch_id": 0, "raw_id": 0,
                  "selected": [0], "state": state,
                  "state_sha256": exact.sha(bytes([1]+[255]*1101)),
                  "proof_binding": {"scope": "artificial control only"}}
        row = {"terms": [[a, c] for a, c in full_terms if a < 1102],
               "original_terms": full_terms, "lower": lower, "upper": upper}
        toy = {"rows": [row], "original_column_ids": list(range(1102)),
               "selected54_boxes": [branch], "limits": exact.LIMITS,
               "matrix_sha256": exact.sha(exact.canonical(row))}
        proof = exact.exclusion(toy, 0, [[0, multiplier]])
        assert proof is not None and int(proof["full1214_coefficients"][1150]) != 0
        check = cold.certificate(proof, toy, [(full_terms, lower, upper)], branch)
        gaps.append(check["gap"]); accepted += 1
        bads = []
        bad = copy.deepcopy(proof); bad["positive_gap"] = "0"; bads.append(bad)
        bad = copy.deepcopy(proof); bad["full1214_coefficients"][1150] = "0"; bads.append(bad)
        bad = copy.deepcopy(proof); bad["conditional_guards"] = [1]; bads.append(bad)
        bad = copy.deepcopy(proof); bad["row_multipliers"][0][1] = str(-multiplier); bads.append(bad)
        bad = copy.deepcopy(proof); bad["row_multipliers"].append(bad["row_multipliers"][0][:]); bads.append(bad)
        bad = copy.deepcopy(proof); bad["minimum_over_entire_box"] = str(int(bad["minimum_over_entire_box"])+1); bads.append(bad)
        for bad in bads:
            try:
                cold.certificate(bad, toy, [(full_terms, lower, upper)], branch)
            except AssertionError:
                rejected += 1
            else:
                raise AssertionError("tampered certificate passed independent replay")
    assert accepted == 3 and rejected == 18
    result = {
        "status": "PASS_INDEPENDENT_SMALL_MODEL_AND_CERTIFICATE_CONTROLS",
        "source": exact.reference(Path(__file__)),
        "source_bindings": {name: exact.reference(path) for name, (path, _) in SOURCES.items()},
        "preparation": exact.reference(PREPARATION), "specification": prep["specification"],
        "matrix_sha256": spec["matrix_sha256"], "all2288_rows_reconstructed": True,
        "all26266_reduced_coefficients_checked": True, "original_coordinates": 1214,
        "complete191_boxes_and54_low_mapping_checked": True,
        "original_row_source": exact.reference(old_path), "unchanged_function_AST_hashes": reuse,
        "full_original_zero_coordinate_lift_controls": accepted,
        "positive_and_negative_row_multiplier_gaps": gaps,
        "tampered_certificate_rejections": rejected,
        "optimizer_calls": 0, "native_library_imported": False,
        "old_trace_or_full_cover_replay": False, "seconds": time.monotonic()-started,
    }
    assert result["seconds"] < 60
    exact.write(output, result)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output.resolve())
    print(json.dumps({k: result[k] for k in ("status", "tampered_certificate_rejections", "seconds")}), flush=True)
