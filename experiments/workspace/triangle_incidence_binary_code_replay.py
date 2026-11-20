"""Portable artifact-only check using a Krawtchouk recurrence, not the builder."""
import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path

RESULT_SHA = "80c87653eb52286cd90633823dfa8e07166e65531eba938b69f9b6957e287e5f"


def sequence(weight):
    values = [1, 99 - 2*weight]
    for j in range(1, 99):
        numerator = (99 - 2*weight)*values[j] - (100 - j)*values[j-1]
        assert numerator % (j+1) == 0
        values.append(numerator // (j+1))
    assert len(values) == 100
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.result.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RESULT_SHA
    result = json.loads(raw)
    assert result["status"] == "EXACT_BINARY_CODE_SIZE_BOUND"
    dual = list(map(Fraction, result["exact_dual"]))
    primal = list(map(Fraction, result["exact_primal"]))
    assert len(dual) == 99 and len(primal) == 7
    assert all(y >= 0 for y in dual) and all(x >= 0 for x in primal)
    weights = [36, 40, 44, 48, 52, 56, 60]
    K = [sequence(w) for w in weights]
    assert sequence(0) == [comb(99, j) for j in range(100)]
    slacks = [-sum(dual[j-1]*K[i][j] for j in range(1, 100)) - 1 for i in range(7)]
    assert slacks == [0]*7
    for j in range(1, 100):
        assert comb(99, j) + sum(primal[i]*K[i][j] for i in range(7)) >= 0
    upper = 1 + sum(dual[j-1]*comb(99, j) for j in range(1, 100))
    assert upper == 1 + sum(primal) == Fraction(5834276864000, 755087)
    assert 2**22 <= upper < 2**23
    report = {"status": "PASS_INDEPENDENT_RECURRENCE_BINARY_CODE_BOUND",
              "result_sha256": RESULT_SHA,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "exact_code_size_upper_bound": str(upper),
              "binary_kernel_dimension_upper_bound": 22,
              "binary_incidence_rank_lower_bound": 77,
              "dual_signs_checked": 99, "dual_columns_checked": 7,
              "primal_inequalities_checked": 99, "primal_bounds_checked": 7,
              "discovery_source_imported": False, "optimizer_called": False}
    assert not args.output.exists()
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
