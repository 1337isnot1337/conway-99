"""Append32 exact selector-PSD cuts to the frozen reduced F0 linear model.

The mathematical matrix stays integral. Only numerical new-row scaling uses
explicit positive powers of two. No optimizer or eigendecomposition is called.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
PSD_SOURCE_SHA256 = "64fa05e1947ac0e59801a400e0b9ee61e3c08691156025509c7390732db8bab2"
PARENT_FILE_SHA256 = "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"
PARENT_MATRIX_SHA256 = "5e417221ed814a5a0dcb03e31820871113bcc0eb8af2856dd2ac493958d16f39"
SCAN_GZIP_SHA256 = "5c74497bb70d44bf2fac7002ed16b4657500c4af2518cab196684c9346449e79"
SCAN_RAW_SHA256 = "7f8a2a22007539a67075aeb122ace3f81f800490723b8ca2c3a510c19ef45997"
PSD_PREPARATION_SHA256 = "1e9de6de2fb86809ebdedc751b2e7a5942ce4cf47c211421e65b530cb2f350cf"
NUMERICAL_PROPOSAL_SHA256 = "20674e3a41842e42232df60e24abf3f34a5a5c8ec9a16a258d4906bb58562fd9"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def imported_psd():
    path = Path(__file__).with_name("root_prism_free_f0_selector_psd_cuts.py")
    assert sha(path.read_bytes()) == PSD_SOURCE_SHA256
    spec = importlib.util.spec_from_file_location("f0_bound_selector_psd", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def new_row_scale(row):
    largest = max(abs(c) for j, c in row["terms"])
    assert largest > 0
    scale = 1 << max(0, largest.bit_length()-1)
    assert scale <= largest < 2*scale
    for value in [row["rhs"]]+[c for j, c in row["terms"]]:
        f = float(value)/scale
        num, den = f.as_integer_ratio()
        assert num*scale == value*den
    return scale


def controls():
    # Positive powers of two change neither an inequality nor its exact dual
    # identity. Check both signs and integer/rational boundary proposals.
    from fractions import Fraction
    count = 0
    for a in range(-16, 17):
        if a == 0:
            continue
        for b in range(-3, 4):
            row = {"terms": [[0, a]], "rhs": b}
            scale = new_row_scale(row)
            for n in range(-3, 7):
                x = Fraction(n, 3)
                assert (a*x <= b) == (Fraction(a, scale)*x <= Fraction(b, scale))
                lam = Fraction(n, 7)
                assert lam*Fraction(a, scale) == (lam/scale)*a
                assert lam*Fraction(b, scale) == (lam/scale)*b
                count += 1
    return {"status": "PASS: exact numerical scaling and dual pullback",
            "finite_exact_scaling_controls": count, "optimizer_calls": 0}


def build():
    psd = imported_psd()
    domain = psd.load_domain()
    parent = domain["reduced"]
    assert sha((LOGS/"f0-second-moments-reduced-model.json.gz").read_bytes()) == PARENT_FILE_SHA256
    assert sha(canonical(parent["matrix"])) == PARENT_MATRIX_SHA256
    compressed = (LOGS/"f0-selector-psd-cuts-scan01.json.gz").read_bytes()
    assert sha(compressed) == SCAN_GZIP_SHA256
    raw = gzip.decompress(compressed)
    assert sha(raw) == SCAN_RAW_SHA256
    scan = json.loads(raw)
    assert scan["source_sha256"] == PSD_SOURCE_SHA256
    assert scan["preparation_sha256"] == PSD_PREPARATION_SHA256
    assert scan["numerical_file_sha256"] == NUMERICAL_PROPOSAL_SHA256
    assert len(scan["cuts"]) == 32
    matrix = deepcopy(parent["matrix"])
    old_eq, old_ineq = len(matrix["equalities"]), len(matrix["inequalities"])
    assert (matrix["variables"], old_eq, old_ineq) == (15200, 5973, 15719)
    seen, certificates, scales = set(), [], [1]*(old_eq+old_ineq)
    for i, item in enumerate(scan["cuts"]):
        certificate = psd.cut(domain, item["certificate"]["vector"])
        assert certificate == item["certificate"]
        assert not certificate["unit_box_implied"]
        key = canonical(certificate["row"])
        assert key not in seen
        seen.add(key)
        row = deepcopy(certificate["row"])
        assert row["rhs"] == 0
        row.update(family="augmented selector PSD", PSD_cut=i)
        row_index = len(matrix["inequalities"])
        matrix["inequalities"].append(row)
        scale = new_row_scale(row)
        scales.append(scale)
        record = {k: v for k, v in certificate.items() if k != "row"}
        record.update(scan_cut=i, mathematical_inequality_index=row_index,
                      combined_row_index=old_eq+row_index, numerical_positive_scale=scale)
        certificates.append(record)
    assert matrix["equalities"] == parent["matrix"]["equalities"]
    assert matrix["inequalities"][:old_ineq] == parent["matrix"]["inequalities"]
    assert sha(canonical(parent["matrix"])) == PARENT_MATRIX_SHA256
    rows = matrix["equalities"]+matrix["inequalities"]
    assert len(rows) == len(scales) == 21724
    assert len(matrix["inequalities"]) == 15751
    assert sum(len(r["terms"]) for r in rows) == 380052
    assert all(type(v) is int and abs(v) < 2**53
               for row in rows for v in [row["rhs"]]+[c for j, c in row["terms"]])
    assert all(s > 0 and s & (s-1) == 0 for s in scales)
    assert scales[:21692] == [1]*21692
    return {
        "schema": "f0-reduced-second-moments-plus32-selector-PSD-v1",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {"parent_file_sha256": PARENT_FILE_SHA256,
                   "parent_matrix_sha256": PARENT_MATRIX_SHA256,
                   "PSD_source_sha256": PSD_SOURCE_SHA256,
                   "scan_gzip_sha256": SCAN_GZIP_SHA256, "scan_raw_sha256": SCAN_RAW_SHA256,
                   "PSD_preparation_sha256": PSD_PREPARATION_SHA256,
                   "numerical_proposal_sha256": NUMERICAL_PROPOSAL_SHA256},
        "matrix": matrix, "matrix_sha256": sha(canonical(matrix)),
        "numerical_row_scales": scales, "numerical_row_scales_sha256": sha(canonical(scales)),
        "numerical_scale_rule": "Old rows scale1. New row divides by 2**floor(log2(maximum absolute integer coefficient)).",
        "dual_rule": "Save raw numerical row multipliers. Divide each by its positive row scale exactly before integer Farkas reconstruction.",
        "cut_certificates": certificates,
        "counts": {"variables": 15200, "equalities": 5973, "inequalities": 15751,
                   "rows": 21724, "nonzeros": 380052, "new_PSD_rows": 32,
                   "new_nonzeros": 196350, "full_selectors": 480,
                   "full_original_acceptance_rows": 650350, "full_original_acceptance_bounds": 183834,
                   "full_additional_quadratic_checks": 32,
                   "maximum_new_integer_coefficient_bits": 27,
                   "maximum_numerical_row_scale": max(scales)},
        "scope": {"whole_PSD_cone_enforced": False, "exact_necessary_PSD_directions": 32,
                  "all_original_linear_rows_retained": True, "all4416_selector_cuts_retained": True,
                  "new_selector_assumptions_or_symmetry": False,
                  "proposing_point_feasibility_assumed": False,
                  "graph_or_feasible_point_constructed": False, "component_excluded": False,
                  "optimizer_calls": 0, "eigendecompositions": 0},
        "controls": controls(),
    }


def save_new(path, value):
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    model = build()
    encoded = canonical(model)
    if args.mode == "prepare":
        assert not args.model.exists()
        args.model.write_bytes(gzip.compress(encoded, mtime=0))
    else:
        saved = json.loads(gzip.decompress(args.model.read_bytes()))
        assert canonical(saved) == encoded
    report = {"status": "PASS: exact32-cut model "+("prepared" if args.mode == "prepare" else "cold rebuilt"),
              "source_sha256": sha(Path(__file__).read_bytes()), "model_file_sha256": sha(args.model.read_bytes()),
              "model_sha256": sha(encoded), "matrix_sha256": model["matrix_sha256"],
              "numerical_row_scales_sha256": model["numerical_row_scales_sha256"],
              "counts": model["counts"], "controls": model["controls"],
              "all_original_prefix_rows_unchanged": True, "all32_literal_cuts_rederived": True,
              "optimizer_calls": 0, "eigendecompositions": 0, "seconds": time.monotonic()-started}
    save_new(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

