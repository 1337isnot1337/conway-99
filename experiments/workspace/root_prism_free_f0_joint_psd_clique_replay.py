"""Cold exact reconstruction and independent finite-box certificate replay.

Only the appended witnesses are rebuilt over hash-bound certified parents.
No numerical helper/driver, census or eigenscan is invoked.
Infeasibility is checked independently by minimizing the combined integer
linear form over the full unit box. Numerical proposals remain uncertified.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import time

BUILDER_SHA = "5bef59a3831030047349a0f2d80b36fffb6aa99e8bfdc1f074d4b776143b459b"
QUERY_SHA = "577b120992399a0a0e958eafd0bd9d7a7344982bbb4788a60bebee7ec7437441"
HELPER_SHA = "f16d9648a396a4c2c78b68262ce4c767351bfd69bdf66237b49b35e0fb8752fc"
MODEL_SHA = "e5aee717846cf7bb1b2e6072438d49b38627119fed65408d2159212f876ec21d"
MODEL_FILE_SHA = "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"
MATRIX_SHA = "607b3a6b1939b70538cbaf5e5d6e395b746745bf50ced097f12d81035723a234"
SCALES_SHA = "ab1b87424535ab03a530119b0ac5f306c5f9b2b8e038d999ffcca2dc183ebf1a"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def number(value):
    if type(value) is int:
        return value
    assert isinstance(value, str) and re.fullmatch(r"-?(0|[1-9][0-9]*)", value)
    return int(value)


def check_integer_certificate(matrix, certificate):
    assert matrix["lower"] == 0 and matrix["upper"] == 1
    equalities, inequalities = matrix["equalities"], matrix["inequalities"]
    lam = [number(v) for v in certificate["equality_multipliers"]]
    mu = [number(v) for v in certificate["inequality_multipliers"]]
    assert len(lam) == len(equalities) and len(mu) == len(inequalities)
    assert min(mu, default=0) >= 0
    coefficients = [0] * matrix["variables"]
    upper = 0
    for multiplier, row in list(zip(lam, equalities)) + list(zip(mu, inequalities)):
        upper += multiplier * row["rhs"]
        for variable, coefficient in row["terms"]:
            coefficients[variable] += multiplier * coefficient
    # Every feasible unit-box vector has c*x >= sum min(c_j,0).
    minimum = sum(min(c, 0) for c in coefficients)
    gap = upper - minimum
    return {"rhs": str(upper), "upper_deficit_sum": str(-minimum), "gap": str(gap),
            "strict_infeasibility": gap < 0, "variables": matrix["variables"],
            "equality_rows": len(lam), "inequality_rows": len(mu)}


def controls():
    model = {"variables": 2, "lower": 0, "upper": 1,
             "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 1}],
             "inequalities": [{"terms": [[0, 1]], "rhs": 1}]}
    checks = 0
    for lam in range(-3, 4):
        for mu in range(4):
            report = check_integer_certificate(model, {"equality_multipliers": [lam], "inequality_multipliers": [mu]})
            assert not report["strict_infeasibility"]
            checks += 1
    impossible = {"variables": 1, "lower": 0, "upper": 1,
                  "equalities": [{"terms": [[0, 1]], "rhs": 2}], "inequalities": []}
    for scale in (1, 3, 2**130 + 1):
        report = check_integer_certificate(impossible, {"equality_multipliers": [str(-scale)], "inequality_multipliers": []})
        assert report["gap"] == str(-scale)
    return {"feasible_integer_certificate_controls": checks, "strict_controls": 3,
            "optimizer_calls": 0}


def cold_model(path):
    source = Path(__file__).with_name("root_prism_free_f0_joint_psd_clique_model.py")
    assert digest(source) == BUILDER_SHA
    assert digest(Path(__file__).with_name("root_prism_free_f0_joint_psd_clique_query.py")) == QUERY_SHA
    assert digest(Path(__file__).with_name("root_prism_free_f0_joint_psd_clique_exact.py")) == HELPER_SHA
    spec = importlib.util.spec_from_file_location("f0_cold_joint_psd_clique_model", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reconstructed = module.build()
    assert digest(path) == MODEL_FILE_SHA
    saved = json.loads(gzip.decompress(Path(path).read_bytes()))
    assert canonical(reconstructed) == canonical(saved)
    assert hashlib.sha256(canonical(saved)).hexdigest() == MODEL_SHA
    assert hashlib.sha256(canonical(saved["matrix"])).hexdigest() == MATRIX_SHA
    assert hashlib.sha256(canonical(saved["numerical_row_scales"])).hexdigest() == SCALES_SHA
    return saved


def replay(model_path, preparation_path, directory=None):
    started = time.monotonic()
    model = cold_model(model_path)
    preparation = json.loads(Path(preparation_path).read_text())
    assert preparation["status"] == "PASS: one-call scaled IPM/no-crossover joint-PSD/clique query prepared; no optimizer"
    assert preparation["source_sha256"] == QUERY_SHA and preparation["helper_source_sha256"] == HELPER_SHA
    assert preparation["model_sha256"] == MODEL_SHA and preparation["matrix_sha256"] == MATRIX_SHA
    assert preparation["model_file_sha256"] == MODEL_FILE_SHA
    assert preparation["numerical_row_scales_sha256"] == SCALES_SHA
    assert preparation["optimizer_calls"] == 0 and preparation["exact_phase_only_if_existing_ray"] is True
    assert preparation["numerical_method"] == "ipm" and preparation["run_crossover"] == "off"
    report = {"status": "PASS: certified parent bindings, appended literal rows and standalone arithmetic controls",
              "source_sha256": digest(__file__), "model_file_sha256": MODEL_FILE_SHA,
              "model_sha256": MODEL_SHA, "matrix_sha256": MATRIX_SHA,
              "preparation_sha256": digest(preparation_path), "counts": model["counts"],
              "controls": controls(), "parent_full_replay_verified_by_hash": True, "parent_Schur_and_path_rows_rederived_this_call": False,
              "parent_edge_zero_witness_replay_verified_by_hash": True, "all21_PSD_rows_rederived": True, "all258_clique_rows_and3096_transports_rederived": True,
              "old27764_row_and_scale_prefixes_unchanged": True,
              "full480_selector_domain_retained": True, "optimizer_calls": 0,
              "numerical_helper_or_driver_imported": False, "primal_feasibility_claimed": False,
              "exact_Farkas_certificate_replayed": False}
    if directory is not None:
        directory = Path(directory)
        result = json.loads((directory / "result.json").read_text())
        assert not result["status"].startswith("RUNNING")
        assert result["model_sha256"] == MODEL_SHA and result["model_file_sha256"] == MODEL_FILE_SHA
        assert result["source_sha256"] == QUERY_SHA and result["helper_source_sha256"] == HELPER_SHA
        assert result["preparation_file_sha256"] == digest(preparation_path)
        assert 0 < result["requested_lp_seconds"] <= 180 and 0 < result["requested_exact_seconds"] <= 60
        assert result["numerical_method"] == "ipm" and result["run_crossover"] == "off"
        numeric_path = directory / "numerical.json"
        if numeric_path.exists():
            numeric = json.loads(numeric_path.read_text())
            assert result["numerical_file_sha256"] == digest(numeric_path)
            assert numeric["source_sha256"] == QUERY_SHA and numeric["helper_source_sha256"] == HELPER_SHA
            assert numeric["model_sha256"] == MODEL_SHA and numeric["numerical_row_scales_sha256"] == SCALES_SHA
            assert numeric["optimizer_calls"] in (0, 1)
            assert result["optimizer_calls_recorded"] == numeric["optimizer_calls"]
            for key, length in (("col_value_hex", 15200), ("row_value_hex", 28043),
                                ("existing_scaled_dual_ray_hex", 28043)):
                if key in numeric:
                    assert len(numeric[key]) == length and all(math.isfinite(float.fromhex(v)) for v in numeric[key])
            if "existing_scaled_dual_ray_hex" in numeric:
                assert numeric["existing_ray_query"] is True
            else:
                assert result.get("exact_phase_calls", 0) == 0
            report["numerical_status"] = numeric.get("numerical_status")
            report["numerical_proposal_available"] = "col_value_hex" in numeric
        exact_path = directory / "exact.json"
        if exact_path.exists():
            exact = json.loads(exact_path.read_text())
            assert result["exact_file_sha256"] == digest(exact_path)
            assert exact["model_sha256"] == MODEL_SHA and exact["helper_source_sha256"] == HELPER_SHA
            assert exact["numerical_file_sha256"] == digest(numeric_path)
            assert exact["optimizer_calls"] == 0 and exact["primal_recovery_attempted"] is False
            assert exact["basis_recovery_attempted"] is False and exact["kind"] in ("farkas", "unresolved")
            if exact["kind"] == "farkas":
                check = check_integer_certificate(model["matrix"], exact["certificate"])
                assert check == exact["exact_check"] and check["strict_infeasibility"]
                report["exact_Farkas_certificate_replayed"] = True
                report["exact_Farkas_check"] = check
        if result["status"].startswith("EXACT_LINEAR_FARKAS_FOUND"):
            assert report["exact_Farkas_certificate_replayed"]
        report["preserved_parent_status"] = result["status"]
        report["result_file_sha256"] = digest(directory / "result.json")
        report["status"] = "PASS: certified parents, exact overlay and terminal record; exact scope preserved"
    report["seconds"] = time.monotonic() - started
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--directory", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    answer = replay(args.model, args.preparation, args.directory)
    args.output.write_text(json.dumps(answer, indent=2) + "\n")
    print(json.dumps(answer, indent=2))
