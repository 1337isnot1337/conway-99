"""One bounded integer-enumerator proposal, with exact MacWilliams acceptance.

A formal enumerator is not a code or a graph. Numerical infeasibility is
never accepted as an exclusion. The prepared query fixes dimension eleven.
"""
import argparse
import hashlib
import json
from math import comb
from pathlib import Path
import time

N, DIMENSION, SIZE = 99, 11, 2048
WEIGHTS = [36, 40, 44, 48, 52, 56, 60]
LOWER = {3: 231, 4: 2079, 5: 23868, 6: 24486, 7: 3465, 8: 3465,
         11: 2079, 12: 693, 15: 99}
CHAIN_SOURCE_SHA = "8befdefb75ff4b4fbaee717d6ad5255f441f4ad2eed62bc8464f3efe6ff5025b"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save(path, value):
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def bindings():
    source = Path(__file__).with_name("triangle_incidence_binary_chain_code.py")
    assert sha(source.read_bytes()) == CHAIN_SOURCE_SHA
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "forced_word_model_source_sha256": CHAIN_SOURCE_SHA}


def krawtchouk(n, degree, weight):
    return sum((-1)**s*comb(weight, s)*comb(n-weight, degree-s)
               for s in range(max(0, degree-(n-weight)), min(degree, weight)+1))


