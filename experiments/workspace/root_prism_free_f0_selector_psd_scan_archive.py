"""Byte-exact gzip transfer of the frozen selector-PSD scan01; no optimizer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

RAW_SHA256 = '7f8a2a22007539a67075aeb122ace3f81f800490723b8ca2c3a510c19ef45997'
GZIP_SHA256 = '5c74497bb70d44bf2fac7002ed16b4657500c4af2518cab196684c9346449e79'
RAW_BYTES = 13777345

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def archive(mode, source, output):
    assert not output.exists()
    raw = source.read_bytes()
    if mode == "pack":
        assert sha(raw) == RAW_SHA256 and len(raw) == RAW_BYTES
        encoded = gzip.compress(raw, mtime=0)
        assert sha(encoded) == GZIP_SHA256 and gzip.decompress(encoded) == raw
    else:
        assert sha(raw) == GZIP_SHA256
        encoded = gzip.decompress(raw)
        assert sha(encoded) == RAW_SHA256 and len(encoded) == RAW_BYTES
    output.write_bytes(encoded)
    assert sha(output.read_bytes()) == sha(encoded)
    return {"status": "PASS: exact scan bytes " + ("compressed" if mode == "pack" else "restored"),
            "source_sha256": sha(Path(__file__).read_bytes()), "input_sha256": sha(raw),
            "output_sha256": sha(encoded), "output_bytes": len(encoded), "optimizer_calls": 0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode", choices=("pack", "unpack"))
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a=p.parse_args()
    assert not a.report.exists()
    result=archive(a.mode,a.source,a.output)
    a.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
