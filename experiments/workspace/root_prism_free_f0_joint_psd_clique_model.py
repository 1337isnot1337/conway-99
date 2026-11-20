"""Append21 checked PSD directions and258 core-pair edge-clique rows.

The full15,200-variable parent and its row/scaling prefixes are unchanged.
Preparation uses certified parent records and checks every new coefficient
from literal witnesses. It repeats no census, eigenscan or optimizer query.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import root_prism_free_f0_joint_psd_zero_scan_v2 as scan

ROOT, LOGS = scan.ROOT, scan.LOGS
PARENT_FILE = "f0-schur-path-model03.json.gz"
PARENT_FILE_SHA = "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"
PARENT_SHA = "7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3"
PARENT_MATRIX_SHA = "24da97cfaf7bdb6e73efcdf9b248d70f30e04443dada5a2c923ab112f10bc812"
PARENT_SCALES_SHA = "0fcd8328b5ead5c51dfba7a624a69b748f38b19c894fd32c310352789e422247"
SOURCES = {
    "root_prism_free_f0_schur_path_model_v3.py": "f76c35fb3e39704e88a250938e3be1d64ad07fba197ea0405fb11ba4aeac74bd",
    "root_prism_free_f0_joint_psd_zero_scan_v2.py": "3bb5b68da04e94944688b71d7900f064c4b4d246f5c02f4a1569d7e094932cea",
    "root_prism_free_f0_core_pair_edge_cliques.py": "2721f32b6bc1778fb7bd4dd7b6893880e2fe0ef014323fb7365e20f02fbb1811",
}
INPUTS = {
    "parent_cold": ["f0-schur-path-query-preflight03.json", "66f4cdb2d259701bac71f56e8e1ee898e7d328f4283d34686e505ab53e625115"],
    "scan_preparation": ["f0-joint-psd-zero-preparation02.json", "f8505003449cdf4f3af83770ed03e48ba1d88875b9982d881e7fc8890b861762"],
    "scan_filter": ["f0-joint-psd-zero-filter02.json.gz", "30cbae97dabfefe4b948684e8387906321d4da5c98c8ecd175a42ae1ba6a4039"],
    "scan": ["f0-joint-psd-zero-scan02.json.gz", "43e590c801ccb85e385253cc475ce6f6bdc09874d10b9c7571170cb2bd06d9a3"],
    "scan_cold": ["f0-joint-psd-zero-scan02-cold-replay.json", "a59a5a8c559d2390847074f04e6fd51df38e2cb0bf333b4d2e88fc503068b7ae"],
    "scan_review": ["f0-joint-psd-zero-independent-source-review.json", "f0716b53c4d6b70a6053ae577df52ab59fe51b9304e6a7d716c354b775fee6a2"],
    "cliques": ["f0-core-pair-edge-cliques01.json.gz", "728f3de4ed0febf90f4062820b5a58c8e31335ebc7e65d354872c7bc8d38370e"],
    "clique_cold": ["f0-core-pair-edge-cliques01-replay.json", "98f2ac73c5a5da4733648e12782b02e4e784353db1aced9615bc2752dcc941e0"],
    "clique_review": ["f0-core-pair-edge-cliques-independent-source-review.json", "eb55b088cf1fe853078a9131e9bf9eafdb4bd7a912143c831a1f80141ce1ff37"],
}
CLIQUE_RAW_SHA = "eb2c2c8829a2c75e59103609b4cb984b52eb44f64868efc7b735b6bb817fef18"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def read(name, expected):
    raw = (LOGS/name).read_bytes()
    assert sha(raw) == expected, name
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def source_bindings():
    for name, expected in SOURCES.items():
        assert sha(Path(__file__).with_name(name).read_bytes()) == expected, name
    return {"source_sha256": sha(Path(__file__).read_bytes()), "sources": SOURCES,
            "inputs": INPUTS, "parent_file_sha256": PARENT_FILE_SHA,
            "parent_model_sha256": PARENT_SHA, "parent_matrix_sha256": PARENT_MATRIX_SHA,
            "parent_scales_sha256": PARENT_SCALES_SHA}


def row_key(row):
    return canonical({"terms": row["terms"], "rhs": row["rhs"]})


def append_row(rows, scales, index, row, family, scale):
    terms = row["terms"]
    assert terms == sorted(terms) and len({j for j, c in terms}) == len(terms)
    assert all(type(j) is int and 0 <= j < 15200 and type(c) is int and c for j, c in terms)
    assert type(row["rhs"]) is int and type(scale) is int and scale > 0 and scale & (scale-1) == 0
    for v in [row["rhs"]]+[c for j, c in terms]:
        assert abs(v) < 2**53 and Fraction(float(v)/scale) == Fraction(v, scale)
    key = row_key(row)
    if key in index:
        return index[key], False
    at = len(rows)
    index[key] = at
    rows.append({"terms": terms, "rhs": row["rhs"], "family": family})
    scales.append(scale)
    return at, True


def checked_psd_rows(inputs):
    prepared, filtered, domain, kernels = scan.load_prepared(
        LOGS/INPUTS["scan_preparation"][0], LOGS/INPUTS["scan_filter"][0])
    result, cold = inputs["scan"], inputs["scan_cold"]
    assert result["source_sha256"] == cold["source_sha256"] == SOURCES["root_prism_free_f0_joint_psd_zero_scan_v2.py"]
    assert cold["status"].startswith("PASS") and cold["result_sha256"] == INPUTS["scan"][1]
    assert cold["retained_cuts"] == len(result["cuts"]) == 21
    assert cold["family_counts"] == {"selector": 16, "plus": 5, "minus": 0}
    assert result["preparation_sha256"] == INPUTS["scan_preparation"][1]
    denominator, numerators, values = scan.base.proposal()
    zeros, seen = set(filtered["certified_zero_variables"]), set()
    output = []
    for i, retained in enumerate(result["cuts"]):
        family, saved = retained["family"], retained["certificate"]
        assert family in ("selector", "plus")
        certificate = scan.base.make_cut(domain, kernels, family, saved["vector"])
        assert certificate == saved
        literal = scan.base.evaluate(domain, kernels, family, certificate, denominator, numerators)
        row, projected = scan.projected_evaluation(certificate, zeros, denominator, numerators, literal)
        assert literal == retained["literal_evaluation"] and projected == retained["projected_evaluation"]
        assert row == retained["row"] and literal["violated"] and projected["violated"]
        assert not any(j in zeros for j, c in row["terms"])
        rule = scan.base.numerical_row_rule(row)
        assert rule == retained["numerical_row_rule"]
        key = row_key(row)
        assert key not in seen
        seen.add(key)
        output.append({"input_index": i, "family": family, "row": row,
                       "scale": rule["term_preserving_positive_dyadic_scale"],
                       "raw_certificate_sha256": sha(canonical(certificate)),
                       "exact_literal_evaluation": literal, "exact_projected_evaluation": projected,
                       "coefficient_range_and_scale": rule})
    assert sum(len(r["row"]["terms"]) for r in output) == 178481
    return domain, zeros, output


def checked_clique_rows(inputs, domain, zeros):
    record, cold = inputs["cliques"], inputs["clique_cold"]
    assert record["source_sha256"] == cold["source_sha256"] == SOURCES["root_prism_free_f0_core_pair_edge_cliques.py"]
    assert cold["record_file_sha256"] == INPUTS["cliques"][1]
    assert cold["record_raw_sha256"] == CLIQUE_RAW_SHA == sha(canonical(record))
    assert cold["status"].startswith("PASS") and record["cuts_constructed"] is True
    assert record["model_variables"] == 15200 and len(record["rows"]) == 258
    assert record["all480_signatures_and68394_eligible_edges_retained"] is True
    assert len(record["ledger"]) == 480*153 and len(record["row_transports"]) == 258
    assert record["component_pairs"] == [list(p) for p in combinations(range(18), 2)]
    triples, edges, xmap, emap = (domain[k] for k in ("triples", "edges", "xmap", "emap"))
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    pair_index = {tuple(p): i for i, p in enumerate(record["component_pairs"])}
    output, transports = [], 0
    for ri, row in enumerate(record["rows"]):
        center, pair, live = row["center"], row["core_pair"], row["live_neighbors_and_edge_ids"]
        assert pair == sorted(set(pair)) and len(pair) == 2 and all(0 <= i < 18 for i in pair)
        assert len(live) >= 2 and len({a for a, e in live}) == len(live)
        first = center*153+pair_index[tuple(pair)]
        assert first == row["first_bucket"]
        assert record["ledger"][first][0] == center and record["ledger"][first][3:] == [len(live), 4, ri]
        for a, e in live:
            assert a != center and edges[e] == sorted((a, center))
            assert set(pair) <= set(triples[a]) and 42+emap[e] not in zeros
        expected_transports = []
        for ai, (g, cg) in enumerate(zip(domain["actions"], domain["core_actions"])):
            moved_pair = tuple(sorted(cg[i+3]-3 for i in pair))
            moved_center = g[center]
            counts = Counter({xmap[moved_center]: -1})
            for a, e in live:
                moved_a = g[a]
                assert set(moved_pair) <= set(triples[moved_a])
                moved_edge = edge_index[tuple(sorted((moved_center, moved_a)))]
                variable = 42+emap[moved_edge]
                assert variable not in zeros
                counts[variable] += 1
            terms = [[j, c] for j, c in sorted(counts.items()) if c]
            assert terms == row["terms"] and row["rhs"] == 0
            index = moved_center*153+pair_index[moved_pair]
            assert record["ledger"][index][3:] == [len(live), 4, ri]
            expected_transports.append([ai, index])
            transports += 1
        assert expected_transports == record["row_transports"][ri]
        output.append({"input_index": ri, "row": {"terms": row["terms"], "rhs": 0},
                       "center": center, "core_pair": pair, "neighbors_and_edge_ids": live,
                       "all12_literal_transport_indices": expected_transports})
    assert transports == 3096 and sum(len(r["row"]["terms"]) for r in output) == 2802
    return output


def build():
    bound = source_bindings()
    parent = read(PARENT_FILE, PARENT_FILE_SHA)
    assert sha(canonical(parent)) == PARENT_SHA
    assert parent["source_sha256"] == SOURCES["root_prism_free_f0_schur_path_model_v3.py"]
    assert sha(canonical(parent["matrix"])) == PARENT_MATRIX_SHA
    assert sha(canonical(parent["numerical_row_scales"])) == PARENT_SCALES_SHA
    inputs = {key: read(*spec) for key, spec in INPUTS.items()}
    pcold = inputs["parent_cold"]
    assert pcold["model_file_sha256"] == PARENT_FILE_SHA and pcold["model_sha256"] == PARENT_SHA
    assert pcold["matrix_sha256"] == PARENT_MATRIX_SHA and pcold["status"].startswith("PASS")
    assert pcold["all5124_path_rows_rederived"] and pcold["old_row_prefixes_unchanged"]
    domain, zeros, psd = checked_psd_rows(inputs)
    cliques = checked_clique_rows(inputs, domain, zeros)
    matrix = dict(parent["matrix"], inequalities=parent["matrix"]["inequalities"][:])
    old_eq, old_ineq = len(matrix["equalities"]), len(matrix["inequalities"])
    assert (matrix["variables"], old_eq, old_ineq) == (15200, 6135, 21629)
    assert matrix["lower"] == 0 and matrix["upper"] == 1
    old_scales = parent["numerical_row_scales"]
    assert len(old_scales) == 27764
    eq_scales, ineq_scales = old_scales[:old_eq], old_scales[old_eq:]
    index = {row_key(row): i for i, row in enumerate(matrix["inequalities"])}
    proofs = []
    for family, records in (("joint PSD", psd), ("core-pair edge clique", cliques)):
        for record in records:
            row = record["row"]
            if family == "joint PSD":
                scale = record["scale"]
            else:
                scale = scan.base.numerical_row_rule(row)["term_preserving_positive_dyadic_scale"]
            position, added = append_row(matrix["inequalities"], ineq_scales, index, row, family, scale)
            proofs.append({"family": family, "input_index": record["input_index"],
                           "mathematical_inequality_index": position, "combined_row_index": old_eq+position,
                           "new_row_appended": added, "row_sha256": sha(row_key(row)),
                           "numerical_row_scale": ineq_scales[position]})
    scales = eq_scales+ineq_scales
    assert matrix["equalities"] == parent["matrix"]["equalities"]
    assert matrix["inequalities"][:old_ineq] == parent["matrix"]["inequalities"]
    assert scales[:27764] == old_scales
    all_rows = matrix["equalities"]+matrix["inequalities"]
    assert len(all_rows) == len(scales)
    appended = [p for p in proofs if p["new_row_appended"]]
    counts = {**parent["counts"], "rows": len(all_rows), "inequalities": len(matrix["inequalities"]),
        "nonzeros": sum(len(r["terms"]) for r in all_rows), "joint_PSD_input_rows": 21,
        "joint_PSD_selector_rows": 16, "joint_PSD_plus_rows": 5,
        "joint_PSD_new_rows": sum(p["family"] == "joint PSD" for p in appended),
        "core_pair_clique_input_rows": 258,
        "core_pair_clique_new_rows": sum(p["family"] == "core-pair edge clique" for p in appended),
        "added_row_inputs": 279, "added_distinct_rows": len(appended),
        "joint_PSD_input_nonzeros": 178481, "core_pair_clique_input_nonzeros": 2802,
        "maximum_mathematical_coefficient_bits": max(abs(v).bit_length() for r in all_rows for j, v in r["terms"]),
        "maximum_numerical_row_scale": max(scales), "total_certified_PSD_directions": 92}
    return {"schema": "f0-complete-path-parent-plus21PSD-and258cliques-v1", **bound,
            "parent": {"file": PARENT_FILE, "file_sha256": PARENT_FILE_SHA,
                       "model_sha256": PARENT_SHA, "matrix_sha256": PARENT_MATRIX_SHA,
                       "numerical_row_scales_sha256": PARENT_SCALES_SHA,
                       "cold_file": INPUTS["parent_cold"][0], "cold_sha256": INPUTS["parent_cold"][1]},
            "matrix": matrix, "matrix_sha256": sha(canonical(matrix)),
            "numerical_row_scales": scales, "numerical_row_scales_sha256": sha(canonical(scales)),
            "append_certificates": proofs, "PSD_proofs": psd, "clique_proofs": cliques,
            "counts": counts,
            "checks": {"retained_PSD_rows_rederived": 21, "exact_PSD_gaps_replayed": 21,
                       "clique_rows_rederived": 258, "literal_clique_transports_replayed": 3096,
                       "old27764_rows_and_scales_unchanged": True,
                       "complete_census_repeated": False, "kernel_inverse_or_census_repeated": False},
            "scope": {**parent["scope"], "point_loaded": True, "point_used_only_for_cut_gap_replay": True,
                      "all15200_variables_retained": True, "all4416_selector_predicates_and_original_RLT_rows_retained": True,
                      "whole_PSD_cone_enforced": False, "new_joint_PSD_directions_added": 21,
                      "complete258_core_pair_edge_clique_rows_added": True,
                      "root128_redundant_greedy_rows_added": False,
                      "parent_was_previously_queried": True, "unchanged_parent_will_not_be_requeried": True,
                      "new_graph_automorphism_or_fixed_selector_assumption": False,
                      "optimizer_calls": 0, "eigendecompositions": 0,
                      "model_feasibility_claimed": False, "component_excluded": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    started = time.monotonic()
    model = build()
    raw = canonical(model)
    if args.mode == "prepare":
        assert not args.model.exists()
        args.model.write_bytes(gzip.compress(raw, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.model.read_bytes()))) == raw
    report = {"status": "PASS:21PSD+258clique overlay "+args.mode,
              "source_sha256": sha(Path(__file__).read_bytes()), "model_file_sha256": sha(args.model.read_bytes()),
              "model_sha256": sha(raw), "matrix_sha256": model["matrix_sha256"],
              "numerical_row_scales_sha256": model["numerical_row_scales_sha256"],
              "counts": model["counts"], "checks": model["checks"],
              "optimizer_calls": 0, "eigendecompositions": 0, "seconds": time.monotonic()-started}
    args.report.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
