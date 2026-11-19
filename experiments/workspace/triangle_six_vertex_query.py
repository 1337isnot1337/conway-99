"""One exact query of all 180 blocks on thirty triangle-containing six-roots.

The classes include every triangle meeting the six labelled root vertices.
The constant class vector is not assumed to be a kernel.
"""
import argparse
import gzip
import json
from pathlib import Path
import time

import triangle_incidence_projector_moments as base
import triangle_projector_conditioned_query as arithmetic

BINDINGS = {
    "base_source": "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9",
    "arithmetic_source": "cd167c52b7b646a64e4faf58816212d427d1c280a45070e77a5eb8b0a29abb43",
    "builder_source": "0749e9850d52949d73eb5ac03ca6111c769accbba15ecd62bd2846e87ea2eaf8",
    "preparation": "34bff87bcb9d5dfae1a76fe858060675f7455dea4ec547501b234a9f31e1556d",
    "model_raw": "c0c518ad5c4446a3318261bfa4664b4c7299542e08af9b43471152f8bcf1bfc4",
    "model_gzip": "865fd8b034387d297ea0bdac4774e5d370c621b46720f241d3733b5b02d34a67",
    "point": "0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df",
}
FAMILIES = ["minus", "plus", "scalar", "Q", "minus_schur", "plus_schur"]
ROOTS = [50, 51, 52, 53, 60, 62, 67, 68, 69, 70, 71, 72, 76, 77, 79,
         80, 83, 84, 85, 86, 87, 88, 90, 93, 94, 95, 96, 97, 98, 99]
ORDERS = [220, 176, 110, 52, 139, 86, 150, 122, 114, 77, 78, 43, 75, 91,
          50, 109, 92, 75, 44, 74, 57, 47, 53, 60, 36, 24, 44, 39, 26, 11]


def inputs(directory, point):
    assert base.digest(Path(base.__file__).read_bytes()) == BINDINGS["base_source"]
    assert base.digest(Path(arithmetic.__file__).read_bytes()) == BINDINGS["arithmetic_source"]
    builder = Path(__file__).with_name("triangle_six_vertex_projectors.py")
    assert base.digest(builder.read_bytes()) == BINDINGS["builder_source"]
    raw = (directory / "preparation.json").read_bytes()
    assert base.digest(raw) == BINDINGS["preparation"]
    prep = json.loads(raw)
    assert prep["complete_thirty_root_coverage"] and prep["classes"] == 2374
    assert prep["family_blocks"] == {name: 30 for name in FAMILIES}
    assert prep["all_thirty_old_Q_tensors_recovered"]
    assert prep["only_triangle_containing_roots"] and not prep["all_62_roots_covered"]
    packed = (directory / "model.json.gz").read_bytes()
    assert base.digest(packed) == BINDINGS["model_gzip"] == prep["model_gzip_sha256"]
    raw = gzip.decompress(packed)
    assert base.digest(raw) == BINDINGS["model_raw"] == prep["model_raw_sha256"]
    model = json.loads(raw)
    assert model["all_intersecting_triangle_classes_retained"]
    assert model["only_thirty_triangle_containing_roots"] and not model["all_62_roots_covered"]
    assert model["constant_class_vector_is_not_assumed_to_be_a_kernel"]
    assert set(model["families"]) == set(FAMILIES)
    assert [d["root_type"] for d in model["domains"]] == ROOTS
    assert [len(d["classes"]) for d in model["domains"]] == ORDERS
    for name in FAMILIES:
        blocks = model["families"][name]
        assert [b["root_type"] for b in blocks] == ROOTS
        assert [b["order"] for b in blocks] == ORDERS
    assert [(f["root_type"], f["family"]) for f in model["root_schur_forms"]] == [
        (r, f) for r in ROOTS for f in ("minus", "plus")
    ]
    assert [f["root_type"] for f in model["first_moment_forms"]] == ROOTS
    raw = point.read_bytes()
    assert base.digest(raw) == BINDINGS["point"]
    counts = json.loads(raw)["induced_counts"]
    assert len(counts) == 48965 and all(type(c) is int and c >= 0 for c in counts)
    return model, counts


