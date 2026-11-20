"""Lossless archive of the three disjoint branch-continuation stages."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/rook-case4-face112-branch-continuation01-"
STAGES = {
    "forward": "6d42fa285b24ca5c0e646922934576ea5d9b0bb0a0b90cbaff7bbdddd95cbd49",
    "cold-old": "acbc2fde9ed1f342e6d33ef9dd24f600f70e23be8623cfdd09a4947475db3c5b",
    "cold-new": "4329b386b6fb5a7493a7159f18c90332cd0765e68cff4e16b67f3456728198e0",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def inventory(files):
    paths, stage_ids = [], {}
    for stage, expected in STAGES.items():
        prefix = BASE+stage+"/"
        assert sha(files[prefix+"result.json"].encode()) == expected
        result = json.loads(files[prefix+"result.json"])
        assert result["stage"] == stage
        ids = result["saved_complete_branch_ids"] if stage == "forward" else result["verified_branch_ids"]
        assert len(ids) == (22 if stage == "cold-old" else 14)
        assert not result.get("remaining_unchecked_ids", [])
        assert not result.get("saved_partial_branch_ids", [])
        stage_ids[stage] = ids
        paths += [prefix+name for name in ("result.json", "progress.json", "supervisor.json",
                                          "child.stdout.log", "child.stderr.log")]
        paths += [prefix+"branch%02d.json" % i for i in ids]
    assert stage_ids["forward"] == stage_ids["cold-new"]
    assert set(stage_ids["cold-old"]).isdisjoint(stage_ids["cold-new"])
    assert len(paths) == len(set(paths)) == 65
    assert set(files) == set(paths)
    return sorted(paths)


def validate(payload):
    assert payload["schema"] == "conway99.face112-branch-continuation-archive.v1"
    assert payload["source_sha256"] == sha(Path(__file__).read_bytes())
    assert payload["stage_result_sha256"] == STAGES
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


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("pack", "restore"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    if a.mode == "pack":
        assert not a.archive.exists()
        files = {}
        for stage in STAGES:
            for path in sorted((a.root/(BASE+stage)).rglob("*")):
                if path.is_file():
                    assert not path.is_symlink()
                    files[str(path.relative_to(a.root))] = path.read_bytes().decode()
        paths = inventory(files)
        payload = {"schema": "conway99.face112-branch-continuation-archive.v1",
                   "source_sha256": sha(Path(__file__).read_bytes()),
                   "stage_result_sha256": STAGES, "files": files,
                   "members": {p: {"sha256": sha(files[p].encode()), "bytes": len(files[p].encode())}
                               for p in paths},
                   "uncompressed_member_bytes": sum(len(files[p].encode()) for p in paths)}
        validate(payload)
        with a.archive.open("xb") as handle:
            handle.write(gzip.compress(canonical(payload), compresslevel=9, mtime=0))
    encoded = a.archive.read_bytes()
    files, paths, total = validate(json.loads(gzip.decompress(encoded)))
    if a.mode == "restore":
        for path in paths:
            target = a.root/path
            assert not target.is_symlink() and target.resolve().is_relative_to(a.root.resolve())
            if target.exists():
                assert target.read_bytes() == files[path].encode(), path
        for path in paths:
            target = a.root/path
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as handle:
                    handle.write(files[path].encode())
    for path in paths:
        assert (a.root/path).read_bytes() == files[path].encode(), path
    report = {"status": "PASS: all65 continuation members restored or checked byte for byte",
              "mode": a.mode, "source_sha256": sha(Path(__file__).read_bytes()),
              "archive_sha256": sha(encoded), "archive_bytes": len(encoded),
              "members": len(paths), "uncompressed_member_bytes": total,
              "forward_branches": 14, "old_cold_branches": 22, "new_cold_branches": 14,
              "production_or_reason_checker_calls": 0, "solver_calls": 0, "case4_excluded": False}
    with a.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report, indent=2))
