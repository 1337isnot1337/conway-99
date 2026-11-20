"""Lossless, hash-bound archive of the first bounded face112 branch attempt."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
PREP = BASE + "rook-case4-face112-branch-batch-preparation01/"
FORWARD = BASE + "rook-case4-face112-branch-batch01/"
COLD = BASE + "rook-case4-face112-branch-batch01-cold/"
ANCHORS = {
    PREP + "preparation.json": "47ebe7180723ab95bdf5370c29a0be6abe80005dc5e0bd7e3df51926282b87ea",
    PREP + "rows.json": "361f04e0176d0ac53bed09ff9c7cdf33d76608b99c3a2426f0cf35345da46a55",
    FORWARD + "result.json": "186df7589b3baf14adda7fcce8409e89e149b5268ff432f12128b7301d09ab4b",
    COLD + "result.json": "b789fc8ee377e1899d4de553ad7c48019fdea8913599fb3c8605bf28cb80205e",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def inventory(files):
    for path, expected in ANCHORS.items():
        assert sha(files[path].encode()) == expected, path
    forward = json.loads(files[FORWARD + "result.json"])
    cold = json.loads(files[COLD + "result.json"])
    fids = forward["saved_complete_branch_ids"] + forward["saved_partial_branch_ids"]
    cids = cold["verified_complete_branch_ids"]
    assert len(fids) == 51 and len(cids) == 28
    paths = [PREP + "preparation.json", PREP + "rows.json"]
    for prefix, ids in ((FORWARD, fids), (COLD, cids)):
        paths += [prefix + name for name in
                  ("result.json", "progress.json", "supervisor.json", "child.stdout.log", "child.stderr.log")]
        paths += [prefix + "branch%02d.json" % i for i in ids]
    assert len(paths) == len(set(paths)) == 91
    assert set(files) == set(paths)
    return sorted(paths)


def validate(payload):
    assert payload["schema"] == "conway99.face112-branch-partial-archive.v1"
    assert payload["archive_source_sha256"] == sha(Path(__file__).read_bytes())
    assert payload["anchors"] == ANCHORS
    files = payload["files"]
    paths = inventory(files)
    total = 0
    for path in paths:
        assert not Path(path).is_absolute() and ".." not in Path(path).parts
        encoded = files[path].encode()
        assert payload["members"][path] == {"sha256": sha(encoded), "bytes": len(encoded)}
        total += len(encoded)
    assert set(payload["members"]) == set(paths)
    assert total == payload["uncompressed_member_bytes"]
    return files, paths, total


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("pack", "verify", "restore"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    if a.mode == "pack":
        assert not a.archive.exists()
        files = {}
        for prefix in (PREP, FORWARD, COLD):
            for path in sorted((a.root/prefix).rglob("*")):
                if path.is_file():
                    assert not path.is_symlink()
                    files[str(path.relative_to(a.root))] = path.read_bytes().decode()
        paths = inventory(files)
        payload = {"schema": "conway99.face112-branch-partial-archive.v1",
                   "archive_source_sha256": sha(Path(__file__).read_bytes()),
                   "anchors": ANCHORS, "files": files,
                   "members": {p: {"sha256": sha(files[p].encode()), "bytes": len(files[p].encode())}
                               for p in paths},
                   "uncompressed_member_bytes": sum(len(files[p].encode()) for p in paths)}
        validate(payload)
        with a.archive.open("xb") as f:
            f.write(gzip.compress(canonical(payload), compresslevel=9, mtime=0))
    encoded_archive = a.archive.read_bytes()
    files, paths, total = validate(json.loads(gzip.decompress(encoded_archive)))
    if a.mode == "restore":
        # Preflight every existing member before writing any missing member.
        for path in paths:
            target = a.root/path
            assert not target.is_symlink()
            assert target.resolve().is_relative_to(a.root.resolve())
            if target.exists():
                assert target.read_bytes() == files[path].encode(), path
        for path in paths:
            target = a.root/path
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as f:
                    f.write(files[path].encode())
    for path in paths:
        assert (a.root/path).read_bytes() == files[path].encode(), path
    report = {"status": "PASS: all91 immutable members and exact partial-coverage anchors checked",
              "mode": a.mode, "source_sha256": sha(Path(__file__).read_bytes()),
              "archive_sha256": sha(encoded_archive), "archive_bytes": len(encoded_archive),
              "member_count": len(paths), "uncompressed_member_bytes": total,
              "forward_complete": 50, "forward_partial": 1, "forward_unqueried": 13,
              "cold_checked_fixed_points": 28, "cold_unchecked_complete": 22,
              "propagation_calls": 0, "reason_checker_calls": 0,
              "solver_calls": 0, "case4_excluded": False}
    with a.output.open("x") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
