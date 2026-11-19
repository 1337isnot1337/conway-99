"""Export the exact literal F0 cuts from the hash-bound public model."""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time

SOURCE = "experiments/logs/root-prism-free/f0-boolean-fractional-model.json.gz"
SOURCE_SHA256 = "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"
REQUEST = "experiments/logs/root-prism-free/f0-literal-cut-export-request01.json"
MAX_COMPRESSED = 32 << 20
MAX_RAW = 128 << 20
MAX_EXPORTED_COMPRESSED = 12 << 20
DECIMAL = re.compile(r"(?:0|-?[1-9][0-9]*)\Z")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    request = json.loads(Path(REQUEST).read_text())
    assert request["mode"] == "export-exact-literal-rows-only"
    assert request["source_path"] == SOURCE and request["source_sha256"] == SOURCE_SHA256
    assert request["driver_sha256"] == digest(Path(__file__).read_bytes())
    assert request["optimizer_calls"] == 0
    raw = Path(SOURCE).read_bytes()
    assert len(raw) <= MAX_COMPRESSED and digest(raw) == SOURCE_SHA256
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as stream:
        expanded = stream.read(MAX_RAW + 1)
    assert len(expanded) <= MAX_RAW
    model = json.loads(expanded)
    rows = model["Boolean_validation"]["full_rows"]
    assert len(rows) == 4416
    terms = 0
    maximum_coefficient_bits = 0
    for row in rows:
        assert set(row) == {"terms", "rhs"}
        assert row["rhs"] == "0"
        used = set()
        for column, coefficient in row["terms"]:
            assert type(column) is int and 0 <= column < 480 and column not in used
            assert type(coefficient) is str and DECIMAL.fullmatch(coefficient)
            value = int(coefficient)
            assert value != 0
            used.add(column)
            maximum_coefficient_bits = max(maximum_coefficient_bits, abs(value).bit_length())
        terms += len(row["terms"])
    assert terms == 442308
    payload = (json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    archive = gzip.compress(payload, compresslevel=9, mtime=0)
    assert len(archive) <= MAX_EXPORTED_COMPRESSED
    args.directory.mkdir(parents=True, exist_ok=False)
    (args.directory / "literal-rows.json.gz").write_bytes(archive)
    report = {
        "schema": "conway99.f0.exact_literal_cut_export.v1",
        "status": "PASS: exact frozen literal rows exported",
        "driver_sha256": digest(Path(__file__).read_bytes()),
        "request_sha256": digest(Path(REQUEST).read_bytes()),
        "source_path": SOURCE,
        "source_sha256": SOURCE_SHA256,
        "source_compressed_bytes": len(raw),
        "source_raw_bytes": len(expanded),
        "source_field": "Boolean_validation.full_rows",
        "rows": len(rows),
        "nonzero_terms": terms,
        "maximum_coefficient_bits": maximum_coefficient_bits,
        "output_path": "literal-rows.json.gz",
        "output_sha256": digest(archive),
        "output_raw_sha256": digest(payload),
        "output_bytes": len(archive),
        "output_raw_bytes": len(payload),
        "optimizer_calls": 0,
        "source_inequality_arithmetic_modified": False,
        "seconds": time.monotonic() - started,
    }
    (args.directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("CONWAY99_F0_LITERAL_EXPORT_REPORT_BEGIN")
    print(json.dumps(report, sort_keys=True))
    print("CONWAY99_F0_LITERAL_EXPORT_REPORT_END")
    encoded = base64.b64encode(archive).decode("ascii")
    print("CONWAY99_F0_LITERAL_EXPORT_BASE64_BEGIN")
    for start in range(0, len(encoded), 4096):
        print(encoded[start:start + 4096])
    print("CONWAY99_F0_LITERAL_EXPORT_BASE64_END")


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    main()
