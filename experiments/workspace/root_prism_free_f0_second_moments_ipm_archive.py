"""Lossless archive of the frozen IPM second-moment run01 records; no optimizer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "exact.json": "f7e63bf885aaf69b5ebe836d979819ae493b67d51c2e853d7b2ba3a02e136a29",
    "exact.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "exact.stdout.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "numerical.json": "20674e3a41842e42232df60e24abf3f34a5a5c8ec9a16a258d4906bb58562fd9",
    "numerical.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "numerical.stdout.log": "66b53601122b126a36e3ec70481eab98288bd1625fded6c3983d8a425c5b6085",
    "result.json": "571ff5c23da8febc4bb0f76a54f1d9196e268d6a7bd1d02b3dc087ab516b3421"
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(record):
    assert record["schema"] == "f0-second-moments-ipm-run01-exact-byte-archive-v1"
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
    record = {"schema": "f0-second-moments-ipm-run01-exact-byte-archive-v1",
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

