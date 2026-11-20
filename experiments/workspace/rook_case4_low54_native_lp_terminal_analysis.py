"""Artifact-only low54 terminal binding audit and four-pair point contraction.

No subject import, native API, row recomputation, old trace replay or optimizer.
The accepted cold arithmetic receipt remains the source of branch exclusions.
"""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import struct
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "experiments/logs/grids-and-triangles"
RUN = LOG / "rook-case4-low54-native-lp-run01"
EXPECTED = {
    "terminal": ("rook-case4-low54-native-lp-run01/result.json", "63b8274dfdfd9cabe55155ab3fb2a8f1d9670dc2dd2c927d048bda1ed0ccce15"),
    "cold": ("rook-case4-low54-native-lp-run01/cold.json", "ea492ec530c512759b93d25afc6900a2468d1f221f75aac2eb39092bd8af73f3"),
    "config": ("rook-case4-low54-native-lp-query-configuration01.json", "a0ac53ac6969ceeaaeedd2fabfa38d8944dd856c85bb461113a70cd92784c272"),
    "gate": ("rook-case4-low54-native-lp-root-gate01.json", "5da4b8f59a0073c64775db4ebd0e4735fcd16ddb2e8c1ab024949854ed063a5d"),
    "spec": ("rook-case4-low54-native-lp-preparation02/specification.json.gz", "b037035bb6756bcb259cc06fc6ae22781f343fedeb38c8ec923dcb19fdb50164"),
    "point": ("rook-case4-box-cut-lp-run01/exact/candidate.json", "7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9"),
    "point_cold": ("rook-case4-box-cut-lp-run01/exact/cold.json", "b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(path):
    b = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(b), "sha256": digest(b)}


def main():
    started = time.monotonic()
    objects, bindings, checked = {}, {}, {}
    for name, (path, expected) in EXPECTED.items():
        p = LOG/path
        raw = p.read_bytes()
        assert digest(raw) == expected
        bindings[name] = ref(p)
        objects[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)

    def check_refs(value):
        if isinstance(value, dict):
            if {"path", "sha256", "bytes"} <= value.keys():
                p = (ROOT/value["path"]).resolve()
                assert p.is_relative_to(ROOT)
                actual = checked.setdefault(str(p), ref(p))
                assert actual == {k: value[k] for k in ("path", "bytes", "sha256")}
            for x in value.values():
                check_refs(x)
        elif isinstance(value, list):
            for x in value:
                check_refs(x)

    for p in sorted(RUN.rglob("*.json")):
        check_refs(json.loads(p.read_bytes()))
    check_refs(objects["config"])
    check_refs(objects["gate"])
    terminal, cold = objects["terminal"], objects["cold"]
    assert terminal["status"] == "ACCEPTED_EXACT_PREFIX" and cold["status"] == "PASS"
    assert not terminal["all54_low_branches_excluded"] and not terminal["case4_excluded"]
    for name in ("forward-owner.json", "cold-owner.json"):
        o = json.loads((RUN/name).read_bytes())
        assert o["exit_code"] == 0 and o["child_reaped"] and not o["hard_timeout"]
        assert o["seconds"] <= o["hard_seconds"]

    forward = json.loads((RUN/"forward/result.json").read_bytes())
    assert forward["native_calls"] == len(forward["records"]) == 54
    assert cold["completed_native_records"] == 54 and cold["unprocessed_low_branches"] == 0
    assert cold["unqueried_high_branches"] == 137 and not cold["new_global_zero_columns"]
    numerical = []
    unresolved, excluded = [], []
    for k, record_ref in enumerate(forward["records"]):
        record = json.loads((ROOT/record_ref["path"]).read_bytes())
        numeric = json.loads((ROOT/record["numeric"]["path"]).read_bytes())
        assert numeric["pilot_index"] == record["pilot_index"] == k
        assert numeric["extra_native_calls"] == 0
        assert not numeric["getDualRay_called"] or numeric["existing_ray"]
        assert numeric["native_seconds"] <= 2.0
        numerical.append(numeric)
        if record["status"] == "UNRESOLVED":
            unresolved.append(numeric["whole_cover_box_index"])
        else:
            assert record["status"] == "EXACT_EXCLUSION_OWNER_CHECKED"
            excluded.append(numeric["whole_cover_box_index"])
    assert len(excluded) == len(cold["checks"]) == terminal["exact_exclusions"] == 4
    assert len(unresolved) == 50
    assert all(x["numerically_optimal"] for x in numerical if x["whole_cover_box_index"] in unresolved)

    point, point_cold, spec = objects["point"], objects["point_cold"], objects["spec"]
    assert point_cold["exact_point_replayed"]
    assert point_cold["candidate_sha256"] == bindings["point"]["sha256"]
    assert spec["latest_point_sha256"] == bindings["point"]["sha256"]
    ids = spec["original_column_ids"]
    assert len(ids) == len(set(ids)) == 1102
    assert digest(struct.pack("<"+"H"*len(ids), *ids)) == point["matrix_binding"]["original_column_ids"]["sha256"]
    d = int(point["common_denominator"])
    live = list(map(int, point["extended_numerators"]))
    assert d > 0 and len(live) == 1103 and all(0 <= x <= d for x in live)
    full = [0]*1214
    for j, v in zip(ids, live[:-1]):
        full[j] = v
    assert full == list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    assert all(full[j] == 0 for j in spec["proved_zero_columns"])

    pairs = []
    for proof in cold["checks"]:
        terms, upper = proof["nogood"]["terms"], proof["nogood"]["upper"]
        assert len(terms) == 2 and all(c == 1 for j, c in terms) and upper == 1
        lhs = sum(c*full[j] for j, c in terms)
        slack = upper*d-lhs
        pairs.append({"whole_cover_box_index": proof["whole_cover_box_index"],
            "terms": terms, "upper": upper, "point_lhs_numerator": str(lhs),
            "point_slack_numerator": str(slack), "point_denominator": str(d),
            "point_violated": slack < 0, "exact_branch_gap": proof["gap"],
            "certificate": proof["certificate"]})

    report = {"status": "PASS_TERMINAL_BINDINGS_AND_EXACT_FOUR_PAIR_CONTRACTION",
        "source": ref(Path(__file__)), "inputs": bindings,
        "current_artifact_references_checked": len(checked),
        "all54_native_calls": 54, "numerical_status_counts": dict(collections.Counter(x["model_status"] for x in numerical)),
        "all_unexcluded50_numerically_optimal": True,
        "unexcluded_whole_cover_indices": unresolved,
        "excluded_whole_cover_indices": excluded, "four_pair_inequalities": pairs,
        "point_rejected_by_any_pair": any(x["point_violated"] for x in pairs),
        "cumulative_native_seconds": forward["cumulative_native_seconds"],
        "maximum_single_native_seconds": max(x["native_seconds"] for x in numerical),
        "remaining_whole_case_boxes": 191-len(excluded),
        "new_global_zero_columns": [], "case4_excluded": False,
        "full_model_feasibility_of_unexcluded_boxes_claimed": False,
        "native_calls_in_this_audit": 0, "old_trace_or_row_replay_repeated": False,
        "seconds": time.monotonic()-started}
    output = LOG/"rook-case4-low54-native-lp-run01-analysis.json"
    assert not output.exists()
    output.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "report": ref(output),
        "pair_point_slacks": [x["point_slack_numerator"] for x in pairs],
        "point_denominator": str(d), "numeric_status_counts": report["numerical_status_counts"]}))


if __name__ == "__main__":
    main()

