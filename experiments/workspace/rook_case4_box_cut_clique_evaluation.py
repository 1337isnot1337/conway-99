"""Evaluate the frozen 1,216 box cliques at the accepted six-cut point.

This performs integer contractions only.  The clique proof and the full point
inspection are reused through their exact, independently accepted bindings.
No model, optimizer, branch propagation, or clique search is repeated.
"""

import gzip
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "point": (BASE + "rook-case4-box-cut-lp-run01/exact/candidate.json",
              "7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9"),
    "point_cold": (BASE + "rook-case4-box-cut-lp-run01/exact/cold.json",
                   "b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317"),
    "terminal": (BASE + "rook-case4-box-cut-lp-run01/result.json",
                 "3785d201b021eb8347c123c536830a46f8533cb4127c74d7710f8f21814e2190"),
    "terminal_bindings": (BASE + "rook-case4-box-cut-lp-run01-bindings.json",
                          "3788903bb955677532e40ca5d4c3b18609e162ad367ddae7bf57bd03e3c3dc57"),
    "cliques": (BASE + "rook-case4-surviving-box-cliques01.json.gz",
                "6cbfb897f5c80ee49ac2c9750195a9b4c03a1a578230c3c5a1ffda4d31387338"),
    "cliques_independent_replay": (
        BASE + "rook-case4-surviving-box-cliques-independent-replay01.json",
        "4d463e8997bc788408daa49e23b9b734662d02231d3f6dd1a1d378ffe90d8e7e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(binding):
    name, digest = binding
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == digest, name
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def integer(value):
    assert type(value) in (int, str)
    if type(value) is str:
        assert value and value.lstrip("-").isdigit()
    return int(value)


def evaluate():
    started = time.monotonic()
    data = {key: read(binding) for key, binding in INPUTS.items()}
    point, cold = data["point"], data["point_cold"]
    terminal, bindings = data["terminal"], data["terminal_bindings"]
    assert terminal["status"] == "EXACT_SIX_CUT_POSITIVE_SELECTOR_POINT"
    assert terminal["latest_point_accepted_cuts"] == 6
    assert terminal["latest_exact_point"] == {
        "candidate": {"path": INPUTS["point"][0], "sha256": INPUTS["point"][1]},
        "cold": {"path": INPUTS["point_cold"][0], "sha256": INPUTS["point_cold"][1]},
    }
    assert bindings["status"] == "PASS_SIX_CUT_TERMINAL_BINDINGS"
    assert cold["exact_point_replayed"] and cold["candidate_sha256"] == INPUTS["point"][1]
    assert cold["registry_sha256"] == point["registry_sha256"]
    assert cold["full_face_rows_checked"] == 167121
    check = point["exact_check"]
    assert check["point_key"] == cold["point_key"]
    assert check["original_native_rows_checked"] == 2271
    assert check["original_coordinate_covers_checked"] == 178533
    assert check["appended_signed_parity_rows_checked"] == 5
    assert check["appended_box_cover_rows_checked"] == 1
    denominator = integer(point["common_denominator"])
    nums = list(map(integer, check["original1214_selector_numerators"]))
    floor = integer(check["t_numerator"])
    assert denominator == 2594289631 and floor == 28189330
    assert len(nums) == 1214 and all(0 <= n <= denominator for n in nums)
    assert sum(n == 0 for n in nums) == 112
    assert sum(n > 0 for n in nums) == 1102 and min(n for n in nums if n) >= floor > 0

    family, replay = data["cliques"], data["cliques_independent_replay"]
    assert replay["status"] == "PASS_INDEPENDENT_SETS_PAIRS_AND_ALL_MAXIMAL_CLIQUES"
    assert replay["clique_certificate"] == list(INPUTS["cliques"])
    assert replay["maximal_cliques"] == 1216 and replay["boxes"] == 191
    assert replay["box_capacities_checked"] == 1216 * 191
    assert family["status"] == "COMPLETE_MAXIMAL_CLIQUE_ENUMERATION"
    rows = family["maximal_cliques"]
    assert len(rows) == 1216
    supports = [tuple(row["support"]) for row in rows]
    assert supports == sorted(set(supports))
    evaluations = []
    for index, row in enumerate(rows):
        support = row["support"]
        assert 2 <= len(support) <= 18 and support == sorted(set(support))
        assert all(type(j) is int and 0 <= j < 1214 for j in support)
        assert row["upper"] == 1
        value = sum(nums[j] for j in support)
        evaluations.append({"index": index, "support": support,
                            "value_numerator": str(value),
                            "slack_numerator": str(denominator - value)})
    violated = [row for row in evaluations if integer(row["slack_numerator"]) < 0]
    tight = [row["index"] for row in evaluations if integer(row["slack_numerator"]) == 0]
    assert time.monotonic() - started < 10
    return {
        "schema": "conway99.rook-case4.six-cut-point-clique-evaluation.v1",
        "status": "EXACT_FROZEN_CLIQUE_FAMILY_EVALUATED",
        "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
        "common_denominator": str(denominator), "t_numerator": str(floor),
        "point_key": check["point_key"], "rows_checked": len(evaluations),
        "all_rows_satisfied": not violated, "violated_rows": violated,
        "tight_row_indices": tight,
        "minimum_slack_numerator": str(min(integer(row["slack_numerator"]) for row in evaluations)),
        "evaluations": evaluations, "seconds": time.monotonic() - started,
        "optimizer_calls": 0, "model_builds": 0, "propagation_replays": 0,
        "clique_searches": 0, "new_clique_completeness_claim": False,
        "boolean_incidence_or_graph_claimed": False, "case4_excluded": False,
    }


if __name__ == "__main__":
    assert __debug__ and len(sys.argv) == 2
    output = Path(sys.argv[1])
    result = evaluate()
    with output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "rows": result["rows_checked"],
                      "violations": len(result["violated_rows"]),
                      "tight_rows": len(result["tight_row_indices"]),
                      "minimum_slack_numerator": result["minimum_slack_numerator"],
                      "sha256": sha(output.read_bytes()), "seconds": result["seconds"]}))
