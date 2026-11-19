"""Exact sufficient dominance test modulo the original literal Gram rows.

For each raw signed gauge g, form r=g-b-sign*z. Here b is the independently
rebuilt baseline allocation and z_a=h_a[q]*target_a[p]-h_a[p]*target_a[q].
An explicit combination of the original 171 Gram equations proves z*x=0.
If every r_a<=0, then x>=0 and b*x<=0 imply g*x<=0. A failed test proves
no converse. All raw gauge data remain untouched. This audit cannot replace
the independent gauge-census cold required before any row is used or dropped.
"""
import argparse
import gzip
import hashlib
import importlib.util
from itertools import combinations, combinations_with_replacement
import json
from math import gcd
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OWNER_SECONDS = 30
SUPERVISOR = ("experiments/workspace/root_prism_free_f0_fixed_selection_exterior_query.py",
              "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3")
PRODUCER_SHA = "760fae86189139db3f51b0adccaec27856c241b47e33c6f251ccbf7aad059981"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    raw = canonical(value) + b"\n"
    if path.suffix == ".gz":
        raw = gzip.compress(raw, compresslevel=6, mtime=0)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(path)


def calculate(configuration, directory, deadline):
    cfg = json.loads(configuration.read_bytes())
    assert cfg["schema"] == "conway99.f0.skew-gauge-dominance-configuration.v1"
    assert cfg["source_sha256"] == digest(__file__) and cfg["owner_seconds"] == OWNER_SECONDS
    loaded = {}
    for key, binding in cfg["inputs"].items():
        path = ROOT / binding["path"]
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == binding["sha256"], key
        loaded[key] = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
    report, owner, gauge_cfg = [loaded[k] for k in ("gauge_report", "gauge_owner", "gauge_configuration")]
    assert owner["report_accepted"] and owner["report_sha256"] == cfg["inputs"]["gauge_report"]["sha256"]
    assert owner["source_sha256"] == report["source_sha256"] == gauge_cfg["producer_sha256"] == PRODUCER_SHA
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert report["configuration_sha256"] == cfg["inputs"]["gauge_configuration"]["sha256"]
    assert report["complete_census_sha256"] == cfg["inputs"]["census"]["sha256"]
    assert report["complete_gauges"] == 306 and report["complete_transports"] == 3672
    assert report["optimizer_calls"] == 0 and report["independent_cold_required"]
    for audit_key, gauge_key in [("parent_run", "run"), ("baseline_cut", "universal_cuts"), ("shared", "shared")]:
        assert cfg["inputs"][audit_key]["sha256"] == gauge_cfg["inputs"][gauge_key]["sha256"]
    assert loaded["parent_run"]["definition"]["base_definition"]["inputs"]["plan"] == cfg["inputs"]["plan"]
    plan, shared, cut, census = [loaded[k] for k in ("plan", "shared", "baseline_cut", "census")]
    triples, core = plan["signature_domain"], plan["core_rows"]
    assert len(triples) == 480 and len(core) == 21
    assert all(len(h) == 3 and h == sorted(set(h)) and all(type(i) is int and 0 <= i < 18 for i in h) for h in triples)
    adjacency = [[core[i + 3] >> (j + 3) & 1 for j in range(18)] for i in range(18)]
    targets = [[2 - int(i in h) - sum(adjacency[i][j] for j in h) for i in range(18)] for h in triples]
    equalities, links = plan["original_selector_equalities"], plan["original_to_native_rows"]
    assert len(equalities) == len(links) == 172
    gram_rows = {}
    for index, row in enumerate(equalities):
        if row["family"] != "Gram":
            assert index == 171 and row["family"] == "population" and row["quota"] == 60
            continue
        i, j = row["core_pair"]
        assert 0 <= i <= j < 18 and (i, j) not in gram_rows
        support = [a for a, h in enumerate(triples) if i in h and j in h]
        quota = 12 * int(i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - adjacency[i][j]
        assert row["support"] == support and row["quota"] == quota
        if support:
            assert type(links[index]) is int
            assert plan["linear_constraints"][links[index]] == {"terms": [[a, 1] for a in support], "domain": [quota, quota]}
        else:
            assert quota == 0 and links[index] is None
        gram_rows[i, j] = index
    assert set(gram_rows) == set(combinations_with_replacement(range(18), 2))
    selected = shared["selected_signature_ids"]
    assert selected == cut["selected_signature_ids_for_allocation_only"] == sorted(set(selected)) and len(selected) == 60
    support = set(selected)
    potentials = [[0] * 18 for _ in range(480)]
    for a, vector in zip(selected, shared["fixed_capacity_potentials"]["integer_potentials60_by18"]):
        assert len(vector) == 18 and all(type(v) is int for v in vector)
        potentials[a] = vector
    assert cut["nonzero_target_potentials"] == [[a, v] for a, v in enumerate(potentials) if any(v)]
    baseline = [sum(v * q for v, q in zip(vector, target)) for vector, target in zip(potentials, targets)]
    positive, edges = [], []
    for a, b in combinations(range(480), 2):
        if len(set(triples[a]) & set(triples[b])) > 1:
            continue
        if any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        edges.append([a, b])
        weight = sum(potentials[a][i] for i in triples[b]) + sum(potentials[b][i] for i in triples[a])
        if weight > 0:
            assert a in support or b in support
            endpoint = a if a in support and b in support else b if a in support else a
            baseline[endpoint] -= weight
            positive.append({"edge": [a, b], "weight": weight, "allocated_endpoint": endpoint,
                             "kind": "internal" if a in support and b in support else "boundary"})
    assert len(edges) == 68394 and value_sha(edges) == cut["global_edge_sha256"]
    assert value_sha(positive) == cut["positive_edge_allocation_sha256"]
    assert sum(baseline[a] for a in selected) == cut["raw_gap"] == 4
    divisor = gcd(*(abs(c) for c in baseline))
    base_terms = [[a, c // divisor] for a, c in enumerate(baseline) if c]
    assert any(row["signed_coefficients"] == base_terms for row in cut["transported_cuts"])
    identities = []
    for p, q in combinations(range(18), 2):
        multipliers = {gram_rows[q, q]: 2, gram_rows[p, p]: -2}
        for j in range(18):
            at = gram_rows[tuple(sorted((p, j)))]
            multipliers[at] = multipliers.get(at, 0) + adjacency[q][j]
            at = gram_rows[tuple(sorted((q, j)))]
            multipliers[at] = multipliers.get(at, 0) - adjacency[p][j]
        multipliers = [[i, c] for i, c in sorted(multipliers.items()) if c]
        vector = [0] * 480
        rhs = 0
        for i, coefficient in multipliers:
            rhs += coefficient * equalities[i]["quota"]
            for a in equalities[i]["support"]:
                vector[a] += coefficient
        expected = [int(q in h) * targets[a][p] - int(p in h) * targets[a][q] for a, h in enumerate(triples)]
        assert vector == expected and rhs == 0
        identities.append({"sites": [p, q], "original_Gram_row_multipliers": multipliers,
                           "all480_coefficients": vector, "combined_rhs": rhs})
    identity_by_pair = {tuple(item["sites"]): item for item in identities}
    expected_families = [(p, q, sign) for p, q in combinations(range(18), 2) for sign in (-1, 1)]
    assert len(census["families"]) == 306 and len(census["transport_coverage"]) == 3672
    results = []
    for index, (family, (p, q, sign)) in enumerate(zip(census["families"], expected_families)):
        assert family["index"] == index and family["sites"] == [p, q] and family["sign"] == sign
        coefficients = family["raw_coefficients"]
        assert len(coefficients) == 480 and all(type(c) is int for c in coefficients)
        assert gcd(*(abs(c) for c in coefficients)) == family["coefficient_gcd"]
        z = identity_by_pair[p, q]["all480_coefficients"]
        remainder = [g - b - sign * v for g, b, v in zip(coefficients, baseline, z)]
        assert all(remainder[a] == 0 for a in selected)
        proved = all(value <= 0 for value in remainder)
        coverage = [row for row in census["transport_coverage"] if row["gauge_index"] == index]
        assert [row["core_action_index"] for row in coverage] == list(range(12))
        results.append({"gauge_index": index, "sites": [p, q], "sign": sign,
                        "status": "DOMINATED_BY_BASELINE_AND_ORIGINAL_GRAM" if proved else "SUFFICIENT_CRITERION_NOT_MET",
                        "dominance_proved": proved, "all480_remainder_coefficients": remainder,
                        "maximum_remainder": max(remainder), "positive_remainder_count": sum(c > 0 for c in remainder),
                        "covered_transported_row_keys": [row["row_key"] for row in coverage]})
        if time.monotonic() >= deadline:
            raise TimeoutError("exact dominance audit owner deadline reached")
    proof = {"schema": "conway99.f0.skew-gauge-Gram-dominance.v1", "baseline_raw_coefficients": baseline,
             "original_Gram_identities": identities, "gauge_checks": results,
             "independent_census_cold_still_required": True, "no_rows_removed_or_modified": True}
    save(directory / "proof.json.gz", proof)
    dominated = [row["gauge_index"] for row in results if row["dominance_proved"]]
    return {"status": "PASS_COMPLETE_EXACT_SUFFICIENT_DOMINANCE_AUDIT", "source_sha256": digest(__file__),
            "configuration_sha256": digest(configuration), "proof_sha256": digest(directory / "proof.json.gz"),
            "original_Gram_rows_bound": 171, "complete_original_Gram_identities": 153, "gauges_checked": 306,
            "dominated_gauge_indices": dominated, "dominated_gauges": len(dominated),
            "covered_transports_proved_dominated": 12 * len(dominated),
            "failing_cases_have_no_converse_claim": True, "independent_census_cold_still_required": True,
            "no_rows_removed_or_modified": True, "optimizer_calls": 0, "native_solver_imported": False}


def main(args):
    started = time.monotonic()
    if args.worker:
        try:
            result = calculate(args.configuration, args.directory, args.deadline)
            assert not any(name.split(".")[0] in {"ortools", "highspy", "scipy", "numpy"} for name in sys.modules)
            assert time.monotonic() < args.deadline
            result.update(seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            save(args.directory / "report.json", result)
        except Exception as error:
            save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error)})
            raise
        return
    args.directory.mkdir(parents=True, exist_ok=False)
    path = ROOT / SUPERVISOR[0]
    assert digest(path) == SUPERVISOR[1]
    spec = importlib.util.spec_from_file_location("gauge_dominance_supervisor", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--configuration", str(args.configuration.resolve()),
               "--directory", str(args.directory.resolve()), "--deadline", str(started + OWNER_SECONDS)]
    save(args.directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervisor.supervise(command, args.directory, started + OWNER_SECONDS)
    owner = {"source_sha256": digest(__file__), "maximum_seconds": OWNER_SECONDS, "supervision": supervision,
             "status": supervision["status"], "report_accepted": False, "optimizer_calls": 0}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= started + OWNER_SECONDS:
        result = json.loads((args.directory / "report.json").read_bytes())
        owner.update(report_accepted=True, report_sha256=digest(args.directory / "report.json"), status=result["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - started - OWNER_SECONDS))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("exact audit assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    assert not args.worker or args.deadline is not None
    main(args)
