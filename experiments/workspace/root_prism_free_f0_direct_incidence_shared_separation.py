"""Reuse the exact shared-row separator on the new literal incidence.

The full eligible-edge domain is retained. A numerical outcome has no
mathematical authority. Only exact arithmetic and an accepted cold owner
can certify the transported universal selector cuts.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = "experiments/workspace/"
LOGS = "experiments/logs/root-prism-free/"
SOURCES = {
    "separator": (WORK + "root_prism_free_f0_shared_reserved_fallback.py", "0685fc162e91a466ed033becb7d01259c4869f2afd9214474b4b0eae7dfcd066"),
    "adapter": (WORK + "root_prism_free_f0_fixed_selection_exterior.py", "2c8a0f7f2bc2a219c994f42618585879e16a6d3a5809627b9aea25be40798160"),
    "supervisor": (WORK + "root_prism_free_f0_fixed_selection_exterior_query.py", "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"),
}
INPUTS = {
    "selection": (LOGS + "f0-direct-literal-query-run01/selection.json", "6c1434b1dbb5a28f19707a3048cb43d64f14370856d03ef7496a3a58fabf4aaa"),
    "model": (LOGS + "f0-fixed-selection-exterior-direct01/model.json", "ec482e37e989a4657a0f7efb801c875062575fa2786efea72ba37c111974b3a9"),
    "domain": (LOGS + "f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4"),
    "literal_cold": (LOGS + "f0-direct-literal-query-run01-cold/report.json", "d9a3cd90320752b08690a761e649210fccc3cef63487f0c72f52f9670226288a"),
    "exterior_cold": (LOGS + "f0-fixed-selection-exterior-query-run01-cold/report.json", "3367e029d8a28ce7195ff7897a2b020d4b3f9cffd2b44c9e955ba048dcf03363"),
    "exterior_cold_owner": (LOGS + "f0-fixed-selection-exterior-query-run01-cold/owner.json", "e600a979c1f5709016fc6bf1d6586cf4dcd30534d2d6b9dc969f19f62ab462b2"),
}
PHASE_SECONDS = 60
OWNER_SECONDS = {"prepare": 60, "run": 120, "cold": 60}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def load_source(key):
    path, expected = SOURCES[key]
    assert digest(ROOT / path) == expected
    spec = importlib.util.spec_from_file_location("shared_reuse_" + key, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def context():
    loaded = {}
    for key, (path, expected) in INPUTS.items():
        raw = (ROOT / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, key
        loaded[key] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    for path, expected in SOURCES.values():
        assert digest(ROOT / path) == expected
    adapter, separator = load_source("adapter"), load_source("separator")
    separator.check_sources()
    ctx, selected = adapter.context(), loaded["selection"]
    complete = adapter.derive(selected, ctx)
    assert complete == loaded["model"]["data"]
    assert adapter.capacity_obstruction(complete, ctx) is None
    domain = loaded["domain"]
    assert domain["component_core_rows"] == ctx["core"]
    assert domain["signature_domain"] == ctx["triples"]
    triples = ctx["triples"]
    targets = [[2 - int(i in h) - sum(ctx["adjacency"][i] >> j & 1 for j in h)
                for i in range(18)] for h in triples]
    neighbors = [sorted(row) for row in ctx["neighborhoods"]]
    assert targets == domain["row_targets"]
    assert neighbors == domain["possible_neighbor_signature_ids"]
    assert sum(map(len, neighbors)) == 2 * 68394
    data, rows = separator.domain(selected, triples, targets, neighbors)
    assert data["design"] == complete["design"] and data["targets"] == complete["targets"]
    assert data["edge_domain"] == complete["edge_domain"]
    assert len(data["edge_domain"]) == 1219 and len(rows) == 1140
    group, frontier = {tuple(range(21))}, [tuple(range(21))]
    while frontier:
        old = frontier.pop()
        for generator in domain["core_generators"]:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == set(range(3))
            assert all((ctx["core"][i] >> j & 1) == (ctx["core"][image[i]] >> image[j] & 1)
                       for i in range(21) for j in range(21))
            if image not in group:
                group.add(image)
                frontier.append(image)
    assert len(group) == 12
    positions, actions = {tuple(h): i for i, h in enumerate(triples)}, []
    for image in sorted(group):
        move = [image[i + 3] - 3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        assert all(sorted(action[b] for b in neighbors[a]) == neighbors[action[a]] for a in range(480))
        assert all(targets[a][i] == targets[action[a]][move[i]] for a in range(480) for i in range(18))
        actions.append({"component_image": move, "signature_image": action})
    cold, owner = loaded["exterior_cold"], loaded["exterior_cold_owner"]
    assert owner["report_accepted"] and owner["fixed_selection_excluded"]
    assert owner["report_sha256"] == INPUTS["exterior_cold"][1]
    assert owner["status"] == cold["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT"
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"]
    assert cold["selection"] == selected
    definition = {"source_sha256": digest(__file__), "sources": SOURCES, "inputs": INPUTS,
                  "shared_box_inventory": separator.inventory(data, rows),
                  "complete_eligible_edges": 68394, "automorphisms": 12,
                  "phase_seconds": PHASE_SECONDS, "owner_seconds": OWNER_SECONDS,
                  "all480_selectors_in_cut_domain": True, "zero_Y_orbit_filter_applied": False,
                  "outside_pair_caps_in_LP": False, "second_component_fixed": False}
    # JSON normalizes the path/hash tuples; compare only canonical forms.
    definition = json.loads(canonical(definition))
    return definition, separator, selected, triples, targets, neighbors, actions


def accepted(directory, limit):
    owner = json.loads((directory / "owner.json").read_bytes())
    report = json.loads((directory / "report.json").read_bytes())
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == limit
    assert owner["report_accepted"] and owner["deadline_overrun_seconds"] == 0
    assert owner["report_sha256"] == digest(directory / "report.json")
    assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["returncode"] == 0
    assert owner["supervision"]["child_reaped"] and owner["status"] == report["status"]
    return report


def worker(mode, directory, preparation, saved_directory):
    started = time.monotonic()
    definition, separator, selected, triples, targets, neighbors, actions = context()
    base = {"definition": definition, "optimizer_calls": 0, "full_graph_constructed": False,
            "whole_component_excluded": False, "new_cuts_require_accepted_cold_owner": True}
    if mode == "prepare":
        controls = separator.controls()
        base.update(status="PASS_PREPARATION_NO_OPTIMIZER", controls=controls)
    else:
        prepared = accepted(preparation, OWNER_SECONDS["prepare"])
        assert prepared["status"] == "PASS_PREPARATION_NO_OPTIMIZER" and prepared["definition"] == definition
        base["preparation_sha256"] = digest(preparation / "report.json")
        if mode == "run":
            result = separator.query(selected, triples, targets, neighbors, directory / "shared.json",
                                     INPUTS["selection"][1], PHASE_SECONDS)
            separator.replay(result, selected, triples, targets, neighbors)
            base.update(status=result["status"], optimizer_calls=result["optimizer_calls"],
                        result_sha256=digest(directory / "shared.json"),
                        cooperative_budget_overrun_seconds=result["cooperative_budget_overrun_seconds"],
                        exact_fixed_design_infeasibility=result["exact_fixed_design_infeasibility"])
            if result["exact_fixed_design_infeasibility"] and result["cooperative_budget_overrun_seconds"] == 0:
                vectors = result["fixed_capacity_potentials"]["integer_potentials60_by18"]
                cuts = separator.lift(selected, vectors, triples, targets, neighbors, actions)
                save(directory / "universal-cuts.json", cuts)
                base["cuts_sha256"] = digest(directory / "universal-cuts.json")
        else:
            run = accepted(saved_directory, OWNER_SECONDS["run"])
            assert run["definition"] == definition
            assert run["preparation_sha256"] == base["preparation_sha256"]
            result_path = saved_directory / "shared.json"
            assert digest(result_path) == run["result_sha256"]
            result = json.loads(result_path.read_bytes())
            assert result["candidate_sha256"] == INPUTS["selection"][1]
            separator.replay(result, selected, triples, targets, neighbors)
            base.update(status="PASS_COLD_NO_NEW_CUT", run_report_sha256=digest(saved_directory / "report.json"),
                        run_owner_sha256=digest(saved_directory / "owner.json"))
            if "cuts_sha256" in run:
                assert result["exact_fixed_design_infeasibility"] and result["cooperative_budget_overrun_seconds"] == 0
                path = saved_directory / "universal-cuts.json"
                assert digest(path) == run["cuts_sha256"]
                vectors = result["fixed_capacity_potentials"]["integer_potentials60_by18"]
                cuts = separator.lift(selected, vectors, triples, targets, neighbors, actions)
                assert cuts == json.loads(path.read_bytes())
                save(directory / "universal-cuts.json", cuts)
                assert digest(directory / "universal-cuts.json") == run["cuts_sha256"]
                base.update(status="PASS_COLD_EXACT_SHARED_GAP_AND_ALL12_UNIVERSAL_CUTS",
                            cuts_sha256=run["cuts_sha256"], normalized_gap=cuts["normalized_gap"])
    base.update(seconds=time.monotonic() - started,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(directory / "report.json", base)


def owned(mode, directory, preparation, saved_directory):
    started = time.monotonic()
    limit = OWNER_SECONDS[mode]
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode, "--directory", str(directory.resolve())]
    if preparation is not None:
        command += ["--preparation", str(preparation.resolve())]
    if saved_directory is not None:
        command += ["--saved-directory", str(saved_directory.resolve())]
    save(directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = load_source("supervisor").supervise(command, directory, started + limit)
    owner = {"status": supervision["status"], "supervision": supervision, "source_sha256": digest(__file__),
             "maximum_seconds": limit, "report_accepted": False, "certified_new_cuts": False}
    report_path = directory / "report.json"
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= started + limit:
        report = json.loads(report_path.read_bytes())
        owner.update(status=report["status"], report_accepted=True, report_sha256=digest(report_path))
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - started - limit))
    if owner["deadline_overrun_seconds"]:
        owner.update(status="UNKNOWN_HARD_DEADLINE", report_accepted=False)
    if mode == "cold" and owner["report_accepted"]:
        owner["certified_new_cuts"] = owner["status"] == "PASS_COLD_EXACT_SHARED_GAP_AND_ALL12_UNIVERSAL_CUTS"
    save(directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "cold", "_prepare", "_run", "_cold"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--saved-directory", type=Path)
    args = parser.parse_args()
    mode = args.mode.lstrip("_")
    assert mode == "prepare" or args.preparation is not None
    assert mode != "cold" or args.saved_directory is not None
    if args.mode.startswith("_"):
        worker(mode, args.directory, args.preparation, args.saved_directory)
    else:
        owned(mode, args.directory, args.preparation, args.saved_directory)
