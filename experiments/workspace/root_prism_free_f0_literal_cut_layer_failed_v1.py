"""Prepare the exact literal selector layer for the complete F0 Fourier target."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = "experiments/logs/root-prism-free/"
INPUTS = {
    "rows": (LOG + "f0-literal-cut-export-ci01/literal-rows.json.gz", "051282b7c8256fa3cad6edd9e9490290cfdfa5f6bef46b609bc32bdd63189b63"),
    "specification": (LOG + "f0-full-fourier-specification-ci01/specification.json.gz", "929703b3a685f95fb28bc6553aef02d5c7f6c879628154c62b8ecfa7d69ba8d5"),
    "preparation": (LOG + "f0-full-fourier-specification-ci01/report.json", "cd96e24126c1ffab578d69d319431d023e055a82acbc883f66e72a9bdf54c96b"),
    "cold": (LOG + "f0-full-fourier-specification-ci01-cold/report.json", "650813eddce7e0c28def494a16756f49b74e1aa13b667806174c13150647e1a5"),
    "radix": ("experiments/workspace/root_prism_free_f0_literal_cut_radix.js", "e484e0e374e5579c75f3bfe9bdac2fa837acf75525d42d6c8f231a560856446c"),
}
ROWS_RAW = "3877ba7ec41c4f85f2d1623cfc5d20fa0d258c8c8319fa5dcd7313f580ac305e"
SPEC_RAW = "46fa44efdbe3640984a010347a3dfb65964b35752c919f4b6aa2fd24317f1d0b"
BASE_VARIABLES, BINARY_COUNT, AUXILIARY_START = 31756, 480, 32236
BASE = 1 << 30
SAFE = (1 << 62) - 1


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    path, expected = INPUTS[name]
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected, name
    if path.endswith(".gz"):
        raw = gzip.decompress(raw)
    if name == "rows":
        assert sha(raw) == ROWS_RAW
    if name == "specification":
        assert sha(raw) == SPEC_RAW
    return json.loads(raw)


def main(directory):
    started = time.monotonic()
    assert not directory.exists()
    rows, spec, prep, cold = [read(name) for name in ("rows", "specification", "preparation", "cold")]
    assert sha((ROOT / INPUTS["radix"][0]).read_bytes()) == INPUTS["radix"][1]
    assert prep["status"].startswith("PASS") and cold["status"].startswith("PASS")
    assert cold["preparation_sha256"] == INPUTS["preparation"][1]
    assert cold["specification_sha256"] == INPUTS["specification"][1]
    assert spec["counts"]["total_variables"] == BASE_VARIABLES
    assert spec["counts"]["target_constraints"] == 54037
    assert spec["counts"]["initial_constraints"] == 53920
    assert len(rows) == 4416 and sum(len(row["terms"]) for row in rows) == 442308
    domains = [[int(d[0]), int(d[-1])] for d in spec["target_variable_domains"]]
    assert len(domains) == BASE_VARIABLES
    variables = [
        {"id": BASE_VARIABLES + a, "kind": "literal", "selector": a, "domain": ["0", "1"]}
        for a in range(BINARY_COUNT)
    ]
    domains.extend([[0, 1] for _ in range(BINARY_COUNT)])
    linear = []
    inverse = spec["literal_inverse_rows"]
    assert len(inverse) == BINARY_COUNT
    for a, entry in enumerate(inverse):
        assert entry["selector"] == a and entry["denominator"] == 12
        terms = [[j, str(c)] for j, c in entry["terms"]]
        assert all(0 <= j < 18764 for j, c in entry["terms"])
        terms.append([BASE_VARIABLES + a, "-12"])
        assert terms == sorted(terms) and len({j for j, c in terms}) == len(terms)
        linear.append({"terms": terms, "domain": ["0", "0"]})
    records, next_id = [], AUXILIARY_START
    for row_id, original in enumerate(rows):
        assert set(original) == {"terms", "rhs"} and original["rhs"] == "0"
        columns = [j for j, c in original["terms"]]
        assert columns == sorted(set(columns)) and all(0 <= j < BINARY_COUNT for j in columns)
        assert all(str(int(c)) == c and int(c) != 0 for j, c in original["terms"])
        shifted = {"terms": [[BASE_VARIABLES + j, c] for j, c in original["terms"]], "rhs": original["rhs"]}
        coefficients = [int(c) for j, c in shifted["terms"]]
        rhs = int(shifted["rhs"])
        first_row, first_variable = len(linear), next_id
        if sum(map(abs, coefficients)) + abs(rhs) <= SAFE:
            route, digits = "direct", 0
            lower = sum(min(0, c) for c in coefficients)
            linear.append({"terms": shifted["terms"], "domain": [str(lower), str(rhs)]})
        else:
            route = "radix"
            slack_upper = max(0, rhs - sum(min(0, c) for c in coefficients))
            magnitude = max([abs(rhs), slack_upper] + list(map(abs, coefficients)))
            digits, capacity = 1, BASE
            while magnitude >= capacity:
                digits += 1
                capacity *= BASE
            assert digits == 3 and 4404 <= row_id < 4416
            carry_bound = len(coefficients) + 2
            for limb in range(digits):
                variables.append({"id": next_id, "kind": "slack", "row": row_id, "limb": limb,
                                  "domain": ["0", str(BASE - 1)]})
                domains.append([0, BASE - 1])
                next_id += 1
            for limb in range(1, digits):
                variables.append({"id": next_id, "kind": "carry", "row": row_id, "limb": limb,
                                  "domain": [str(-carry_bound), str(carry_bound)]})
                domains.append([-carry_bound, carry_bound])
                next_id += 1
            def digit(value, limb):
                return (-1 if value < 0 else 1) * ((abs(value) // (BASE ** limb)) % BASE)
            for limb in range(digits):
                terms = [[j, str(digit(int(c), limb))] for j, c in shifted["terms"] if digit(int(c), limb)]
                terms.append([first_variable + limb, "1"])
                if limb:
                    terms.append([first_variable + digits + limb - 1, "1"])
                if limb + 1 < digits:
                    terms.append([first_variable + digits + limb, str(-BASE)])
                terms.sort()
                value = str(digit(rhs, limb))
                linear.append({"terms": terms, "domain": [value, value]})
        records.append({
            "original_row_id": row_id, "original_row_sha256": sha(canonical(original)),
            "shifted_row_sha256": sha(canonical(shifted)), "route": route,
            "linear_offset": first_row, "linear_count": len(linear) - first_row,
            "first_auxiliary": first_variable, "auxiliary_count": next_id - first_variable,
            "radix_digits": digits,
        })
    assert [r["original_row_id"] for r in records if r["route"] == "direct"] == list(range(4404))
    assert [r["original_row_id"] for r in records if r["route"] == "radix"] == list(range(4404, 4416))
    assert len(variables) == 540 and next_id == len(domains) == 32296 and len(linear) == 4920
    assert [v["id"] for v in variables] == list(range(BASE_VARIABLES, next_id))
    maximum_activity = 0
    for row in linear:
        lo = hi = absolute = 0
        for j, text in row["terms"]:
            c = int(text)
            a, b = [c * value for value in domains[j]]
            lo += min(a, b)
            hi += max(a, b)
            absolute += max(abs(a), abs(b))
        assert -SAFE <= lo <= hi <= SAFE and hi - lo <= (1 << 63) - 1
        assert absolute + max(abs(int(v)) for v in row["domain"]) <= SAFE
        maximum_activity = max(maximum_activity, absolute)
    domain_sum = sum(max(abs(lo), abs(hi), hi - lo) for lo, hi in domains)
    assert domain_sum < (1 << 63) - 1
    definition = {
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {key: {"path": path, "sha256": digest} for key, (path, digest) in INPUTS.items()},
        "rows_raw_sha256": ROWS_RAW, "specification_raw_sha256": SPEC_RAW,
    }
    layer = {
        "schema": "conway99.f0.literal-cut-native-layer.v1",
        "status": "EXACT_LITERAL_LAYER_SPECIFICATION; native model not built",
        "definition": definition, "base_native_variables": BASE_VARIABLES,
        "binary_offset": BASE_VARIABLES, "binary_count": BINARY_COUNT,
        "auxiliary_start": AUXILIARY_START, "next_variable": next_id,
        "variables": variables, "linear_constraints": linear, "cut_records": records,
        "counts": {
            "literal_Booleans": 480, "inverse_links": 480, "original_cuts": 4416,
            "direct_cuts": 4404, "radix_cuts": 12, "radix_equalities": 36, "radix_auxiliaries": 60,
            "added_variables": 540, "added_linear_constraints": 4920,
            "final_variables": 32296, "final_target_constraints": 58957,
            "final_initial_constraints": 58840, "external_pool_constraints": 117,
            "total_products": 16280, "total_tables": 44,
        },
        "arithmetic": {
            "maximum_new_sum_absolute_term_bounds": str(maximum_activity),
            "whole_final_variable_domain_sum": str(domain_sum),
            "all_original_coefficients_retained_exactly": True,
            "coefficient_rounding_or_weakening": False,
        },
        "optimizer_calls": 0, "native_model_built": False,
    }
    raw = canonical(layer)
    assert len(raw) <= 32 << 20
    payload = gzip.compress(raw, mtime=0)
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "layer.json.gz"
    path.write_bytes(payload)
    report = {
        "status": "PASS: exact literal layer prepared; independent replay required",
        "definition": definition,
        "layer": {"path": str(path.relative_to(ROOT)), "sha256": sha(payload),
                  "raw_sha256": sha(raw), "bytes": len(payload), "raw_bytes": len(raw)},
        "counts": layer["counts"], "arithmetic": layer["arithmetic"],
        "seconds": time.monotonic() - started,
        "optimizer_calls": 0, "native_model_built": False,
    }
    (directory / "report.json").write_bytes(canonical(report) + b"\n")
    print(json.dumps({"status": report["status"], "layer": report["layer"], "seconds": report["seconds"]}))


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    main(parser.parse_args().directory.resolve())
