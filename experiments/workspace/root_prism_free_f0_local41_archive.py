"""Lossless archive of the frozen 41-center local SAT batch; no solver."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath

PREFIX = "experiments/logs/root-prism-free/"
CENTERS = [336, 50, 37, 57, 63, 53, 47, 2, 39, 33, 354, 52, 10, 32,
           51, 45, 40, 34, 8, 38, 41, 43, 58, 345, 9, 342, 339, 25,
           344, 338, 347, 24, 343, 11, 356, 35, 46, 36, 346, 0, 44]
SOURCES = {
    "experiments/workspace/root_prism_free_f0_local_neighbors.py":
        "cf3f4e250ce9c33bbc3c1c0714f0188de012d0d4d36ae32d427d15771349a6e9",
    "experiments/workspace/root_prism_free_f0_local_neighbors_batch.py":
        "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278",
    "experiments/workspace/root_prism_free_f0_local_neighbors_control_continuation.py":
        "fa2568be85c35da9b2ce7db6db3a4d04a4750167eedbb59526cbe5a0bda431ba",
}
ANCHORS = {
    "f0-local41-preparation01/progress.json":
        "6ee765f55f4c4741a1683cc82404bd6d7fd059767720a3af69e7f498ba88f04c",
    "f0-local41-preparation02/preparation.json":
        "2213372cd8615df2c177c08d7dfd034812eeb385a75266ada1403d331d765976",
    "f0-local41-batch01-preparation-failure.json":
        "2ac53294b1a05cd81755bcf427b77da8a5d5f8d3423613a849d03a925e03966d",
    "f0-local41-batch02-preparation.json":
        "57bf84bdf102444aad209bf9c7fd5e62c1fc4f7bf584fa3fac8d0b75e71627ae",
    "f0-local41-batch01/result.json":
        "e71590c6b6786cec61b79b35ba70e5fc858b2c8706ca037e84f9034a9981c264",
    "f0-local41-batch01-replay/result.json":
        "4d880e00aeb3a947ba12d814a30f88bd8469cae67798793dfa82f6294bb9de91",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def expected_paths():
    names = {
        "f0-local41-preparation01/progress.json",
        "f0-local41-preparation01.log",
        "f0-local41-preparation02/preparation.json",
        "f0-local41-preparation02/progress.json",
        "f0-local41-preparation02.log",
        "f0-local41-batch01-preparation-failure.json",
        "f0-local41-batch01-preparation.log",
        "f0-local41-batch02-preparation.json",
        "f0-local41-batch02-preparation.log",
        "f0-local41-batch02-controls/status.json",
        "f0-local41-batch01/result.json",
        "f0-local41-batch01.log",
        "f0-local41-batch01-replay/result.json",
        "f0-local41-batch01-replay.log",
    }
    for center in CENTERS:
        for name in ("instance.json", "model.json", "model.cnf"):
            names.add(f"f0-local41-preparation02/center-{center}/{name}")
        for name in ("supervisor.json", "child-result.json", "assignment.json",
                     "child.stdout.log", "child.stderr.log"):
            names.add(f"f0-local41-batch01/center-{center}/{name}")
    for run, children in (("01", ("exit0", "exit3")),
                          ("02", ("exit3", "deadline"))):
        for child in children:
            for name in ("supervisor.json", "child.stdout.log", "child.stderr.log"):
                names.add(f"f0-local41-batch{run}-controls/{child}/{name}")
    assert len(names) == 354
    return {PREFIX + name for name in names}


def validate(record):
    assert record["schema"] == "conway99.f0-local41-lossless-archive.v1"
    assert record["archive_source_sha256"] == sha(Path(__file__).read_bytes())
    assert record["source_bindings"] == SOURCES
    assert set(record["files"]) == expected_paths()
    decoded = {}
    for name, item in record["files"].items():
        p = PurePosixPath(name)
        assert not p.is_absolute() and ".." not in p.parts
        assert str(p) == name and name.startswith(PREFIX)
        raw = item["text"].encode("utf-8")
        assert len(raw) == item["bytes"] and sha(raw) == item["sha256"]
        decoded[name] = raw
    for name, digest in ANCHORS.items():
        assert sha(decoded[PREFIX + name]) == digest
    get = lambda name: json.loads(decoded[PREFIX + name])
    prep = get("f0-local41-preparation02/preparation.json")
    run = get("f0-local41-batch01/result.json")
    replay = get("f0-local41-batch01-replay/result.json")
    assert prep["centers"] == run["centers"] == CENTERS
    assert run["attempted_centers"] == run["SAT_centers"] == CENTERS
    assert run["unqueried_centers"] == run["unverified_UNSAT_centers"] == []
    assert run["selector_zeros_claimed"] == []
    assert not run["graph_completion_claimed"]
    assert len(run["records"]) == len(replay["records"]) == 41
    assert replay["status"] == "PASS_COMPLETE_MODEL_AND_AVAILABLE_CERTIFICATE_REPLAY"
    assert replay["production_solver_calls"] == 0
    for center, observed, checked in zip(CENTERS, run["records"], replay["records"]):
        assert observed["center"] == checked["center"] == center
        assert observed["status"] == "SAT_EXACT_LOCAL_WITNESS"
        assert observed["production_solve_calls"] == 1
        assert checked["status"] == "PASS_EXACT_SAT_REPLAY"
        assert observed["witness"] == checked["witness"]
        md = get(f"f0-local41-preparation02/center-{center}/model.json")
        cnf = decoded[PREFIX + f"f0-local41-preparation02/center-{center}/model.cnf"]
        assert sha(cnf) == md["cnf_sha256"] == checked["cnf_sha256"]
        assert len(cnf) == md["cnf_bytes"]
        base = PREFIX + f"f0-local41-batch01/center-{center}/"
        assert sha(decoded[base + "assignment.json"]) == observed["assignment_sha256"]
        assert sha(decoded[base + "child-result.json"]) == observed["child_result_sha256"]
    assert record["raw_file_bytes"] == sum(map(len, decoded.values()))
    return decoded


def read_archive(path):
    raw = path.read_bytes()
    record = json.loads(gzip.decompress(raw))
    return raw, record, validate(record)


def report_for(raw, record, decoded):
    inventory = [{"path": name, "bytes": len(data), "sha256": sha(data)}
                 for name, data in sorted(decoded.items())]
    return {
        "status": "PASS: complete exact-byte local batch archive",
        "archive_sha256": sha(raw),
        "archive_bytes": len(raw),
        "archive_source_sha256": record["archive_source_sha256"],
        "files": len(decoded),
        "raw_file_bytes": sum(map(len, decoded.values())),
        "file_inventory": inventory,
        "new_centers": 41,
        "SAT_witnesses": 41,
        "model_rebuilds": 0,
        "solver_calls": 0,
        "scope": "Archive binding only; native mathematical replay is separately frozen.",
    }


def pack(root, output):
    assert not output.exists()
    for name, digest in SOURCES.items():
        assert sha((root / name).read_bytes()) == digest
    record = {
        "schema": "conway99.f0-local41-lossless-archive.v1",
        "archive_source_sha256": sha(Path(__file__).read_bytes()),
        "source_bindings": SOURCES,
        "files": {},
    }
    for name in sorted(expected_paths()):
        path = root / name
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        record["files"][name] = {
            "bytes": len(raw), "sha256": sha(raw), "text": raw.decode("utf-8")}
    record["raw_file_bytes"] = sum(x["bytes"] for x in record["files"].values())
    validate(record)
    raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    compressed = gzip.compress(raw, mtime=0)
    assert gzip.decompress(compressed) == raw
    with output.open("xb") as f:
        f.write(compressed)
    saved, again, decoded = read_archive(output)
    return report_for(saved, again, decoded)


def restore(archive, root, verify_only):
    raw, record, decoded = read_archive(archive)
    root = root.resolve()
    # Preflight every path before creating any file. Existing files must match.
    present, missing = [], []
    for name, data in decoded.items():
        path = root / name
        assert path.resolve().is_relative_to(root)
        assert not any(p.is_symlink() for p in [path, *path.parents] if p != root)
        if path.exists():
            assert path.is_file() and path.read_bytes() == data
            present.append(name)
        else:
            missing.append(name)
    if verify_only:
        assert not missing
    else:
        for name in missing:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as f:
                f.write(decoded[name])
            assert path.read_bytes() == decoded[name]
    result = report_for(raw, record, decoded)
    result.update({"status": "PASS: all archive bytes verified" if verify_only
                   else "PASS: archive restored without replacing existing files",
                   "root": str(root), "existing_equal_files": len(present),
                   "newly_restored_files": 0 if verify_only else len(missing),
                   "existing_files_overwritten": 0})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("pack", "restore", "verify"))
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists()
    result = (pack(a.root, a.archive) if a.mode == "pack"
              else restore(a.archive, a.root, a.mode == "verify"))
    with a.report.open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "file_inventory"}, indent=2))


if __name__ == "__main__":
    main()

