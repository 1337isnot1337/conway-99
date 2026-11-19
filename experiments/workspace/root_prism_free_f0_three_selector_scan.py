"""Bounded three-selector separation and exact common-core-pair evaluation.

Numerical arrays select candidates. Only exact dyadic gaps are accepted.
The frozen Boolean formulas justify every retained row independently of
the numerical proposal's feasibility. Replay does not repeat the scan.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "scope_source": ("experiments/workspace/root_prism_free_f0_three_selector_inequalities.py", "1b3f77db3479971b51b40b0f48246d3944dd14c963cae2c77959c4400bd3d3bb"),
    "scope": (BASE+"f0-three-selector-inequalities-scope01.json", "c7f574ef0ed1a05a54dc33404c5c8a1fa4c6c059340d45503a4ceeea88d8c655"),
    "scope_review": (BASE+"f0-three-selector-inequalities-independent-source-review.json", "9709536c1a25c85dcef8b97c104e0d98b6bcce3a7ebf46cb63f82df6595a5f14"),
    "model": (BASE+"f0-schur-path-model03.json.gz", "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"),
    "cliques": (BASE+"f0-core-pair-edge-cliques01.json.gz", "728f3de4ed0febf90f4062820b5a58c8e31335ebc7e65d354872c7bc8d38370e"),
    "clique_review": (BASE+"f0-core-pair-edge-cliques-independent-source-review.json", "eb55b088cf1fe853078a9131e9bf9eafdb4bd7a912143c831a1f80141ce1ff37"),
}
MODEL_SHA = "7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3"
QUERY_SHA = "d074b272ccf4f963b242ea6ba8308e83602d0a71d0d500f6e204a484545e9e7a"
HELPER_SHA = "e039d525a93ab2972ac53538060feb7b6e16dd9f671bb051d29c543b6008b794"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def load_inputs(point_path):
    data = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest, name
        if name != "scope_source":
            data[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    spec = importlib.util.spec_from_file_location("three_selector_frozen_scope", ROOT/INPUTS["scope_source"][0])
    scope = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scope)
    geometry = scope.load_domain()
    assert geometry["representatives"] == data["scope"]["center_representatives"]
    point_raw = point_path.read_bytes()
    point = json.loads(point_raw)
    assert point["model_sha256"] == MODEL_SHA
    assert point["source_sha256"] == QUERY_SHA and point["helper_source_sha256"] == HELPER_SHA
    assert point["variables"] == 15200 and len(point["col_value_hex"]) == 15200
    values = [float.fromhex(s) for s in point["col_value_hex"]]
    assert all(math.isfinite(x) for x in values)
    ratios = [x.as_integer_ratio() for x in values]
    denominator = max(d for n, d in ratios)
    assert denominator > 0 and denominator & (denominator-1) == 0
    assert all(denominator % d == 0 for n, d in ratios)
    numerators = [n*(denominator//d) for n, d in ratios]
    assert len(data["cliques"]["rows"]) == 258
    return data, scope, geometry, point, sha(point_raw), values, numerators, denominator


def row_key(row):
    return canonical([row["terms"], row["rhs"]]).decode()


def gap(row, numerators, denominator):
    return sum(c*numerators[j] for j, c in row["terms"])-row["rhs"]*denominator


def array_controls():
    import numpy as np
    checked = 0
    # Distinct, nonsymmetric toy values expose swapped anchor/pair indexing.
    for n in (3, 4, 7):
        xs = np.arange(n, dtype=float)/8
        pairs = np.zeros((n, n))
        for a in range(n):
            for c in range(a+1, n):
                pairs[a, c] = pairs[c, a] = (3*a+5*c+1)/32
        for b in range(n):
            others = np.array([a for a in range(n) if a != b])
            ii, jj = np.triu_indices(n-1, 1)
            aa, cc = others[ii], others[jj]
            triangle = pairs[aa, b]+pairs[b, cc]-pairs[aa, cc]-xs[b]
            perimeter = xs[aa]+xs[b]+xs[cc]-pairs[aa, b]-pairs[b, cc]-pairs[aa, cc]-1
            for k, (a, c) in enumerate(zip(aa, cc)):
                assert triangle[k] == pairs[a, b]+pairs[b, c]-pairs[a, c]-xs[b]
                assert perimeter[k] == xs[a]+xs[b]+xs[c]-pairs[a, b]-pairs[b, c]-pairs[a, c]-1
                checked += 2
    return {"dense_anchor_formula_checks": checked, "exact_gap_arithmetic": "Python integer common denominator", "optimizer_calls": 0}


def preparation(point_path):
    data, scope, geometry, point, point_sha, values, nums, den = load_inputs(point_path)
    maximum = max(map(abs, nums))
    # A triangle/perimeter has at most six unit terms and |rhs|<=1.
    # A core-pair row has at most twelve edges and one selector.
    bound = 13*maximum+den
    assert bound.bit_length() <= 2110
    return {
        "status": "PREPARED_FROZEN_POINT_THREE_SELECTOR_AND_258_CLIQUE_EVALUATION",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "point_path": str(point_path.relative_to(ROOT)), "point_sha256": point_sha,
        "point_numerical_status": point["numerical_status"], "point_value_valid": point["value_valid"],
        "exact_common_denominator": str(den), "exact_denominator_bits": den.bit_length(),
        "maximum_absolute_coordinate_numerator_bits": maximum.bit_length(),
        "absolute_row_gap_numerator_bound": str(bound), "gap_bound_bits": bound.bit_length(),
        "anchor_representatives": geometry["representatives"],
        "planned_array_evaluations_per_family": 4808202,
        "maximum_numeric_candidates_per_anchor_and_family": 8,
        "maximum_exact_new_rows_per_family": 64, "core_pair_rows_evaluated_exactly": 258,
        "maximum_scan_seconds_including_loading": 30,
        "controls": array_controls(), "numeric_scan_calls": 0, "optimizer_calls": 0,
        "point_feasibility_claimed": False,
    }


def scan(prep, deadline):
    import numpy as np
    data, scope, geometry, point, point_sha, values, nums, den = load_inputs(ROOT/prep["point_path"])
    assert point_sha == prep["point_sha256"] and str(den) == prep["exact_common_denominator"]
    parent_rows = {row_key(row) for row in data["model"]["matrix"]["inequalities"]}
    xs = np.array([values[geometry["reverse"][geometry["xmap"][a]]] for a in range(480)])
    pairs = np.zeros((480, 480))
    for a in range(480):
        for c in range(a+1, 480):
            old = 5847+geometry["pair_to_orbit"][scope.pair_id(a, c)]
            value = 0.0 if old in geometry["fixed"] else values[geometry["reverse"][old]]
            pairs[a, c] = pairs[c, a] = value
    retained = {"triangle": {}, "perimeter": {}}
    candidates = Counter(); anchors = []; timed_out = False
    ii, jj = np.triu_indices(479, 1)
    for b in geometry["representatives"]:
        if time.monotonic() >= deadline:
            timed_out = True; break
        others = np.array([a for a in range(480) if a != b])
        aa, cc = others[ii], others[jj]
        anchor = {"center": b, "pair_evaluations_per_family": len(aa), "families": {}}
        for family in ("triangle", "perimeter"):
            if family == "triangle":
                gaps = pairs[aa, b]+pairs[b, cc]-pairs[aa, cc]-xs[b]
            else:
                gaps = xs[aa]+xs[b]+xs[cc]-pairs[aa, b]-pairs[b, cc]-pairs[aa, cc]-1
            assert np.all(np.isfinite(gaps))
            selection = np.argpartition(gaps, -8)[-8:]
            selection = sorted(map(int, selection), key=lambda k: (-float(gaps[k]), int(aa[k]), int(cc[k])))
            anchor["families"][family] = {"maximum_numerical_gap_hex": float(gaps[selection[0]]).hex(), "numerically_positive_rows": int(np.count_nonzero(gaps > 0))}
            for k in selection:
                candidates[family+"_selected"] += 1
                if gaps[k] <= 0:
                    continue
                a, c = int(aa[k]), int(cc[k])
                row = scope.literal_row(family, a, b, c, geometry)
                exact_gap = gap(row, nums, den)
                if exact_gap <= 0:
                    candidates[family+"_not_exactly_positive"] += 1; continue
                key = row_key(row)
                if key in parent_rows:
                    candidates[family+"_already_in_parent"] += 1; continue
                candidate = {"family": family, "literal_selectors": [a, b, c], "terms": row["terms"], "rhs": row["rhs"], "gap_numerator": str(exact_gap), "gap_denominator": str(den), "numerical_gap_hex": float(gaps[k]).hex(), "gap_above_1e_minus8": exact_gap*100000000 > den}
                retained[family].setdefault(key, candidate)
        anchors.append(anchor)
    cuts = []
    for family in ("triangle", "perimeter"):
        choices = sorted(retained[family].values(), key=lambda r: (-int(r["gap_numerator"]), r["literal_selectors"]))
        cuts.extend(choices[:64])
    clique_gaps = [gap(row, nums, den) for row in data["cliques"]["rows"]]
    return {
        "status": "COMPLETE_NUMERICAL_CANDIDATE_SCAN_EXACT_RETAINED_CUTS" if not timed_out else "PARTIAL_NUMERICAL_SCAN_EXACT_RETAINED_CUTS",
        "source_sha256": sha(Path(__file__).read_bytes()), "point_sha256": point_sha,
        "model_sha256": MODEL_SHA, "exact_common_denominator": str(den),
        "completed_anchors": anchors, "complete_anchor_scope": len(anchors) == 42,
        "array_evaluations_per_family": sum(a["pair_evaluations_per_family"] for a in anchors),
        "candidate_counts": dict(candidates),
        "distinct_positive_new_candidates_before_cap": {k: len(v) for k, v in retained.items()},
        "retained_cut_counts": dict(Counter(r["family"] for r in cuts)), "rows": cuts,
        "clique_gap_numerators_in_published_row_order": list(map(str, clique_gaps)),
        "exactly_positive_clique_rows": [i for i, n in enumerate(clique_gaps) if n > 0],
        "clique_gaps_above_1e_minus8": [i for i, n in enumerate(clique_gaps) if n*100000000 > den],
        "numeric_scan_calls": 1, "optimizer_calls": 0, "point_feasibility_claimed": False,
        "all_three_selector_inequalities_checked_exactly": False,
        "scope": "Only retained rows have exact positive-gap acceptance. Numerical coverage cannot certify that all other rows pass. All258published core-pair rows are evaluated exactly.",
    }


def replay(prep, result):
    data, scope, geometry, point, point_sha, values, nums, den = load_inputs(ROOT/prep["point_path"])
    assert point_sha == prep["point_sha256"] == result["point_sha256"]
    assert result["source_sha256"] == prep["source_sha256"] == sha(Path(__file__).read_bytes())
    assert result["exact_common_denominator"] == prep["exact_common_denominator"] == str(den)
    seen = set(); counts = Counter()
    parent_rows = {row_key(row) for row in data["model"]["matrix"]["inequalities"]}
    for saved in result["rows"]:
        a, b, c = saved["literal_selectors"]
        assert b in geometry["representatives"] and a < c and len({a, b, c}) == 3
        row = scope.literal_row(saved["family"], a, b, c, geometry)
        assert row["terms"] == saved["terms"] and row["rhs"] == saved["rhs"]
        key = row_key(row)
        assert key not in seen and key not in parent_rows
        seen.add(key); counts[saved["family"]] += 1
        exact_gap = gap(row, nums, den)
        assert exact_gap == int(saved["gap_numerator"]) > 0
        assert str(den) == saved["gap_denominator"]
        assert saved["gap_above_1e_minus8"] == (exact_gap*100000000 > den)
    assert dict(counts) == result["retained_cut_counts"] and all(n <= 64 for n in counts.values())
    clique_gaps = [gap(row, nums, den) for row in data["cliques"]["rows"]]
    assert list(map(str, clique_gaps)) == result["clique_gap_numerators_in_published_row_order"]
    assert [i for i, n in enumerate(clique_gaps) if n > 0] == result["exactly_positive_clique_rows"]
    assert [i for i, n in enumerate(clique_gaps) if n*100000000 > den] == result["clique_gaps_above_1e_minus8"]
    anchors = result["completed_anchors"]
    assert [a["center"] for a in anchors] == geometry["representatives"][:len(anchors)]
    assert all(a["pair_evaluations_per_family"] == 114481 for a in anchors)
    assert result["array_evaluations_per_family"] == 114481*len(anchors)
    assert result["complete_anchor_scope"] == (len(anchors) == 42)
    return {"status": "PASS: literal Boolean rows and exact dyadic gaps replayed", "retained_cut_counts": dict(counts), "clique_rows_replayed": 258, "exactly_positive_clique_rows": len(result["exactly_positive_clique_rows"]), "numerical_scan_repeated": False, "numerical_maxima_independently_certified": False, "point_feasibility_claimed": False, "optimizer_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "scan", "replay"))
    parser.add_argument("--point", type=Path)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); start = time.monotonic()
    assert not args.output.exists()
    if args.mode == "prepare":
        assert args.point is not None and not args.preparation.exists()
        result = preparation(args.point.resolve())
        args.preparation.write_text(json.dumps(result, indent=2)+"\n")
    else:
        prep = json.loads(args.preparation.read_bytes())
        assert prep["source_sha256"] == sha(Path(__file__).read_bytes())
        assert prep["inputs"] == {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()}
        if args.mode == "scan":
            assert args.record is not None and not args.record.exists()
            result = scan(prep, start+30)
            result["preparation_sha256"] = sha(args.preparation.read_bytes())
            args.record.write_text(json.dumps(result, indent=2)+"\n")
        else:
            result_record = json.loads(args.record.read_bytes())
            assert result_record["preparation_sha256"] == sha(args.preparation.read_bytes())
            result = replay(prep, result_record)
            result["record_sha256"] = sha(args.record.read_bytes())
    report = {k: v for k, v in result.items() if k not in ("rows", "completed_anchors", "clique_gap_numerators_in_published_row_order")}
    report["seconds"] = time.monotonic()-start
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
