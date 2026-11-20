"""Lossless archive/restoration binding for the prepared native proto."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free/f0-population-products-cpsat01"
RAW_SHA = "aa43ef31991213634b0cc812b61a5d1247c1915c6690def64a54247854ee8589"
RAW_BYTES = 11588655


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("archive", "verify", "restore"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw_path, archive_path, record_path = BASE/"model.pb", BASE/"model.pb.gz", BASE/"archive.json"
    if args.mode == "archive":
        raw = raw_path.read_bytes()
        assert len(raw) == RAW_BYTES and sha(raw) == RAW_SHA
        compressed = gzip.compress(raw, mtime=0)
        with archive_path.open("xb") as stream:
            stream.write(compressed)
        record = {"source_sha256": sha(Path(__file__).read_bytes()),
                  "raw": {"path": str(raw_path.relative_to(ROOT)), "sha256": RAW_SHA, "bytes": RAW_BYTES},
                  "archive": {"path": str(archive_path.relative_to(ROOT)), "sha256": sha(compressed), "bytes": len(compressed)},
                  "compression": "gzip with mtime=0", "semantic_changes": False}
        with record_path.open("x") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
    else:
        record = json.loads(record_path.read_bytes())
        assert record["source_sha256"] == sha(Path(__file__).read_bytes())
        compressed = archive_path.read_bytes()
        assert record["raw"] == {"path": str(raw_path.relative_to(ROOT)), "sha256": RAW_SHA, "bytes": RAW_BYTES}
        assert record["archive"]["sha256"] == sha(compressed) and record["archive"]["bytes"] == len(compressed)
    raw = gzip.decompress(compressed)
    assert len(raw) == RAW_BYTES and sha(raw) == RAW_SHA
    restored = False
    if args.mode == "restore" and not raw_path.exists():
        with raw_path.open("xb") as stream:
            stream.write(raw)
        restored = True
    if raw_path.exists():
        assert raw_path.read_bytes() == raw
    result = {"status": "PASS: exact native proto archive " + args.mode,
              "source_sha256": sha(Path(__file__).read_bytes()),
              "archive_record_sha256": sha(record_path.read_bytes()),
              "raw_sha256": RAW_SHA, "raw_bytes": RAW_BYTES,
              "archive_sha256": sha(compressed), "archive_bytes": len(compressed),
              "raw_file_restored": restored, "optimizer_calls": 0}
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
