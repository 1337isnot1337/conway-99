"""Verify the complete explicit driver/replay delta without importing subjects."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "experiments/workspace"
LOGS = ROOT / "experiments/logs/root-prism-free"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan_path = LOGS / "f0-schur-path-v3-adapter-explicit-substitutions.json"
    plan = json.loads(plan_path.read_text())
    reports = []
    for suffix in ("query", "replay", "native_matrix_audit"):
        old = WORK / ("root_prism_free_f0_schur_motif_" + suffix + ".py")
        new = WORK / ("root_prism_free_f0_schur_path_" + suffix + "_v3.py")
        expected = old.read_text()
        for before, after in plan[suffix]:
            assert before in expected
            expected = expected.replace(before, after)
        assert expected == new.read_text()
        assert ast.dump(ast.parse(expected)) == ast.dump(ast.parse(new.read_text()))
        reports.append({"parent": str(old.relative_to(ROOT)), "parent_sha256": sha(old),
                        "new": str(new.relative_to(ROOT)), "new_sha256": sha(new),
                        "complete_source_matches_explicit_substitutions": True})
    old = WORK / "root_prism_free_f0_schur_motif_exact.py"
    new = WORK / "root_prism_free_f0_schur_path_exact_v3.py"
    def function(path, name):
        return next(node for node in ast.parse(path.read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == name)
    class RowCount(ast.NodeTransformer):
        def visit_Constant(self, node):
            if type(node.value) is int and node.value == 27764:
                return ast.copy_location(ast.Constant(22640), node)
            return node
    assert ast.dump(function(old, "exact_phase")) == ast.dump(RowCount().visit(function(new, "exact_phase")))
    assert "exact_scaled, pullback_ray, controls = parent.exact_scaled, parent.pullback_ray, parent.controls" in new.read_text()
    result = {"status": "PASS: complete path overlay query/replay/native delta and exact phase",
              "source_sha256": sha(Path(__file__)), "substitution_plan_sha256": sha(plan_path),
              "full_source_comparisons": reports,
              "exact_helper_sha256": sha(new),
              "exact_phase_AST_equal_except_complete_row_count": True,
              "same_bound_scaling_ray_and_arithmetic_controls_reused": True,
              "new_loader_requires_separate_mathematical_source_review": True,
              "subjects_imported": False, "model_rebuilt": False, "optimizer_calls": 0}
    output = LOGS / "f0-schur-path-v3-reuse-controls.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
