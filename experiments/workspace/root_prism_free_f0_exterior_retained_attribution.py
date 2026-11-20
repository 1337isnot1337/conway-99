"""Attribute the checked 116-clause core to frozen mathematical obligations.

The only additions to the reused build AST are read-only boundary callbacks.
Removing those calls must recover the original AST exactly. The resulting full
CNF must have the frozen byte hash. No solver or proof checker is called.
"""
import argparse
import ast
from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
BINDINGS = {
    "adapter": ("experiments/workspace/root_prism_free_f0_fixed_selection_exterior.py", "2c8a0f7f2bc2a219c994f42618585879e16a6d3a5809627b9aea25be40798160"),
    "model": (BASE + "f0-fixed-selection-exterior-direct01/model.json", "ec482e37e989a4657a0f7efb801c875062575fa2786efea72ba37c111974b3a9"),
    "cnf": (BASE + "f0-fixed-selection-exterior-direct01/model.cnf", "d5bb8807367519fc32e7a4d05305533154d7ecf134483cde2d9ee2c96a1532a6"),
    "retained": (BASE + "f0-fixed-selection-exterior-query-run01/retained.cnf", "aa4e78e057ed8b70e88ce4a003e0e8d1b47a62bdac1d0c36b5e40e95e46b962a"),
    "cold": (BASE + "f0-fixed-selection-exterior-query-run01-cold/report.json", "3367e029d8a28ce7195ff7897a2b020d4b3f9cffd2b44c9e955ba048dcf03363"),
    "owner": (BASE + "f0-fixed-selection-exterior-query-run01-cold/owner.json", "e600a979c1f5709016fc6bf1d6586cf4dcd30534d2d6b9dc969f19f62ab462b2"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(key, raw=False):
    path, expected = BINDINGS[key]
    value = (ROOT / path).read_bytes()
    assert sha(value) == expected, key
    return value if raw else json.loads(value)


class Annotate(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "equality":
            kind = node.value.args[2].value
            assert kind in ("degree", "mixed_Gram")
            marker = ast.parse("_begin('degree', v, None, cnf, pool)" if kind == "degree"
                               else "_begin('mixed', v, i, cnf, pool)").body[0]
            return [ast.copy_location(marker, node), node]
        return self.generic_visit(node)

    def visit_For(self, node):
        node = self.generic_visit(node)
        if isinstance(node.target, ast.Tuple) and [v.id for v in node.target.elts] == ["u", "v"]:
            node.body.insert(0, ast.copy_location(ast.parse("_begin('pair_cap', u, v, cnf, pool)").body[0], node))
        return node


class RemoveAnnotations(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "_begin":
            return None
        return self.generic_visit(node)


def attribute():
    start = time.monotonic()
    for key in BINDINGS:
        read(key, raw=True)
    model, cold, owner = read("model"), read("cold"), read("owner")
    assert owner["report_accepted"] and owner["fixed_selection_excluded"]
    assert owner["report_sha256"] == BINDINGS["cold"][1]
    assert cold["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT"
    assert cold["full_CNF_sha256"] == model["cnf_sha256"] == BINDINGS["cnf"][1]
    spec = importlib.util.spec_from_file_location("frozen_attribution_adapter", ROOT / BINDINGS["adapter"][0])
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    original = adapter.source_functions()["build"]
    tagged = Annotate().visit(copy.deepcopy(original))
    restored = RemoveAnnotations().visit(copy.deepcopy(tagged))
    assert ast.dump(restored, include_attributes=False) == ast.dump(original, include_attributes=False)
    groups = []
    def begin(kind, a, b, cnf, pool):
        groups.append({"kind": kind, "a": a, "b": b, "first_clause": len(cnf.clauses), "first_auxiliary_after": pool.top})
    api = adapter.reused_api()
    api["_begin"] = begin
    tree = ast.fix_missing_locations(ast.Module(body=[tagged], type_ignores=[]))
    exec(compile(tree, "frozen_build_with_read_only_boundaries", "exec"), api)
    cnf, formula = api["build"](model["data"])
    assert formula == model["formula"]
    stream = io.StringIO()
    cnf.to_fp(stream)
    assert sha(stream.getvalue().encode()) == BINDINGS["cnf"][1]
    assert Counter(g["kind"] for g in groups) == {"degree": 60, "mixed": 1080, "pair_cap": 1770}
    for k, group in enumerate(groups):
        nxt = groups[k + 1] if k + 1 < len(groups) else {"first_clause": len(cnf.clauses), "first_auxiliary_after": cnf.nv}
        group.update(last_clause_exclusive=nxt["first_clause"], last_auxiliary=nxt["first_auxiliary_after"])
    retained = list(api["read_clauses"](ROOT / BINDINGS["retained"][0]))
    wanted = Counter(tuple(sorted(row)) for row in retained)
    assert len(retained) == len(wanted) == 116
    positions = defaultdict(list)
    for index, row in enumerate(cnf.clauses):
        key = tuple(sorted(row))
        if key in wanted:
            positions[key].append(index)
    assert set(positions) == set(wanted) and all(len(v) == 1 for v in positions.values())
    data = model["data"]
    selected, edges, masks = data["design_source_indices"], data["edge_domain"], data["masks"]
    attributed, hits = [], Counter()
    for row in retained:
        index = positions[tuple(sorted(row))][0]
        matches = [k for k, g in enumerate(groups) if g["first_clause"] <= index < g["last_clause_exclusive"]]
        assert len(matches) == 1
        group_id = matches[0]
        hits[group_id] += 1
        attributed.append({"retained_clause": row, "original_clause_index": index, "group_id": group_id})
    hit_groups = []
    for k, count in sorted(hits.items()):
        g = dict(groups[k], group_id=k, retained_clauses=count)
        a, b = g["a"], g["b"]
        if g["kind"] in ("degree", "mixed"):
            support = [[i + 1, v if u == a else u] for i, (u, v) in enumerate(edges) if a in (u, v)]
            if g["kind"] == "mixed":
                support = [[i, v] for i, v in support if masks[v] >> b & 1]
            g.update(anchor_signature=selected[a], core_site=b,
                     target=8 if g["kind"] == "degree" else data["targets"][a][b],
                     complete_row_terms=[[i, selected[v]] for i, v in support])
        else:
            g.update(pair_signatures=[selected[a], selected[b]], pair_capacity=2 - data["overlaps"][a][b])
        hit_groups.append(g)
    primary_ids = sorted({abs(v) for row in retained for v in row if abs(v) <= len(edges)})
    common = set(edges[primary_ids[0] - 1])
    for i in primary_ids:
        common.intersection_update(edges[i - 1])
    return {"status": "PASS_COMPLETE_RETAINED_CLAUSE_ATTRIBUTION", "bindings": BINDINGS,
            "source_sha256": sha(Path(__file__).read_bytes()), "formula": formula,
            "original_build_AST_sha256": sha(ast.dump(original, include_attributes=False).encode()),
            "removing_read_only_markers_recovers_original_AST": True,
            "complete_CNF_byte_hash_reproduced": BINDINGS["cnf"][1],
            "group_counts": dict(Counter(g["kind"] for g in groups)), "hit_groups": hit_groups,
            "retained_clause_attribution": attributed,
            "primary_edges": [{"variable": i, "local_endpoints": edges[i - 1],
                               "signature_endpoints": [selected[v] for v in edges[i - 1]]} for i in primary_ids],
            "common_primary_endpoints": sorted(common),
            "common_primary_signatures": [selected[v] for v in sorted(common)],
            "production_solver_calls": 0, "proof_checker_calls": 0,
            "smaller_selector_cut_claimed": False, "seconds": time.monotonic() - start}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    record = attribute()
    args.output.write_text(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": record["status"], "seconds": record["seconds"],
                      "source_sha256": record["source_sha256"], "report_sha256": sha(args.output.read_bytes()),
                      "hit_group_count": len(record["hit_groups"])}))
