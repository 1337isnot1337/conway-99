"""Independent cold replay of the IPM/crossover second-moment query.

No production query/helper is imported. The exact reduction is rebuilt, and
points are restored and passed to the frozen independent original checker.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

MODEL_FILE_SHA256 = "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"
MODEL_SHA256 = "684b3a646a95d8404bf7b46a3ab170ef88b82e54fdb02aec3a34b8f9613847ae"
MATRIX_SHA256 = "5e417221ed814a5a0dcb03e31820871113bcc0eb8af2856dd2ac493958d16f39"
DRIVER_SHA256 = "c6f2658796459167b885b9f9f7ecbf75b6ba92808c4115e6962b806aafe786e7"
HELPER_SHA256 = "0ade9c2f04415b325e7f217023dd072abaf4b8cdf60cd9fe07a2cfe93e416536"
PREPARATION_SHA256 = "1f0ce9a5de0343217c9cae7b4f42899baae2929bf6c24c1ccd0484a0ddb300ea"
REDUCTION_SOURCE_SHA256 = "1f9549100f5bad7476fc21d1152e6637cac7f448987e57d7652204d5e8df279c"
ORIGINAL_REPLAY_SHA256 = "d2a22dd43540a998b4bb3629a7fe39c17aa6cf52b05b6ab2ce8c8b020400b19e"


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


old = imported("root_prism_free_f0_second_moments_replay", ORIGINAL_REPLAY_SHA256)
finite_box_ray, controls, save_new = old.finite_box_ray, old.controls, old.save_new


def load_bound(model_path):
    raw = Path(model_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert objsha(model) == MODEL_SHA256 and objsha(model["matrix"]) == MATRIX_SHA256
    logdir = Path(__file__).resolve().parents[1]/"logs/root-prism-free"
    parent_path = logdir/"f0-second-moments-preparation02.json.gz"
    rank_path = logdir/"f0-second-moments-selector-rank.json.gz"
    builder = imported("root_prism_free_f0_second_moments_reduced", REDUCTION_SOURCE_SHA256)
    rebuilt = builder.build(parent_path, rank_path)
    rebuilt["controls"] = builder.controls()
    assert canonical(rebuilt) == canonical(model)
    assert sha(Path(__file__).with_name("root_prism_free_f0_second_moments_reduced_exact.py")) == HELPER_SHA256
    assert sha(Path(__file__).with_name("root_prism_free_f0_second_moments_ipm_query.py")) == DRIVER_SHA256
    parent, base = old.load_bound(parent_path)
    model["_original"] = parent
    return model, base


def literal_domain(model, base):
    return old.literal_domain(model["_original"], base)


def literal_point(model, base, point):
    denominator, values = old.matrix_point(model["matrix"], point)
    restored = [0]*15589
    assert len(values) == len(model["kept_original_variables"]) == 15200
    for j, value in zip(model["kept_original_variables"], values):
        restored[j] = value
    original_point = {"denominator": str(denominator), "numerators": list(map(str, restored))}
    checked = old.literal_point(model["_original"], base, original_point)
    assert checked["full_rows"] == 650350 and checked["full_variable_bounds"] == 183834
    return {"status": "PASS: reduced quotient and every original literal point row",
            "restored_zero_coordinates": 389, "original_full_check": checked,
            "PSD_checked": False, "graph_constructed": False}


def preflight(model_path):
    model, base = load_bound(model_path)
    domain = literal_domain(model, base)
    return {"status": "PASS: cold equivalent model and independent full replay preflight; no optimizer",
            "source_sha256": sha(__file__), "model_file_sha256": MODEL_FILE_SHA256,
            "model_sha256": MODEL_SHA256, "matrix_sha256": MATRIX_SHA256,
            "driver_sha256": DRIVER_SHA256, "helper_sha256": HELPER_SHA256,
            "cold_reduction_rebuilt": True,
            "literal_domain": {"selectors": 480, "edges": len(domain["edges"]),
                               "pairs": len(domain["pairs"]), "zeros": len(domain["zeros"]),
                               "original_equalities": len(domain["rows"])},
            "reduced_variables": 15200, "reduced_rows": 21692,
            "original_full_point_acceptance": {"rows": 650350, "bounds": 183834},
            "controls": controls(), "optimizer_calls": 0, "PSD_checked": False}

def replay(model_path, preparation_path, directory):
    assert sha(preparation_path) == PREPARATION_SHA256
    model, base = load_bound(model_path)
    literal_domain(model, base)
    directory = Path(directory)
    result = json.loads((directory/"result.json").read_text())
    assert result["source_sha256"] == DRIVER_SHA256 and result["helper_source_sha256"] == HELPER_SHA256
    assert result["preparation_file_sha256"] == PREPARATION_SHA256
    assert result["model_sha256"] == MODEL_SHA256 and result["model_file_sha256"] == MODEL_FILE_SHA256
    assert result["PSD_constraints_enforced"] is False
    assert result["numerical_method"] == "ipm" and result["run_crossover"] == "on"
    assert result["lp_hard_limit_seconds"] == result["requested_lp_seconds"]
    assert result["numerical_output_reserve_seconds"] == 3
    assert 0 < result["requested_lp_seconds"] <= 180 and 0 < result["requested_exact_seconds"] <= 60
    assert result["production_optimizer_calls_authorized"] == result["exact_phase_calls_authorized"] == 1
    report = {"status": "PASS: terminal scope replay; no exact conclusion",
              "source_sha256": sha(__file__), "run_result_sha256": sha(directory/"result.json"),
              "terminal_status": result["status"], "optimizer_calls": 0,
              "PSD_checked": False, "graph_constructed": False}
    numerical_path = directory/"numerical.json"
    if numerical_path.exists():
        numeric = json.loads(numerical_path.read_text())
        assert sha(numerical_path) == result["numerical_file_sha256"]
        assert numeric["model_sha256"] == MODEL_SHA256
        assert numeric["source_sha256"] == DRIVER_SHA256 and numeric["helper_source_sha256"] == HELPER_SHA256
        assert numeric["optimizer_calls"] in (0, 1)
        assert numeric["numerical_method"] == "ipm" and numeric["run_crossover"] == "on"
        assert numeric["output_reserve_seconds"] == 3.0
        assert result["optimizer_calls_recorded"] == numeric["optimizer_calls"]
        report["original_optimizer_calls"] = numeric["optimizer_calls"]
        if numeric.get("basis_valid"):
            assert len(numeric["column_basis_status"]) == 15200 and len(numeric["row_basis_status"]) == 21692
        report["numerical_basis_valid"] = numeric.get("basis_valid", False)
    exact_path = directory/"exact.json"
    process = result.get("exact_process", {})
    if process.get("exit_code") == 0 and process.get("hard_timeout") is False:
        exact = json.loads(exact_path.read_text())
        assert sha(exact_path) == result["exact_file_sha256"]
        assert exact["helper_source_sha256"] == HELPER_SHA256 and exact["model_sha256"] == MODEL_SHA256
        assert exact["numerical_file_sha256"] == sha(numerical_path) and exact["optimizer_calls"] == 0
        if exact["kind"] == "point":
            assert result["status"] == "EXACT_LINEAR_POINT_FOUND: independent full replay pending"
            report["point_replay"] = literal_point(model, base, exact["point"])
            report["status"] = "PASS: exact second-moment linear feasible point"
        elif exact["kind"] == "farkas":
            assert result["status"] == "EXACT_LINEAR_FARKAS_FOUND: independent full replay pending"
            check = finite_box_ray(model["matrix"], exact["certificate"])
            assert check["strict"]
            report["ray_replay"] = check
            report["status"] = "PASS: exact second-moment linear infeasibility certificate"
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

