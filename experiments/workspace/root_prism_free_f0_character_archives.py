"""Verify or restore the losslessly archived native count-model bytes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
ENTRIES = [
    ("f0-population-products-cpsat01/model.pb.gz", "37f744fd78fde8f3d6ca28ea4bcc63205299fb8c947b5212667ee08212b5f266",
     "f0-population-products-cpsat01/model.pb", "aa43ef31991213634b0cc812b61a5d1247c1915c6690def64a54247854ee8589", 11588655),
    ("f0-population-profile-cpsat01/model.pb.gz", "e1bd3e50c48f0a600a202aabbeecc80627fc4b6b1096ef32cdd8c17c8ed7d431",
     "f0-population-profile-cpsat01/model.pb", "500ab3e32622fe59eb45044a5d2610b087c030786df821ee06b85c8f0f3d21ef", 11647585),
    ("f0-character-cpsat01/model.pb.gz", "81acda719e5d7a65ccfeb95bcd956785ee9283d60630aed2f8933599933f3f57",
     "f0-character-cpsat01/model.pb", "5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb", 12498481),
    ("f0-character-cpsat01/model.pb.gz", "81acda719e5d7a65ccfeb95bcd956785ee9283d60630aed2f8933599933f3f57",
     "f0-character-query-run01/constructed-model.pb", "5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb", 12498481),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(restore):
    records = []
    for archive_name, archive_sha, target_name, target_sha, size in ENTRIES:
        archive = (LOGS / archive_name).read_bytes()
        assert sha(archive) == archive_sha
        raw = gzip.decompress(archive)
        assert len(raw) == size and sha(raw) == target_sha
        target = LOGS / target_name
        existed = target.exists()
        if existed:
            assert target.read_bytes() == raw
        elif restore:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
        records.append({"archive": str((LOGS / archive_name).relative_to(ROOT)), "archive_sha256": archive_sha,
                        "target": str(target.relative_to(ROOT)), "target_sha256": target_sha, "bytes": size,
                        "already_present_and_equal": existed, "restored": restore and not existed})
    return {"status": "PASS: all four native byte targets match their lossless archives",
            "source_sha256": sha(Path(__file__).read_bytes()), "mode": "restore" if restore else "verify",
            "targets": records, "optimizer_calls": 0, "existing_files_overwritten": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "restore"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.mode == "restore")
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