def kernel_checks(model, name, root_position, matrix):
    domain = model["domains"][root_position]
    checked = {}
    if name in ("Q", "minus_schur", "plus_schur"):
        stars = []
        for vertex in range(6):
            chosen = [
                i for i, c in enumerate(domain["classes"])
                if c["root_intersection_mask"] & (1 << vertex)
            ]
            stars.append(all(sum(row[i] for i in chosen) == 0 for row in matrix))
        checked["all_six_root_point_stars_zero"] = all(stars)
    if name.endswith("_schur"):
        original = name.removesuffix("_schur")
        form = next(
            f for f in model["root_schur_forms"]
            if f["root_type"] == domain["root_type"] and f["family"] == original
        )
        checked["all_core_triangle_rows_zero"] = all(
            all(x == 0 for x in matrix[i])
            for i in form["core_triangle_class_indices"]
        )
    return checked


def matrices_at_root(model, counts, position):
    rid = ROOTS[position]
    matrices = {}
    for name in FAMILIES:
        block = model["families"][name][position]
        matrices[name] = base.contract({"blocks": [block]}, counts)[rid]
    first = model["first_moment_forms"][position]
    assert first["root_type"] == rid
    p = [counts[gid] * coefficient for gid, coefficient in first["forms"]]
    assert len(p) == ORDERS[position]
    for i in range(ORDERS[position]):
        for j in range(i + 1):
            actual = (
                11 * matrices["Q"][i][j]
                + 110 * matrices["minus"][i][j]
                + 3 * matrices["plus"][i][j]
                + 10 * matrices["scalar"][i][j]
            )
            assert actual == (2310 * p[i] if i == j else 0)
    return matrices


def query(args):
    assert 0 < args.seconds <= 60 and not args.output.exists()
    start = time.monotonic()
    deadline = start + args.seconds
    model, counts = inputs(args.directory, args.point)
    report = {
        "status": "INCOMPLETE",
        "source_sha256": base.digest(Path(__file__).read_bytes()),
        "bindings": BINDINGS,
        "families": FAMILIES,
        "blocks": [],
        "complete_30_root_180_block_coverage": False,
        "all_2374_intersecting_triangle_classes_retained": True,
        "only_thirty_triangle_containing_roots": True,
        "all_62_roots_covered": False,
        "constant_class_vector_is_not_assumed_to_be_a_kernel": True,
        "optimizer_called": False,
        "graph_existence_resolved": False,
    }
    try:
        for position, rid in enumerate(ROOTS):
            base.check_time(deadline)
            matrices = matrices_at_root(model, counts, position)
            for name in FAMILIES:
                base.check_time(deadline)
                block = model["families"][name][position]
                matrix = matrices[name]
                checked = kernel_checks(model, name, position, matrix)
                assert all(checked.values())
                polynomial = arithmetic.characteristic(matrix)
                positive = all(x >= 0 for x in polynomial)
                record = {
                    "family": name,
                    "root_type": rid,
                    "order": len(matrix),
                    "matrix": [list(map(str, row)) for row in matrix],
                    "det_tI_plus_matrix_coefficients": list(map(str, polynomial)),
                    "exact_positive_semidefinite": positive,
                    "kernel_checks": checked,
                }
                report["blocks"].append(record)
                if not positive:
                    vector, value = base.exact_negative_vector(matrix, deadline)
                    form, primitive, reconstructed = arithmetic.vector_form(block, vector, counts)
                    assert reconstructed == value < 0
                    record.update(
                        integer_negative_vector=list(map(str, vector)),
                        quadratic_value=str(value),
                        primitive_induced_count_inequality=form,
                        primitive_value=primitive,
                        fresh_literal_product_replay_required_before_optimization=True,
                    )
            print(json.dumps({"completed_root": rid, "completed_blocks": len(report["blocks"])}), flush=True)
        base.check_time(deadline)
        assert len(report["blocks"]) == 180
        report["complete_30_root_180_block_coverage"] = True
        report["all_127647_coefficient_partition_entries_checked_at_point"] = True
        report["status"] = (
            "EXACT_ALL_180_SIX_ROOT_TRIANGLE_KERNEL_BLOCKS_PSD"
            if all(b["exact_positive_semidefinite"] for b in report["blocks"])
            else "EXACT_SIX_ROOT_TRIANGLE_KERNEL_SEPARATOR"
        )
    except Exception as error:
        report.update(
            status="INCOMPLETE_NO_WHOLE_MODEL_CONCLUSION",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        raise
    finally:
        report["seconds"] = time.monotonic() - start
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k != "blocks"}, indent=2))


