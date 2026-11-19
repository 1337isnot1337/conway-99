"""Exact F0 model with graph Schur cuts and visible-prism restrictions.

All 15,200 variables and the complete frozen 32-selector-PSD model remain.
Append 162 Y=0 equations, the 17+22 proved graph-Schur directions, and the
715 three-exterior prism rows. Identical new inequalities share one row;
every proof input retains its own provenance. No optimizer or eigenscan.
"""
import argparse
from copy import deepcopy
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
PARENT_MATRIX_SHA = "b49a35a0c19e43a70bc8957f0fe09e03f17113ff67caab40a4d4fa63307cca01"
PARENT_MODEL_SHA = "d098a4b84405823aa38e9d2def7b675c6166507f7350937f1dc0f65af7274dcd"
INPUTS = {
    "parent": ("f0-selector-psd-model01.json.gz", "3302546078e2277c8ce30d032110bb527c6a986a74f76fc1f78451bf4da4b804"),
    "full_kernel": ("f0-full-core-schur-kernels01.json.gz", "a49b8309032b2c599c637285f4a4584bb7d55659640e594df1e6fdd50bf826c1"),
    "old_scan": ("f0-graph-schur-cuts-scan01.json.gz", "2e743329a4e241f1d7b3c89e1821d9d1e5419cf1417f3a985563e5b1e8376383"),
    "full_scan": ("f0-full-core-schur-cuts-scan01.json.gz", "d28ee0220975500373085c5913071490f1eb4b31a351aa108501cc6bd5c70a54"),
    "edge_motifs": ("f0-edge-motif-census01.json.gz", "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
    "edge_audit": ("f0-edge-motif-independent-audit.json", "549797f76d7815ce6059399978a0e3788a15314433104e03a4db7e6211c8aae7"),
    "three_prisms": ("f0-three-vertex-prism-cuts01.json.gz", "b445ad3268cb7016a7a5df07cef9c6fda1a0c7d96fa5a560f897c9449814b194"),
    "three_peer": ("f0-three-vertex-prism-independent-source-review.json", "8465bbe9e202a036026533bf2c56e2e299efb60c9013a43b5061b013743828b6"),
}
SOURCES = {
    "kernel": ("root_prism_free_f0_full_core_schur_kernels.py", "141392693e8d4b7e140c329cfa4128b8794bd376713558394ef014975e2fc63f"),
    "cut": ("root_prism_free_f0_graph_schur_cuts.py", "45ce5c3cd1dffa1eaef611b4aa31964244d87e2f2c5078b99b417aa4ffb8edb5"),
    "three_prisms": ("root_prism_free_f0_three_vertex_prism_cuts.py", "8f468ed033b66b61a9c9452ead079f41b6e738d3b9dfaadee476ced49104ce22"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def read_inputs():
    result = {}
    for key, (name, expected) in INPUTS.items():
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected
        result[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    return result


def module(key):
    name, expected = SOURCES[key]
    path = Path(__file__).with_name(name)
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location("f0_schur_motif_bound_" + key, path)
    answer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(answer)
    return answer


def mathematical_row(row):
    return {"terms": deepcopy(row["terms"]), "rhs": row["rhs"]}


def row_key(row):
    return canonical(mathematical_row(row))


def row_scale(row):
    largest = max((abs(c) for _, c in row["terms"]), default=0)
    scale = 1 << max(0, largest.bit_length() - 1)
    for value in [row["rhs"]] + [c for _, c in row["terms"]]:
        assert type(value) is int and abs(value) < 2**53
        assert Fraction(float(value) / scale) == Fraction(value, scale)
    return scale


def append_inequality(inequalities, scales, index, row, family):
    key = row_key(row)
    if key in index:
        return index[key], False
    position = len(inequalities)
    index[key] = position
    added = mathematical_row(row)
    added["family"] = family
    inequalities.append(added)
    scales.append(row_scale(added))
    return position, True


def assembly_controls():
    original = [{"terms": [[0, -1], [1, 1]], "rhs": 0, "family": "old"}]
    rows, scales = deepcopy(original), [1]
    index = {row_key(row): i for i, row in enumerate(rows)}
    assert append_inequality(rows, scales, index,
                             {"terms": [[0, -1], [1, 1]], "rhs": 0, "ignored": "proof"}, "new") == (0, False)
    assert append_inequality(rows, scales, index,
                             {"terms": [[0, 5], [1, -9]], "rhs": 0}, "new") == (1, True)
    assert rows[:1] == original and scales == [1, 8]
    count = 0
    for c in (-2**31 + 1, -9, -1, 0, 1, 9, 2**31 - 1):
        for d in (1, 3, 7):
            row = {"terms": [[0, c]], "rhs": 0}
            scale = row_scale(row)
            assert (c * Fraction(2, d) <= 0) == (Fraction(c, scale) * Fraction(2, d) <= 0)
            count += 1
    # Appending equalities shifts combined indices, not the inequality scales.
    old_eq_scales, new_eq_scales = [1, 1], [1, 1, 1]
    combined = old_eq_scales + new_eq_scales + scales
    assert combined[len(old_eq_scales) + len(new_eq_scales):] == scales
    return {"status": "PASS: proof-preserving deduplication, scale and combined-index controls",
            "exact_large_integer_scaling_controls": count, "optimizer_calls": 0}


def verify_edge_witnesses(domain, census):
    core, triples, edges = domain["core"], domain["triples"], domain["edges"]
    zeros = census["forced_zero_original_Y_variables"]
    assert len(zeros) == len(set(zeros)) == 162
    assert all(42 <= j < 5847 for j in zeros)
    forbidden = {e for j in zeros for e in domain["edge_orbits"][j - 42]}
    witnessed = set()
    for item in census["literal_motif_witnesses"]:
        e = item["edge_id"]
        assert e not in witnessed and item["kind"] == "P"
        witnessed.add(e)
        a, b = edges[e]
        assert item["pair"] == [a, b] and 42 + domain["emap"][e] in zeros
        rows = core[:] + [0, 0]
        for v, h in ((21, triples[a]), (22, triples[b])):
            for i in h:
                rows[v] |= 1 << (i + 3)
                rows[i + 3] |= 1 << v
        rows[21] |= 1 << 22
        rows[22] |= 1 << 21
        sites = item["sites"]
        assert len(sites) == len(set(sites)) == 6
        for side in (sites[:3], sites[3:]):
            assert all(rows[u] >> v & 1 for u in side for v in side if u != v)
        assert all(sum(rows[u] >> v & 1 for v in sites[3:]) == 1 for u in sites[:3])
        assert all(sum(rows[v] >> u & 1 for u in sites[:3]) == 1 for v in sites[3:])
    assert witnessed == forbidden and len(witnessed) == 1884
    return zeros


def build():
    inputs = read_inputs()
    parent = inputs["parent"]
    assert sha(canonical(parent)) == PARENT_MODEL_SHA
    assert sha(canonical(parent["matrix"])) == PARENT_MATRIX_SHA
    assert inputs["edge_audit"]["status"].startswith("PASS")
    assert inputs["three_peer"]["status"].startswith("PASS")
    assert inputs["three_peer"]["source_sha256"] == SOURCES["three_prisms"][1]
    kernels, cuts, three = module("kernel"), module("cut"), module("three_prisms")
    # One complete exact domain/inverse reconstruction serves both core sizes.
    domain, old_kernels, independent = kernels.load_inputs()
    _, _, deviations = kernels.fiber_data(domain)
    full_kernels = {name: kernels.full_kernel(domain, old_kernels[name], deviations,
                   independent["families"][i], float("inf")) for i, name in enumerate(("plus", "minus"))}
    assert inputs["full_kernel"]["kernels"] == [full_kernels[k] for k in ("plus", "minus")]
    assert inputs["full_kernel"]["source_sha256"] == SOURCES["kernel"][1]
    assert three.build(30) == inputs["three_prisms"]
    zeros = verify_edge_witnesses(domain, inputs["edge_motifs"])
    matrix = deepcopy(parent["matrix"])
    old_eq, old_ineq = len(matrix["equalities"]), len(matrix["inequalities"])
    assert (matrix["variables"], old_eq, old_ineq) == (15200, 5973, 15751)
    assert matrix["lower"] == 0 and matrix["upper"] == 1
    old_scales = parent["numerical_row_scales"]
    assert len(old_scales) == old_eq + old_ineq
    eq_scales, inequality_scales = old_scales[:old_eq], old_scales[old_eq:]
    zero_records = []
    for original in zeros:
        reduced = domain["reverse"][original]
        assert reduced == original and original not in domain["fixed"]
        position = len(matrix["equalities"])
        matrix["equalities"].append({"terms": [[reduced, 1]], "rhs": 0,
                                      "family": "visible two-exterior prism edge zero"})
        eq_scales.append(1)
        zero_records.append({"original_variable": original, "reduced_variable": reduced,
                             "mathematical_equality_index": position, "edge_orbit": original - 42,
                             "literal_edges": len(domain["edge_orbits"][original - 42])})
    index = {}
    for i, row in enumerate(matrix["inequalities"]):
        index.setdefault(row_key(row), i)
    schur_records, triple_records = [], []
    for name, expected_count, by_family in (("old_scan", 17, old_kernels), ("full_scan", 22, full_kernels)):
        scan = inputs[name]
        assert len(scan["cuts"]) == expected_count and scan["status"] == "EXACT_CUTS"
        assert scan["model_sha256"] == PARENT_MODEL_SHA
        assert scan["optimizer_calls"] == 0
        for i, saved in enumerate(scan["cuts"]):
            family = saved["family"]
            certificate = cuts.cut(domain, by_family[family], saved["vector"])
            assert all(saved[k] == v for k, v in certificate.items())
            position, appended = append_inequality(matrix["inequalities"], inequality_scales, index,
                                                   certificate["row"], name + ": " + family)
            if appended:
                assert inequality_scales[position] == certificate["numerical_row_rule"]["positive_power_of_two_scale"]
            proof = {k: v for k, v in certificate.items() if k != "row"}
            proof.update(input=name, input_cut_index=i, mathematical_inequality_index=position,
                         new_row_appended=appended, row_sha256=sha(row_key(certificate["row"])),
                         actual_numerical_row_scale=inequality_scales[position],
                         tiny_minus_gap_possible_redundancy=family == "minus")
            schur_records.append(proof)
    for i, row in enumerate(inputs["three_prisms"]["rows"]):
        position, appended = append_inequality(matrix["inequalities"], inequality_scales, index,
                                               row, "visible three-exterior prism")
        triple_records.append({"input_row_index": i, "mathematical_inequality_index": position,
                               "new_row_appended": appended, "first_literal_witness": row["first_witness"],
                               "endpoint": row["endpoint"], "row_sha256": sha(row_key(row))})
    assert len(schur_records) == 39 and len(triple_records) == 715
    assert matrix["equalities"][:old_eq] == parent["matrix"]["equalities"]
    assert matrix["inequalities"][:old_ineq] == parent["matrix"]["inequalities"]
    assert len(matrix["equalities"]) == old_eq + 162
    scales = eq_scales + inequality_scales
    rows = matrix["equalities"] + matrix["inequalities"]
    assert len(scales) == len(rows)
    assert eq_scales[:old_eq] == old_scales[:old_eq]
    assert inequality_scales[:old_ineq] == old_scales[old_eq:]
    maximum_bits = 0
    for row, scale in zip(rows, scales):
        indices = [j for j, c in row["terms"]]
        assert indices == sorted(set(indices)) and all(0 <= j < 15200 for j in indices)
        assert type(scale) is int and scale > 0 and scale & (scale - 1) == 0
        for value in [row["rhs"]] + [c for j, c in row["terms"]]:
            assert type(value) is int and abs(value) < 2**53
            assert Fraction(float(value) / scale) == Fraction(value, scale)
            maximum_bits = max(maximum_bits, abs(value).bit_length())
    for proof in schur_records + triple_records:
        proof["combined_row_index"] = len(matrix["equalities"]) + proof["mathematical_inequality_index"]
    counts = {"variables": 15200, "equalities": len(matrix["equalities"]),
              "inequalities": len(matrix["inequalities"]), "rows": len(rows),
              "nonzeros": sum(len(r["terms"]) for r in rows), "full_selector_domain": 480,
              "full_eligible_edges": 68394, "new_Y_zero_orbits": 162, "new_literal_Y_zeros": 1884,
              "inherited_selector_PSD_cuts": 32, "old18_Schur_proof_inputs": 17,
              "full21_Schur_proof_inputs": 22,
              "new_distinct_Schur_rows": sum(r["new_row_appended"] for r in schur_records),
              "three_exterior_prism_proof_inputs": 715,
              "new_distinct_three_exterior_rows": sum(r["new_row_appended"] for r in triple_records),
              "new_nonzeros": sum(len(r["terms"]) for r in rows) - 380052,
              "maximum_mathematical_coefficient_bits": maximum_bits,
              "maximum_numerical_row_scale": max(scales),
              "original_full_acceptance_rows": 650350, "original_full_acceptance_bounds": 183834}
    return {"schema": "f0-second-moments-Schur-and-prism-model-v1",
            "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS, "bound_sources": SOURCES,
            "parent_model_sha256": PARENT_MODEL_SHA, "parent_matrix_sha256": PARENT_MATRIX_SHA,
            "matrix": matrix, "matrix_sha256": sha(canonical(matrix)),
            "numerical_row_scales": scales, "numerical_row_scales_sha256": sha(canonical(scales)),
            "numerical_scaling": "Keep every inherited row scale; each appended row uses a positive exact power of two.",
            "ray_pullback": "Divide saved numerical multipliers by the row scales as exact Fractions.",
            "zero_certificates": zero_records, "Schur_cut_certificates": schur_records,
            "three_exterior_certificates": triple_records, "counts": counts, "controls": assembly_controls(),
            "scope": {"component_zero_in_global_prism_and_F_free_split18plus18_case": True,
                      "other_component_and_alignment_free": True, "all480_selectors_retained": True,
                      "all68394_edge_variables_lifted_in_quotient": True,
                      "all4416_selector_predicates_and_original_RLT_rows_retained": True,
                      "new_graph_automorphism_or_fixed_selector_assumption": False,
                      "whole_PSD_cone_enforced": False, "minus_small_gap_redundancy_not_resolved": True,
                      "model_feasibility_claimed": False, "component_excluded": False,
                      "optimizer_calls": 0, "eigendecompositions": 0}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    started = time.monotonic()
    model = build()
    raw = canonical(model)
    if args.mode == "prepare":
        assert not args.model.exists()
        args.model.write_bytes(gzip.compress(raw, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.model.read_bytes()))) == raw
    report = {"status": "PASS: exact Schur/prism model " + ("prepared" if args.mode == "prepare" else "cold rebuilt"),
              "source_sha256": sha(Path(__file__).read_bytes()), "model_file_sha256": sha(args.model.read_bytes()),
              "model_sha256": sha(raw), "matrix_sha256": model["matrix_sha256"],
              "numerical_row_scales_sha256": model["numerical_row_scales_sha256"],
              "counts": model["counts"], "controls": model["controls"],
              "inherited_equality_and_inequality_prefixes_unchanged": True,
              "all39_full480_Schur_rows_rederived": True, "all1884_prism_edge_witnesses_checked": True,
              "all715_three_exterior_rows_rederived": True, "optimizer_calls": 0,
              "eigendecompositions": 0, "seconds": time.monotonic() - started}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
