"""Add the complete 5,124 two-edge prism rows to the frozen Schur model.

The fully prepared parent remains unrun. This overlay preserves its complete
matrix/scaling prefixes and every variable. It binds the completed census and its cold replay, then independently
checks every appended literal witness and all twelve actual-core transports.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
PARENT_SOURCE = "root_prism_free_f0_schur_motif_model.py"
PARENT_SOURCE_SHA = "077e371e399346ab513ac41a717b181a3e11285ccda38600f12586f61b4375f5"
PARENT_FILE = "f0-schur-motif-model01.json.gz"
PARENT_FILE_SHA = "5f039eb2864f838cf15df987ca7eebef1600eb4085afb3083538dc5514fdb889"
PARENT_SHA = "92d6a65bcfffd3f5c6f2518b5fe4d1ebefb874eb6e72e15229a690ee9198ae19"
PARENT_MATRIX_SHA = "74a83420ac5585a0fa840092aa64d5b7c6732a0f42a32a10adb6af4df504c364"
PARENT_SCALES_SHA = "6874a86bbb22f1ad383de3622374776774d42b56ea31e39d6e1022a57babf4ef"
PATH_SOURCE = "root_prism_free_f0_path_prism_cuts.py"
PATH_SOURCE_SHA = "b332326f90a428565d12d58fefa230bcfb3c5ac4b1e86983115cbc73979c339b"
PATH_FILE = "f0-path-prism-cuts01.json.gz"
PATH_FILE_SHA = "d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886"
PATH_RAW_SHA = "970bff3808d58dfab072974c42a65e04679f301daef258ae4e43c8fccfe1c6f6"
PATH_COLD_FILE = "f0-path-prism-cuts01-replay.json"
PATH_COLD_SHA = "690613ccd1fd9cdf6e7c67988d9d1fac50cd751793dec53ebbadf2c5337b038f"

PARENT_COLD_FILE = "f0-schur-motif-model01-cold-replay.json"
PARENT_COLD_SHA = "3395a7353e134e289fde671fa48e8d3477377df1b7cab0ffcb3c815ff48c1a06"
DOMAIN_FILE = "f0-boolean-fractional-model.json.gz"
DOMAIN_SHA = "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"
PATH_REVIEW_FILE = "f0-path-prism-independent-source-review.json"
PATH_REVIEW_SHA = "4471e71acaa8fbbd34ebf988e32da366d647c40ccb58ca17c3f63bc89f1c212c"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def imported(name, expected):
    path = Path(__file__).with_name(name)
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location("bound_" + path.stem, path)
    answer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(answer)
    return answer


def verify_appended_rows(paths):
    """Rebuild the complete appended coefficient list from literal witnesses.

    Census completeness is supplied by the bound original cold certificate.
    This checker imports no census builder and repeats no bucket search.
    """
    raw = (LOGS / DOMAIN_FILE).read_bytes()
    assert sha(raw) == DOMAIN_SHA
    domain = json.loads(gzip.decompress(raw))["validation"]
    core, triples, edges = (domain[k] for k in ("core", "triples", "edges"))
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    assert paths["inputs"]["domain"]["sha256"] == DOMAIN_SHA
    edge_index = {tuple(edge): i for i, edge in enumerate(edges)}
    assert len(edge_index) == 68394
    xmap, ymap = {}, {}
    for i, orbit in enumerate(domain["selector_orbits"]):
        for a in orbit:
            assert a not in xmap
            xmap[a] = i
    for i, orbit in enumerate(domain["edge_orbits"]):
        for edge in orbit:
            assert edge not in ymap
            ymap[edge] = 42 + i
    assert len(domain["selector_orbits"]) == 42 and set(xmap) == set(range(480))
    assert len(domain["edge_orbits"]) == 5805 and set(ymap) == set(range(68394))
    action_record = paths["actual_core_action_verification"]
    moves, actions = action_record["core_actions"], action_record["selector_actions"]
    assert len(moves) == len(actions) == len(set(map(tuple, moves))) == 12
    assert len(set(map(tuple, actions))) == 12
    action_index = {tuple(move): i for i, move in enumerate(moves)}
    assert tuple(range(21)) in action_index
    for move, action in zip(moves, actions):
        assert sorted(move) == list(range(21)) and sorted(action) == list(range(480))
        assert set(move[:3]) == set(range(3))
        assert all(((core[i] >> j) & 1) == ((core[move[i]] >> move[j]) & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(move[j+3]-3 for j in h) == triples[action[a]]
                   for a, h in enumerate(triples))
    compositions = []
    for i, left in enumerate(moves):
        for j, right in enumerate(moves):
            k = action_index[tuple(left[right[v]] for v in range(21))]
            assert all(actions[k][a] == actions[i][actions[j][a]] for a in range(480))
            compositions.append([i, j, k])
    assert compositions == action_record["all_144_compositions"]
    for orbit in domain["selector_orbits"]:
        assert sorted({action[orbit[0]] for action in actions}) == orbit
    for orbit in domain["edge_orbits"]:
        a, b = edges[orbit[0]]
        assert sorted({edge_index[tuple(sorted((action[a], action[b])))]
                       for action in actions}) == orbit
    witnesses = paths["literal_witnesses"]
    assert len(witnesses) == 107520
    def literal(witness, row_id):
        a, b, c, x, y, z, ab, bc, disposition, _, saved_row, _, _ = witness
        assert disposition == 2 and saved_row == row_id
        assert len({a, b, c}) == len({x, y, z}) == 3
        assert edges[ab] == sorted((a, b)) and edges[bc] == sorted((b, c))
        sites = {x, y, z}
        assert set(triples[a]) & sites == {x, z}
        assert set(triples[b]) & sites == {x}
        assert set(triples[c]) & sites == {y, z}
        assert (core[x+3] >> (y+3)) & 1 and (core[y+3] >> (z+3)) & 1
        assert not (core[x+3] >> (z+3)) & 1
        # The omitted edge ac is impossible: b and core site z are two
        # already prescribed common neighbors of an adjacent pair.
        # The six-site induced graph is checked with that forced absence.
        labels = [21, 22, x+3, 23, y+3, z+3]
        outside = {21: a, 22: b, 23: c}
        def adjacent(u, v):
            if u < 21 and v < 21:
                return (core[u] >> v) & 1
            if u >= 21 and v >= 21:
                return int(tuple(sorted((u, v))) in ((21, 22), (22, 23)))
            if u < 21:
                u, v = v, u
            return int(v >= 3 and v-3 in triples[outside[u]])
        assert [sum(adjacent(u, v) << j for j, v in enumerate(labels))
                for u in labels] == [38, 13, 19, 50, 44, 25]
        coefficients = Counter({xmap[b]: -1})
        coefficients[ymap[ab]] += 1
        coefficients[ymap[bc]] += 1
        return [[j, value] for j, value in sorted(coefficients.items()) if value]
    count = 0
    for i, row in enumerate(paths["rows"]):
        first = witnesses[row["first_literal_witness"]]
        assert literal(first, i) == row["terms"] == row["original_terms"]
        assert row["rhs"] == 0
        transport = paths["quotient_row_transport_witnesses"][i]
        assert transport["row_id"] == i
        listed = transport["literal_witness_transports"]
        assert [a for a, index in listed] == list(range(12))
        a, b, c, x, y, z = first[:6]
        for action_id, index in listed:
            action, move = actions[action_id], moves[action_id]
            witness = witnesses[index]
            assert witness[:6] == [action[a], action[b], action[c],
                                   move[x+3]-3, move[y+3]-3, move[z+3]-3]
            assert literal(witness, i) == row["terms"]
            count += 1
    assert count == 61488
    return {"domain_sha256": DOMAIN_SHA, "appended_rows_checked": 5124,
            "literal_transport_checks": count, "group_compositions_checked": 144,
            "complete_census_repeated": False, "original_census_builder_imported": False,
            "coefficient_two_rows": sum(len(row["terms"]) == 2 for row in paths["rows"])}


def build():
    parent_source = imported(PARENT_SOURCE, PARENT_SOURCE_SHA)
    raw = (LOGS / PARENT_FILE).read_bytes()
    assert sha(raw) == PARENT_FILE_SHA
    parent = json.loads(gzip.decompress(raw))
    assert sha(canonical(parent)) == PARENT_SHA and parent["source_sha256"] == PARENT_SOURCE_SHA
    assert sha(canonical(parent["matrix"])) == PARENT_MATRIX_SHA
    assert sha(canonical(parent["numerical_row_scales"])) == PARENT_SCALES_SHA
    raw_cold = (LOGS / PARENT_COLD_FILE).read_bytes()
    assert sha(raw_cold) == PARENT_COLD_SHA
    parent_cold = json.loads(raw_cold)
    assert parent_cold["status"] == "PASS: exact Schur/prism model cold rebuilt"
    assert parent_cold["source_sha256"] == PARENT_SOURCE_SHA
    assert parent_cold["model_file_sha256"] == PARENT_FILE_SHA
    assert parent_cold["model_sha256"] == PARENT_SHA
    assert parent_cold["matrix_sha256"] == PARENT_MATRIX_SHA
    assert parent_cold["numerical_row_scales_sha256"] == PARENT_SCALES_SHA
    assert sha(Path(__file__).with_name(PATH_SOURCE).read_bytes()) == PATH_SOURCE_SHA
    assert sha((LOGS / PATH_REVIEW_FILE).read_bytes()) == PATH_REVIEW_SHA
    raw = (LOGS / PATH_FILE).read_bytes()
    assert sha(raw) == PATH_FILE_SHA
    plain = gzip.decompress(raw)
    assert sha(plain) == PATH_RAW_SHA
    paths = json.loads(plain)
    assert paths["source_sha256"] == PATH_SOURCE_SHA
    cold = (LOGS / PATH_COLD_FILE).read_bytes()
    assert sha(cold) == PATH_COLD_SHA
    cold_record = json.loads(cold)
    assert cold_record["status"] == "PASS: complete two-edge prism cuts cold replayed"
    assert cold_record["record_file_sha256"] == PATH_FILE_SHA
    assert cold_record["source_sha256"] == PATH_SOURCE_SHA
    assert cold_record["record_raw_sha256"] == PATH_RAW_SHA
    assert paths["complete_all107520_literal_pattern_configurations"] is True
    appended_check = verify_appended_rows(paths)
    assert len(paths["rows"]) == 5124 and paths["census"]["actual_core_row_transports"] == 61488
    assert paths["joint_reduced_model_variables"] == 15200
    assert paths["quotient_coordinate_coincidences_combined_by_integer_addition"] is True
    matrix = deepcopy(parent["matrix"])
    old_eq, old_ineq = len(matrix["equalities"]), len(matrix["inequalities"])
    assert (matrix["variables"], old_eq, old_ineq) == (15200, 6135, 16505)
    scales = parent["numerical_row_scales"][:]
    assert len(scales) == 22640
    eq_scales, ineq_scales = scales[:old_eq], scales[old_eq:]
    index = {}
    for i, row in enumerate(matrix["inequalities"]):
        index.setdefault(parent_source.row_key(row), i)
    certificates = []
    for i, row in enumerate(paths["rows"]):
        assert row["rhs"] == 0 and row["terms"] == row["original_terms"]
        assert all(0 <= j < 5847 for j, coefficient in row["terms"])
        assert sorted(coefficient for j, coefficient in row["terms"]) in ([-1, 1, 1], [-1, 2])
        position, added = parent_source.append_inequality(matrix["inequalities"], ineq_scales, index,
                                                          row, "visible three-exterior two-edge prism")
        witness_index = row["first_literal_witness"]
        witness = paths["literal_witnesses"][witness_index]
        assert witness[8] == 2 and witness[10] == i
        transports = paths["quotient_row_transport_witnesses"][i]
        assert transports["row_id"] == i and len(transports["literal_witness_transports"]) == 12
        certificates.append({"input_row_index": i, "mathematical_inequality_index": position,
                             "combined_row_index": old_eq + position, "new_row_appended": added,
                             "first_literal_witness": witness_index,
                             "literal_witness_transports": transports["literal_witness_transports"],
                             "row_sha256": sha(parent_source.row_key(row)),
                             "numerical_row_scale": ineq_scales[position]})
    scales = eq_scales + ineq_scales
    assert matrix["equalities"] == parent["matrix"]["equalities"]
    assert matrix["inequalities"][:old_ineq] == parent["matrix"]["inequalities"]
    assert scales[:22640] == parent["numerical_row_scales"]
    assert len(certificates) == 5124 and all(record["new_row_appended"] for record in certificates)
    rows = matrix["equalities"] + matrix["inequalities"]
    assert len(rows) == len(scales) == 27764
    assert len(matrix["inequalities"]) == 21629
    assert sum(len(row["terms"]) for row in rows) == 905276
    assert sum(len(row["terms"]) == 2 for row in matrix["inequalities"][old_ineq:]) == 2
    counts = {**parent["counts"], "equalities": 6135, "inequalities": 21629, "rows": 27764,
              "nonzeros": 905276, "two_edge_prism_inputs": 5124, "two_edge_prism_new_rows": 5124,
              "two_edge_prism_added_nonzeros": 15370, "two_edge_prism_doubled_Y_rows": 2,
              "total_added_nonzeros_above32PSD_parent": 525224}
    return {"schema": "f0-Schur-prism-model-plus-complete-two-edge-prisms-v1",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "parent": {"source": PARENT_SOURCE, "source_sha256": PARENT_SOURCE_SHA,
                       "file": PARENT_FILE, "file_sha256": PARENT_FILE_SHA, "model_sha256": PARENT_SHA,
                       "matrix_sha256": PARENT_MATRIX_SHA, "scales_sha256": PARENT_SCALES_SHA,
                       "prepared_but_unrun": True, "cold_replay_file": PARENT_COLD_FILE,
                       "cold_replay_sha256": PARENT_COLD_SHA},
            "path_proof": {"source": PATH_SOURCE, "source_sha256": PATH_SOURCE_SHA,
                           "file": PATH_FILE, "file_sha256": PATH_FILE_SHA, "raw_sha256": PATH_RAW_SHA,
                           "cold_replay_file": PATH_COLD_FILE, "cold_replay_sha256": PATH_COLD_SHA,
                           "source_review_file": PATH_REVIEW_FILE, "source_review_sha256": PATH_REVIEW_SHA},
            "matrix": matrix, "matrix_sha256": sha(canonical(matrix)),
            "numerical_row_scales": scales, "numerical_row_scales_sha256": sha(canonical(scales)),
            "path_cut_certificates": certificates, "counts": counts,
            "controls": {"path_boolean_controls": paths["controls"],
                         "parent_assembly_controls": parent["controls"],
                         "all61488_literal_transports_replayed": True, "direct_appended_check": appended_check},
            "scope": {**parent["scope"], "complete_two_edge_exterior_prism_family_added": True,
                      "all_old_row_and_scale_prefixes_unchanged": True,
                      "prepared_parent_will_not_be_queried": True,
                      "two_exterior_edges_in_same_orbit_sum_to_coefficient_two": True,
                      "extra_selector_or_exterior_edge_variables": 0,
                      "point_loaded": False, "optimizer_calls": 0, "eigendecompositions": 0}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    started = time.monotonic()
    model = build()
    encoded = canonical(model)
    if args.mode == "prepare":
        assert not args.model.exists()
        args.model.write_bytes(gzip.compress(encoded, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.model.read_bytes()))) == encoded
    result = {"status": "PASS: complete path-prism overlay " + ("prepared" if args.mode == "prepare" else "replayed from certified parents and literal witnesses"),
              "source_sha256": sha(Path(__file__).read_bytes()), "model_file_sha256": sha(args.model.read_bytes()),
              "model_sha256": sha(encoded), "matrix_sha256": model["matrix_sha256"],
              "numerical_row_scales_sha256": model["numerical_row_scales_sha256"], "counts": model["counts"],
              "all5124_rows_and61488_transports_rederived": True, "parent_prefixes_exactly_preserved": True,
              "full_parent_rebuilt_this_call": False, "complete_census_repeated": False,
              "certified_parent_cold_records_checked": True, "optimizer_calls": 0,
              "seconds": time.monotonic() - started}
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
