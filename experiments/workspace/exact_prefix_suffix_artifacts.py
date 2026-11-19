"""Store and restore exact bulk files from a bound base prefix and suffix.

Packing never changes a source target. Restoration checks every byte/hash
binding before creating a target, and never overwrites an existing file.
Gzip targets also bind their decompressed contents when requested.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile

if not __debug__:
    raise RuntimeError("exact artifact validation requires assertions")

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "conway99.exact-prefix-suffix-artifacts.v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def info(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def path_in(root, name):
    assert type(name) is str and "\\" not in name
    relative = PurePosixPath(name)
    assert not relative.is_absolute() and relative.parts and ".." not in relative.parts
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    return path


def check(data, binding):
    assert type(binding["bytes"]) is int and binding["bytes"] >= 0
    assert info(data) == {"bytes": binding["bytes"], "sha256": binding["sha256"]}


def base_data(root, binding):
    encoded = path_in(root, binding["path"]).read_bytes()
    check(encoded, binding)
    assert binding["codec"] in ("identity", "gzip")
    data = gzip.decompress(encoded) if binding["codec"] == "gzip" else encoded
    check(data, binding["decoded"])
    return data


def pack(specification, manifest_path, root=ROOT):
    """Each spec has base_path, base_codec, target_path and suffix_path."""
    assert not manifest_path.exists()
    entries = []
    assert len({item["target_path"] for item in specification}) == len(specification)
    assert len({item["suffix_path"] for item in specification}) == len(specification)
    assert all(not path_in(root, item["suffix_path"]).exists() for item in specification)
    assert all(manifest_path.resolve() != path_in(root, item[k]) for item in specification
               for k in ("base_path", "target_path", "suffix_path"))
    for item in specification:
        base_path, target_path, suffix_path = [path_in(root, item[k]) for k in ("base_path", "target_path", "suffix_path")]
        assert len({base_path, target_path, suffix_path}) == 3
        encoded, target = base_path.read_bytes(), target_path.read_bytes()
        assert item["base_codec"] in ("identity", "gzip")
        base = gzip.decompress(encoded) if item["base_codec"] == "gzip" else encoded
        n = 0
        for a, b in zip(base, target):
            if a != b:
                break
            n += 1
        suffix = target[n:]
        assert base[:n] + suffix == target
        target_binding = dict(info(target), path=item["target_path"])
        if item.get("verify_target_gzip", False):
            target_binding["gzip_content"] = info(gzip.decompress(target))
        suffix_path.parent.mkdir(parents=True, exist_ok=True)
        with suffix_path.open("xb") as stream:
            stream.write(suffix)
        entries.append({"base": dict(info(encoded), path=item["base_path"], codec=item["base_codec"], decoded=info(base)),
                        "prefix_bytes": n, "suffix": dict(info(suffix), path=item["suffix_path"]),
                        "target": target_binding})
    manifest = {"schema": SCHEMA, "helper_sha256": info(Path(__file__).read_bytes())["sha256"],
                "entries": entries, "source_targets_modified": False}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("xb") as stream:
        stream.write(canonical(manifest))
    return manifest


def restore(manifest_path, root=ROOT):
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["schema"] == SCHEMA
    assert manifest["helper_sha256"] == info(Path(__file__).read_bytes())["sha256"]
    assert manifest["source_targets_modified"] is False
    assert len({item["target"]["path"] for item in manifest["entries"]}) == len(manifest["entries"])
    results = []
    cache = {}
    for item in manifest["entries"]:
        b = item["base"]
        cache_key = canonical(b)
        if cache_key not in cache:
            cache[cache_key] = base_data(root, b)
        base = cache[cache_key]
        suffix = path_in(root, item["suffix"]["path"]).read_bytes()
        check(suffix, item["suffix"])
        n = item["prefix_bytes"]
        assert type(n) is int and 0 <= n <= len(base)
        data = base[:n] + suffix
        check(data, item["target"])
        if "gzip_content" in item["target"]:
            check(gzip.decompress(data), item["target"]["gzip_content"])
        target = path_in(root, item["target"]["path"])
        assert target not in (path_in(root, b["path"]), path_in(root, item["suffix"]["path"]))
        if target.exists():
            current = target.read_bytes()
            check(current, item["target"])
            assert current == data
            status = "ALREADY_EXACT"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(data)
                try:
                    os.link(temporary, target)
                    status = "CREATED_EXACT"
                except FileExistsError:
                    current = target.read_bytes()
                    check(current, item["target"])
                    assert current == data
                    status = "ALREADY_EXACT"
            finally:
                if temporary is not None:
                    temporary.unlink()
            assert target.read_bytes() == data
        results.append({"path": item["target"]["path"], "status": status, **info(data)})
    return {"status": "PASS_COMPLETE_BYTE_EXACT_RESTORATION", "manifest_sha256": info(manifest_path.read_bytes())["sha256"],
            "files": results, "optimizer_calls": 0, "existing_files_overwritten": False}


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("pack", "restore"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--specification", type=Path)
    args = parser.parse_args()
    if args.mode == "pack":
        assert args.specification is not None
        result = pack(json.loads(args.specification.read_bytes()), args.manifest.resolve())
        print(json.dumps({"status": "PACKED_EXACT_PREFIX_SUFFIX", "files": len(result["entries"]),
                          "manifest": str(args.manifest), "suffix_bytes": sum(e["suffix"]["bytes"] for e in result["entries"])}, sort_keys=True))
    else:
        print(json.dumps(restore(args.manifest.resolve()), sort_keys=True))