def replay(args):
    assert not args.output.exists()
    start = time.monotonic()
    model, counts = inputs(args.directory, args.point)
    raw = args.result.read_bytes()
    saved = json.loads(raw)
    assert saved["source_sha256"] == base.digest(Path(__file__).read_bytes())
    assert saved["bindings"] == BINDINGS and saved["families"] == FAMILIES
    assert saved["complete_30_root_180_block_coverage"] and len(saved["blocks"]) == 180
    assert saved["all_2374_intersecting_triangle_classes_retained"]
    assert saved["only_thirty_triangle_containing_roots"] and not saved["all_62_roots_covered"]
    assert saved["constant_class_vector_is_not_assumed_to_be_a_kernel"]
    assert saved["all_127647_coefficient_partition_entries_checked_at_point"]
    records = []
    position_saved = 0
    for position, rid in enumerate(ROOTS):
        matrices = matrices_at_root(model, counts, position)
        for name in FAMILIES:
            block = model["families"][name][position]
            item = saved["blocks"][position_saved]
            position_saved += 1
            matrix = matrices[name]
            assert item["family"] == name and item["root_type"] == rid and item["order"] == len(matrix)
            assert matrix == [[int(x) for x in row] for row in item["matrix"]]
            checked = kernel_checks(model, name, position, matrix)
            assert checked == item["kernel_checks"] and all(checked.values())
            polynomial = arithmetic.characteristic(matrix)
            assert polynomial == list(map(int, item["det_tI_plus_matrix_coefficients"]))
            positive = all(x >= 0 for x in polynomial)
            assert positive == item["exact_positive_semidefinite"]
            record = {
                "family": name, "root_type": rid, "order": len(matrix),
                "exact_positive_semidefinite": positive, "kernel_checks": checked,
            }
            if positive:
                record["nullity"] = next(i for i, c in enumerate(polynomial) if c)
            else:
                vector = list(map(int, item["integer_negative_vector"]))
                assert len(vector) == len(matrix)
                value = sum(vector[i] * matrix[i][j] * vector[j]
                            for i in range(len(matrix)) for j in range(len(matrix)))
                form, primitive, reconstructed = arithmetic.vector_form(block, vector, counts)
                assert value == reconstructed == int(item["quadratic_value"]) < 0
                assert form == item["primitive_induced_count_inequality"]
                assert primitive == item["primitive_value"]
                assert item["fresh_literal_product_replay_required_before_optimization"]
                record["primitive_value"] = primitive
            records.append(record)
    expected = (
        "EXACT_ALL_180_SIX_ROOT_TRIANGLE_KERNEL_BLOCKS_PSD"
        if all(b["exact_positive_semidefinite"] for b in records)
        else "EXACT_SIX_ROOT_TRIANGLE_KERNEL_SEPARATOR"
    )
    assert saved["status"] == expected
    report = {
        "status": "PASS_EXACT_THIRTY_SIX_ROOT_TRIANGLE_KERNEL_QUERY_REPLAY",
        "source_sha256": base.digest(Path(__file__).read_bytes()),
        "bindings": BINDINGS,
        "result_sha256": base.digest(raw),
        "blocks": records,
        "complete_30_root_180_block_coverage": True,
        "tensor_generation_repeated": False,
        "optimizer_called": False,
        "seconds": time.monotonic() - start,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["query", "replay"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--point", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    if args.mode == "query":
        query(args)
    else:
        assert args.result
        replay(args)


if __name__ == "__main__":
    main()
