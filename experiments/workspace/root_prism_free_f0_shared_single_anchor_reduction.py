"""Resume exact dominance reduction from the preserved complete fresh census.

The first 65-second attempt saved all rows but did not finish reduction.
This wrapper leaves that attempt intact. It caches immutable row weights
and rejects impossible support inclusion before the same cross-products.
No numerical model, optimizer, or historical potential bank is loaded.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "producer": ("experiments/workspace/root_prism_free_f0_shared_single_anchor_reanchoring.py", "878e7058cd6aab4761adf56e2ca90e0cbc199d463a1824d26da0171632793676"),
    "helper": ("experiments/workspace/root_prism_free_f0_local_row_dominance.py", "d91591788e7f97742736df8bb6cdafaddb46939668054fb7450e351a2d276566"),
    "configuration": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring-configuration01.json", "42b6a6651435adbfb81d33819917f870df2d69f7205878d01899ea9a2ef8ba53"),
    "bank": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring01/bank.json", "ba861832d39d865e62b648ba6e342f8f960075f96d3f48861952794c128e9fa0"),
    "census": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring01/complete-census.json.gz", "8741c7ff5cdeba72e330b0ec4ecf51f10e55f9f2491904d3e2eba1f7ce70974c"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(kind):
    path, expected = INPUTS[kind]
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected, path
    if path.endswith(".py"):
        spec = importlib.util.spec_from_file_location("resume_" + kind, ROOT / path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def statistics(entries):
    return {
        "rows": len(entries),
        "terms_min_max": [min((len(e["row"]["terms"]) for e in entries), default=0),
                          max((len(e["row"]["terms"]) for e in entries), default=0)],
        "maximum_absolute_coefficient": max((abs(c) for e in entries for _, c in e["row"]["terms"]), default=0),
        "maximum_coefficient_bits": max((abs(c).bit_length() for e in entries for _, c in e["row"]["terms"]), default=0),
        "maximum_absolute_activity": max((sum(abs(c) for _, c in e["row"]["terms"]) for e in entries), default=0),
        "rows_cutting_any_accepted_candidate": sum(bool(e["candidate_violations"]) for e in entries),
    }


def run(directory):
    started = time.monotonic()
    deadline = started + 120
    producer, helper = load("producer"), load("helper")
    config, bank, census = load("configuration"), load("bank"), load("census")
    assert bank["configuration_sha256"] == INPUTS["configuration"][1]
    assert census["bank"]["sha256"] == INPUTS["bank"][1]
    assert census["domain"] == config["domain"] and not census["whole_component_excluded"]
    planned = [producer.normalized(e["row"]) for e in producer.read(config["prefix253"])]
    planned += [producer.normalized({"terms": r, "rhs": 0})
                for r in producer.read(config["extra48"])["new_rows_upper_zero_vs_frozen157"]]
    planned_keys = {helper.key(r) for r in planned}
    assert len(planned) == len(planned_keys) == 301
    literal = [producer.normalized(r) for r in producer.read(config["literal_rows"])]
    assert len(literal) == 4416
    rows = census["rows"]
    assert len(rows) == 12204 and len(census["attempts"]) == 54720
    assert [e["key"] for e in rows] == sorted(set(e["key"] for e in rows))
    for entry in rows:
        assert entry["row"] == producer.normalized(entry["row"])
        assert entry["key"] == helper.key(entry["row"])
        assert entry["in_planned301"] == (entry["key"] in planned_keys)
    fresh = [e for e in rows if not e["in_planned301"]]
    authoritative = [{"row": r, "origin": {"family": "literal4416", "index": i}} for i, r in enumerate(literal)]
    authoritative += [{"row": r, "origin": {"family": "planned301", "index": i}} for i, r in enumerate(planned)]
    cache = {}

    def cached(value):
        key = value["key"]
        if key not in cache:
            weights = dict(value["weights"])
            cache[key] = (weights, sum(1 << j for j in weights))
        return cache[key]

    def equivalent_dominates(first, second):
        assert time.monotonic() < deadline
        if first["anchor"] != second["anchor"]:
            return False
        left, mask_left = cached(first)
        right, mask_right = cached(second)
        if mask_left & ~mask_right:
            return False
        return all(w * second["demand"] <= right[j] * first["demand"] for j, w in left.items())

    helper.dominates = equivalent_dominates
    reduced = helper.reduce_rows([{"row": e["row"], "origin": {"raw_row_key": e["key"]}} for e in fresh], authoritative)
    assert time.monotonic() < deadline
    reduction_ref = producer.save(directory, "dominance.json.gz", reduced)
    selected = [set(c["selection"]) for c in bank["candidates"]]
    retained = reduced["retained"]
    for item in retained:
        item["candidate_violations"] = [[i, gap] for i, support in enumerate(selected) if item["anchor"] in support
            for gap in [sum(c for j, c in item["row"]["terms"] if j in support)] if gap > 0]
    common = {"source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
              "complete_census": {"path": INPUTS["census"][0], "sha256": INPUTS["census"][1]},
              "dominance": reduction_ref, "all_planned301_and_original4416_preserved": True,
              "reduction_criterion": "exact_same_anchor_coordinatewise_sufficient_dominance_after_boolean_capping",
              "minimal_under_all_boolean_implications_claimed": False}
    export_ref = producer.save(directory, "retained-rows.json", dict(common,
        status="EXACT_REANCHORED_ROWS_PENDING_INDEPENDENT_COLD", retained=retained,
        rows_upper_zero=[item["row"]["terms"] for item in retained]))
    report = dict(common, status="COMPLETE_EXACT_SHARED_SINGLE_ANCHOR_CENSUS_PENDING_COLD",
        retained_rows=export_ref, single_anchor_certificates=10, primitive_transported_potentials=len(bank["bank"]),
        anchor_potential_pairs=len(census["attempts"]), positive_demand_pairs=sum(x[2] > 0 for x in census["attempts"]),
        all_rows=statistics(rows), new_vs_planned301=statistics(fresh), retained_frontier=statistics(retained),
        dominance_counts=reduced["counts"], rows_removed_from_planned301=0, rows_removed_from_literal4416=0,
        optimizer_calls=0, native_imports=0, historical_potential_bank_read=False, whole_component_excluded=False,
        first_attempt_terminal_accepted=False, resume_deadline_seconds=120, seconds=time.monotonic() - started)
    assert time.monotonic() < deadline
    producer.save(directory, "report.json", report)
    return report


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    result = run(directory)
    print(json.dumps({k: result[k] for k in ("status", "new_vs_planned301", "retained_frontier", "dominance_counts", "seconds")}, sort_keys=True))
