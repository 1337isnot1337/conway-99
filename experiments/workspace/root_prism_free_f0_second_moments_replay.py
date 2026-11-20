"""Optimizer-free, independent literal replay for the F0 second-moment query.

This module imports neither the production driver nor its exact helper.
The bound preparation supplies the finite domain. Core Gram rows, mixed
targets, zero-product certificates and literal moment rows are rebuilt here.
"""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import re

MODEL_FILE_SHA256 = "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"
MODEL_SHA256 = "df20b045881fbb39233aa88b870f76715b1233920a00d9a53373cd8025d5de91"
MATRIX_SHA256 = "0f97fd60d2b0b24fa75e6a3d0ee96363b98fb7ea652611d3779ef38946ae8bd1"
BASE_FILE_SHA256 = "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"
DRIVER_SHA256 = "e79b4d42c2e9b530c01f41d11e71bd904ab9533ca46e0f0347c5fd98602b728d"
HELPER_SHA256 = "3986ac84e6d891a0dc362db05f7785ae4294fe58a31a6241f0b63721de5868cd"
PREPARATION_SHA256 = "b08ec24d7fa5928b825b556f24dd23cab92e3fd54a1df1861ff2a039bb7a86e7"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def objsha(value):
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def read_integer(value):
    if type(value) is int:
        return value
    assert type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]*)", value)
    return int(value)


def save_new(path, value):
    path = Path(path)
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2) + "\n")


