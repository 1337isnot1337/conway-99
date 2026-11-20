"""Bounded matching diagnostic for the saved center355 eight-neighbor set.

This examines at most 210 matchings on seven unlocked X vertices. It
never fixes that set in a new free model and never queries another center.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import factorial
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "point": (BASE+"f0-local-center355-pilot01/result.json",
              "691770408d6af35c86cd06004344b51159dbd6ba8ceafd2b185b5764ee37cd0e"),
    "cold": (BASE+"f0-local-center355-pilot01-replay/result.json",
             "d7f61ccc7b2916d545fab07443104fe8d01a9b71368248ed063fb1361730b217"),
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "edge_zeros": (BASE+"f0-edge-motif-census01.json.gz",
                   "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def add_edges(rows, edges):
    result = rows[:]
    for a, b in edges:
        assert a != b and not ((result[a] >> b) & 1)
        result[a] |= 1 << b
        result[b] |= 1 << a
    return result


def cap_violation(rows):
    for a, b in combinations(range(len(rows)), 2):
        common = rows[a] & rows[b]
        if common.bit_count() > 2-((rows[a] >> b) & 1):
            return {"pair": [a, b], "adjacent": (rows[a] >> b) & 1,
                    "common_neighbors": [v for v in range(len(rows)) if (common >> v) & 1]}
    return None


def prism_witness(rows):
    triangles = [t for t in combinations(range(len(rows)), 3)
                 if all((rows[a] >> b) & 1 for a, b in combinations(t, 2))]
    for left, right in combinations(triangles, 2):
        if set(left) & set(right):
            continue
        if (all(sum((rows[a] >> b) & 1 for b in right) == 1 for a in left)
                and all(sum((rows[a] >> b) & 1 for a in left) == 1 for b in right)):
            return {"triangles": [list(left), list(right)],
                    "cross_edges": [[a, b] for a in left for b in right if (rows[a] >> b) & 1]}
    return None


def matchings(vertices, size):
    for edges in combinations(list(combinations(vertices, 2)), size):
        if len({v for edge in edges for v in edge}) == 2*size:
            yield edges


def controls():
    rows = [38, 13, 19, 50, 44, 25]
    assert prism_witness(rows) is not None and cap_violation(rows) is None
    controls = 0
    for order in permutations(range(6)):
        moved = [sum(((rows[order[a]] >> order[b]) & 1) << b for b in range(6)) for a in range(6)]
        assert prism_witness(moved) is not None
        controls += 1
    for a, b in combinations(range(6), 2):
        changed = rows[:]
        changed[a] ^= 1 << b
        changed[b] ^= 1 << a
        assert prism_witness(changed) is None
        controls += 1
    count_controls = 0
    for n in range(8):
        for k in range(n//2+1):
            expected = factorial(n)//(factorial(n-2*k)*2**k*factorial(k))
            assert sum(1 for _ in matchings(list(range(n)), k)) == expected
            count_controls += 1
    return {"literal_prism_label_and_one_edge_toggle_controls": controls,
            "complete_matching_count_controls": count_controls}


def load():
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    point, cold, data = loaded["point"], loaded["cold"], loaded["domain"]["validation"]
    assert point["status"] == "SAT_EXACT_LOCAL_BOOLEAN_NEIGHBOR_WITNESS"
    assert cold["status"] == "PASS: exact SAT local-row and CNF replay"
    assert cold["native_witness"] == point["native_witness"]
    witness = point["native_witness"]
    ids = witness["selected_neighbor_ids"]
    signatures = witness["selected_neighbor_signatures"]
    assert len(ids) == 8 and signatures == [data["triples"][i] for i in ids]
    center_signature = data["triples"][355]
    core = data["core"]
    base = core[:]+[0]*9
    for vertex, signature in enumerate([center_signature]+signatures, start=21):
        for i in signature:
            base[vertex] |= 1 << (i+3)
            base[i+3] |= 1 << vertex
    base = add_edges(base, [(21, v) for v in range(22, 30)])
    assert base == witness["partial_adjacency_rows"] and cap_violation(base) is None
    core_edges = [list(p) for p in combinations(center_signature, 2) if (core[p[0]+3] >> (p[1]+3)) & 1]
    assert core_edges == [[6, 13]]
    locked = [i for i, h in enumerate(signatures) if set(h) & set(center_signature)]
    assert locked == [7] and set(signatures[7]) & set(center_signature) == {11}
    unlocked = [i for i in range(8) if i not in locked]
    assert len(unlocked) == 7
    edge_index = {tuple(pair): i for i, pair in enumerate(data["edges"])}
    ymap = {e: 42+o for o, group in enumerate(data["edge_orbits"]) for e in group}
    zeros = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    return loaded, data, ids, signatures, base, unlocked, edge_index, ymap, zeros


def scope():
    _, _, ids, _, base, unlocked, _, _, _ = load()
    return {"schema": "conway99.f0-center355-saved-matching-scope.v1",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "selected_neighbor_ids": ids, "unlocked_local_X_indices": unlocked,
            "locked_local_X_indices": [7], "locked_core_site": 11,
            "core_neighbor_internal_edge": [6, 13],
            "required_internal_X_matching_sizes": [2, 3],
            "all_unlocked_pairs": 21, "maximum_two_edge_matchings": 105,
            "maximum_three_edge_matchings": 105, "maximum_matching_cases": 210,
            "visible_vertices": len(base), "cap_pairs": 435,
            "maximum_seconds": 10, "scope": "Saved eight-neighbor set only; no whole-center exclusion.",
            "controls": controls(), "production_diagnostic_executed": False, "optimizer_calls": 0}


def diagnose(deadline, completed):
    _, data, ids, signatures, base, unlocked, edge_index, ymap, zeros = load()
    initial_prism = prism_witness(base)
    edge_records = []
    for a, c in combinations(unlocked, 2):
        pair = tuple(sorted((ids[a], ids[c])))
        reason = None
        evidence = None
        single_edge_prism = None
        if set(signatures[a]) & set(signatures[c]):
            reason = "shared_core_site_already_has_center_as_common_neighbor"
        elif pair not in edge_index:
            reason = "outside_edge_not_eligible_in_frozen_domain"
        elif ymap[edge_index[pair]] in zeros:
            reason = "certified_zero_edge"
        else:
            proposed = add_edges(base, [(22+a, 22+c)])
            evidence = cap_violation(proposed)
            if evidence is not None:
                reason = "visible_common_neighbor_cap"
            else:
                # An induced prism is not an upward-monotone obstruction:
                # later edges might add a chord. Record this observation,
                # but test prism absence only after the whole matching.
                single_edge_prism = prism_witness(proposed)
        edge_records.append({"local_pair": [a, c], "signature_pair": list(pair),
                             "admissible": reason is None, "reason": reason, "evidence": evidence,
                             "single_edge_prism_not_used_to_prune": single_edge_prism})
    admissible = {tuple(r["local_pair"]) for r in edge_records if r["admissible"]}
    successes, counts = [], Counter()
    for size in (2, 3):
        for matching in matchings(unlocked, size):
            if time.monotonic() >= deadline:
                raise TimeoutError("bounded saved-neighbor matching diagnostic")
            rejected = next((list(edge) for edge in matching if edge not in admissible), None)
            if rejected is not None:
                record = {"matching": [list(e) for e in matching], "status": "REJECTED_SINGLE_EDGE",
                          "rejected_edge": rejected}
            else:
                proposed = add_edges(base, [(22+a, 22+c) for a, c in matching])
                cap, prism = cap_violation(proposed), prism_witness(proposed)
                if cap is not None or prism is not None:
                    record = {"matching": [list(e) for e in matching], "status": "REJECTED_JOINT_VISIBLE_CONSTRAINT",
                              "cap": cap, "prism": prism}
                else:
                    neighbors = [v for v in range(30) if (proposed[21] >> v) & 1]
                    degrees = [sum((proposed[v] >> w) & 1 for w in neighbors) for v in neighbors]
                    assert all(d <= 1 for d in degrees)
                    assert sum(d == 0 for d in degrees) == 7-2*size
                    record = {"matching": [list(e) for e in matching], "status": "PASS_VISIBLE_MATCHING",
                              "unmatched_X_count": 7-2*size}
                    successes.append(record)
            completed.append(record)
            counts[str(size)+"_"+record["status"]] += 1
    assert len(completed) == 210
    return {"status": "COMPLETE_SAVED_NEIGHBOR_MATCHING_DIAGNOSTIC",
            "edge_dispositions": edge_records, "matching_dispositions": completed,
            "counts": dict(counts), "passing_matchings": successes,
            "base_has_no_visible_prism": initial_prism is None,
            "base_prism_witness": initial_prism, "all210_matchings_covered": True,
            "single_edge_prisms_never_prune_a_full_matching": True,
            "center355_excluded": False, "global_graph_completion_claimed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "diagnose"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    assert 0 < args.seconds <= 10
    if args.mode == "prepare":
        assert not args.preparation.exists()
        result = scope()
        args.preparation.write_bytes(canonical(result)+b"\n")
        print(json.dumps({"status": "PREPARED: no matching diagnostic",
                          "source_sha256": result["source_sha256"],
                          "preparation_sha256": sha(args.preparation.read_bytes()),
                          "maximum_matching_cases": 210, "controls": result["controls"]}, indent=2))
        return
    assert args.output is not None and not args.output.exists()
    prepared = json.loads(args.preparation.read_bytes())
    assert prepared == scope()
    started = time.monotonic()
    completed = []
    try:
        result = diagnose(started+args.seconds, completed)
    except Exception as error:
        result = {"status": "INCOMPLETE_NO_COMPLETE_DIAGNOSTIC_CLAIM",
                  "error_type": type(error).__name__, "message": str(error),
                  "completed_matching_records": completed}
        raise
    finally:
        result["source_sha256"] = sha(Path(__file__).read_bytes())
        result["preparation_sha256"] = sha(args.preparation.read_bytes())
        result["seconds"] = time.monotonic()-started
        result["optimizer_calls"] = 0
        args.output.write_text(json.dumps(result, indent=2)+"\n")
        print(json.dumps({k: v for k, v in result.items()
                          if k not in ("edge_dispositions", "matching_dispositions", "passing_matchings",
                                       "completed_matching_records")}, indent=2))


if __name__ == "__main__":
    main()
