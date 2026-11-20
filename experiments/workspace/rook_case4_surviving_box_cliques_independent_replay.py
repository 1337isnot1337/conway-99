"""Set-based pair reconstruction and independent NetworkX clique enumeration."""
from collections import Counter
import gzip
import hashlib
import inspect
from itertools import combinations
import json
from pathlib import Path
import sys
import time

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
PAIR = (BASE + "rook-case4-surviving-box-pair-scan01.json.gz",
        "19d96dd0af3ebaaab33c88456872883f5a51afea53ce3c9d0d57d6e6e0ccdadc")
CLIQUES = (BASE + "rook-case4-surviving-box-cliques01.json.gz",
           "6cbfb897f5c80ee49ac2c9750195a9b4c03a1a578230c3c5a1ffda4d31387338")
KNOWN_CAPACITY = [23, 260, 399, 403, 406, 761, 762, 763, 764, 765, 803]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(binding):
    name, digest = binding
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == digest
    if name.endswith(".py"):
        return None
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def replay():
    started = time.monotonic()
    pair, clique_record = read(PAIR), read(CLIQUES)
    data = {key: read(binding) for key, binding in pair["inputs"].items()}
    boxes, accepted, owner = data["boxes"], data["replay"], data["owner"]
    assert accepted["status"] == "PASS_INDEPENDENT_H27_LOW_FACE_CUT_AND_CAPACITY_EQUIVALENCE"
    assert accepted["all260_cold_record_bindings_checked"]
    assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
    assert owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["independent-replay.json"]["sha256"] == pair["inputs"]["replay"][1]
    ids = boxes["original_column_ids"]
    states = boxes["boxes"]
    assert len(ids) == 1102 and len(states) == 191
    assert ids == sorted(set(range(1214)) - set(boxes["proved_zero_columns"]))
    assert ids == pair["original_column_ids"]
    assert pair["box_order"] == [item["index"] for item in states]
    assert len(set(pair["box_order"])) == 191
    for item in states:
        state = item["state"]
        assert len(state) == 1102 and set(state) <= set("01?")
        assert sha(bytes(255 if c == "?" else int(c) for c in state)) == item["state_sha256"]
    possible = [{k for k, item in enumerate(states) if item["state"][j] != "0"} for j in range(1102)]
    forced = [{k for k, item in enumerate(states) if item["state"][j] == "1"} for j in range(1102)]
    assert all(possible) and all(len(s) < 191 for s in forced)
    assert [hex(sum(1 << k for k in s)) for s in possible] == pair["possible_box_masks_hex"]
    assert [hex(sum(1 << k for k in s)) for s in forced] == pair["forced_one_box_masks_hex"]
    edges = [[ids[i], ids[j]] for i, j in combinations(range(1102), 2) if possible[i].isdisjoint(possible[j])]
    implications = [[ids[i], ids[j]] for i in range(1102) for j in range(1102)
                    if i != j and possible[i].issubset(forced[j])]
    assert edges == pair["conflicts"] and len(edges) == pair["conflict_count"] == 2855
    assert implications == pair["implications"] == [] and pair["implication_count"] == 0
    assert pair["unordered_pairs_checked"] == 606651 and pair["ordered_distinct_pairs_checked"] == 1213302
    graph = nx.Graph()
    graph.add_edges_from(edges)
    assert graph.number_of_nodes() == clique_record["active_conflict_vertices"] == 665
    assert graph.number_of_edges() == clique_record["conflict_edges"] == 2855
    supports = sorted(tuple(sorted(c)) for c in nx.find_cliques(graph))
    assert len(supports) == len(set(supports)) == 1216
    assert supports == [tuple(item["support"]) for item in clique_record["maximal_cliques"]]
    point = data["point"]
    assert data["point_cold"]["exact_point_replayed"]
    assert data["point_cold"]["candidate_sha256"] == pair["inputs"]["point"][1]
    nums = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    denominator = int(point["common_denominator"])
    assert len(nums) == 1214 and denominator == 3461944222
    assert pair["violated_conflicts"] == [[a, b, str(nums[a] + nums[b] - denominator)]
                                          for a, b in edges if nums[a] + nums[b] > denominator] == []
    assert pair["violated_implications"] == []
    positions = {a: i for i, a in enumerate(ids)}
    violations, capacities = [], 0
    for support, saved in zip(supports, clique_record["maximal_cliques"]):
        assert len(support) >= 2
        assert all(graph.has_edge(a, b) for a, b in combinations(support, 2))
        assert not any(all(graph.has_edge(a, b) for a in support) for b in graph if b not in support)
        maxima = [sum(item["state"][positions[a]] != "0" for a in support) for item in states]
        assert max(maxima) <= 1 and maxima == saved["all191_box_maxima"]
        excess = sum(nums[a] for a in support) - denominator
        assert saved["upper"] == 1 and saved["current_point_excess_numerator"] == str(excess)
        capacities += len(maxima)
        if excess > 0:
            violations.append(saved)
    assert violations == clique_record["violated_cliques"] and len(violations) == 1
    assert violations[0]["support"] == KNOWN_CAPACITY
    assert violations[0]["current_point_excess_numerator"] == "37621464"
    assert {str(k): v for k, v in sorted(Counter(map(len, supports)).items())} == clique_record["size_histogram"]
    assert clique_record["status"] == "COMPLETE_MAXIMAL_CLIQUE_ENUMERATION"
    assert time.monotonic() - started < 60
    return {"status": "PASS_INDEPENDENT_SETS_PAIRS_AND_ALL_MAXIMAL_CLIQUES",
            "source_sha256": sha(Path(__file__).read_bytes()), "pair_certificate": PAIR,
            "clique_certificate": CLIQUES, "networkx_version": nx.__version__,
            "networkx_find_cliques_source_sha256": sha(inspect.getsource(nx.find_cliques).encode()),
            "possible_and_forced_coordinate_sets_checked": 1102, "boxes": 191,
            "unordered_pairs_checked": 606651, "ordered_distinct_pairs_checked": 1213302,
            "conflicts": 2855, "implications": 0, "active_conflict_vertices": 665,
            "maximal_cliques": 1216, "box_capacities_checked": capacities,
            "size_histogram": clique_record["size_histogram"],
            "violated_cliques": [{"support": KNOWN_CAPACITY, "excess_numerator": "37621464"}],
            "new_violated_clique_beyond_known_capacity": False,
            "producer_imports": 0, "optimizer_calls": 0, "propagation_replays": 0,
            "case4_excluded": False, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    assert __debug__ and len(sys.argv) == 2
    output = Path(sys.argv[1])
    result = replay()
    with output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "sha256": sha(output.read_bytes()),
                      "seconds": result["seconds"]}, sort_keys=True))