def recurrence(n, weight):
    values = [1, n-2*weight]
    for j in range(1, n):
        numerator = (n-2*weight)*values[j]-(n-j+1)*values[j-1]
        assert numerator % (j+1) == 0
        values.append(numerator//(j+1))
    return values


def transform(n, primal):
    size = sum(primal)
    assert primal[0] == 1 and size > 0
    columns = {w: recurrence(n, w) for w, a in enumerate(primal) if a}
    dual = []
    for j in range(n+1):
        value = sum(primal[w]*column[j] for w, column in columns.items())
        assert value % size == 0, ("nonintegral dual weight", j, value, size)
        dual.append(value//size)
    return dual


def controls():
    cases = []
    for k in (3, 4):
        n = (1 << k)-1
        generators = [sum(((column >> bit) & 1) << (column-1)
                          for column in range(1, 1 << k)) for bit in range(k)]
        cases.append(("simplex_"+str(k), n, generators))
    cases.append(("RM_1_3", 8, [255, 240, 204, 170]))
    results = []
    for name, n, generators in cases:
        words = {0}
        for g in generators:
            words |= {w ^ g for w in words}
        primal = [sum(w.bit_count() == j for w in words) for j in range(n+1)]
        dual_words = [v for v in range(1 << n)
                      if all((v & g).bit_count() % 2 == 0 for g in generators)]
        literal_dual = [sum(w.bit_count() == j for w in dual_words) for j in range(n+1)]
        assert transform(n, primal) == literal_dual
        assert all(a <= b for a, b in zip(primal, literal_dual))
        for w in range(n+1):
            assert recurrence(n, w) == [krawtchouk(n, j, w) for j in range(n+1)]
        for j in range(n+1):
            residue = sum((krawtchouk(n, j, w) % len(words))*primal[w]
                          for w in range(1, n+1)) + comb(n, j) % len(words)
            assert residue % len(words) == 0
            assert 0 <= residue//len(words) <= len(words)-1
        results.append({"name": name, "length": n, "size": len(words),
                        "dual_size": len(dual_words), "all_literal_dual_counts_equal": True})
    return results


def model():
    full = [[krawtchouk(N, j, w) for w in WEIGHTS] for j in range(N+1)]
    congruences, lookup = [], {}
    for j in range(1, N+1):
        row = [c % SIZE for c in full[j]]
        rhs = -(comb(N, j) % SIZE)
        key = tuple(row+[rhs])
        if key not in lookup:
            lookup[key] = len(congruences)
            congruences.append({"degrees": [], "residues": row, "rhs": rhs})
        congruences[lookup[key]]["degrees"].append(j)
    degrees = list(range(1, 11))
    assert all(abs(c) < 2**53 for j in degrees for c in full[j])
    assert all(abs(SIZE*LOWER.get(j, 0)-comb(N, j)) < 2**53 for j in degrees)
    return {"length": N, "dimension": DIMENSION, "size": SIZE,
            "allowed_nonzero_weights": WEIGHTS, "sum_nonzero_counts": SIZE-1,
            "full_krawtchouk_rows": full,
            "full_forced_dual_lower_bounds": [[j, value] for j, value in sorted(LOWER.items())],
            "integrality_congruences": congruences,
            "numerical_inequality_degrees": degrees,
            "variable_count": len(WEIGHTS)+len(congruences),
            "variable_lower_bounds": [0]*(len(WEIGHTS)+len(congruences)),
            "variable_upper_bounds": [SIZE-1]*(len(WEIGHTS)+len(congruences)),
            "optimizer_is_only_proposal": True,
            "acceptance": "All100 exact dual counts, integrality, nonnegativity, forced words, dual sum and self-orthogonal inclusion."}


def prepared(path):
    raw = path.read_bytes()
    record = json.loads(raw)
    assert record["bindings"] == bindings()
    assert record["model_sha256"] == sha(canonical(model()))
    assert canonical(record["model"]) == canonical(model())
    return record


def accept(values):
    assert len(values) == len(WEIGHTS) and all(type(v) is int and v >= 0 for v in values)
    assert sum(values) == SIZE-1
    primal = [0]*(N+1)
    primal[0] = 1
    for w, value in zip(WEIGHTS, values):
        primal[w] = value
    dual = transform(N, primal)
    assert dual[0] == 1 and all(v >= 0 for v in dual)
    assert sum(dual) == 1 << (N-DIMENSION)
    assert all(dual[j] >= value for j, value in LOWER.items())
    assert all(a <= b for a, b in zip(primal, dual))
    assert dual == list(reversed(dual))
    return {"primal_weight_counts": primal, "dual_weight_counts": dual,
            "exact_all_100_macwilliams_coefficients": True,
            "all_forced_word_bounds": True, "self_orthogonal_inclusion_counts": True,
            "actual_code_constructed": False, "actual_graph_constructed": False}


def query(preparation, output):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    start = time.monotonic()
    checked = prepared(preparation)
    m = checked["model"]
    width = m["variable_count"]
    rows, lower, upper = [], [], []
    rows.append([1]*7+[0]*(width-7)); lower.append(SIZE-1); upper.append(SIZE-1)
    for i, record in enumerate(m["integrality_congruences"]):
        row = record["residues"]+[0]*(width-7)
        row[7+i] = -SIZE
        rows.append(row); lower.append(record["rhs"]); upper.append(record["rhs"])
    for j in m["numerical_inequality_degrees"]:
        rows.append(m["full_krawtchouk_rows"][j]+[0]*(width-7))
        lower.append(SIZE*LOWER.get(j, 0)-comb(N, j)); upper.append(np.inf)
    proposal = milp(np.zeros(width), integrality=np.ones(width),
                    bounds=Bounds(m["variable_lower_bounds"], m["variable_upper_bounds"]),
                    constraints=LinearConstraint(np.array(rows, dtype=float), lower, upper),
                    options={"time_limit": 15, "mip_rel_gap": 0})
    result = {"status": "UNKNOWN_NO_ACCEPTED_ENUMERATOR", "bindings": bindings(),
              "preparation_sha256": sha(preparation.read_bytes()),
              "model_sha256": checked["model_sha256"], "optimizer_calls": 1,
              "numerical_status": int(proposal.status), "numerical_message": str(proposal.message),
              "numerical_infeasibility_is_not_an_exclusion": True,
              "code_existence_resolved": False, "graph_existence_resolved": False}
    if proposal.x is not None:
        result["numerical_values_hex"] = [float(x).hex() for x in proposal.x]
        values = [int(round(float(x))) for x in proposal.x[:7]]
        result["rounded_nonzero_counts"] = values
        try:
            certificate = accept(values)
            result.update(status="EXACT_FORMAL_DIMENSION_ELEVEN_ENUMERATOR", certificate=certificate)
        except AssertionError as error:
            result["exact_rejection"] = str(error)
    result["seconds"] = time.monotonic()-start
    save(output, result)
    return result


def replay(preparation, result_path, output):
    m = prepared(preparation)
    result = json.loads(result_path.read_text())
    assert result["bindings"] == bindings() and result["model_sha256"] == m["model_sha256"]
    assert result["preparation_sha256"] == sha(preparation.read_bytes())
    assert result["status"] == "EXACT_FORMAL_DIMENSION_ELEVEN_ENUMERATOR"
    certificate = accept(result["rounded_nonzero_counts"])
    assert certificate == result["certificate"]
    report = {"status": "PASS_EXACT_FORMAL_ENUMERATOR_REPLAY", "bindings": bindings(),
              "result_sha256": sha(result_path.read_bytes()),
              "nonzero_weight_counts": result["rounded_nonzero_counts"],
              "all100_dual_counts_checked": True, "optimizer_calls": 0,
              "formal_dimension": DIMENSION, "actual_code_constructed": False}
    save(output, report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "query", "replay"))
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--result", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.mode == "prepare":
        m = model()
        result = {"status": "PREPARED_NO_OPTIMIZER", "bindings": bindings(), "model": m,
                  "model_sha256": sha(canonical(m)), "controls": controls(),
                  "limits": {"optimizer_calls": 1, "solver_seconds": 15},
                  "all99_divisibility_conditions_retained": True,
                  "numerical_row_coefficients_exact_in_binary64": True}
        save(args.preparation, result)
    elif args.mode == "query":
        assert args.output
        result = query(args.preparation, args.output)
    else:
        assert args.result and args.output
        result = replay(args.preparation, args.result, args.output)
    print(json.dumps({k: v for k, v in result.items() if k not in ("model", "certificate")}, indent=2))


if __name__ == "__main__":
    main()
