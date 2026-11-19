"""No-eigensolver control for the single NumPy-Boolean serialization repair."""
import ast
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OLD = "root_prism_free_f0_joint_psd_zero_scan.py"
NEW = "root_prism_free_f0_joint_psd_zero_scan_v2.py"
OLD_SHA = "555ce146b2f7ae05641872d2bd3b8a9a86f690680d1c82e2f32e6ea4640114b7"
NEW_SHA = "3bb5b68da04e94944688b71d7900f064c4b4d246f5c02f4a1569d7e094932cea"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def metadata_node(tree):
    found = [n for n in ast.walk(tree) if isinstance(n, ast.Dict) and
             any(isinstance(k, ast.Constant) and k.value == "minimum_is_numerical_zero_scale" for k in n.keys)]
    assert len(found) == 1
    return found[0]


def check():
    old_raw, new_raw = (Path(__file__).with_name(n).read_bytes() for n in (OLD, NEW))
    assert digest(old_raw) == OLD_SHA and digest(new_raw) == NEW_SHA
    old, new = ast.parse(old_raw), ast.parse(new_raw)
    projected = copy.deepcopy(old)
    node = metadata_node(projected)
    position = next(i for i, k in enumerate(node.keys) if isinstance(k, ast.Constant) and
                    k.value == "minimum_is_numerical_zero_scale")
    node.values[position] = ast.Call(func=ast.Name(id="bool", ctx=ast.Load()),
                                    args=[node.values[position]], keywords=[])
    assert ast.dump(projected, include_attributes=False) == ast.dump(new, include_attributes=False)
    fixed_expression = compile(ast.fix_missing_locations(ast.Expression(metadata_node(new))), "metadata", "eval")
    old_expression = compile(ast.fix_missing_locations(ast.Expression(metadata_node(old))), "old_metadata", "eval")
    checks = 0
    for low in (-1.0, -1e-16, 0.0, 1e-16, 1.0):
        for norm in (0.0, 1.0, 2.0):
            for tolerance in (1e-10, 1e-20):
                local = {"eigenvalues": np.asarray([low, low+1, low+2]), "norm": norm, "tolerance": tolerance}
                value = eval(fixed_expression, {"np": np}, local)
                assert type(value["minimum_is_numerical_zero_scale"]) is bool
                assert json.loads(json.dumps(value, allow_nan=False)) == value
                prior = eval(old_expression, {"np": np}, local)
                assert isinstance(prior["minimum_is_numerical_zero_scale"], np.bool_)
                try:
                    json.dumps(prior, allow_nan=False)
                except TypeError:
                    pass
                else:
                    raise AssertionError("old serialization failure was not reproduced")
                checks += 1
    return {"status": "PASS: single metadata-only AST repair and actual NumPy JSON controls",
            "source_sha256": digest(Path(__file__).read_bytes()), "old_source_sha256": OLD_SHA,
            "new_source_sha256": NEW_SHA, "complete_AST_only_change": "wrap numerical-zero comparison in built-in bool",
            "actual_numpy_metadata_dictionaries_checked": checks,
            "old_failure_reproduced": True, "subjects_imported": False,
            "kernel_or_cache_reconstruction": False, "eigendecompositions": 0, "optimizer_calls": 0}


if __name__ == "__main__":
    result = check()
    output = ROOT/"experiments/logs/root-prism-free/f0-joint-psd-json-control.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True), flush=True)
