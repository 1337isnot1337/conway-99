"""No-run check that HiGHS receives every scaled matrix coefficient.

Uses exactly the frozen query's options and CSC conversion. It calls
passModel/getLp/getNumNz, never Highs.run or getDualRay.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

HELPER_SHA = "1ed513c9164282de0a70c197f1a9fbfcf6f9e964e3506b3af521e2f7ea800c1b"
QUERY_SHA = "4ab761312051920674e891f00cd7e2806e0a953bddda6075950becf9bf9fa34b"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    helper_path = Path(__file__).with_name("root_prism_free_f0_schur_motif_exact.py")
    query_path = Path(__file__).with_name("root_prism_free_f0_schur_motif_query.py")
    assert hashlib.sha256(helper_path.read_bytes()).hexdigest() == HELPER_SHA
    assert hashlib.sha256(query_path.read_bytes()).hexdigest() == QUERY_SHA
    spec = importlib.util.spec_from_file_location("f0_native_transport_bound_helper", helper_path)
    exact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exact)
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "highspy")}
    assert versions == {"numpy": "2.3.5", "scipy": "1.17.0", "highspy": "1.16.0"}
    import highspy
    import numpy as np
    from scipy import sparse
    model = exact.load_model(args.model)
    matrix, scales = model["matrix"], model["numerical_row_scales"]
    rows = matrix["equalities"] + matrix["inequalities"]
    n, m = matrix["variables"], len(rows)
    ri, ci, coefficients = [], [], []
    minimum, minimum_count, example = None, 0, None
    for i, (row, scale) in enumerate(zip(rows, scales)):
        for j, value in row["terms"]:
            assert value != 0
            rational = Fraction(abs(value), scale)
            if minimum is None or rational < minimum:
                minimum, minimum_count, example = rational, 1, [i, j, value, scale]
            elif rational == minimum:
                minimum_count += 1
            ri.append(i)
            ci.append(j)
            coefficients.append(exact.exact_scaled(value, scale))
    numerical = sparse.csc_matrix((np.asarray(coefficients), (ri, ci)), shape=(m, n))
    numerical.sort_indices()
    assert numerical.nnz == len(coefficients) == 889906
    rhs = np.asarray([exact.exact_scaled(row["rhs"], scale) for row, scale in zip(rows, scales)])
    lower = rhs.copy()
    lower[len(matrix["equalities"]):] = -highspy.kHighsInf
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = n, m
    lp.col_cost_ = np.zeros(n)
    lp.col_lower_, lp.col_upper_ = np.zeros(n), np.ones(n)
    lp.row_lower_, lp.row_upper_ = lower, rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = numerical.indptr
    lp.a_matrix_.index_ = numerical.indices
    lp.a_matrix_.value_ = numerical.data
    solver = highspy.Highs()
    for name, value in (("output_flag", True), ("threads", 1), ("solver", "ipm"),
                        ("run_crossover", "off"), ("presolve", "on"), ("random_seed", 0)):
        assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
    status, threshold = solver.getOptionValue("small_matrix_value")
    assert status == highspy.HighsStatus.kOk and minimum > Fraction(threshold)
    assert solver.passModel(lp) == highspy.HighsStatus.kOk
    retained = solver.getNumNz()
    assert retained == 889906
    received = solver.getLp()
    assert received.num_col_ == n and received.num_row_ == m
    assert received.a_matrix_.format_ == highspy.MatrixFormat.kColwise
    assert np.array_equal(received.a_matrix_.start_, numerical.indptr)
    assert np.array_equal(received.a_matrix_.index_, numerical.indices)
    assert np.array_equal(received.a_matrix_.value_, numerical.data)
    assert np.array_equal(received.row_lower_, lower) and np.array_equal(received.row_upper_, rhs)
    assert np.array_equal(received.col_lower_, np.zeros(n)) and np.array_equal(received.col_upper_, np.ones(n))
    assert np.array_equal(received.col_cost_, np.zeros(n))
    assert solver.getRunTime() == 0
    result = {"status": "PASS: all889906 scaled coefficients retained exactly by native passModel",
              "source_sha256": exact.digest(__file__), "helper_sha256": HELPER_SHA,
              "query_sha256": QUERY_SHA, "model_sha256": exact.MODEL_SHA256,
              "model_file_sha256": exact.digest(args.model), "matrix_sha256": exact.MATRIX_SHA256,
              "numerical_row_scales_sha256": exact.SCALES_SHA256, "dependency_versions": versions,
              "minimum_nonzero_scaled_coefficient": str(minimum),
              "minimum_nonzero_scaled_coefficient_float": float(minimum),
              "minimum_count": minimum_count, "minimum_example_combined_row_column_integer_scale": example,
              "native_small_matrix_value": threshold, "native_small_matrix_value_hex": float(threshold).hex(),
              "minimum_strictly_above_native_threshold": True,
              "variables": n, "rows": m, "nonzeros_before_passModel": numerical.nnz,
              "native_getNumNz_after_passModel": retained,
              "entire_native_CSC_indices_values_and_row_column_bounds_equal": True,
              "native_option_changed_to_lower_threshold": False,
              "native_runtime": solver.getRunTime(), "optimizer_calls": 0,
              "Highs_run_calls": 0, "getDualRay_calls": 0,
              "scope": "Input transport only. No numerical feasibility or internal presolve conclusion.",
              "seconds": time.monotonic() - started}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
