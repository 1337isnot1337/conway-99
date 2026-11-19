"""Independent artifact-only replay of conditioned native-row exclusions.

No subject import, native library, solver, large cover matrix, or old trace
replay. The small native rows are reconstructed from the frozen original
inventory. Every retained certificate is recomputed in all 1,214 coordinates.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def read(ref):
    path = ROOT/ref["path"]
    raw = path.read_bytes()
    assert sha(raw) == ref["sha256"]
    if "bytes" in ref:
        assert len(raw) == ref["bytes"]
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def integer(value):
    assert type(value) is str
    result = int(value)
    assert str(result) == value
    return result


def original_and_added_rows(data):
    inventory = data["native"]["primary_inventory"]
    result = []

    def add(terms, lower, upper):
        assert type(lower) is type(upper) is int and lower <= upper
        coefficients = {}
        for a, value in terms:
            assert type(a) is type(value) is int and 0 <= a < 1214
            coefficients[a] = coefficients.get(a, 0)+value
        result.append(([[a, v] for a, v in sorted(coefficients.items()) if v], lower, upper))

    for _, _, quota, support in inventory["Gram_rows"]:
        add([(a, 1) for a in support], quota, quota)
    for _, support in inventory["original_signature_rows"]:
        add([(a, 1) for a in support], 0, 1)
    for row in inventory["triple_rows"]:
        add([(a, 1) for a in row["members"]], 0, 1)
    for clause in inventory["Gram_conflict_clauses"]:
        assert len(clause) == 2 and all(type(v) is int and v < 0 for v in clause)
        add([(-v-1, 1) for v in clause], 0, 1)
    for row in inventory["uncapped_integer_cuts"]:
        terms = list(row["positive_terms"])+[[row["target_column"], -row["positive_demand"]]]
        assert row["positive_demand"] > 0 and all(w > 0 for _, w in row["positive_terms"])
        add(terms, 0, sum(w for _, w in row["positive_terms"]))
    assert len(result) == 2271
    base = data["base_model"]
    for support, interval in zip(base["integer_cover_live_original_supports"], base["integer_cover_ranges"]):
        assert interval == [1, 1]
        add([(a, 1) for a in support], *interval)
    for pair in base["added_pair_rows"]:
        add([(a, 1) for a in pair], 0, 1)
    add([(a, 1) for a in base["third_parity_cover_original_support"]], *base["third_parity_cover_range"])
    for row in base["weighted_parity_rows"]:
        add(row["terms"], row["lower"], row["upper"])
    assert len(result) == 2280
    for row in data["full_rows_preparation"]["appended_rows"]:
        add(row["terms"], row["lower"], row["upper"])
    final = data["six_cut_preparation"]["registry"][5]
    assert final["proof_kind"] == "cold_complete_branch_box_capacity"
    row = final["certificate"]["inequality"]
    assert row == {"terms": [[a, 1] for a in (23, 260, 399, 403, 406, 761, 762, 763, 764, 765, 803)], "upper": 1}
    add(row["terms"], 0, row["upper"])
    assert len(result) == 2288
    return result


def domain(config):
    for ref in config["source_bindings"].values():
        path = ROOT/ref["path"]
        assert reference(path) == ref
    assert config["source_bindings"]["cold"] == reference(Path(__file__))
    preparation = read(config["preparation"])
    assert config["specification"] == preparation["specification"]
    spec = read(config["specification"])
    assert spec["source_sha256"] == config["source_bindings"]["helper"]["sha256"]
    assert spec["limits"] == config["limits"] == preparation["limits"]
    assert spec["matrix_sha256"] == preparation["matrix_sha256"] == sha(canonical(spec["matrix"]))
    data = {name: read({"path": p, "sha256": h}) for name, (p, h) in spec["input_bindings"].items()}
    compact, cold, owner = data["boxes"], data["box_cold"], data["box_cold_owner"]
    assert cold["status"] == "PASS" and cold["checked"] == 260
    assert (cold["checked_fixed_points"], cold["checked_contradictions"], cold["checked_partial"]) == (191, 69, 0)
    assert cold["all260_nonpartial_branches_checked"] and cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert owner["exit_code"] == 0 and owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["child_result"]["sha256"] == spec["input_bindings"]["box_cold"][1]
    columns = compact["original_column_ids"]
    zeros = compact["proved_zero_columns"]
    assert len(columns) == 1102 and len(zeros) == 112
    assert columns == sorted(set(range(1214))-set(zeros))
    assert columns == spec["original_column_ids"] and zeros == spec["proved_zero_columns"]
    assert zeros == data["base_model"]["fixed_zero_columns"]
    assert spec["all191_boxes"] == compact["boxes"] and len(compact["boxes"]) == 191
    position = {a: j for j, a in enumerate(columns)}
    rows = original_and_added_rows(data)
    pointers, indices, coefficients = [0], [], []
    for r, (terms, lower, upper) in enumerate(rows):
        encoded = spec["rows"][r]
        assert encoded["row_id"] == r and encoded["original_terms"] == terms
        assert (encoded["lower"], encoded["upper"]) == (lower, upper)
        reduced = [[position[a], v] for a, v in terms if a in position]
        assert encoded["terms"] == reduced
        indices.extend(j for j, v in reduced)
        coefficients.extend(v for j, v in reduced)
        pointers.append(len(indices))
    expected_matrix = {"variables": 1102, "rows": 2288, "row_pointers": pointers,
        "column_indices": indices, "coefficients": coefficients,
        "row_lower": [lo for _, lo, _ in rows], "row_upper": [hi for _, _, hi in rows]}
    assert spec["matrix"] == expected_matrix
    # Independently recover the positive weighted partition, without new branching.
    weights = [0]*1214
    rhs = 0
    for r in (214, 344, 582):
        terms, lower, upper = rows[r]
        assert lower == upper
        rhs += lower
        for a, value in terms:
            weights[a] += value
    assert rhs == 3
    live = {a: weights[a] for a in columns if weights[a]}
    assert Counter(live.values()) == {1: 26, 2: 9, 3: 1}
    selected = []
    proof_refs = {b["index"]: b for b in compact["all260_proof_bindings"]}
    for box in compact["boxes"]:
        assert len(box["state"]) == 1102 and set(box["state"]) <= set("01?")
        assert sha(bytes(255 if s == "?" else int(s) for s in box["state"])) == box["state_sha256"]
        chosen = [a for a in live if box["state"][position[a]] == "1"]
        assert all(box["state"][position[a]] != "?" for a in live)
        assert chosen == box["selected"] and sum(live[a] for a in chosen) == 3
        odd = sum(live[a] % 2 for a in chosen)
        assert odd in (1, 3)
        if odd == 1:
            assert box["kind"] in ("weight3_singleton", "weight1_weight2_pair")
            selected.append({**box, "pilot_index": len(selected), "proof_binding": proof_refs[box["index"]]})
    assert len(selected) == 54 and selected == spec["selected54_boxes"]
    assert [b["index"] for b in selected] == config["selected_whole_cover_indices"]
    return spec, rows


def certificate(proof, specification, rows, branch):
    assert proof["kind"] == "EXACT_CONDITIONED_NATIVE_ROW_EXCLUSION"
    for name, expected in (("pilot_index", branch["pilot_index"]), ("whole_cover_box_index", branch["index"]),
                           ("prior_branch_id", branch["prior_branch_id"]), ("raw_pattern_id", branch["raw_id"]),
                           ("state_sha256", branch["state_sha256"]), ("cold_branch_proof", branch["proof_binding"]),
                           ("matrix_sha256", specification["matrix_sha256"])):
        assert proof[name] == expected
    multipliers = [[r, integer(v)] for r, v in proof["row_multipliers"]]
    assert multipliers == sorted(multipliers) and len({r for r, v in multipliers}) == len(multipliers)
    vector, endpoint = [0]*1214, 0
    for r, value in multipliers:
        assert type(r) is int and 0 <= r < len(rows) and value
        assert abs(value).bit_length() <= specification["limits"]["maximum_exact_integer_bits"]
        terms, lower, upper = rows[r]
        endpoint += value*(upper if value > 0 else lower)
        for a, c in terms:
            vector[a] += value*c
    lower, upper = [0]*1214, [0]*1214
    for a, state in zip(specification["original_column_ids"], branch["state"]):
        lower[a], upper[a] = int(state == "1"), int(state != "0")
    minimum = 0
    for a in range(1214):
        minimum += min(vector[a]*lower[a], vector[a]*upper[a])
    assert minimum > endpoint
    assert [str(v) for v in vector] == proof["full1214_coefficients"]
    assert sha(canonical([lower, upper])) == proof["full1214_bounds_sha256"]
    assert (integer(proof["combined_row_upper"]), integer(proof["minimum_over_entire_box"]), integer(proof["positive_gap"])) == (endpoint, minimum, minimum-endpoint)
    assert proof["conditional_guards"] == branch["selected"]
    assert len(branch["selected"]) in (1, 2) and all(lower[a] == 1 for a in branch["selected"])
    assert proof["implied_Boolean_nogood"] == {"terms": [[a, 1] for a in branch["selected"]], "upper": len(branch["selected"])-1}
    assert proof["case4_excluded"] is False and proof["numerical_ray_feasibility_assumed"] is False
    return {"pilot_index": branch["pilot_index"], "whole_cover_box_index": branch["index"],
            "minimum": str(minimum), "upper": str(endpoint), "gap": str(minimum-endpoint),
            "row_multiplier_count": len(multipliers), "all_original_coordinates_checked": 1214,
            "nogood": proof["implied_Boolean_nogood"]}


def replay(configuration, directory, output):
    started = time.monotonic()
    config = json.loads(configuration.read_bytes())
    config_ref = reference(configuration)
    deadline = started+config["limits"]["cold_seconds"]
    result = {"status": "RUNNING", "configuration": config_ref, "checks": [],
        "exact_exclusions": 0, "completed_native_records": 0, "all54_low_branches_excluded": False,
        "case4_excluded": False, "whole_graph_problem_resolved": False,
        "optimizer_calls": 0, "old_trace_replay_repeated": False, "large_cover_matrix_loaded": False}
    try:
        spec, rows = domain(config)
        owner = json.loads((directory/"forward-owner.json").read_bytes())
        assert owner["child_reaped"]
        result["forward_owner"] = reference(directory/"forward-owner.json")
        path = directory/"forward/records.jsonl"
        raw = path.read_bytes() if path.exists() else b""
        complete, tail = raw.rsplit(b"\n", 1) if b"\n" in raw else (b"", raw)
        refs = [json.loads(line) for line in complete.splitlines() if line]
        assert len(refs) <= 54
        result["incomplete_transcript_tail_bytes"] = len(tail)
        for k, ref in enumerate(refs):
            assert time.monotonic() < deadline
            record = read(ref)
            branch = spec["selected54_boxes"][k]
            assert record["pilot_index"] == k and record["whole_cover_box_index"] == branch["index"]
            assert record["state_sha256"] == branch["state_sha256"]
            native = read(record["numeric"])
            assert native["configuration"] == config_ref and native["pilot_index"] == k
            assert native["whole_cover_box_index"] == branch["index"]
            assert native["matrix_sha256"] == spec["matrix_sha256"] and native["extra_native_calls"] == 0
            lo = [int(v == "1") for v in branch["state"]]
            hi = [int(v != "0") for v in branch["state"]]
            assert native["bounds_reset"] == {"variables_reset": 1102, "whole_cover_box_index": branch["index"],
                "state_sha256": branch["state_sha256"], "lower_upper_sha256": sha(canonical([lo, hi]))}
            assert 0 < native["requested_seconds"] <= config["limits"]["requested_native_seconds_per_branch"]
            assert not native["getDualRay_called"] or native["existing_ray"]
            if record["certificate"] is not None:
                proof = read(record["certificate"])
                assert record["status"] == "EXACT_EXCLUSION_OWNER_CHECKED"
                assert proof["configuration"] == config_ref and proof["specification"] == config["specification"]
                assert proof["numeric"] == record["numeric"]
                checked = certificate(proof, spec, rows, branch)
                result["checks"].append({**checked, "certificate": record["certificate"]})
            else:
                assert record["status"] == "UNRESOLVED"
            result["completed_native_records"] += 1
        terminal_path = directory/"forward/result.json"
        if terminal_path.exists():
            terminal = json.loads(terminal_path.read_bytes())
            assert terminal["configuration"] == config_ref and terminal["source_bindings"] == config["source_bindings"]
            assert terminal["limits"] == config["limits"] and terminal["records"] == refs
            assert len(refs) <= terminal["native_calls"] <= 54
            assert terminal["exact_exclusions"] == len(result["checks"])
            result["forward_terminal"] = reference(terminal_path)
            result["reported_native_calls"] = terminal["native_calls"]
            result["reported_native_seconds"] = terminal["cumulative_native_seconds"]
        result["exact_exclusions"] = len(result["checks"])
        result["all54_low_branches_excluded"] = len(refs) == len(result["checks"]) == 54 and not tail
        result["unresolved_attempted_branches"] = len(refs)-len(result["checks"])
        result["unprocessed_low_branches"] = 54-len(refs)
        result["unqueried_high_branches"] = 137
        result["new_global_zero_columns"] = spec["partition"]["Q"] if result["all54_low_branches_excluded"] else []
        result["status"] = "PASS"
        assert time.monotonic() < deadline
    except Exception as error:
        result.update(status="ERROR_NO_UNCHECKED_PREFIX_ACCEPTED", error_type=type(error).__name__, error=str(error),
                      exact_exclusions=0, all54_low_branches_excluded=False, new_global_zero_columns=[])
    result["seconds"] = time.monotonic()-started
    assert not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical(result)+b"\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.configuration.resolve(), args.directory.resolve(), args.output.resolve())
    print(json.dumps({k: result[k] for k in ("status", "exact_exclusions", "completed_native_records", "seconds")}), flush=True)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
