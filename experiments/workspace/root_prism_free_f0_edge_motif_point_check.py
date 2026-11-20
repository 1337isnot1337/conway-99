"""Check that new visible-prism Y zeros reject the old exact Boolean point."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "census": (BASE+"f0-edge-motif-census01.json.gz", "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
    "model": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "point": (BASE+"f0-boolean-fractional-model-point.json", "047417fc0e266bce4fa29a58b2483c16f6c3bd8549de941ab220245c5e8ba2c7"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    data = {}
    for key, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected
        data[key] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    model, saved, census = data["model"], data["point"], data["census"]
    assert saved["model_file_sha256"] == INPUTS["model"][1]
    assert saved["exact_check"]["status"].startswith("PASS: exact rational point")
    matrix = model["matrix"]
    den = int(saved["point"]["denominator"])
    nums = list(map(int, saved["point"]["numerators"]))
    assert den > 0 and len(nums) == matrix["variables"] == 5847
    assert matrix["lower"] == 0 and matrix["upper"] == 1
    for j, x in enumerate(nums):
        assert matrix["lower"]*den <= x <= matrix["upper"]*den
    for row in matrix["equalities"]:
        assert sum(c*nums[j] for j, c in row["terms"]) == row["rhs"]*den
    for row in matrix["inequalities"]:
        assert sum(c*nums[j] for j, c in row["terms"]) <= row["rhs"]*den
    zeros = census["forced_zero_original_Y_variables"]
    assert len(zeros) == 162 and all(42 <= j < 5847 for j in zeros)
    violations = [{"original_variable": j, "edge_orbit": j-42, "positive_numerator": str(nums[j])}
                  for j in zeros if nums[j] > 0]
    assert len(violations) == 9
    return {"status": "PASS: old exact Boolean point passes all old rows and violates nine new Y zeros",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "old_equalities_checked": len(matrix["equalities"]),
            "old_inequalities_checked": len(matrix["inequalities"]),
            "old_variable_bounds_checked": 5847, "new_Y_zero_rows_checked": 162,
            "common_denominator": str(den), "new_violations": violations,
            "old_boolean_relaxation_strictly_strengthened": True,
            "joint_second_moment_feasibility_or_infeasibility_not_claimed": True,
            "optimizer_calls": 0, "new_numerical_point_queries": 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = build()
    if args.mode == "prepare":
        assert not args.record.exists()
        args.record.write_text(json.dumps(result, indent=2)+"\n")
    else:
        assert json.loads(args.record.read_bytes()) == result
        assert args.output is not None and not args.output.exists()
        args.output.write_text(json.dumps({"status": "PASS: exact edge-motif point-check replay",
                                          "source_sha256": result["source_sha256"],
                                          "record_sha256": sha(args.record.read_bytes()),
                                          "optimizer_calls": 0}, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
