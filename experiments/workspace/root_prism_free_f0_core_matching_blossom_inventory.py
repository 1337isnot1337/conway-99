"""Compact, source-bound inventory of the completed F0 blossom certificates.

Only previously cold-checked rows are copied. A separate optional point scan
reports exact row evaluations and never accepts a count or graph witness.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "result": ("f0-core-matching-blossom-family-run01/result.json", "901ead85d602598336d1031f1ebc58cacf18ab9c258cd73654b04c6eca635b86"),
    "cold": ("f0-core-matching-blossom-family-run01-cold.json", "664074cc423d925778e3e4e4898db996fdec0f30c6e0bf633b5e2a74ca796bc1"),
    "gate": ("f0-core-matching-blossom-family-root-gate01.json", "976e31eec53c14dd95ab21137935b9b7c052891de0bce72f11dabd25fdcc4331"),
    "domains": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
}
FAMILY_SOURCE = "21e2a8e84821b88c214eb5e514c6095b2b163e19ae1a1b4849c5e3c47a42e6f5"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    path, expected = INPUTS[name]
    raw = (BASE/path).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def binding():
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": str((BASE/p).relative_to(ROOT)), "sha256": h}
                       for k, (p, h) in INPUTS.items()}, "family_source_sha256": FAMILY_SOURCE}


def build():
    started = time.monotonic()
    result, cold, gate, domains = [read(k) for k in INPUTS]
    assert result["status"] == "COMPLETE" and result["complete"]
    assert result["processed_triples"] == 549480 and result["distinct_rows"] == 8894
    assert result["source_sha256"] == cold["source_sha256"] == gate["source_sha256"] == FAMILY_SOURCE
    assert cold["complete_saved_prefix_checked"] and cold["producer_complete"]
    assert cold["record_sha256"] == INPUTS["result"][1]
    assert cold["checked_chunks"] == 18 and cold["checked_rows"] == 8894
    assert cold["checked_triples"] == 549480 and cold["checked_live_cliques"] == 106584
    assert gate["status"].startswith("PASS")
    boxes = domains["target_variable_domains"]
    assert len(boxes) == 18444
    rows, active, omitted, chunks = [], [], [], []
    for site, info in enumerate(result["chunks"]):
        assert info["path"] == "core%02d.json.gz" % site and info["complete_core"]
        path = BASE/"f0-core-matching-blossom-family-run01"/info["path"]
        packed = path.read_bytes()
        assert sha(packed) == info["sha256"]
        raw = gzip.decompress(packed)
        assert sha(raw) == info["raw_sha256"] and len(raw) == info["raw_bytes"]
        chunk = json.loads(raw)
        assert chunk["core_site"] == site and chunk["complete_core"]
        chunks.append({"path": str(path.relative_to(ROOT)), "sha256": sha(packed),
                       "raw_sha256": sha(raw)})
        for position, row in enumerate(chunk["new_rows"]):
            assert row["id"] == len(rows)
            terms = row["terms"]
            assert terms == sorted(terms) and len({j for j, _ in terms}) == len(terms)
            assert 2 <= len(terms) <= 3 and all(42 <= j < 15038 and c in (1, 2) for j, c in terms)
            assert row["rhs"] in (6, 12)
            upper_bounds = [[j, boxes[j][-1]] for j, _ in terms]
            value = sum(c*boxes[j][-1] for j, c in terms)
            assert value == row["comparison"]["current_box_maximum"]
            implied = value <= row["rhs"]
            assert implied == row["comparison"]["implied_by_current_explicit_boxes"]
            compact = {"id": row["id"], "terms": terms, "rhs": row["rhs"],
                       "witness_ref": {"chunk": site, "new_rows_index": position}}
            rows.append(compact)
            if implied:
                omitted.append({**compact, "upper_bounds": upper_bounds, "box_maximum": value})
            else:
                active.append(compact)
    assert len(rows) == 8894 and len(active) == 6854 and len(omitted) == 2040
    assert sorted(r["id"] for r in active+omitted) == list(range(8894))
    assert len({r["id"] for r in active+omitted}) == 8894
    assert sum(len(r["terms"]) for r in rows) == 26662
    common = {"schema": "conway99.f0.compact-core-blossom-rows.v1", "definition": binding(),
              "proof_chunks": chunks, "optimizer_calls": 0,
              "production_candidates": 0, "full_model_nonredundance_claimed": False}
    return {
        "all": {**common, "selection": "all complete normalized rows", "rows": rows},
        "selected": {**common, "selection": "not implied by the explicitly bound domain boxes alone", "rows": active},
        "omitted": {**common, "selection": "complete complement; exact positive-coefficient box proofs",
                    "omission_domain_sha256": INPUTS["domains"][1], "rows": omitted,
                    "transport_requirement": "At later native integration, verify each used native upper bound is at most its saved upper bound."},
        "seconds": time.monotonic()-started,
    }


def write_inventory(directory):
    assert not directory.exists()
    built = build()
    directory.mkdir(parents=True)
    files = {}
    for key in ("all", "selected", "omitted"):
        raw = canonical(built[key]) + b"\n"
        packed = gzip.compress(raw, compresslevel=9, mtime=0)
        name = key+"-rows.json.gz"
        (directory/name).write_bytes(packed)
        files[key] = {"path": name, "sha256": sha(packed), "raw_sha256": sha(raw),
                      "rows": len(built[key]["rows"]),
                      "nonzeros": sum(len(r["terms"]) for r in built[key]["rows"]),
                      "bytes": len(packed)}
    report = {"status": "PASS: compact full inventory and exact box-complement partition",
              "definition": binding(), "files": files, "all_rows": 8894, "selected_rows": 6854,
              "omitted_rows": 2040, "all_nonzeros": 26662, "optimizer_calls": 0,
              "production_candidates": 0, "new_family_cases_enumerated": 0,
              "seconds": built["seconds"]}
    (directory/"report.json").write_bytes(canonical(report)+b"\n")
    return report


def checked_inventory(directory):
    report_raw = (directory/"report.json").read_bytes()
    report = json.loads(report_raw)
    assert report["definition"] == binding()
    assert report["status"].startswith("PASS")
    out = {}
    for key, info in report["files"].items():
        packed = (directory/info["path"]).read_bytes()
        assert sha(packed) == info["sha256"]
        raw = gzip.decompress(packed)
        assert sha(raw) == info["raw_sha256"]
        out[key] = json.loads(raw)
        assert out[key]["definition"] == binding()
        assert len(out[key]["rows"]) == info["rows"]
    assert [r["id"] for r in out["all"]["rows"]] == list(range(8894))
    return report, out


def scan(directory, candidate, output):
    assert not output.exists()
    report, inventory = checked_inventory(directory)
    raw = candidate.read_bytes()
    values = json.loads(raw)
    assert isinstance(values, list) and len(values) == 32296 and all(type(v) is int for v in values)
    bad, minimum_slack = [], None
    for row in inventory["all"]["rows"]:
        value = sum(c*values[j] for j, c in row["terms"])
        slack = row["rhs"]-value
        minimum_slack = slack if minimum_slack is None else min(minimum_slack, slack)
        if slack < 0:
            bad.append({"id": row["id"], "activity": str(value), "rhs": row["rhs"],
                        "witness_ref": row["witness_ref"]})
    result = {"status": "EXACT_ROW_EVALUATION_ONLY", "definition": binding(),
              "inventory_report_sha256": sha((directory/"report.json").read_bytes()),
              "candidate_file_sha256": sha(raw), "canonical_vector_sha256": sha(canonical(values)),
              "checked_rows": 8894, "violations": bad, "minimum_slack": str(minimum_slack),
              "candidate_count_acceptance_checked": False, "literal_incidence_acceptance_checked": False,
              "graph_or_exterior_realization_claimed": False, "optimizer_calls": 0}
    output.write_bytes(canonical(result)+b"\n")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("prepare", "scan"))
    ap.add_argument("--directory", type=Path, required=True)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.mode == "prepare":
        result = write_inventory(args.directory)
    else:
        assert args.candidate is not None and args.output is not None
        result = scan(args.directory, args.candidate, args.output)
    print(json.dumps({k: result[k] for k in ("status", "all_rows", "selected_rows", "omitted_rows",
                                            "all_nonzeros", "seconds", "checked_rows") if k in result}, indent=2))


if __name__ == "__main__":
    main()
