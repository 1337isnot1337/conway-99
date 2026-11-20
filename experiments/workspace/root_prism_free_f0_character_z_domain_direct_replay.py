"""Direct independent archive/domain check after the preserved cold timeout.

Only standard-library operations and generated protobuf parsing are used.
No subject builder, native CpModel, solver, clique search or row census is
imported or run. The successful old cold and Z native preparation are bound.
"""
import argparse
import gc
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
OWNER = ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278")
SUBJECT = ("root_prism_free_f0_character_z_domain_overlay.py", "723841fafdfc151ef68e5b3877479361d38b84a06b86b83d9a7f69e0aed3460d")
INPUTS = {
    "parent_plan": ("f0-character-pool-model01/plan.json.gz", "b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef"),
    "parent_cold": ("f0-character-pool-model01-cold.json", "24a450d6d6c3bf537e6c049aaad2bf843e154a0586e463a2fc14eaff48eac2c8"),
    "new_plan": ("f0-character-z-domain-overlay01/plan.json.gz", "99a312d9a2694431adc30d5cbe8f7f344ea91e6f9ebe8fc997ba8e6d0df52ddf"),
    "native_preparation": ("f0-character-z-domain-overlay01/report.json", "944cb8f1fdafd1e26260d3def404ffd7afde43e2fe93e97a6a258cc9bcbda6bd"),
    "native_owner": ("f0-character-z-domain-overlay01/owner-result.json", "e725486810c047656929d84b8f201fd421b310af80444d643464600fbed7b7d9"),
    "failed_cold": ("f0-character-z-domain-overlay01-cold/owner-result.json", "b3e18a04586a4bdb2616a73ccf70256c0d4b9eaf1fc7f39a3e7ef436cc4beeef"),
    "target_archive": ("f0-character-z-domain-overlay01/target.pb.gz", "6ed622ba17fe8ee02fd8aff5fbf0192909719da298775e898c01465dfbb910b4"),
    "initial_archive": ("f0-character-z-domain-overlay01/initial.pb.gz", "9a7948ae71c545115917d426856a134df3ab466ee1c1dc6c8656e0e449a39332"),
    "packing_preparation": ("f0-pair-orbit-packing-preparation01.json.gz", "09412183bb01527a6fa2aeb23623b95af925767d5067bb363f10a2a8f8254a13"),
    "packing_result": ("f0-pair-orbit-packing-scan01.json.gz", "1bbba3061689f8faaf8fadcf556c0097d2b190673ab063a675259c007508b2bb"),
    "packing_cold": ("f0-pair-orbit-packing-scan01-cold.json", "c684243851efa7e12e9b9e5c7f857532421c1954233a5d9d6e24acfe5c826843"),
    "packing_ledger": ("f0-pair-orbit-packing-scan01-ledger.jsonl.gz", "4c53542bc89575b799b9e3d8b5905ae3dfe9782aa954db9d9afdf2a07c83d839"),
}
PROTO_SHA = {"target": ("7deafd3d162f505873eaa2dfc2b532294ac99b058b54b84ba7cce73444016df1",
                        "0612fd82507ac454209ba5f376654248461fc8c0506b9a4a382f5e628487d9ae", 34398),
             "initial": ("3337449ad74d102ba772d3d07472bf95ef378ba722118aa31be255e1c261e395",
                         "36bd4fe3650ede346bab0885abcb9cef7a96cb0e150dffc8fcf51bbe695e7d4d", 34281)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def memory():
    found = {"getrusage_peak_rss_KiB": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            found[line.split(":")[0] + "_KiB"] = int(line.split()[1])
    return found


def bindings():
    for name, expected in (OWNER, SUBJECT):
        assert file_sha(ROOT / "experiments/workspace" / name) == expected
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def literal_domain(domain):
    assert domain and len(domain) % 2 == 0 and all(type(x) is int for x in domain)
    assert 0 <= domain[0] <= domain[-1] <= 12
    assert all(domain[i] <= domain[i + 1] for i in range(0, len(domain), 2))
    assert all(domain[i] + 1 < domain[i + 1] for i in range(1, len(domain) - 1, 2))
    return [v for lo, hi in zip(domain[::2], domain[1::2]) for v in range(lo, hi + 1)]


def intervals(values):
    assert values == sorted(set(values)) and values
    result = []
    for value in values:
        if result and result[-1] + 1 == value:
            result[-1] = value
        else:
            result.extend((value, value))
    return result


def worker(directory, deadline):
    started, stages = time.monotonic(), []
    def stage(label):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started, "memory": memory()})
        save(directory / "stages.json", {"stages": stages})
        if time.monotonic() > deadline:
            raise TimeoutError("direct domain/archive deadline")
    stage("started")
    bindings()
    parent, new, native, owner, failed, packing, cold, preparation = [read(k) for k in (
        "parent_plan", "new_plan", "native_preparation", "native_owner", "failed_cold",
        "packing_result", "packing_cold", "packing_preparation")]
    assert read("parent_cold")["status"].startswith("PASS")
    assert native["status"].startswith("PASS") and native["definition"]["source_sha256"] == SUBJECT[1]
    assert owner["report_accepted"] and owner["report_sha256"] == INPUTS["native_preparation"][1]
    assert failed["status"] == "UNKNOWN_HARD_DEADLINE" and not failed["report_accepted"]
    assert cold["status"].startswith("PASS") and cold["checked_orbits"] == 9353
    assert cold["record_sha256"] == INPUTS["packing_result"][1]
    assert cold["preparation_sha256"] == packing["preparation_sha256"] == INPUTS["packing_preparation"][1]
    assert packing["complete"] and packing["summary"]["completed_orbits"] == 9353
    assert packing["inputs"]["current_plan"] == list(INPUTS["parent_plan"])
    assert packing["ledger_sha256"] == INPUTS["packing_ledger"][1]
    assert new["source_sha256"] == SUBJECT[1]
    assert {k: v for k, v in new.items() if k not in ("source_sha256", "target_variable_domains", "Z_domain_overlay")} == {
        k: v for k, v in parent.items() if k not in ("source_sha256", "target_variable_domains")}
    old_domains, new_domains = parent["target_variable_domains"], new["target_variable_domains"]
    assert len(old_domains) == len(new_domains) == 18444
    appendix, scope = new["Z_domain_overlay"], preparation["scope"]["retained_orbits"]
    assert len(scope) == len(appendix["complete_intersections"]) == 9353
    assert appendix["parent_plan"] == list(INPUTS["parent_plan"])
    assert appendix["parent_source_sha256"] == parent["source_sha256"]
    assert appendix["packing_result_sha256"] == INPUTS["packing_result"][1]
    assert appendix["packing_cold_sha256"] == INPUTS["packing_cold"][1]
    stage("all_frozen_bindings_and_complete_non_domain_plan_fields_checked")
    digest, size, changed, improvements = hashlib.sha256(), 0, [], []
    with gzip.open(LOGS / INPUTS["packing_ledger"][0], "rb") as stream:
        for i, col in enumerate(range(5685, 15038)):
            line = next(stream); digest.update(line); size += len(line)
            record = json.loads(line)
            old, actual, saved = old_domains[col], new_domains[col], scope[i]
            assert record["count_column"] == saved["count_column"] == col
            assert record["pair_orbit"] == saved["pair_orbit"]
            assert saved["current_domain"] == old and record["previous_current_upper_bound"] == old[-1]
            upper = record["maximum_compatible_pair_objects"]
            assert type(upper) is int and 1 <= upper <= saved["orbit_size_upper_bound"] <= 12
            expected = intervals([v for v in literal_domain(old) if v <= upper])
            assert actual == expected and literal_domain(actual)[0] == 0
            assert appendix["complete_intersections"][i] == {
                "ledger_index": i, "ledger_record_sha256": sha(line), "pair_orbit": saved["pair_orbit"],
                "count_column": col, "certified_upper": upper, "old_domain": old, "new_domain": expected}
            assert record["improves_current_upper_bound"] == (actual != old)
            if actual != old:
                changed.append(col)
                improvements.append({"pair_orbit": saved["pair_orbit"], "count_column": col,
                                     "old_upper": old[-1], "new_upper": upper})
            if (i + 1) % 1000 == 0:
                stage("certified_domain_prefix_" + str(i + 1))
        assert not stream.read(1)
    assert digest.hexdigest() == packing["ledger_raw_sha256"] and size == packing["ledger_raw_bytes"]
    assert improvements == packing["summary"]["improved_current_bounds"]
    assert len(changed) == 8251 and changed == appendix["changed_columns"]
    assert [j for j in range(18444) if old_domains[j] != new_domains[j]] == changed
    assert appendix["unchanged_columns"] == [j for j in range(18444) if old_domains[j] == new_domains[j]]
    assert appendix["non_Z_columns_unchanged"] == 9091 and appendix["retained_Z_domains_unchanged"] == 1102
    stage("every9353_Z_and9091_other_domain_checked")
    del preparation, scope, packing, appendix, improvements
    gc.collect()
    from ortools.sat import cp_model_pb2
    proto_results = {}
    for name, (new_sha, old_sha, count) in PROTO_SHA.items():
        path, expected = INPUTS[name + "_archive"]
        raw = gzip.decompress((LOGS / path).read_bytes())
        assert sha(raw) == new_sha
        assert native["outputs"][name]["sha256"] == expected
        assert native["outputs"][name]["raw_sha256"] == new_sha
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        del raw
        assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
        assert len(proto.variables) == 18444 and len(proto.constraints) == count
        assert [list(v.domain) for v in proto.variables] == new_domains
        for j in changed:
            proto.variables[j].domain[:] = old_domains[j]
        assert sha(proto.SerializeToString()) == old_sha
        proto_results[name] = {"new_raw_proto_sha256": new_sha, "restored_old_raw_proto_sha256": old_sha,
                               "all_constraints_and_non_domain_variable_fields_unchanged": True}
        del proto
        gc.collect()
        stage(name + "_domains_checked_and_old_entire_proto_hash_restored")
    report = {"status": "PASS: independent direct Z-domain and full protobuf restoration replay",
              "source_sha256": file_sha(Path(__file__)), "subject_source_sha256": SUBJECT[1],
              "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
              "all_retained_Z_orbits_checked": 9353, "changed_Z_domains": 8251,
              "unchanged_Z_domains": 1102, "unchanged_non_Z_domains": 9091,
              "complete_non_domain_plan_equality": True, "protobuf_restorations": proto_results,
              "failed_cold_unchanged": "UNKNOWN_HARD_DEADLINE",
              "native_model_construction_or_validation_repeated": False,
              "old_literal_clique_certificates_replayed_here": False,
              "native_preparation_and_complete_clique_cold_bound": True,
              "subject_modules_imported": False, "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_feasibility_claimed": False, "seconds": time.monotonic() - started,
              "terminal_memory": memory(), "stages_sha256": file_sha(directory / "stages.json")}
    save(directory / "report.json", report)


def owned(directory):
    started = time.monotonic(); deadline = started + 60
    bindings()
    path = ROOT / "experiments/workspace" / OWNER[0]
    spec = importlib.util.spec_from_file_location("frozen_direct_domain_owner", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    directory.mkdir(parents=True, exist_ok=False)
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--directory", str(directory.resolve()),
               "--deadline", str(deadline)]
    supervision = module.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision, "maximum_owned_seconds": 60,
              "source_sha256": file_sha(Path(__file__)), "report_accepted": False, "optimizer_calls": 0}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((directory / "report.json").read_bytes())
        assert report["status"].startswith("PASS")
        result.update(status=report["status"], report_accepted=True, report_sha256=file_sha(directory / "report.json"))
    result.update(owner_seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("replay", "_worker"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "replay":
        owned(args.directory)
    else:
        assert args.deadline is not None
        worker(args.directory, args.deadline)
