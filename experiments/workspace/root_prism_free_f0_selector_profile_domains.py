"""Project the frozen complete local profile tables to coordinate domains.

This reads the checked tables, not a numerical point. It performs no solver
query and does not assert cross-orbit compatibility or global feasibility.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "profiles": ("f0-selector-orbit-profiles01.json.gz", "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "profile_replay": ("f0-selector-orbit-profiles01-cold.json", "cb10cd7dc77236d9caed7c7b8a410a33f7b998bea8d257b500d3c9f8561a76f8"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    filename, expected = INPUTS[name]
    raw = (BASE / filename).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if filename.endswith(".gz") else raw)


def build():
    profiles, cold, domains = [read(name) for name in INPUTS]
    assert cold["status"].startswith("PASS")
    rows, seen = [], set()
    for table in profiles["tables"]:
        for pos, column in enumerate(table["count_columns"]):
            assert column not in seen
            seen.add(column)
            allowed = sorted({p["counts"][pos] for p in table["profiles"]})
            size = domains["new15038_orbit_sizes"][column]
            assert allowed[0] == 0 and allowed[-1] <= size
            witness = {str(v): next(i for i, p in enumerate(table["profiles"])
                                   if p["counts"][pos] == v) for v in allowed}
            rows.append({"count_column": column,
                         "original15589_column": domains["new15038_to_original15589"][column],
                         "selector_orbit": table["selector_orbit"], "table_position": pos,
                         "orbit_size_bound": size, "allowed_values": allowed,
                         "profile_witness_index_for_each_value": witness,
                         "improved_upper_bound": allowed[-1] < size,
                         "holes_below_maximum": sorted(set(range(allowed[-1]+1))-set(allowed))})
    assert len(rows) == 362 and len(seen & set(range(42))) == 42
    improved = [r for r in rows if r["improved_upper_bound"]]
    hist = Counter((r["orbit_size_bound"], r["allowed_values"][-1]) for r in improved)
    return {"schema": "conway99.f0-selector-profile-coordinate-domains.v1",
            "status": "EXACT_PROJECTION_OF_CHECKED_LOCAL_TABLES",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+v[0], "sha256": v[1]}
                       for k, v in INPUTS.items()},
            "coordinate_domains": sorted(rows, key=lambda r: r["count_column"]),
            "covered_count_columns": len(rows), "covered_selector_populations": 42,
            "covered_within_orbit_pair_populations": len(rows)-42,
            "improved_upper_bounds": len(improved),
            "improved_selector_population_bounds": sum(r["count_column"] < 42 for r in improved),
            "improvement_histogram": [{"old": a, "new": b, "columns": n}
                                       for (a, b), n in sorted(hist.items())],
            "domains_with_holes_below_maximum": sum(bool(r["holes_below_maximum"]) for r in rows),
            "validity": "Each coordinate must equal a coordinate of one permitted local profile. The recorded set is its exact projection; each allowed value has a table-row witness.",
            "global_incidence_claimed": False, "new_constraints_beyond_full_profile_tables": False,
            "optimizer_calls": 0, "solver_calls": 0, "F0_excluded": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build()
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()+b"\n"
    with args.output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({k: v for k, v in result.items() if k not in ("coordinate_domains", "inputs")}, indent=2))
    print("sha256="+sha(raw))
