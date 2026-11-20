"""Independent recurrence replay of the star and chain coding certificates."""
import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path

WEIGHTS = [36, 40, 44, 48, 52, 56, 60]
BINDINGS = {
    "star": {"result": "5a9ff2bfefa83fabb1b9dd43c939e92058dc98d7d97ffee3d3901906501c5bb3",
             "bound": "5471926272/290905", "dimension": 14},
    "chain": {"result": "cb06a3fe46a94c0821b4570f55aceec868001fcd0efd697340d83fd1ef522c2f",
              "bound": "140594432/35063", "dimension": 11},
}


def krawtchouk_sequence(weight):
    out = [1, 99-2*weight]
    for degree in range(1, 99):
        numerator = (99-2*weight)*out[-1] - (100-degree)*out[-2]
        assert numerator % (degree+1) == 0
        out.append(numerator//(degree+1))
    return out


def verify(kind, path):
    binding = BINDINGS[kind]
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == binding["result"]
    record = json.loads(raw)
    dual = list(map(Fraction, record["exact_dual"]))
    primal = list(map(Fraction, record["exact_primal"]))
    assert len(dual) == 99 and len(primal) == 7
    assert all(x >= 0 for x in dual+primal)
    lower = {3: 99*7//3, 6: comb(231, 2)-99*comb(7, 2)}
    for k in range(2, 8):
        lower[2*k+k%2] = 99*comb(7, k)
    if kind == "chain":
        lower[5] = 231*3*6**2 - 9*120
    values = [krawtchouk_sequence(w) for w in WEIGHTS]
    assert krawtchouk_sequence(0) == [comb(99, j) for j in range(100)]
    slacks = [sum(dual[j-1]*(lower.get(j, 0)-column[j]) for j in range(1, 100))-1
              for column in values]
    assert all(s >= 0 for s in slacks)
    for j in range(1, 100):
        assert sum((lower.get(j, 0)-values[i][j])*primal[i] for i in range(7)) <= comb(99, j)-lower.get(j, 0)
    upper = 1 + sum(dual[j-1]*(comb(99, j)-lower.get(j, 0)) for j in range(1, 100))
    assert upper == 1+sum(primal) == Fraction(binding["bound"])
    dimension = binding["dimension"]
    assert 2**dimension <= upper < 2**(dimension+1)
    if kind == "chain":
        integer_slacks = [-6432*column[1]+13*(2079-column[4])+17*(23868-column[5])-315567
                          for column in values]
        assert integer_slacks == [0, 232704, 0, 28416, 225280, 235776, 0]
        assert 315567+6432*99+13*(comb(99, 4)-2079)+17*(comb(99, 5)-23868) == 1265349888
        assert 315567*4096 > 1265349888
    return {"status": "PASS_INDEPENDENT_STRENGTHENED_CODE_BOUND", "kind": kind,
            "result_sha256": binding["result"],
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "exact_code_size_upper_bound": str(upper),
            "binary_kernel_dimension_upper_bound": dimension,
            "binary_incidence_rank_lower_bound": 99-dimension,
            "dual_signs_checked": 99, "dual_columns_checked": 7,
            "primal_constraints_checked": 99, "primal_bounds_checked": 7,
            "exact_LP_optimum": True, "optimizer_called": False,
            "discovery_source_imported": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("kind", choices=BINDINGS)
    p.add_argument("result", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    report = verify(a.kind, a.result)
    assert not a.output.exists()
    a.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
