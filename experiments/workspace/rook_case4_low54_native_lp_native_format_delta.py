"""Preserve failed preflight source; repair only cached CSR/CSC transport audit."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "7f3f3db6422932def93ef9b9efa52415a1499d8d0675c48c776d3318f74bfa13"
EXTRA = "def audit_sparse(matrix, storage, starts, indices, values):\n    n, m = matrix[\"variables\"], matrix[\"rows\"]\n    assert storage in (\"rowwise\", \"colwise\")\n    assert len(indices) == len(values) == len(matrix[\"coefficients\"])\n    assert len(starts) == (m if storage == \"rowwise\" else n)+1\n    assert all(type(v) is int for v in starts+indices)\n    assert starts[0] == 0 and starts[-1] == len(indices) and starts == sorted(starts)\n    restored = [[] for _ in range(m)]\n    if storage == \"rowwise\":\n        for r in range(m):\n            for k in range(starts[r], starts[r+1]):\n                assert 0 <= indices[k] < n\n                restored[r].append([indices[k], values[k]])\n    else:\n        for j in range(n):\n            for k in range(starts[j], starts[j+1]):\n                assert 0 <= indices[k] < m\n                restored[indices[k]].append([j, values[k]])\n    p, idx, val = matrix[\"row_pointers\"], matrix[\"column_indices\"], matrix[\"coefficients\"]\n    expected = [[[idx[k], val[k]] for k in range(p[r], p[r+1])] for r in range(m)]\n    assert [sorted(row) for row in restored] == expected\n    assert all(len(row) == len({j for j, value in row}) for row in restored)\n    return {\"storage\": storage, \"entries\": len(values), \"all_signed_entries_exact\": True}\n\n\n"
OLD = "    assert ra.format_ == highspy.MatrixFormat.kRowwise\n    assert starts == matrix[\"row_pointers\"] and indices == matrix[\"column_indices\"]\n    assert values == matrix[\"coefficients\"] and row_lower == matrix[\"row_lower\"] and row_upper == matrix[\"row_upper\"]\n"
NEW = "    assert ra.format_ in (highspy.MatrixFormat.kRowwise, highspy.MatrixFormat.kColwise)\n    transport = audit_sparse(matrix, \"rowwise\" if ra.format_ == highspy.MatrixFormat.kRowwise else \"colwise\",\n                             starts, indices, values)\n    assert row_lower == matrix[\"row_lower\"] and row_upper == matrix[\"row_upper\"]\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    path = ROOT/"experiments/workspace/rook_case4_low54_native_lp_query.py"
    old = path.read_text()
    assert sha(old.encode()) == BASE_SHA
    preserved = path.with_name("rook_case4_low54_native_lp_query_unrun_v2.py")
    assert not preserved.exists()
    preserved.write_text(old)
    assert old.count("def native(specification, directory):\n") == 1 and old.count(OLD) == 1
    new = old.replace("def native(specification, directory):\n", EXTRA+"def native(specification, directory):\n")
    new = new.replace(OLD, NEW)
    before = '             "native_matrix_loads": 1, "every_native_coefficient_and_endpoint_checked": True,'
    after = '             "native_matrix_loads": 1, "native_sparse_transport": transport,\n             "every_native_coefficient_and_endpoint_checked": True,'
    assert new.count(before) == 1
    new = new.replace(before, after)
    old_ast, new_ast = ast.parse(old), ast.parse(new)
    old_functions = {n.name: n for n in old_ast.body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name: n for n in new_ast.body if isinstance(n, ast.FunctionDef)}
    assert set(new_functions) == set(old_functions)|{"audit_sparse"}
    unchanged = {}
    for name, node in old_functions.items():
        if name == "native":
            continue
        a, b = ast.dump(node, include_attributes=False), ast.dump(new_functions[name], include_attributes=False)
        assert a == b
        unchanged[name] = sha(a.encode())
    a = [ast.dump(n, include_attributes=False) for n in old_ast.body if not isinstance(n, ast.FunctionDef)]
    b = [ast.dump(n, include_attributes=False) for n in new_ast.body if not isinstance(n, ast.FunctionDef)]
    assert a == b
    namespace = {}
    exec(compile(ast.Module(body=[new_functions["audit_sparse"]], type_ignores=[]), "<pure transport control>", "exec"), namespace)
    check = namespace["audit_sparse"]
    matrix = {"variables": 4, "rows": 3, "row_pointers": [0, 2, 2, 3],
              "column_indices": [0, 3, 1], "coefficients": [2, -1, 3]}
    check(matrix, "rowwise", [0, 2, 2, 3], [0, 3, 1], [2., -1., 3.])
    check(matrix, "colwise", [0, 1, 2, 2, 3], [0, 2, 0], [2., 3., -1.])
    bads = [
        ("rowwise", [0, 2, 2, 3], [0, 3, 1], [2., -1., 4.]),
        ("colwise", [0, 1, 2, 2, 3], [0, 1, 0], [2., 3., -1.]),
        ("rowwise", [0, 2, 1, 3], [0, 3, 1], [2., -1., 3.]),
        ("rowwise", [0, 2, 2, 3], [0, 0, 1], [2., -1., 3.]),
        ("colwise", [0, 1, 2, 2, 3], [0, 3, 0], [2., 3., -1.]),
        ("colwise", [0, 1, 2, 2, 3], [0, 2, 0], [2., float("nan"), -1.]),
    ]
    rejected = 0
    for args in bads:
        try:
            check(matrix, *args)
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError("bad sparse transport accepted")
    assert rejected == 6
    path.write_text(new)
    report = {"status": "PASS_NARROW_CACHED_CSR_CSC_TRANSPORT_REPAIR",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "old_source": str(preserved.relative_to(ROOT)), "old_sha256": BASE_SHA,
        "new_source": str(path.relative_to(ROOT)), "new_sha256": sha(new.encode()),
        "only_old_function_changed": "native", "one_new_pure_function": "audit_sparse",
        "unchanged_function_AST_hashes": unchanged,
        "module_level_AST_unchanged": True, "positive_CSR_CSC_controls": 2,
        "malformed_transport_controls_rejected": rejected,
        "native_or_solver_imported": False, "native_calls": 0,
        "old_failed_preflight_preserved": "experiments/logs/grids-and-triangles/rook-case4-low54-native-lp-preflight02",
        "mathematical_matrix_or_bound_change": False}
    output = ROOT/"experiments/logs/grids-and-triangles/rook-case4-low54-native-lp-native-format-delta01.json"
    assert not output.exists()
    output.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"new_sha256": report["new_sha256"], "unchanged_functions": len(unchanged),
                      "report_sha256": sha(output.read_bytes()), "controls": [2, rejected]}), flush=True)


if __name__ == "__main__":
    main()
