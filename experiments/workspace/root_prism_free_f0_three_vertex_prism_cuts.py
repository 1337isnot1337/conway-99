"""Prepare mixed Y/Z cuts from three exterior vertices and one prism edge.

If y_ab and z_c together force a visible prism, then
y_ab+Z_ac<=x_a and y_ab+Z_bc<=x_b. All68394 eligible edges are scanned;
the known162 zero edge orbits and389 zero pair orbits are accounted for.
No numerical point or optimizer is accessed.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "reduction": (BASE+"f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "edge_zeros": (BASE+"f0-edge-motif-census01.json.gz", "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def pair_id(a, b):
    assert a != b
    a, b = sorted((a, b))
    return a*(959-a)//2+b-a-1


def literal_prism(core, triples, a, b, c, u, v, w):
    rows = core[:]+[0, 0, 0]
    for vertex, signature in ((21, triples[a]), (22, triples[b]), (23, triples[c])):
        for j in signature:
            rows[vertex] |= 1 << (j+3); rows[j+3] |= 1 << vertex
    rows[21] |= 1 << 22; rows[22] |= 1 << 21
    sites = [21, 22, u+3, 23, v+3, w+3]
    small = [sum(((rows[x] >> y) & 1) << j for j, y in enumerate(sites)) for x in sites]
    assert len(set(sites)) == 6 and all(row.bit_count() == 3 for row in small)
    assert all((small[i] >> j) & 1 for side in (range(3), range(3, 6)) for i in side for j in side if i != j)
    assert all(sum((small[i] >> j) & 1 for j in range(3, 6)) == 1 for i in range(3))
    assert all(sum((small[i] >> j) & 1 for j in range(3)) == 1 for i in range(3, 6))
    # Two known common neighbors prohibit either other exterior edge.
    assert len(set(triples[a]) & set(triples[c])) == 2
    assert len(set(triples[b]) & set(triples[c])) == 2
    return {"sites": sites, "induced_rows": small,
            "other_two_exterior_edges_forbidden_by_common_neighbor_caps": True}


def boolean_controls():
    cases = 0
    for za, zb, zc, y in product((0, 1), repeat=4):
        if y > za or y > zb or y*zc:
            continue
        assert y+za*zc <= za and y+zb*zc <= zb
        cases += 1
    assert cases == 9
    return {"all_binary_assignments_satisfying_edge_activation_and_prism_absence": cases,
            "both_mixed_linear_inequalities_checked": True}


def build(seconds):
    started = time.monotonic(); deadline = started+seconds
    loaded = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert sha(raw) == expected
        loaded[name] = json.loads(gzip.decompress(raw))
    data = loaded["domain"]["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    lookup = {tuple(h): i for i, h in enumerate(triples)}
    assert len(lookup) == 480
    xmap = {a: o for o, group in enumerate(data["selector_orbits"]) for a in group}
    ymap = {e: 42+o for o, group in enumerate(data["edge_orbits"]) for e in group}
    pmap = loaded["moments"]["pair_to_orbit"]
    assert len(pmap) == 114960 and len(xmap) == 480 and len(ymap) == 68394
    kept = loaded["reduction"]["kept_original_variables"]
    fixed = {j for j, _ in loaded["reduction"]["fixed_zero_original_variables"]}
    assert len(kept) == 15200 and len(fixed) == 389
    reverse = {j: i for i, j in enumerate(kept)}
    zero_y = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    assert len(zero_y) == 162
    census = Counter(); rows = []; row_ids = {}; witnesses = []; seen = set()
    for ei, (a, b) in enumerate(edges):
        if ei % 512 == 0:
            assert time.monotonic() < deadline, "bounded three-vertex prism preparation"
        census["eligible_edges_scanned"] += 1
        common = set(triples[a]) & set(triples[b])
        if not common:
            continue
        assert len(common) == 1
        u = next(iter(common))
        for v in triples[a]:
            if v == u:
                continue
            for w in triples[b]:
                if w == u or not ((core[v+3] >> (w+3)) & 1):
                    continue
                c = lookup.get(tuple(sorted((u, v, w))))
                if c is None:
                    continue
                assert c not in (a, b)
                key = (a, b, c)
                assert key not in seen; seen.add(key)
                literal = literal_prism(core, triples, a, b, c, u, v, w)
                record = {"exterior_edge": [a, b], "third_selector": c,
                          "edge_id": ei, "original_Y_variable": ymap[ei], **literal,
                          "cut_dispositions": []}
                census["literal_three_selector_prisms"] += 1
                for endpoint in (a, b):
                    pair = 5847+pmap[pair_id(endpoint, c)]
                    if ymap[ei] in zero_y:
                        reason = {"reason": "known_Y_zero_then_pair_activation", "endpoint": endpoint}
                        census["rows_redundant_from_known_Y_zero"] += 1
                    elif pair in fixed:
                        reason = {"reason": "known_Z_zero_then_edge_activation", "endpoint": endpoint}
                        census["rows_redundant_from_known_Z_zero"] += 1
                    else:
                        terms = tuple(sorted(((reverse[xmap[endpoint]], -1),
                                              (reverse[ymap[ei]], 1), (reverse[pair], 1))))
                        assert len({j for j, c0 in terms}) == 3
                        if terms not in row_ids:
                            row_ids[terms] = len(rows)
                            rows.append({"terms": [list(t) for t in terms], "rhs": 0,
                                         "first_witness": len(witnesses), "endpoint": endpoint})
                        reason = {"reason": "retained_quotient_inequality", "endpoint": endpoint,
                                  "row_id": row_ids[terms]}
                        census["retained_literal_inequalities"] += 1
                    record["cut_dispositions"].append(reason)
                witnesses.append(record)
    assert census["eligible_edges_scanned"] == 68394
    assert sum(census[k] for k in ("rows_redundant_from_known_Y_zero", "rows_redundant_from_known_Z_zero",
                                  "retained_literal_inequalities")) == 2*len(witnesses)
    census["distinct_quotient_inequalities"] = len(rows)
    assert time.monotonic() < deadline, "bounded three-vertex prism preparation"
    return {"status": "COMPLETE_THREE_EXTERIOR_VERTEX_ONE_EDGE_PRISM_CUT_PREPARATION",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "controls": boolean_controls(), "census": dict(census), "rows": rows,
            "literal_prism_witnesses": witnesses, "complete_all68394_edge_coverage": True,
            "all480_selectors_retained": True, "model_variables": 15200,
            "no_edge_product_or_third_selector_moment_used": True,
            "point_loaded": False, "optimizer_calls": 0,
            "scope": "Visible prisms with three exterior vertices and exactly one exterior edge; no other prism/F families claimed complete."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=30)
    args = p.parse_args()
    assert 0 < args.seconds <= 30 and not args.output.exists()
    started = time.monotonic(); result = build(args.seconds); raw = canonical(result)
    if args.mode == "prepare":
        assert not args.record.exists()
        args.record.write_bytes(gzip.compress(raw, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.record.read_bytes()))) == raw
    report = {"status": "PASS: three-vertex prism cuts "+("prepared" if args.mode == "prepare" else "cold replayed"),
              "source_sha256": result["source_sha256"], "record_file_sha256": sha(args.record.read_bytes()),
              "record_raw_sha256": sha(raw), "census": result["census"],
              "controls": result["controls"], "point_loaded": False, "optimizer_calls": 0,
              "seconds": time.monotonic()-started}
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
