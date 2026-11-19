"""Reuse the exact fixed-incidence exterior Boolean model for an explicit selection.

Preparation checks source reuse and historical data, with no candidate or solver.
The historical input loader is never called. All second-component choices remain free.
"""
import argparse
import ast
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
WORK = "experiments/workspace/"
INPUTS = {
    "baseline": (BASE + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "old_model": (BASE + "f0-first-design-exterior-model.json", "d98d817a7e9410f6fd88186adacdf23b886e543f3e18f7a9ec98af07e6558078"),
    "old_result": (BASE + "f0-first-design-exterior-run01/result.json", "bebe84b739f45bf3fa48daf8b18668bc17724569cebb98d98a0998cfadb6d985"),
    "old_cold": (BASE + "f0-first-design-exterior-run01-cold-replay.json", "6240d173c5f15919a74e0062f8a81f3b25bd55a3928f3bd9e94b0531ed5a4847"),
    "old_selection": (BASE + "f0-incidence-case00-run01/result.json", "64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf"),
}
SOURCES = {
    "exterior": (WORK + "root_prism_free_f0_first_design_exterior.py", "f0c5105526b9374935b4ba961859261249f44f2b311d98138ac3c8aeb5ed56cd"),
    "old_coupling": (WORK + "root_prism_free_f0_coupling.py", "5bb3ec13893aee488272dcb7372c12bddf68d28ae4a199cd170be9342d47df50"),
    "supervisor": (WORK + "root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
FUNCTIONS = ("build", "inspect", "read_clauses")
SECONDS = 60


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    raw = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    return sha(raw)


def read(key):
    name, digest = INPUTS[key]
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == digest, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def source_functions():
    name, digest = SOURCES["exterior"]
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == digest
    tree = ast.parse(raw, filename=name)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in FUNCTIONS}
    assert set(functions) == set(FUNCTIONS)
    return functions


def definition():
    for name, digest in SOURCES.values():
        assert sha((ROOT / name).read_bytes()) == digest
    functions = source_functions()
    return {
        "schema": "conway99.f0.fixed-selection-exterior-adapter.v1",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "sources": {k: {"path": p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "reused_function_ast_sha256": {
            k: sha(ast.dump(functions[k], include_attributes=False).encode()) for k in FUNCTIONS
        },
        "historical_input_loader_called": False, "original_eligible_edges": 68394,
        "proved_162_zero_Y_orbits_applied": False,
        "maximum_owned_seconds_per_build_or_cold": SECONDS, "solver_calls": 0,
        "scope": "One specified first incidence; the second component and its alignment are free.",
    }


def context():
    model = read("baseline")["validation"]
    core, triples = model["core"], model["triples"]
    assert len(core) == 21 and len(triples) == 480
    assert all(type(row) is int and 0 <= row < 1 << 21 for row in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    assert len(set(map(tuple, triples))) == 480
    assert all(t == sorted(set(t)) and len(t) == 3 and 0 <= t[0] < t[-1] < 18 for t in triples)
    adjacency = [(row >> 3) & ((1 << 18) - 1) for row in core[3:21]]
    assert all(row.bit_count() == 3 for row in adjacency)
    gram = [[12 * (i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count()
             - (core[i + 3] >> (j + 3) & 1) for j in range(18)] for i in range(18)]
    edges = model["edges"]
    assert len(edges) == 68394 and len(set(map(tuple, edges))) == 68394
    assert all(0 <= a < b < 480 for a, b in edges)
    neighborhoods = [set() for _ in triples]
    for a, b in edges:
        neighborhoods[a].add(b)
        neighborhoods[b].add(a)
    return {"core": core, "triples": triples, "adjacency": adjacency, "gram": gram,
            "edges": set(map(tuple, edges)), "neighborhoods": neighborhoods}


def derive(selected, ctx):
    assert type(selected) is list and len(selected) == 60
    assert all(type(a) is int and 0 <= a < 480 for a in selected)
    assert selected == sorted(set(selected))
    design = [ctx["triples"][a] for a in selected]
    for i in range(18):
        for j in range(i, 18):
            assert sum(i in h and j in h for h in design) == ctx["gram"][i][j]
    masks = [sum(1 << i for i in h) for h in design]
    adjacency = ctx["adjacency"]
    targets = [[2 - int(mask >> i & 1) - (adjacency[i] & mask).bit_count()
                for i in range(18)] for mask in masks]
    assert all(sum(row) == 24 and all(q in (0, 1, 2) for q in row) for row in targets)
    overlaps = [[(a & b).bit_count() for b in masks] for a in masks]
    edges = []
    for u in range(60):
        for v in range(u):
            assert overlaps[u][v] <= 2
            allowed = (overlaps[u][v] <= 1
                       and all(targets[u][i] > 0 for i in design[v])
                       and all(targets[v][i] > 0 for i in design[u]))
            assert allowed == (tuple(sorted((selected[u], selected[v]))) in ctx["edges"])
            if allowed:
                edges.append([u, v])
    return {"design": design, "design_source_indices": selected,
            "component_adjacency_rows": adjacency, "masks": masks, "targets": targets,
            "overlaps": overlaps, "edge_domain": edges}


def capacity_obstruction(data, ctx):
    """A universal selector row if an original degree/mixed row lacks support."""
    selected = set(data["design_source_indices"])
    for vertex, a in enumerate(data["design_source_indices"]):
        for site in [None] + list(range(18)):
            demand = 8 if site is None else data["targets"][vertex][site]
            support = sorted(b for b in ctx["neighborhoods"][a]
                             if site is None or site in ctx["triples"][b])
            supplied = sorted(selected.intersection(support))
            if len(supplied) < demand:
                coefficients = Counter({a: demand})
                for b in support:
                    coefficients[b] -= 1
                return {"kind": "original degree capacity" if site is None else "original mixed capacity",
                        "anchor_signature": a, "core_site": site, "demand": demand,
                        "complete_original_eligible_support": support, "selected_support": supplied,
                        "literal_cut": {"terms": [[j, coefficients[j]] for j in sorted(coefficients)
                                                  if coefficients[j]], "rhs": 0},
                        "actual_violation": demand - len(supplied)}
    return None


def reused_api():
    from pysat.card import CardEnc, EncType
    from pysat.formula import CNF, IDPool
    import pysat
    functions = source_functions()
    namespace = {"Counter": Counter, "combinations": combinations, "Path": Path,
                 "CardEnc": CardEnc, "EncType": EncType, "CNF": CNF, "IDPool": IDPool}
    for name in FUNCTIONS:
        tree = ast.Module(body=[functions[name]], type_ignores=[])
        exec(compile(tree, SOURCES["exterior"][0], "exec"), namespace)
    namespace["pysat_version"] = pysat.__version__
    return namespace


def prepare():
    conf, ctx = definition(), context()
    old, selection, result, cold = [read(k) for k in ("old_model", "old_selection", "old_result", "old_cold")]
    selected = selection["incidence_witness"]["selected_columns"]
    data = derive(selected, ctx)
    assert data == old["data"]
    assert old["source_sha256"] == result["source_sha256"] == cold["source_sha256"] == SOURCES["exterior"][1]
    assert old["coupling_source_sha256"] == SOURCES["old_coupling"][1]
    assert old["incidence_result_sha256"] == INPUTS["old_selection"][1]
    assert result["model_sha256"] == cold["model_sha256"] == INPUTS["old_model"][1]
    assert result["cnf_sha256"] == cold["cnf_sha256"] == old["cnf_sha256"]
    assert cold["status"] == "cold complete domain/CNF rebuild, retained inclusion and DRAT PASS"
    certificate = result["retained_certificate"]
    for path_key, hash_key in (("cnf", "cnf_sha256"), ("proof", "proof_sha256"),
                               ("checker_log", "checker_log_sha256")):
        assert sha((ROOT / certificate[path_key]).read_bytes()) == certificate[hash_key]
    assert sha((ROOT / cold["checker_log"]).read_bytes()) == cold["checker_log_sha256"]
    return {"status": "PASS: pure function reuse and complete historical data comparison",
            "definition": conf, "historical_data_sha256": sha(canonical(data)),
            "historical_primaries": old["formula"]["primary_variables"],
            "original_selector_equations_checked": 172, "eligible_pair_comparisons": 1770,
            "historical_proof_replayed_again": False, "historical_proof_bindings_checked": True,
            "historical_first_incidence_does_not_restrict_new_candidates": True,
            "CNF_built": False, "native_imported": False, "new_candidate": False, "solver_calls": 0}


def build(selection_path, preparation_path, directory, saved_directory=None):
    raw = preparation_path.read_bytes()
    prepared = json.loads(raw)
    assert prepared["status"].startswith("PASS") and prepared["definition"] == definition()
    selection_raw = selection_path.read_bytes()
    selected = json.loads(selection_raw)
    ctx = context()
    data = derive(selected, ctx)
    obstacle = capacity_obstruction(data, ctx)
    binding = {"definition": definition(), "preparation_sha256": sha(raw),
               "selection_sha256": sha(selection_raw), "canonical_selection_sha256": sha(canonical(selected)),
               "original_selector_equations_checked": 172, "data": data,
               "current_complete_cut_acceptance_checked": False, "all480_selectors_otherwise_unrestricted": True,
               "second_component_fixed": False, "solver_calls": 0}
    if obstacle is not None:
        binding.update(status="EXACT_CAPACITY_OBSTRUCTION", obstruction=obstacle, CNF_built=False)
    else:
        api = reused_api()
        cnf, formula = api["build"](data)
        path = directory / "model.cnf"
        cnf.to_file(path)
        assert path.stat().st_size <= 64 << 20
        binding.update(status="BUILT: necessary fixed-selection exterior CNF; no solver",
                       formula=formula, cnf_sha256=sha(path.read_bytes()), cnf_bytes=path.stat().st_size,
                       pysat_version=api["pysat_version"], CNF_built=True)
    if saved_directory is None:
        save(directory / "model.json", binding)
        return binding
    old_raw = (saved_directory / "model.json").read_bytes()
    old = json.loads(old_raw)
    assert binding == old
    if binding["CNF_built"]:
        assert sha((saved_directory / "model.cnf").read_bytes()) == binding["cnf_sha256"]
    return {"status": "PASS: independent input, whole data and complete CNF/capacity reconstruction",
            "model_sha256": sha(old_raw), "definition": definition(), "selection_sha256": sha(selection_raw),
            "CNF_built": binding["CNF_built"], "solver_calls": 0,
            "graph_or_whole_case_exclusion_claimed": False}


def owned(mode, selection, preparation, directory, saved_directory):
    import importlib.util
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started + SECONDS
    name, expected = SOURCES["supervisor"]
    path = ROOT / name
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location("fixed_exterior_supervisor", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    command = [sys.executable, str(Path(__file__).resolve()), "_worker",
               "--selection", str(selection.resolve()), "--preparation", str(preparation.resolve()),
               "--directory", str(directory.resolve())]
    if saved_directory is not None:
        command += ["--saved-directory", str(saved_directory.resolve())]
    save(directory / "initial-owner.json", {"source_sha256": sha(Path(__file__).read_bytes()),
                                           "maximum_seconds": SECONDS, "solver_calls": 0})
    supervised = supervisor.supervise(command, directory, deadline)
    seconds = time.monotonic() - started
    accepted = supervised["status"] == "CHILD_EXITED" and seconds <= SECONDS
    report = {"status": "PASS" if accepted else supervised["status"], "supervision": supervised,
              "seconds": seconds, "maximum_seconds": SECONDS, "report_accepted": accepted, "solver_calls": 0}
    if accepted:
        report["report_sha256"] = sha((directory / "report.json").read_bytes())
    save(directory / "owner.json", report)
    return report


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "build", "cold", "_worker"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--saved-directory", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    if args.mode == "prepare":
        assert args.output is not None and not args.output.exists()
        report = prepare()
        report["seconds"] = time.monotonic() - started
        digest = save(args.output, report)
    elif args.mode == "_worker":
        report = build(args.selection, args.preparation, args.directory, args.saved_directory)
        report["seconds"] = time.monotonic() - started
        digest = save(args.directory / "report.json", report)
    else:
        assert args.selection and args.preparation and args.directory
        assert (args.mode == "cold") == (args.saved_directory is not None)
        report = owned(args.mode, args.selection, args.preparation, args.directory, args.saved_directory)
        digest = sha((args.directory / "owner.json").read_bytes())
    print(json.dumps({"status": report["status"], "sha256": digest, "seconds": report["seconds"]}))


if __name__ == "__main__":
    main()
