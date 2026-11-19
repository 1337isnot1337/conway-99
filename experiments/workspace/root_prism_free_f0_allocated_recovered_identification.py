"""Read-only identification of the recovered final allocated F0 transcript.

This checks byte identities and authenticates the saved cold-replay report.
It does not rerun the mathematical transcript replay or an optimizer.
"""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
PREFIX = "experiments/logs/root-prism-free/f0-allocated-lazy-continuation-run01/"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def checked(path, expected):
    raw = (ROOT/path).read_bytes()
    assert digest(raw) == expected, path
    return raw

manifest_raw = checked("experiments/logs/root-prism-free/f0-allocated-lazy-continuation-run01-transcript-bundle.json", "75e803942a2cda8332f20a90f5b668d13cff4978652b85238708130ce7c776cb")
manifest = json.loads(manifest_raw)
archive = checked(manifest["archive"], "7345f9cef9f0785310a7568067ba2a2e5dc90c72c8fe843051d3d3993a245ce0")
assert len(archive) == manifest["archive_bytes"] == 6766832
tar = gzip.decompress(archive)
assert digest(tar) == manifest["tar_sha256"] == "6e0048c80653fb86b8f5e5167aafc70aa08c5a07d900f19e8e5427e3708286f0"
expected = {row["path"]: row for row in manifest["records"]}
assert len(expected) == len(manifest["records"]) == 363
recovered, total, present = {}, 0, 0
with tarfile.open(fileobj=io.BytesIO(tar), mode="r:") as handle:
    for member in handle:
        assert member.isfile() and member.name in expected and member.name not in recovered
        assert member.name.startswith(PREFIX) and ".." not in Path(member.name).parts
        row = expected[member.name]
        raw = handle.extractfile(member).read()
        assert len(raw) == row["bytes"] == member.size
        assert digest(raw) == row["sha256"]
        local = ROOT/member.name
        if local.exists():
            assert local.read_bytes() == raw
            present += 1
        recovered[member.name] = json.loads(gzip.decompress(raw) if member.name.endswith(".gz") else raw)
        total += len(raw)
assert set(recovered) == set(expected) and total == manifest["uncompressed_record_bytes"] == 37909307

cold_path = "experiments/logs/root-prism-free/f0-allocated-lazy-continuation-run01-cold-replay.json"
cold = json.loads(checked(cold_path, "4c437fb8ad028bc9aa55753cc0da33d557d884c75962531e991fc2743b2dde9a"))
restored_path = "experiments/logs/root-prism-free/f0-allocated-lazy-continuation-run01-bundle-replay.json"
restored = json.loads(checked(restored_path, "a49b360af77d410948b7cb8d0016d7fe8a22238ff45187b623dae3b98ed12875"))
assert restored["restoration_requested"] and restored["missing_files_written"] == 0
assert restored["equal_existing_files_preserved"] == 363 and restored["unequal_existing_files_never_overwritten"]
assert cold["source_sha256"] == "46b30a4e7c64db612cff606bd56aa05da44356547f617e977a8fa17ac0da4c8d"
checked("experiments/workspace/root_prism_free_f0_allocated_lazy_continuation.py", cold["source_sha256"])
checked("experiments/workspace/root_prism_free_f0_allocated_lazy_transcript_bundle.py", manifest["source_sha256"])
checked("experiments/logs/root-prism-free/f0-allocated-lazy-continuation-preparation.json.gz", cold["preparation_sha256"])
result = recovered[PREFIX+"result.json"]
assert cold["result_sha256"] == manifest["result_sha256"] == "6955adbab024f3a3668258c5fad56592d05025acf381d4a4a71d1915b788deab"
individual = recovered[PREFIX+"individual-registry.json.gz"]
shared = recovered[PREFIX+"symmetric-registry.json.gz"]
quadratic = recovered[PREFIX+"quadratic-registry.json.gz"]
assert len(individual) == 3948 and len(shared) == 456 and len(quadratic) == 38
assert cold["final_snapshot"]["individual_cuts"] == len(individual)
assert cold["final_snapshot"]["symmetric_cuts"] == len(shared)
assert cold["final_quadratic_snapshot"]["base_potential_families"] == len(quadratic)
assert not cold["optimizer_or_solver_called"] and not cold["whole_component_excluded"]
assert not cold["full_graph_completion"] and not cold["UNSAT_proof_checked"]
report = {
    "status": "PASS: all363 recovered members and saved replay/source bindings checked exactly",
    "source_sha256": digest(Path(__file__).read_bytes()),
    "archive_sha256": digest(archive), "manifest_sha256": digest(manifest_raw),
    "tar_sha256": digest(tar), "records": len(recovered),
    "uncompressed_record_bytes": total, "present_equal_local_records": present,
    "individual_cuts": len(individual), "shared_cuts": len(shared),
    "total_selector_cuts": len(individual)+len(shared),
    "base_quadratic_families": len(quadratic),
    "saved_cold_replay_sha256": digest((ROOT/cold_path).read_bytes()),
    "saved_restoration_replay_sha256": digest((ROOT/restored_path).read_bytes()),
    "saved_cold_status": cold["status"], "saved_final_snapshot": cold["final_snapshot"],
    "saved_restoration_status": restored["status"],
    "saved_final_status": restored["frozen_result_status"],
    "fresh_mathematical_transcript_replay": False,
    "optimizer_called": False, "files_modified": False,
    "scope": "Byte/source identification only; final4,404 rows are separate from the earlier2,928-cut seed."
}
print(json.dumps(report, sort_keys=True, indent=2))
