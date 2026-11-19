"""Cache existing selector handles while appending the unchanged exact rows.

All seed binding, arithmetic, cap checks and provenance come unchanged
from frozen registry v5. Only native variable-handle lookup is cached.
The controller still compares the full native protobuf byte for byte.
"""
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ("experiments/workspace/root_prism_free_f0_direct_master_registry_v5.py",
          "af36bd758df4eb694443a5762c55804027396c68c84e8d15a6399110e75d6fd4")
path = ROOT / LEGACY[0]
assert hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY[1]
spec = importlib.util.spec_from_file_location("frozen_master_registry_v5", path)
_legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_legacy)

for _name in ("digest", "canonical", "value_sha", "save", "source", "read", "normalized", "encode_domain",
              "add_rows", "inspect_extra", "append_expected", "shared_rows", "matching_rows", "controls", "context"):
    globals()[_name] = getattr(_legacy, _name)
MAX_EXTRA_ROWS, MAX_ACTIVITY = _legacy.MAX_EXTRA_ROWS, _legacy.MAX_ACTIVITY
assert MAX_EXTRA_ROWS == 16384 and MAX_ACTIVITY == 1 << 60


def append_native(cp_model, model, additions):
    selectors = [model.get_int_var_from_proto_index(j) for j in range(480)]
    for entry in additions:
        row = entry["row"]
        assert all(type(j) is int and 0 <= j < 480 for j, _ in row["terms"])
        variables = [selectors[j] for j, _ in row["terms"]]
        expr = cp_model.LinearExpr.weighted_sum(variables, [c for _, c in row["terms"]])
        model.add_linear_expression_in_domain(expr, cp_model.Domain.from_flat_intervals(encode_domain(row)))
    assert model.validate() == ""
