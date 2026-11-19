"""Reproduce the unrun cache-only transport repair without native imports."""

import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "experiments/workspace/rook_case4_box_hull_membership_query.py"
NEW = ROOT / "experiments/workspace/rook_case4_box_hull_membership_query_cached_unrun_v2.py"
OLD_SHA = "aa557c7b99ec3de71e9ecde3f6f7dfa3ca71066a835086cdd3b3f2eb7be558e5"
STUB = ROOT.parent / "conway-99/.venv/lib/python3.12/site-packages/highspy/_core/__init__.pyi"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main(output):
    original = OLD.read_bytes()
    assert sha(original) == OLD_SHA
    text = original.decode()
    first = "    a = actual.a_matrix_\n"
    last = "    existence = h.getDualRayExist()\n"
    assert text.count(first) == text.count(last) == 1
    begin, end = text.index(first), text.index(last)
    old_block = text[begin:end]
    tail = old_block[len(first):]
    for name, cached in (("start_", "native_starts"), ("index_", "native_indices"), ("value_", "native_values")):
        tail = tail.replace("a." + name, cached)
    new_block = first + ("    native_starts = list(a.start_)\n"
                         "    native_indices = list(a.index_)\n"
                         "    native_values = list(a.value_)\n") + tail
    changed = (text[:begin] + new_block + text[end:]).encode()
    if NEW.exists():
        assert NEW.read_bytes() == changed
    else:
        with NEW.open("xb") as stream:
            stream.write(changed)
    old_ast, new_ast = ast.parse(original), ast.parse(changed)
    old_functions = {node.name: node for node in old_ast.body if isinstance(node, ast.FunctionDef)}
    new_functions = {node.name: node for node in new_ast.body if isinstance(node, ast.FunctionDef)}
    assert old_functions.keys() == new_functions.keys()
    unchanged = []
    for name in old_functions:
        if name != "native_model":
            assert ast.dump(old_functions[name]) == ast.dump(new_functions[name]), name
            unchanged.append(name)
    old_rest = ast.Module(body=[n for n in old_ast.body if not isinstance(n, ast.FunctionDef)], type_ignores=[])
    new_rest = ast.Module(body=[n for n in new_ast.body if not isinstance(n, ast.FunctionDef)], type_ignores=[])
    assert ast.dump(old_rest) == ast.dump(new_rest)
    getters = {name: 0 for name in ("start_", "index_", "value_")}
    for node in ast.walk(new_functions["native_model"]):
        if (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
                and isinstance(node.value, ast.Name) and node.value.id == "a" and node.attr in getters):
            getters[node.attr] += 1
    assert getters == {"start_": 1, "index_": 1, "value_": 1}
    stub = STUB.read_bytes()
    cls = next(n for n in ast.parse(stub).body if isinstance(n, ast.ClassDef) and n.name == "HighsSparseMatrix")
    annotations = {}
    for node in cls.body:
        if (isinstance(node, ast.FunctionDef) and node.name in getters
                and any(isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list)):
            annotations[node.name] = ast.unparse(node.returns)
    assert annotations == {"index_": "list[int]", "start_": "list[int]", "value_": "list[float]"}
    result = {
        "status": "PASS_UNRUN_CACHE_ONLY_NATIVE_TRANSPORT_REPAIR",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "original": {"path": str(OLD.relative_to(ROOT)), "sha256": OLD_SHA},
        "unrun_repaired_source": {"path": str(NEW.relative_to(ROOT)), "sha256": sha(changed)},
        "explicit_old_block": old_block, "explicit_new_block": new_block,
        "unchanged_function_names": unchanged, "unchanged_function_count": len(unchanged),
        "module_level_statements_unchanged": True, "native_getter_load_counts": getters,
        "installed_type_stub_sha256": sha(stub), "getter_return_annotations": annotations,
        "original_successful_result_preserved": True, "configuration01_unchanged": True,
        "native_imports": 0, "optimizer_calls": 0, "source_imports": 0,
        "runtime_speedup_measured": False, "new_configuration_or_query_run": False,
    }
    with output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return result


if __name__ == "__main__":
    assert __debug__ and len(sys.argv) == 2
    result = main(Path(sys.argv[1]))
    print(json.dumps({"status": result["status"], "new_source": result["unrun_repaired_source"],
                      "unchanged_functions": result["unchanged_function_count"]}))
