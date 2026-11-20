"""Lossless archive of the frozen reduced second-moment run01 records; no optimizer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "exact.json": "0a3b19ebd18c4bf9ae0ed08c192953116b38da4211165bfcc319891f24f8242d",
    "exact.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "exact.stdout.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "numerical.json": "dff47477cd91be1dcaedde33d672ea0a3382ebc6214d319e5bfad04daa72eac3",
    "numerical.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "numerical.stdout.log": "3e7bced6a689d10e25a5ee9cc3e157eb02681e2c7e259617b00b7bcd61c1418a",
    "result.json": "962f7dce4270f80e55b798d8284546b2ec8ed9b00acb436709f858a1d617dd98"
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(record):
    assert record["schema"] == "f0-second-moments-reduced-run01-exact-byte-archive-v1"
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
    record = {"schema": "f0-second-moments-reduced-run01-exact-byte-archive-v1",
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

