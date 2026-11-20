"""Exact complementary triangle-projector blocks on the nine four-roots.

Preparation derives every class first moment from its literal root-plus-
triangle graph. It checks the normalization against every catalogue host
of orders four through seven. No count point enters preparation.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import factorial, gcd, isqrt
from pathlib import Path
import time

from flint import fmpz_mat
import pynauty

import triangle_incidence_projector_moments as base
import triangle_incidence_projector_full_classes as full

BASE_SHA = "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9"
FULL_SHA = "d26499a0eec07c2c80a28818f0a40319fc0b14f54140a28253c820eb00d44f2a"
FULL_PREP_SHA = "48a3788a0ca55dd445971f71dba46be49f4291b0ddd6b920beebb5de87e66fb7"
FULL_RAW_SHA = "819aa1954ce038865404433995eb401ad7111cad0a21992f4ba8c42e3e04687c"
FULL_GZIP_SHA = "9305dffa83a024f574321dd5843244724d3cd82b569c0749d2ed135ccdc01938"
ORDERS = [107, 93, 72, 49, 79, 58, 41, 34, 41]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_checks():
    assert digest(Path(base.__file__).read_bytes()) == BASE_SHA
    assert digest(Path(full.__file__).read_bytes()) == FULL_SHA


def parent_model(directory):
    source_checks()
    raw = (directory / "preparation.json").read_bytes()
    assert digest(raw) == FULL_PREP_SHA
    prep = json.loads(raw)
    compressed = (directory / "model.json.gz").read_bytes()
    assert digest(compressed) == FULL_GZIP_SHA == prep["model_gzip_sha256"]
    raw = gzip.decompress(compressed)
    assert digest(raw) == FULL_RAW_SHA == prep["model_raw_sha256"]
    model = json.loads(raw)
    assert [b["order"] for b in model["blocks"]] == ORDERS
    assert sum(ORDERS) == 574
    return model


def fixed_root_stabilizer(rows):
    """Literal enumeration; permutations fix the four labelled root sites."""
    n = len(rows)
    count = 0
    for tail in permutations(range(4, n)):
        image = tuple(range(4)) + tail
        if all(((rows[a] >> b) & 1) == ((rows[image[a]] >> image[b]) & 1)
               for a, b in combinations(range(n), 2)):
            count += 1
    return count


def prepare_forms(data, parent):
    graphs, levels, aut, _ = data
    lookup = {(len(graphs[i]), pynauty.certificate(base.nauty(graphs[i]))): i
              for n in range(4, 8) for i in levels[n]}
    assert len(lookup) == sum(len(levels[n]) for n in range(4, 8))
    domains = []
    stabilizers = Counter()
    repeated_nonzero = []
    for domain in parent["domains"]:
        records = []
        for index, c in enumerate(domain["classes"]):
            inside, masks = full.class_key(c)
            rows = full.extension(domain["root_rows"], inside, masks)
            assert rows is not None and base.cap_valid(rows)
            graph_id = lookup[len(rows), pynauty.certificate(base.nauty(rows))]
            multiplicities = Counter(masks)
            divisor = 1
            for multiplicity in multiplicities.values():
                divisor *= factorial(multiplicity)
            assert fixed_root_stabilizer(rows) == divisor
            group_order = int(aut[graph_id])
            assert group_order > 0 and group_order % divisor == 0
            coefficient = group_order // divisor
            records.append({"class_index": index, "root_intersection_mask": inside,
                            "outside_masks": list(masks), "literal_rows": list(rows),
                            "catalogue_type": graph_id,
                            "automorphism_order": group_order,
                            "free_label_stabilizer": divisor,
                            "coefficient": coefficient})
            stabilizers[divisor] += 1
            if any(m and k > 1 for m, k in multiplicities.items()):
                repeated_nonzero.append([domain["root_type"], index, graph_id, divisor, coefficient])
        domains.append({"root_type": domain["root_type"], "root_rows": domain["root_rows"],
                        "order": len(records), "classes": records})
    assert [d["order"] for d in domains] == ORDERS
    return {"schema": "conway99.triangle-projector-complement-first-moments.v1",
            "parent_full_model_raw_sha256": FULL_RAW_SHA,
            "catalogue_sha256": base.CATALOGUE_SHA,
            "normalization": "p_C = Aut(H union T) / product_m multiplicity(m)! times the unlabelled induced count of H union T",
            "domains": domains,
            "free_stabilizer_census": dict(sorted(stabilizers.items())),
            "repeated_nonzero_mask_classes": repeated_nonzero,
            "all_574_classes_retained": True, "count_point_loaded": False}


def first_moments(forms, counts):
    return {d["root_type"]: [c["coefficient"] * counts[c["catalogue_type"]]
                            for c in d["classes"]] for d in forms["domains"]}


def direct_first_moments(rows, parent, root_maps):
    out = {d["root_type"]: [0] * len(d["classes"]) for d in parent["domains"]}
    maps = {d["root_type"]: {full.class_key(c): j for j, c in enumerate(d["classes"])}
            for d in parent["domains"]}
    ts = base.triangles(rows)
    root_embeddings = 0
    for root in combinations(range(len(rows)), 4):
        root_id, transports = root_maps[base.graph_code(base.induced(rows, root))]
        for transport in transports:
            labelled = tuple(root[i] for i in transport)
            root_embeddings += 1
            for triangle in ts:
                out[root_id][maps[root_id][full.full_classify(rows, triangle, labelled)]] += 1
    return out, root_embeddings, root_embeddings * len(ts)


def host_controls(data, parent, forms, deadline):
    graphs, levels, aut, _ = data
    _, root_maps = base.domains_and_root_maps(graphs, levels, aut)
    lookup = {(len(graphs[i]), pynauty.certificate(base.nauty(graphs[i]))): i
              for n in range(4, 8) for i in levels[n]}
    records = []
    for order in range(4, 8):
        for graph_id in levels[order]:
            base.check_time(deadline)
            rows = graphs[graph_id]
            counts = [0] * len(graphs)
            for size in range(4, order + 1):
                for subset in combinations(range(order), size):
                    selected = base.induced(rows, subset)
                    pos = lookup[size, pynauty.certificate(base.nauty(selected))]
                    counts[pos] += 1
            actual, embeddings, pairs = direct_first_moments(rows, parent, root_maps)
            proposed = first_moments(forms, counts)
            assert actual == proposed, (graph_id, "first-moment normalization")
            records.append({"host_type": graph_id, "order": order,
                            "labelled_root_embeddings": embeddings,
                            "root_triangle_pairs": pairs,
                            "all_574_forms_equal": True,
                            "direct_first_moments_sha256": digest(base.canonical(actual))})
    assert len(records) == 300
    return records


def location(entry):
    i = (isqrt(8 * entry + 1) - 1) // 2
    j = entry - i * (i + 1) // 2
    assert 0 <= j <= i
    return i, j


def characteristic(matrix):
    n = len(matrix)
    minus = list(map(int, fmpz_mat(matrix).charpoly()))
    plus = [(-1 if (n + i) % 2 else 1) * c for i, c in enumerate(minus)]
    assert len(plus) == n + 1 and plus[-1] == 1
    return plus


def matrices(parent, forms, counts):
    original = base.contract(parent, counts)
    p = first_moments(forms, counts)
    out = {}
    for root_id, M in original.items():
        out[root_id] = [[210 * p[root_id][i] * int(i == j) - M[i][j]
                         for j in range(len(M))] for i in range(len(M))]
    return out, p


def negative_form(block, domain, vector, counts):
    form = Counter()
    for entry, graph_id, coefficient in block["terms"]:
        i, j = location(entry)
        form[graph_id] -= coefficient * vector[i] * vector[j] * (1 if i == j else 2)
    for i, c in enumerate(domain["classes"]):
        form[c["catalogue_type"]] += 210 * c["coefficient"] * vector[i] * vector[i]
    form = {i: c for i, c in form.items() if c}
    value = sum(c * counts[i] for i, c in form.items())
    divisor = 0
    for c in form.values():
        divisor = gcd(divisor, abs(c))
    assert divisor > 0 and value % divisor == 0
    return [[i, str(c // divisor)] for i, c in sorted(form.items())], str(value // divisor), value


def arithmetic_controls():
    cases = [([[1, 1], [1, 1]], True), ([[1, 2], [2, 1]], False),
             ([[0, 1], [1, 0]], False)]
    report = []
    for M, expected in cases:
        cp = characteristic(M)
        assert all(c >= 0 for c in cp) == expected
        row = {"matrix": M, "charpoly": cp, "PSD": expected}
        if not expected:
            v, value = base.exact_negative_vector(M, time.monotonic() + 5)
            # Artificial first moments zero, so parent terms encode -M.
            block = {"terms": [[i * (i + 1) // 2 + j, 0, -M[i][j]]
                               for i in range(2) for j in range(i + 1) if M[i][j]]}
            domain = {"classes": [{"catalogue_type": 0, "coefficient": 0}] * 2}
            form, primitive, exact = negative_form(block, domain, v, [1])
            assert exact == value < 0 and int(primitive) < 0
            row.update(integer_negative_vector=v, value=value, primitive_form=form)
        report.append(row)
    return report


def prepare(args):
    assert 0 < args.seconds <= 60 and not args.directory.exists()
    start = time.monotonic()
    deadline = start + args.seconds
    parent = parent_model(args.full_directory)
    data = base.load_catalogue(args.catalogue)
    forms = prepare_forms(data, parent)
    controls = host_controls(data, parent, forms, deadline)
    tiny = arithmetic_controls()
    base.check_time(deadline)
    raw = base.canonical(forms)
    args.directory.mkdir(parents=True)
    (args.directory / "first-moments.json").write_bytes(raw)
    report = {"status": "COMPLETE_POINT_INDEPENDENT_COMPLEMENTARY_TRIANGLE_PREPARATION",
              "source_sha256": digest(Path(__file__).read_bytes()),
              "base_source_sha256": BASE_SHA, "full_source_sha256": FULL_SHA,
              "parent_preparation_sha256": FULL_PREP_SHA,
              "parent_model_raw_sha256": FULL_RAW_SHA,
              "parent_model_gzip_sha256": FULL_GZIP_SHA,
              "catalogue_sha256": base.CATALOGUE_SHA,
              "first_moments_sha256": digest(raw), "first_moments_bytes": len(raw),
              "root_types": [d["root_type"] for d in forms["domains"]],
              "block_orders": ORDERS, "classes": 574, "lower_entries": 21190,
              "parent_pair_tensor_nonzeros": 135819,
              "new_first_moment_terms": 574,
              "free_stabilizer_census": forms["free_stabilizer_census"],
              "repeated_nonzero_mask_classes": forms["repeated_nonzero_mask_classes"],
              "small_host_controls": controls, "arithmetic_controls": tiny,
              "point_query_requires_separate_gate": True,
              "count_point_loaded": False, "optimizer_called": False,
              "seconds": time.monotonic() - start}
    (args.directory / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("small_host_controls", "repeated_nonzero_mask_classes")}, indent=2))


def inputs(args):
    parent = parent_model(args.full_directory)
    prep_raw = (args.directory / "preparation.json").read_bytes()
    prep = json.loads(prep_raw)
    assert prep["source_sha256"] == digest(Path(__file__).read_bytes())
    assert prep["parent_model_raw_sha256"] == FULL_RAW_SHA
    raw = (args.directory / "first-moments.json").read_bytes()
    assert digest(raw) == prep["first_moments_sha256"]
    forms = json.loads(raw)
    assert forms["parent_full_model_raw_sha256"] == FULL_RAW_SHA
    assert [d["order"] for d in forms["domains"]] == ORDERS
    point_raw = args.point.read_bytes()
    assert digest(point_raw) == base.POINT_SHA
    counts = json.loads(point_raw)["induced_counts"]
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    return parent, forms, counts, digest(prep_raw), digest(raw)


def query(args):
    assert 0 < args.seconds <= 30 and not args.output.exists()
    start = time.monotonic()
    deadline = start + args.seconds
    parent, forms, counts, prep_sha, forms_sha = inputs(args)
    terminal = {"status": "INCOMPLETE", "source_sha256": digest(Path(__file__).read_bytes()),
                "preparation_sha256": prep_sha, "first_moments_sha256": forms_sha,
                "parent_model_raw_sha256": FULL_RAW_SHA, "point_sha256": base.POINT_SHA,
                "blocks": [], "complete_nine_block_coverage": False,
                "optimizer_called": False, "unrestricted_existence_resolved": False}
    try:
        all_matrices, p = matrices(parent, forms, counts)
        for block, domain in zip(parent["blocks"], forms["domains"]):
            base.check_time(deadline)
            root_id = block["root_type"]
            assert domain["root_type"] == root_id
            M = all_matrices[root_id]
            cp = characteristic(M)
            psd = all(c >= 0 for c in cp)
            record = {"root_type": root_id, "order": len(M),
                      "first_moments": list(map(str, p[root_id])),
                      "matrix": [[str(x) for x in row] for row in M],
                      "det_tI_plus_matrix_coefficients": list(map(str, cp)),
                      "exact_positive_semidefinite": psd}
            if not psd:
                v, value = base.exact_negative_vector(M, deadline)
                form, primitive, reconstructed = negative_form(block, domain, v, counts)
                assert reconstructed == value < 0
                record.update(integer_negative_vector=list(map(str, v)), quadratic_value=str(value),
                              primitive_induced_count_inequality=form, primitive_value=primitive)
            terminal["blocks"].append(record)
        base.check_time(deadline)
        terminal["complete_nine_block_coverage"] = True
        terminal["status"] = ("EXACT_ALL_NINE_COMPLEMENTARY_TRIANGLE_BLOCKS_PSD"
                              if all(b["exact_positive_semidefinite"] for b in terminal["blocks"])
                              else "EXACT_COMPLEMENTARY_TRIANGLE_SEPARATOR")
    except Exception as error:
        terminal.update(status="INCOMPLETE_NO_WHOLE_MODEL_CONCLUSION",
                        error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        terminal["seconds"] = time.monotonic() - start
        args.output.write_text(json.dumps(terminal, indent=2) + "\n")
        print(json.dumps({k: v for k, v in terminal.items() if k != "blocks"}, indent=2))


def replay(args):
    assert not args.output.exists()
    start = time.monotonic()
    parent, forms, counts, prep_sha, forms_sha = inputs(args)
    raw = args.result.read_bytes()
    result = json.loads(raw)
    assert result["source_sha256"] == digest(Path(__file__).read_bytes())
    assert result["preparation_sha256"] == prep_sha and result["first_moments_sha256"] == forms_sha
    assert result["parent_model_raw_sha256"] == FULL_RAW_SHA and result["point_sha256"] == base.POINT_SHA
    assert result["complete_nine_block_coverage"] and len(result["blocks"]) == 9
    all_matrices, p = matrices(parent, forms, counts)
    report = []
    for block, domain, saved in zip(parent["blocks"], forms["domains"], result["blocks"]):
        root_id = block["root_type"]
        assert root_id == domain["root_type"] == saved["root_type"]
        M = all_matrices[root_id]
        assert saved["order"] == len(M)
        assert p[root_id] == list(map(int, saved["first_moments"]))
        assert M == [[int(x) for x in row] for row in saved["matrix"]]
        cp = characteristic(M)
        assert cp == list(map(int, saved["det_tI_plus_matrix_coefficients"]))
        psd = all(c >= 0 for c in cp)
        assert psd == saved["exact_positive_semidefinite"]
        record = {"root_type": root_id, "order": len(M), "exact_positive_semidefinite": psd}
        if psd:
            record["nullity"] = next(i for i, c in enumerate(cp) if c)
        else:
            v = list(map(int, saved["integer_negative_vector"]))
            assert len(v) == len(M)
            value = sum(v[i] * M[i][j] * v[j] for i in range(len(M)) for j in range(len(M)))
            form, primitive, reconstructed = negative_form(block, domain, v, counts)
            assert reconstructed == value == int(saved["quadratic_value"]) < 0
            assert form == saved["primitive_induced_count_inequality"] and primitive == saved["primitive_value"]
            record["primitive_value"] = primitive
        report.append(record)
    expected = ("EXACT_ALL_NINE_COMPLEMENTARY_TRIANGLE_BLOCKS_PSD"
                if all(r["exact_positive_semidefinite"] for r in report)
                else "EXACT_COMPLEMENTARY_TRIANGLE_SEPARATOR")
    assert result["status"] == expected
    output = {"status": "PASS_EXACT_COMPLEMENTARY_TRIANGLE_QUERY_REPLAY",
              "source_sha256": digest(Path(__file__).read_bytes()),
              "result_sha256": digest(raw), "preparation_sha256": prep_sha,
              "first_moments_sha256": forms_sha, "parent_model_raw_sha256": FULL_RAW_SHA,
              "point_sha256": base.POINT_SHA, "blocks": report,
              "complete_nine_block_coverage": True, "tensor_generation_repeated": False,
              "optimizer_called": False, "seconds": time.monotonic() - start}
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "query", "replay"])
    parser.add_argument("--full-directory", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path)
    parser.add_argument("--point", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--seconds", type=float, default=30)
    args = parser.parse_args()
    if args.mode == "prepare":
        assert args.catalogue
        prepare(args)
    elif args.mode == "query":
        assert args.point and args.output
        query(args)
    else:
        assert args.point and args.output and args.result
        replay(args)


if __name__ == "__main__":
    main()
