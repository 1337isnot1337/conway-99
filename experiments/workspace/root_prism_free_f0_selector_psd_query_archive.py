"""Lossless archive of the frozen32-PSD-cut second-moment run01 records; no optimizer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "exact.json": "183d8640fcea05cfb7f480a611341e224b5de15f45be6c5d62b022277020ca73",
    "exact.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "exact.stdout.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "numerical.json": "ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf",
    "numerical.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "numerical.stdout.log": "e014915e0b492f7bb8d572d74fcfed8069a9dff248dc2ba31264f2500574b643",
    "result.json": "c766de716a7c0f4c372894d9dd68811e90b2570304c6f687d01362f4d72595d0"
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(record):
    assert record["schema"] == "f0-selector-psd-query-run01-exact-byte-archive-v1"
    assert record["archive_source_sha256"] == sha(Path(__file__).read_bytes())
    assert set(record["files"]) == set(EXPECTED)
    decoded = {}
    for name, item in record["files"].items():
        assert name == Path(name).name
        raw = item["text"].encode("utf-8")
        assert item["sha256"] == sha(raw) == EXPECTED[name]
        assert item["bytes"] == len(raw)
        decoded[name] = raw
    result = json.loads(decoded["result.json"])
    assert result["status"] == "UNKNOWN: no exact point or infeasibility certificate"
    assert result["optimizer_calls_recorded"] == 1
    return decoded


def pack(directory, output):
    assert not output.exists()
    assert {p.name for p in directory.iterdir() if p.is_file()} == set(EXPECTED)
    record = {"schema": "f0-selector-psd-query-run01-exact-byte-archive-v1",
              "archive_source_sha256": sha(Path(__file__).read_bytes()), "files": {}}
    for name in sorted(EXPECTED):
        raw = (directory/name).read_bytes()
        record["files"][name] = {"sha256": sha(raw), "bytes": len(raw), "text": raw.decode("utf-8")}
    validate(record)
    raw = json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    compressed = gzip.compress(raw, mtime=0)
    assert gzip.decompress(compressed) == raw
    output.write_bytes(compressed)
    return {"status": "PASS: all frozen bytes archived", "path": str(output),
            "sha256": sha(compressed), "bytes": len(compressed),
            "raw_file_bytes": sum(v["bytes"] for v in record["files"].values()),
            "files": len(EXPECTED), "optimizer_calls": 0}


def unpack(archive, directory):
    assert not directory.exists()
    raw = archive.read_bytes()
    record = json.loads(gzip.decompress(raw))
    decoded = validate(record)
    directory.mkdir(parents=True)
    for name, data in decoded.items():
        path = directory/name
        path.write_bytes(data)
        assert sha(path.read_bytes()) == EXPECTED[name]
    return {"status": "PASS: all frozen bytes restored into a fresh directory",
            "archive_sha256": sha(raw), "directory": str(directory),
            "file_sha256": EXPECTED, "optimizer_calls": 0}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    q = sub.add_parser("pack")
    q.add_argument("--directory", type=Path, required=True)
    q.add_argument("--output", type=Path, required=True)
    q = sub.add_parser("unpack")
    q.add_argument("--archive", type=Path, required=True)
    q.add_argument("--directory", type=Path, required=True)
    a = p.parse_args()
    report = pack(a.directory, a.output) if a.mode == "pack" else unpack(a.archive, a.directory)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

