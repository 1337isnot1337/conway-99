"""Point-independent exact audit of conditioning on the triangle and component.

The old core has eighteen vertices. Add the three root-triangle vertices.
The plus projector has one core dependency, so two triangle vertices suffice.
No numerical proposal, optimizer, or spectral scan is read or run.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import time

from flint import fmpq_mat

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "old_schur": (BASE+"f0-second-moments-preparation02.json.gz",
                  "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fraction(x):
    return Fraction(str(x))


def submatrix(matrix, rows, columns):
    return fmpq_mat([[matrix[i, j] for j in columns] for i in rows])


def as_strings(matrix):
    return [[str(matrix[i, j]) for j in range(matrix.ncols())]
            for i in range(matrix.nrows())]


def positive_ldl(matrix):
    work = [[fraction(matrix[i, j]) for j in range(matrix.nrows())]
            for i in range(matrix.nrows())]
    pivots = []
    for k in range(len(work)):
        pivot = work[k][k]
        assert pivot > 0
        pivots.append(str(pivot))
        for i in range(k+1, len(work)):
            for j in range(i, len(work)):
                work[i][j] -= work[i][k]*work[k][j]/pivot
                work[j][i] = work[i][j]
    return pivots


def build():
    loaded = {}
    for key, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected
        loaded[key] = json.loads(gzip.decompress(raw))
    data = loaded["domain"]["validation"]
    core, triples = data["core"], data["triples"]
    assert len(core) == 21 and len(triples) == 480
    assert all(((core[i] >> j) & 1) == int(i != j) for i in range(3) for j in range(3))
    fibers = [[j for j in range(18) if (core[i] >> (j+3)) & 1] for i in range(3)]
    assert all(len(f) == 6 for f in fibers)
    assert sorted(j for f in fibers for j in f) == list(range(18))
    adjacency = [[(core[i+3] >> (j+3)) & 1 for j in range(18)] for i in range(18)]
    assert all(sum(row[j] for j in f) == 1 for row in adjacency for f in fibers)
    eta = [[sum(j in h for j in f) for f in fibers] for h in triples]
    deviations = [[v-1 for v in row] for row in eta]
    assert all(sum(row) == 0 for row in deviations)
    pairs = [(a, b) for a in range(480) for b in range(a, 480)]
    reports = []
    for index, (name, diagonal, edge, constant) in enumerate(
            (("plus", 27, -9, 1), ("minus", 44, 11, -2))):
        k21 = fmpq_mat([[diagonal*(i == j)+edge*((core[i] >> j) & 1)+constant
                        for j in range(21)] for i in range(21)])
        old = list(range(3, 21))
        c = submatrix(k21, old, old)
        c_inv = c.inv()
        r = submatrix(k21, list(range(3)), old)
        schur = submatrix(k21, list(range(3)), list(range(3)))-r*c_inv*r.transpose()
        expected_schur = [[18*int(i == j)-6 if name == "plus" else
                           Fraction(1221, 41) if i == j else Fraction(1089, 82)
                           for j in range(3)] for i in range(3)]
        assert as_strings(schur) == [[str(v) for v in row] for row in expected_schur]
        u = fmpq_mat([[constant+edge*int(i in h) for i in range(18)] for h in triples])
        q = fmpq_mat([[constant]*3 for h in triples])-u*c_inv*r.transpose()
        for a, deviation in enumerate(deviations):
            expected = [-3*v if name == "plus" else -Fraction(77, 41)-Fraction(11, 4)*v
                        for v in deviation]
            assert [str(q[a, j]) for j in range(3)] == list(map(str, expected))
        if name == "plus":
            assert k21.rank() == 20
            assert all(sum(schur[i, j] for j in range(3)) == 0 for i in range(3))
            assert all(sum(q[a, j] for j in range(3)) == 0 for a in range(480))
            chosen = [0, 1]+old
        else:
            assert k21.rank() == 21
            chosen = list(range(21))
        selected_core = submatrix(k21, chosen, chosen)
        pivots = positive_ldl(selected_core)
        cross = fmpq_mat([[constant if i < 3 else constant+edge*int(i-3 in h)
                          for i in chosen] for h in triples])
        h_old = u*c_inv*u.transpose()
        h_new = cross*selected_core.inv()*cross.transpose()
        prior = loaded["old_schur"]["PSD_requirements"]["projectors"][index]
        old_den = int(prior["inverse_denominator"])
        assert prior["core_matrix"] == as_integer_matrix(c)
        xmap = [None]*480
        for orbit, members in enumerate(data["selector_orbits"]):
            for a in members:
                assert xmap[a] is None
                xmap[a] = orbit
        pmap = loaded["old_schur"]["pair_to_orbit"]
        off_index = 0
        coefficients = []
        for a, b in pairs:
            dot = sum(x*y for x, y in zip(deviations[a], deviations[b]))
            correction = Fraction(dot, 2) if name == "plus" else Fraction(77, 410)+Fraction(11*dot, 24)
            assert fraction(h_new[a, b]-h_old[a, b]) == correction
            if a == b:
                saved = int(prior["H_diagonal_by_selector_orbit"][xmap[a]])
                coefficients.append(Fraction(diagonal+constant)-fraction(h_new[a, b]))
            else:
                saved = int(prior["H_off_diagonal_by_pair_orbit"][pmap[off_index]])
                off_index += 1
                coefficients.append(Fraction(constant)-fraction(h_new[a, b]))
            assert fraction(h_old[a, b]) == Fraction(saved, old_den)
        assert off_index == 114960
        coefficients.append(Fraction(edge))
        denominator = lcm(*(v.denominator for v in coefficients))
        integers = [int(v*denominator) for v in coefficients]
        divisor = gcd(*integers)
        integers = [v//divisor for v in integers]
        reports.append({
            "family": name, "rank21": k21.rank(), "selected_core_vertices": chosen,
            "selected_core_positive_LDL_pivots": pivots,
            "triangle_schur": as_strings(schur), "residual_cross_vectors_checked": 480,
            "all_115440_full_vs_old_kernel_entries_checked": True,
            "old_saved_kernel_entries_checked": 115440,
            "correction": "dot(d_a,d_b)/2" if name == "plus" else "77/410+11*dot(d_a,d_b)/24",
            "coefficient_common_denominator": denominator, "positive_common_divisor": divisor,
            "primitive_kernel_maximum_absolute_coefficient": max(map(abs, integers)),
            "primitive_kernel_maximum_coefficient_bits": max(abs(v).bit_length() for v in integers),
            "safe_raw_orbit_bound_at_vector1024": 24*1024**2*max(map(abs, integers)),
            "primitive_kernel_sha256": sha(json.dumps(integers,separators=(",", ":")).encode()),
        })
    return {"status": "PASS: exact full-core Schur corrections; no point query",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "fiber_sizes": list(map(len, fibers)), "fiber_neighbor_counts_all_one": True,
            "signature_count": 480, "fiber_count_types": [list(v) for v in sorted(set(map(tuple, eta)))],
            "families": reports, "optimizer_calls": 0, "point_contractions": 0,
            "scope": "Necessary for the fixed F0 component in the prism/F-free split18+18 branch; other component and alignment free.",
            "strict_strength_over_existing_averaged_constraints_not_claimed": True}


def as_integer_matrix(matrix):
    result = [[int(matrix[i, j]) for j in range(matrix.ncols())] for i in range(matrix.nrows())]
    assert fmpq_mat(result) == matrix
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    start = time.monotonic()
    result = build()
    if args.mode == "prepare":
        assert not args.record.exists()
        args.record.write_text(json.dumps(result, indent=2)+"\n")
    else:
        assert json.loads(args.record.read_bytes()) == result
        assert args.output is not None and not args.output.exists()
        args.output.write_text(json.dumps({"status": "PASS: cold full-core Schur audit",
                                          "source_sha256": result["source_sha256"],
                                          "record_sha256": sha(args.record.read_bytes()),
                                          "optimizer_calls": 0, "point_contractions": 0}, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "seconds": time.monotonic()-start,
                      "source_sha256": result["source_sha256"], "families": result["families"]}, indent=2))


if __name__ == "__main__":
    main()