def load_bound(model_path):
    raw = Path(model_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert objsha(model) == MODEL_SHA256 and objsha(model["matrix"]) == MATRIX_SHA256
    base_path = Path(__file__).resolve().parents[1] / "logs/root-prism-free/f0-boolean-fractional-model.json.gz"
    assert sha(base_path) == BASE_FILE_SHA256
    base = json.loads(gzip.decompress(base_path.read_bytes()))
    assert model["matrix"]["equalities"][:686] == base["matrix"]["equalities"]
    assert model["matrix"]["inequalities"][:11449] == base["matrix"]["inequalities"]
    assert sha(Path(__file__).with_name("root_prism_free_f0_second_moments_exact.py")) == HELPER_SHA256
    assert sha(Path(__file__).with_name("root_prism_free_f0_second_moments_query.py")) == DRIVER_SHA256
    return model, base


def literal_domain(model, base):
    data = base["validation"]
    triples, core = data["triples"], data["core"]
    assert len(triples) == 480 and triples == sorted(triples)
    assert len(set(tuple(h) for h in triples)) == 480
    assert all(h == sorted(set(h)) and len(h) == 3 and 0 <= h[0] <= h[-1] < 18 for h in triples)
    assert len(core) == 21
    assert all(not ((core[i] >> i) & 1) for i in range(21))
    assert all(((core[i] >> j) & 1) == ((core[j] >> i) & 1) for i in range(21) for j in range(21))
    gram = []
    for i in range(18):
        for j in range(i, 18):
            quota = 12*(i == j)+2-(core[i+3] & core[j+3]).bit_count()-((core[i+3] >> (j+3)) & 1)
            support = [a for a, h in enumerate(triples) if i in h and j in h]
            gram.append({"family": "Gram", "core_pair": [i, j], "quota": quota, "support": support})
    rows = gram + [{"family": "population", "quota": 60, "support": list(range(480))}]
    assert rows == model["original_selector_equalities"]
    targets = [[2-int(i in h)-sum((core[i+3] >> (j+3)) & 1 for j in h)
                for i in range(18)] for h in triples]
    assert targets == data["targets"] and all(sum(q) == 24 for q in targets)
    edges = []
    sets = list(map(set, triples))
    for a in range(480):
        for b in range(a+1, 480):
            if len(sets[a] & sets[b]) <= 1 and all(targets[a][i] > 0 for i in triples[b]) and all(targets[b][i] > 0 for i in triples[a]):
                edges.append([a, b])
    assert edges == data["edges"] and len(edges) == 68394
    pairs = list(itertools.combinations(range(480), 2))
    pair_index = {p: i for i, p in enumerate(pairs)}
    quota_zeros = set()
    for row in gram:
        if row["quota"] == 1:
            quota_zeros.update(itertools.combinations(row["support"], 2))
    motif_zeros = {tuple(sorted(pair)) for pair in data["motif_pairs"]}
    assert len(quota_zeros) == 4320 and len(motif_zeros) == 90 and quota_zeros.isdisjoint(motif_zeros)
    zeros = quota_zeros | motif_zeros
    recorded = {pairs[c["pair_id"]] for c in model["zero_moment_certificates"]}
    assert len(recorded) == len(model["zero_moment_certificates"]) == 4410 and recorded == zeros
    assert not zeros.intersection(map(tuple, edges))
    for certificate in model["zero_moment_certificates"]:
        pair = pairs[certificate["pair_id"]]
        if certificate["kind"] == "quota-one nonnegative lifted equality":
            row = gram[certificate["selector_Gram_row"]]
            assert row["quota"] == 1 and all(a in row["support"] for a in pair)
            assert sorted([certificate["anchor"], certificate["other"]]) == list(pair)
        else:
            assert pair in motif_zeros
    assert all(pair_index[p] < 114960 for p in zeros)
    return {"rows": rows, "targets": targets, "pairs": pairs, "zeros": zeros, "edges": edges}


def matrix_point(matrix, point):
    den = read_integer(point["denominator"])
    value = list(map(read_integer, point["numerators"]))
    assert den > 0 and len(value) == matrix["variables"]
    assert all(0 <= v <= den for v in value)
    for row in matrix["equalities"]:
        assert sum(c*value[j] for j, c in row["terms"]) == row["rhs"]*den
    for row in matrix["inequalities"]:
        assert sum(c*value[j] for j, c in row["terms"]) <= row["rhs"]*den
    return den, value


def expand_orbits(values, orbits, size):
    output = [None]*size
    assert len(values) == len(orbits)
    for value, members in zip(values, orbits):
        for i in members:
            assert 0 <= i < size and output[i] is None
            output[i] = value
    assert None not in output
    return output


def literal_point(model, base, point):
    domain = literal_domain(model, base)
    den, values = matrix_point(model["matrix"], point)
    data = base["validation"]
    x = expand_orbits(values[:42], data["selector_orbits"], 480)
    Y = expand_orbits(values[42:5847], data["edge_orbits"], 68394)
    flatZ = expand_orbits(values[5847:], model["pair_orbits"], 114960)
    Z = [[0]*480 for _ in range(480)]
    for a in range(480):
        Z[a][a] = x[a]
    for p, (a, b) in enumerate(domain["pairs"]):
        Z[a][b] = Z[b][a] = flatZ[p]
        assert flatZ[p] == values[5847+model["pair_to_orbit"][p]]
    assert all(0 <= v <= den for v in x+Y+flatZ)
    for row in domain["rows"]:
        assert sum(x[a] for a in row["support"]) == row["quota"]*den
    mixed = [[0]*18 for _ in range(480)]
    for value, (a, b) in zip(Y, domain["edges"]):
        assert value <= x[a] and value <= x[b] and value <= Z[a][b]
        for i in data["triples"][b]:
            mixed[a][i] += value
        for i in data["triples"][a]:
            mixed[b][i] += value
    for a in range(480):
        assert mixed[a] == [q*x[a] for q in domain["targets"][a]]
        for row in domain["rows"]:
            assert sum(Z[a][b] for b in row["support"]) == row["quota"]*x[a]
    for a, b in data["motif_pairs"]:
        assert x[a]+x[b] <= den
    for row in base["Boolean_validation"]["full_rows"]:
        assert sum(read_integer(c)*x[a] for a, c in row["terms"]) <= read_integer(row["rhs"])*den
    assert len(base["Boolean_validation"]["full_rows"]) == 4416
    for a, b in domain["pairs"]:
        assert 0 <= Z[a][b] <= min(x[a], x[b])
        assert Z[a][b] >= x[a]+x[b]-den
    for a, b in domain["zeros"]:
        assert Z[a][b] == 0
    return {"status": "PASS: independent full literal rational point replay",
            "full_rows": 650350, "full_variable_bounds": 183834,
            "Gram_rows": 171, "population_rows": 1, "mixed_rows": 8640,
            "activation_rows": 136788, "motif_rows": 90, "Boolean_rows": 4416,
            "RLT_rows": 82560, "pair_bound_rows": 344880, "Y_to_Z_rows": 68394,
            "certified_zero_rows": 4410, "denominator_bits": den.bit_length(),
            "PSD_checked": False, "graph_constructed": False}


def finite_box_ray(matrix, certificate):
    lam = list(map(read_integer, certificate["equality_multipliers"]))
    mu = list(map(read_integer, certificate["inequality_multipliers"]))
    assert len(lam) == len(matrix["equalities"]) and len(mu) == len(matrix["inequalities"])
    assert all(v >= 0 for v in mu)
    coefficients = [0]*matrix["variables"]
    rhs = 0
    for rows, weights in ((matrix["equalities"], lam), (matrix["inequalities"], mu)):
        for row, weight in zip(rows, weights):
            rhs += weight*row["rhs"]
            for j, coefficient in row["terms"]:
                coefficients[j] += weight*coefficient
    # The box minimum of the summed left side is sum min(coefficient,0).
    box_minimum = sum(min(c, 0) for c in coefficients)
    gap = rhs-box_minimum
    return {"strict": gap < 0, "gap": str(gap), "rhs": str(rhs),
            "box_minimum": str(box_minimum), "row_count": len(lam)+len(mu)}


def controls():
    feasible = {"variables": 2, "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 1}],
                "inequalities": [{"terms": [[0, 1], [1, -1]], "rhs": 0}]}
    matrix_point(feasible, {"denominator": "3", "numerators": ["1", "2"]})
    feasible_checks = 0
    for lam in range(-8, 9):
        for mu in range(9):
            assert not finite_box_ray(feasible, {"equality_multipliers": [lam], "inequality_multipliers": [mu]})["strict"]
            feasible_checks += 1
    impossible = {"variables": 2, "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 3}], "inequalities": []}
    assert finite_box_ray(impossible, {"equality_multipliers": [-1], "inequality_multipliers": []})["gap"] == "-1"
    assert finite_box_ray(impossible, {"equality_multipliers": [str(-(1 << 131))], "inequality_multipliers": []})["gap"] == str(-(1 << 131))
    try:
        finite_box_ray(feasible, {"equality_multipliers": [0], "inequality_multipliers": [-1]})
    except AssertionError:
        pass
    else:
        raise AssertionError("negative inequality multiplier accepted")
    return {"status": "PASS", "feasible_multiplier_controls": feasible_checks,
            "strict_controls": 2, "large_integer_bits": 132, "negative_multiplier_rejected": True,
            "production_optimizer_calls": 0}


def preflight(model_path):
    model, base = load_bound(model_path)
    domain = literal_domain(model, base)
    return {"status": "PASS: independent domain and exact replay preflight; no optimizer",
            "source_sha256": sha(__file__), "model_file_sha256": MODEL_FILE_SHA256,
            "model_sha256": MODEL_SHA256, "matrix_sha256": MATRIX_SHA256,
            "driver_sha256": DRIVER_SHA256, "helper_sha256": HELPER_SHA256,
            "literal_domain": {"selectors": 480, "edges": len(domain["edges"]),
                               "pairs": len(domain["pairs"]), "zeros": len(domain["zeros"]),
                               "original_equalities": len(domain["rows"])},
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
    assert 0 < result["requested_lp_seconds"] <= 60 and 0 < result["requested_exact_seconds"] <= 60
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
        assert result["optimizer_calls_recorded"] == numeric["optimizer_calls"]
        report["original_optimizer_calls"] = numeric["optimizer_calls"]
        if numeric.get("basis_valid"):
            assert len(numeric["column_basis_status"]) == 15589 and len(numeric["row_basis_status"]) == 53287
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

