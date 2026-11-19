"""Lossless compact export of the independently checked fresh row family."""
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "full_export": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring02/retained-rows.json.xz", "e82cd96fb6d57b6a7dd447b01b4857d257fee9b547ca5a892bf0895c14b3b3ac"),
    "cold": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring02-independent-cold.json.gz", "c5eca2313768571598d9d402723f2308ac5f1b0bb1c7c44212a0ce2abb3301f2"),
    "report": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring02/report.json", "324eb0884b2da0b5ef81756077261780e7f1619e0f5ad01105a6a02879d3d9ee"),
    "peer_review": ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring-peer-source-review01.json", "2a24f8672ec7f798f8d2fe8c93f6d0e92681e4522dcef82c0f9866ccabb3b4af"),
    "cold_source": ("experiments/workspace/root_prism_free_f0_shared_single_anchor_reanchoring_replay.py", "76df109a6d68bb16b7ddf90f9de3dd9240ec3699f363c88fa58f0965b3070629"),
}
FULL_SHA256 = "5897295a988c38b8cd459402eef1e7e2ea29519c6363f02c9ac71aab73d7163f"
COLD_SHA256 = "4d5b7a4a10bc1deed16509b0ed2dfbcc2d4794178054846a4c3f5768f967f05f"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(kind):
    name, expected = INPUTS[kind]
    content = (ROOT / name).read_bytes()
    assert sha(content) == expected
    raw = lzma.decompress(content) if name.endswith(".xz") else gzip.decompress(content) if name.endswith(".gz") else content
    return json.loads(raw), sha(raw)


def export(path):
    started = time.monotonic()
    full, full_sha = read("full_export")
    cold, cold_sha = read("cold")
    report, _ = read("report")
    peer, _ = read("peer_review")
    assert full_sha == FULL_SHA256 and cold_sha == COLD_SHA256
    assert sha((ROOT / INPUTS["cold_source"][0]).read_bytes()) == INPUTS["cold_source"][1]
    assert cold["source_sha256"] == INPUTS["cold_source"][1]
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_SHARED_CENSUS_AND_DIRECT_COVERAGE"
    assert peer["status"] == "PASS_COMPLETE_INDEPENDENT_REPLAY_SOURCE_REVIEW" and not peer["blockers"]
    assert peer["cold"]["sha256"] == cold_sha
    assert cold["retained_export_sha256"] == full_sha
    assert cold["reduction_report_sha256"] == INPUTS["report"][1]
    assert report["retained_rows"]["sha256"] == full_sha
    assert cold["complete_census_sha256"] == full["complete_census"]["sha256"]
    assert cold["dominance_sha256"] == full["dominance"]["sha256"]
    assert full["rows_upper_zero"] == cold["rows_upper_zero"] == [e["row"]["terms"] for e in full["retained"]]
    assert len(full["retained"]) == report["retained_frontier"]["rows"] == 12168
    provenance = []
    for row in full["retained"]:
        assert row["row"]["rhs"] == 0 and sha(canonical(row["row"])) == row["key"]
        assert all(type(j) is int and type(c) is int for j, c in row["row"]["terms"])
        provenance.append({"capped_row_key": row["key"], "raw_row_origins": row["origins"],
                           "candidate_violations": row["candidate_violations"]})
    result = {
        "status": "CERTIFIED_COMPLETE_SHARED_SINGLE_ANCHOR_REANCHORED_ROWS",
        "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
        "full_export_raw_sha256": full_sha, "independent_cold_raw_sha256": cold_sha,
        "complete_census": full["complete_census"], "dominance": full["dominance"],
        "configuration_sha256": cold["configuration_sha256"], "bank_sha256": cold["bank_sha256"],
        "prefix253_value_sha256": cold["prefix253_value_sha256"],
        "row_count": len(provenance), "rows_upper_zero": full["rows_upper_zero"],
        "row_provenance": provenance, "provenance_resolution": "raw_row_key indexes the complete census, which binds potential_id, anchor, demand and the complete bank origins",
        "statistics": report["retained_frontier"], "all_original4416_and_planned301_must_remain": True,
        "no_rows_selected_or_removed_during_export": True, "optimizer_calls": 0,
        "native_imports": 0, "whole_component_excluded": False,
    }
    raw = canonical(result) + b"\n"
    encoded = gzip.compress(raw, compresslevel=6, mtime=0)
    assert time.monotonic() - started < 60
    with path.open("xb") as stream:
        stream.write(encoded)
    return {"status": result["status"], "path": str(path.relative_to(ROOT)), "sha256": sha(encoded),
            "raw_sha256": sha(raw), "bytes": len(encoded), "raw_bytes": len(raw),
            "rows": len(provenance), "seconds": time.monotonic() - started}


if __name__ == "__main__":
    assert __debug__ and len(sys.argv) == 2
    print(json.dumps(export(Path(sys.argv[1]).resolve()), sort_keys=True))
