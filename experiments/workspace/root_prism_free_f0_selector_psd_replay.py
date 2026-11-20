"""Independent full replay of the reduced F0 model plus32 PSD directions.

No production query/helper or PSD cut generator is imported. The frozen
independent parent checker is reused; every new coefficient is rebuilt from
its481-integer vector using complete480/114960 literal coordinates.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

MODEL_FILE_SHA256 = "3302546078e2277c8ce30d032110bb527c6a986a74f76fc1f78451bf4da4b804"
MODEL_SHA256 = "d098a4b84405823aa38e9d2def7b675c6166507f7350937f1dc0f65af7274dcd"
MATRIX_SHA256 = "b49a35a0c19e43a70bc8957f0fe09e03f17113ff67caab40a4d4fa63307cca01"
SCALES_SHA256 = "7d9c593cbf3e2ab127bc37575029acf236edc21018e9e5a6e5d8199f7b5ebc57"
DRIVER_SHA256 = "5e9ebe327f6ae5ccbb85d0697faca359b9517d17b9a8f0ccf375317eab1e44b3"
HELPER_SHA256 = "9834bf571545ab401cc7667e818a19c956d09b4636d577cc5de961d313be746b"
PREPARATION_SHA256 = "69190862dc537ec7c98d05f2e3c33ee33813334936db894332a4b7aa7a94c585"
BUILDER_SHA256 = "1c21e5eb27db84dba33f782c7755e18433b2ce087328b87d89f74a0698090a8b"
PARENT_REPLAY_SHA256 = "9cae35ba181c9ad3fd95f211a5b874ecaaeaa74b0bc2ef51310872ebe5c56efe"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def objsha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def imported(name, expected):
    path = Path(__file__).with_name(name+".py")
    assert sha(path) == expected
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parent = imported("root_prism_free_f0_second_moments_reduced_replay", PARENT_REPLAY_SHA256)
finite_box_ray, save_new = parent.finite_box_ray, parent.save_new


def coefficient_replay(model, reduced, base):
    full = reduced["_original"]
    xmap = [None]*480
    for orbit, members in enumerate(base["validation"]["selector_orbits"]):
        for a in members:
            assert xmap[a] is None
            xmap[a] = orbit
    assert None not in xmap and len(full["pair_to_orbit"]) == 114960
    pairs = [(a, b) for a in range(480) for b in range(a+1, 480)]
    removed = {j for j, r in reduced["fixed_zero_original_variables"]}
    assert len(removed) == 389
    reverse = {j: i for i, j in enumerate(reduced["kept_original_variables"])}
    scales = model["numerical_row_scales"]
    records = []
    for i, certificate in enumerate(model["cut_certificates"]):
        vector = certificate["vector"]
        assert len(vector) == 481 and all(type(v) is int for v in vector)
        assert any(vector) and math.gcd(*vector) == 1
        assert next(v for v in vector if v) > 0 and max(map(abs, vector)) <= 4096
        c, v = vector[0], vector[1:]
        assert c == 0
        diagonal = [-(q*q+2*c*q) for q in v]
        off = [-2*v[a]*v[b] for a, b in pairs]
        assert objsha(diagonal) == certificate["literal_diagonal_sha256"]
        assert objsha(off) == certificate["literal_off_diagonal_sha256"]
        coefficients = defaultdict(int)
        for a, value in enumerate(diagonal):
            coefficients[xmap[a]] += value
        for p, value in enumerate(off):
            coefficients[5847+full["pair_to_orbit"][p]] += value
        raw_terms = sorted((reverse[j], value) for j, value in coefficients.items()
                           if j not in removed and value)
        divisor = math.gcd(c*c, *(abs(value) for j, value in raw_terms)) or 1
        assert divisor == certificate["positive_divisor"]
        row = {"terms": [[j, value//divisor] for j, value in raw_terms],
               "rhs": c*c//divisor, "family": "augmented selector PSD", "PSD_cut": i}
        assert row == model["matrix"]["inequalities"][15719+i]
        assert certificate["scan_cut"] == i
        assert certificate["mathematical_inequality_index"] == 15719+i
        assert certificate["combined_row_index"] == 21692+i
        assert certificate["zero_coordinates_substituted"] == 389
        assert not certificate["unit_box_implied"]
        assert sum(max(value, 0) for j, value in row["terms"]) > row["rhs"]
        largest = max(abs(value) for j, value in row["terms"])
        scale = 1 << (largest.bit_length()-1)
        assert scales[21692+i] == certificate["numerical_positive_scale"] == scale
        records.append({"cut": i, "terms": len(row["terms"]), "divisor": divisor,
                        "numerical_scale": scale, "literal_variables": 480+114960})
    return records, xmap, pairs


def load_bound(model_path):
    assert sha(model_path) == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(Path(model_path).read_bytes()))
    assert objsha(model) == MODEL_SHA256 and objsha(model["matrix"]) == MATRIX_SHA256
    assert model["source_sha256"] == BUILDER_SHA256
    for filename, expected in (
            ("root_prism_free_f0_selector_psd_model.py", BUILDER_SHA256),
            ("root_prism_free_f0_selector_psd_exact.py", HELPER_SHA256),
            ("root_prism_free_f0_selector_psd_query.py", DRIVER_SHA256)):
        assert sha(Path(__file__).with_name(filename)) == expected
    logdir = Path(__file__).resolve().parents[1]/"logs/root-prism-free"
    reduced, base = parent.load_bound(logdir/"f0-second-moments-reduced-model.json.gz")
    matrix = model["matrix"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert matrix["equalities"] == reduced["matrix"]["equalities"]
    assert matrix["inequalities"][:15719] == reduced["matrix"]["inequalities"]
    assert len(matrix["equalities"]) == 5973 and len(matrix["inequalities"]) == 15751
    rows = matrix["equalities"]+matrix["inequalities"]
    assert len(rows) == 21724 and sum(len(r["terms"]) for r in rows) == 380052
    scales = model["numerical_row_scales"]
    assert objsha(scales) == model["numerical_row_scales_sha256"] == SCALES_SHA256
    assert len(scales) == len(rows) and scales[:21692] == [1]*21692
    for row, scale in zip(rows, scales):
        assert type(scale) is int and scale > 0 and scale & (scale-1) == 0
        ids = [j for j, v in row["terms"]]
        assert ids == sorted(set(ids)) and all(type(j) is int and 0 <= j < 15200 for j in ids)
        for value in [row["rhs"]]+[v for j, v in row["terms"]]:
            assert type(value) is int and abs(value) < 2**53
            assert Fraction(float(value)/scale) == Fraction(value, scale)
    assert len(model["cut_certificates"]) == 32
    records, xmap, pairs = coefficient_replay(model, reduced, base)
    assert model["scope"]["whole_PSD_cone_enforced"] is False
    assert model["scope"]["exact_necessary_PSD_directions"] == 32
    model["_reduced"], model["_cut_replay"] = reduced, records
    model["_xmap"], model["_pairs"] = xmap, pairs
    return model, base


def literal_point(model, base, point):
    den, values = parent.old.matrix_point(model["matrix"], point)
    checked = parent.literal_point(model["_reduced"], base, point)
    old_values = [0]*15589
    for j, value in zip(model["_reduced"]["kept_original_variables"], values):
        old_values[j] = value
    full = model["_reduced"]["_original"]
    x = [old_values[model["_xmap"][a]] for a in range(480)]
    z = [old_values[5847+o] for o in full["pair_to_orbit"]]
    quadratics = []
    for i, certificate in enumerate(model["cut_certificates"]):
        c, v = certificate["vector"][0], certificate["vector"][1:]
        value = c*c*den + sum((v[a]**2+2*c*v[a])*x[a] for a in range(480))
        value += 2*sum(v[a]*v[b]*entry for (a, b), entry in zip(model["_pairs"], z))
        row = model["matrix"]["inequalities"][15719+i]
        residual = sum(coefficient*values[j] for j, coefficient in row["terms"])-row["rhs"]*den
        assert value == -certificate["positive_divisor"]*residual and value >= 0
        quadratics.append(str(value))
    return {"status": "PASS: full original point and32 literal selector-PSD directions",
            "original_full_check": checked, "full_rows": 650350,
            "full_variable_bounds": 183834, "additional_full480_quadratic_checks": 32,
            "quadratic_numerators": quadratics, "denominator": str(den),
            "whole_PSD_cone_checked": False, "graph_constructed": False}


def preflight(model_path):
    model, base = load_bound(model_path)
    domain = parent.literal_domain(model["_reduced"], base)
    return {"status": "PASS: independent cold32-PSD-cut query preflight; no optimizer",
            "source_sha256": sha(__file__), "model_file_sha256": MODEL_FILE_SHA256,
            "model_sha256": MODEL_SHA256, "matrix_sha256": MATRIX_SHA256,
            "numerical_row_scales_sha256": SCALES_SHA256,
            "driver_sha256": DRIVER_SHA256, "helper_sha256": HELPER_SHA256,
            "cold_parent_reduction_rebuilt": True, "new_coefficient_replays": model["_cut_replay"],
            "literal_domain": {"selectors": 480, "edges": len(domain["edges"]),
                               "pairs": len(domain["pairs"]), "zeros": len(domain["zeros"])},
            "variables": 15200, "rows": 21724, "nonzeros": 380052,
            "point_acceptance": {"original_rows": 650350, "bounds": 183834, "additional_PSD_directions": 32},
            "controls": parent.controls(), "optimizer_calls": 0, "whole_PSD_cone_checked": False}


def replay(model_path, preparation_path, directory):
    assert sha(preparation_path) == PREPARATION_SHA256
    model, base = load_bound(model_path)
    parent.literal_domain(model["_reduced"], base)
    directory = Path(directory)
    result = json.loads((directory/"result.json").read_text())
    assert result["source_sha256"] == DRIVER_SHA256 and result["helper_source_sha256"] == HELPER_SHA256
    assert result["preparation_file_sha256"] == PREPARATION_SHA256
    assert result["model_sha256"] == MODEL_SHA256 and result["model_file_sha256"] == MODEL_FILE_SHA256
    assert result["numerical_row_scales_sha256"] == SCALES_SHA256
    assert result["whole_PSD_cone_enforced"] is False and result["certified_PSD_directions_enforced"] == 32
    assert result["parent_reduction_preserved"] and result["strengthened_by32_exact_PSD_rows"]
    assert 0 < result["requested_lp_seconds"] <= 180 and 0 < result["requested_exact_seconds"] <= 60
    assert result["production_optimizer_calls_authorized"] == result["exact_phase_calls_authorized"] == 1
    assert result["numerical_method"] == "ipm" and result["run_crossover"] == "on"
    report = {"status": "PASS: terminal scope replay; no exact conclusion",
              "source_sha256": sha(__file__), "run_result_sha256": sha(directory/"result.json"),
              "terminal_status": result["status"], "optimizer_calls": 0,
              "certified_PSD_directions": 32, "whole_PSD_cone_checked": False, "graph_constructed": False}
    numerical_path = directory/"numerical.json"
    if numerical_path.exists():
        numeric = json.loads(numerical_path.read_text())
        assert sha(numerical_path) == result["numerical_file_sha256"]
        assert numeric["model_sha256"] == MODEL_SHA256
        assert numeric["source_sha256"] == DRIVER_SHA256 and numeric["helper_source_sha256"] == HELPER_SHA256
        assert numeric["numerical_row_scales_sha256"] == SCALES_SHA256
        assert numeric["optimizer_calls"] in (0, 1)
        assert result["optimizer_calls_recorded"] == numeric["optimizer_calls"]
        assert "existing_dual_ray_hex" not in numeric
        if "existing_scaled_dual_ray_hex" in numeric:
            values = [float.fromhex(v) for v in numeric["existing_scaled_dual_ray_hex"]]
            assert len(values) == 21724 and all(math.isfinite(v) for v in values)
            assert numeric["existing_ray_query"] is True
        report["original_optimizer_calls"] = numeric["optimizer_calls"]
        if numeric.get("basis_valid"):
            assert len(numeric["column_basis_status"]) == 15200 and len(numeric["row_basis_status"]) == 21724
        report["numerical_basis_valid"] = numeric.get("basis_valid", False)
    exact_path = directory/"exact.json"
    process = result.get("exact_process", {})
    if process.get("exit_code") == 0 and process.get("hard_timeout") is False:
        exact = json.loads(exact_path.read_text())
        assert sha(exact_path) == result["exact_file_sha256"]
        assert exact["helper_source_sha256"] == HELPER_SHA256 and exact["model_sha256"] == MODEL_SHA256
        assert exact["numerical_file_sha256"] == sha(numerical_path) and exact["optimizer_calls"] == 0
        assert exact["numerical_row_scales_sha256"] == SCALES_SHA256
        assert exact["whole_PSD_cone_enforced_or_certified"] is False
        if exact["kind"] == "point":
            assert result["status"] == "EXACT_LINEAR_POINT_FOUND: independent full replay pending"
            report["point_replay"] = literal_point(model, base, exact["point"])
            report["status"] = "PASS: exact linear feasible point including32 PSD directions"
        elif exact["kind"] == "farkas":
            assert result["status"] == "EXACT_LINEAR_FARKAS_FOUND: independent full replay pending"
            check = finite_box_ray(model["matrix"], exact["certificate"])
            assert check["strict"]
            report["ray_replay"] = check
            report["status"] = "PASS: exact linear infeasibility certificate including32 PSD directions"
        else:
            assert exact["kind"] == "unresolved" and result["status"].startswith("UNKNOWN:")
    else:
        assert result["status"].startswith(("UNKNOWN:", "ERROR:"))
    report["file_hashes"] = {p.name: sha(p) for p in sorted(directory.iterdir()) if p.is_file()}
    return report


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("replay")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "preflight":
        record = preflight(args.model)
    else:
        record = replay(args.model, args.preparation, args.directory)
    save_new(args.output, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

