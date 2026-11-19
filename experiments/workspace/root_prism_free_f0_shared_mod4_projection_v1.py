"""Bounded full-domain Z/4 compatibility projection, with complete witnesses.

All 480 degree and 8640 mixed rows are included on all 68394 eligible edges.
No selector incidence is fixed and no activation or edge bound is imposed.
Every zero-edge obligation and every surviving even rank witness is saved.
The finite main calculation requires a prior source and preparation gate.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = "experiments/workspace/"
LOGS = "experiments/logs/root-prism-free/"
FIXED_SOURCES = {
    "core": (WORK + "root_prism_free_f0_mod4_linear_v1.py", "5e36e6cede9d9a926a016abd9fd5ed2793df264ae6a9e9d1a40b9e76f0786758"),
    "domain": (WORK + "root_prism_free_f0_shared_mod2_projection.py", "a548fe26b54a559909bece50df984e0755d9321adc7e8a41d0b6e836c8b34fd5"),
    "gram": (WORK + "root_prism_free_f0_direct_literal_model.py", "b500336db29820777afb59076384a48382fa54453fce5b232a072719893cea40"),
    "supervisor": (WORK + "rook_case4_box_hull_membership_query.py", "aa557c7b99ec3de71e9ecde3f6f7dfa3ca71066a835086cdd3b3f2eb7be558e5"),
    "supervisor_helper": (WORK + "rook_case4_box_hull_membership.py", "54330f430c0c4dae03a0298533121ce43482ceb295f54df715ad2f2180d3503c"),
}
INPUTS = {
    "domain": (LOGS + "f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4"),
    "core_controls": (LOGS + "f0-shared-mod4-core-controls01.json", "fad19e1700113ced52c5d8e47b9a698d88201328432ca2eb163bce3f9cf9d932"),
    "mod2_rank": (LOGS + "f0-shared-mod2-projection01/report.json", "e794dfc28b83296833d158e0732e9b786f430f7c682f294d171a74dc2cb7eebc"),
    "rational_kernel_cold": (LOGS + "f0-shared-rational-kernel01-cold.json", "45d90993f1c78af166d2db8e886754a883592f492ee9bea92cead2790b6b7e3a"),
}
LIMITS = {"preparation_seconds": 30, "preparation_owner_seconds": 45,
          "main_seconds": 120, "main_owner_seconds": 135,
          "cold_seconds": 120, "cold_owner_seconds": 135,
          "maximum_raw_certificate_bytes": 134217728}
DIMENSIONS = {"selectors": 480, "sites": 18, "edges": 68394,
              "degree_rows": 480, "mixed_rows": 8640, "gram_rows": 172}
COLD_PATH = WORK + "root_prism_free_f0_shared_mod4_projection_cold_v1.py"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}


def binding(pair):
    return {"path": pair[0], "sha256": pair[1]}


def read(ref):
    path = ROOT / ref["path"]
    raw = path.read_bytes()
    assert sha(raw) == ref["sha256"]
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def write(path, value):
    raw = canonical(value) + b"\n"
    if path.suffix == ".gz":
        assert len(raw) <= LIMITS["maximum_raw_certificate_bytes"]
        stored = gzip.compress(raw, compresslevel=6, mtime=0)
    else:
        stored = raw
    with path.open("xb") as stream:
        stream.write(stored)
    return reference(path)


def definition():
    sources = {name: binding(pair) for name, pair in FIXED_SOURCES.items()}
    sources["producer"] = reference(Path(__file__).resolve())
    sources["cold"] = reference(ROOT / COLD_PATH)
    return {"schema": "conway99.f0.shared-mod4-configuration.v1", "sources": sources,
            "inputs": {name: binding(pair) for name, pair in INPUTS.items()},
            "dimensions": DIMENSIONS, "limits": LIMITS,
            "all_original_rows": 9120, "selector_constant_coordinate": 480,
            "row_order": "19*a: degree; 19*a+1+i: mixed site i",
            "main_requires_root_source_and_preparation_gate": True,
            "all_obligations_including_zero_rhs_retained": True,
            "even_rank_witnesses_retained": True, "native_optimizer_authorized": False,
            "whole_component_exclusion_or_integer_feasibility_claimed": False}


def load(configuration):
    config = json.loads(configuration.read_bytes())
    assert config == definition()
    for group in (config["sources"], config["inputs"]):
        for ref in group.values():
            assert reference(ROOT / ref["path"]) == ref
    return config


def module(ref, name):
    path = ROOT / ref["path"]
    assert reference(path) == ref
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def inventory(triples, targets, edges, gram):
    present = [set() for _ in triples]
    degree = [0] * len(triples)
    for a, b in edges:
        present[a].update(triples[b]); present[b].update(triples[a])
        degree[a] += 1; degree[b] += 1
    hashes = {name: sha(canonical(value)) for name, value in (("triples", triples), ("targets", targets), ("edges", edges), ("gram", gram))}
    result = dict(DIMENSIONS, original_rows=9120, nonempty_degree_rows=sum(d > 0 for d in degree),
                  nonempty_mixed_rows=sum(map(len, present)), original_unit_entries=8 * len(edges), domain_hashes=hashes)
    assert result["nonempty_degree_rows"] == 480 and result["nonempty_mixed_rows"] == 7884
    return result


def context(config):
    core = module(config["sources"]["core"], "mod4_frozen_core")
    domain = module(config["sources"]["domain"], "mod4_frozen_domain")
    triples, targets, edges, gram = domain.load_domain()
    return core, triples, targets, edges, gram, inventory(triples, targets, edges, gram)


def pack(value):
    return {"low_hex": format(value[0], "x"), "high_hex": format(value[1], "x")}


def validate_preparation(configuration, directory, expected_inventory):
    report_ref = reference(directory / "report.json")
    report = read(report_ref)
    owner = json.loads((directory / "owner.json").read_bytes())
    assert owner["report_accepted"] and owner["report"] == report_ref
    assert owner["mode"] == "prepare" and owner["configuration"] == reference(configuration)
    assert owner["source_sha256"] == sha(Path(__file__).read_bytes())
    assert owner["supervision"]["child_reaped"] and not owner["supervision"]["hard_timeout"] and owner["supervision"]["exit_code"] == 0
    assert report["status"] == "PASS_MOD4_SOURCE_BINDINGS_DOMAIN_AND_SMALL_CONTROLS"
    assert report["configuration"] == reference(configuration) and report["inventory"] == expected_inventory
    assert not report["full_domain_elimination_started"]
    return report_ref


def worker(mode, configuration, directory, preparation):
    started = time.monotonic()
    config = load(configuration)
    seconds = LIMITS["preparation_seconds" if mode == "prepare" else "main_seconds"]
    def check():
        if time.monotonic() - started >= seconds:
            raise TimeoutError("bounded mod4 phase cooperative deadline")
    core, triples, targets, edges, gram, inv = context(config)
    result = {"configuration": reference(configuration), "source": config["sources"]["producer"],
              "inventory": inv, "optimizer_calls": 0, "native_imports": 0,
              "whole_component_excluded": False, "integer_or_all_prime_feasibility_claimed": False,
              "all_edges_present_without_activation_bounds": True}
    if mode == "prepare":
        controls = read(config["inputs"]["core_controls"])
        assert controls["status"] == "PASS_EXHAUSTIVE_SMALL_MOD4_ARITHMETIC_MODULE_AND_KERNEL_CONTROLS"
        assert controls["source"] == config["sources"]["core"] and controls["all_two_by_two_matrices"] == 256
        assert controls["complete_annihilator_generations_checked"] == 256 and controls["optimizer_calls"] == 0
        old = read(config["inputs"]["mod2_rank"])
        assert old["status"] == "COMPLETE_EXACT_MOD2_SHARED_PROJECTION" and old["edge_pivots_found"] == 7713 and old["processed_rows"] == 8640
        cold = module(config["sources"]["cold"], "mod4_independent_cold_controls")
        independent = cold.controls()
        independent_ref = write(directory / "independent-small-controls.json", independent)
        result.update(status="PASS_MOD4_SOURCE_BINDINGS_DOMAIN_AND_SMALL_CONTROLS",
                      accepted_core_controls=config["inputs"]["core_controls"], independent_small_controls=independent_ref,
                      full_domain_elimination_started=False, expected_unit_rank_from_accepted_mod2=7713,
                      maximum_obligations=1407, logical_two_plane_bytes_per_row=2*((68394+7)//8+(9120+7)//8+(481+7)//8),
                      logical_size_is_not_an_RSS_limit=True)
    else:
        result["preparation"] = validate_preparation(configuration, preparation, inv)
        row_masks = [0] * 9120
        for e, (a, b) in enumerate(edges):
            if e % 4096 == 0:
                check()
            bit = 1 << e
            row_masks[19*a] |= bit; row_masks[19*b] |= bit
            for i in triples[b]:
                row_masks[19*a+1+i] |= bit
            for i in triples[a]:
                row_masks[19*b+1+i] |= bit
        for a in range(480):
            parity = 0
            for i in range(18):
                parity ^= row_masks[19*a+1+i]
            assert parity == row_masks[19*a]
        rows = []
        for r, mask in enumerate(row_masks):
            a, offset = divmod(r, 19)
            target = 8 if offset == 0 else targets[a][offset-1]
            rows.append(((mask, 0), (1 << r, 0), core.encode([(a, target)])))
        del row_masks
        gram_rows = [(core.encode([(a, 1) for a in item["support"]] + [(480, -item["rhs"])]), (1 << r, 0), core.ZERO) for r, item in enumerate(gram)]
        gram_basis = core.decompose(gram_rows, check)
        write(directory / "inventory.json", dict(inv, stage="before_complete_mod4_elimination"))
        basis = core.decompose(rows, check)
        assert len(basis["units"]) == 7713
        assert len(basis["units"]) + len(basis["even"]) <= 7731
        obligations, nonzero, new = [], 0, 0
        for index, (kind, row) in enumerate(basis["generators"]):
            check()
            assert row[0] == core.ZERO
            remainder, gram_witness = core.reduce_vector(row[2], gram_basis)
            nonzero += int(row[2] != core.ZERO); new += int(remainder != core.ZERO)
            obligations.append({"index": index, "kind": kind, "original_row_multipliers": pack(row[1]),
                "selector_rhs": pack(row[2]), "gram_row_multipliers": pack(gram_witness), "remainder": pack(remainder),
                "nonzero_selector_congruence": row[2] != core.ZERO, "implied_by_original_gram": remainder == core.ZERO})
        even_witnesses = []
        for pivot in sorted(basis["even"]):
            row = basis["even"][pivot]
            assert row[0][0] == 0 and row[0][1] and not (row[0][1] & basis["unit_mask"])
            even_witnesses.append({"pivot": pivot, "edge_half_hex": format(row[0][1], "x"),
                "original_row_multipliers": pack(row[1]), "selector_rhs": pack(row[2])})
        certificate = {"configuration": reference(configuration), "domain_hashes": inv["domain_hashes"],
            "unit_pivots": sorted(basis["units"]), "even_rank_witnesses": even_witnesses,
            "obligations": obligations, "all_original_rows_processed": 9120,
            "zero_residuals_and_doubled_even_rows_form_complete_left_kernel_generating_set": True,
            "no_independence_claim_for_kernel_generating_set": True}
        certificate_ref = write(directory / "certificates.json.gz", certificate)
        result.update(status="COMPLETE_EXACT_MOD4_SHARED_PROJECTION_AWAITING_INDEPENDENT_COLD",
            full_domain_elimination_started=True, original_rows_processed=9120,
            unit_rank=len(basis["units"]), even_rank=len(basis["even"]),
            gram_unit_rank=len(gram_basis["units"]), gram_even_rank=len(gram_basis["even"]),
            zero_residual_count=len(basis["zero"]), obligations=len(obligations),
            nonzero_selector_congruences=nonzero, not_implied_by_original_gram=new,
            unit_operations=basis["unit_operations"], unit_cleanup_operations=basis["unit_cleanup_operations"],
            even_operations=basis["even_operations"], certificates=certificate_ref,
            all_obligations_retained=True, independent_cold_required=True,
            higher_two_power_torsion_conclusion_claimed=False)
    check()
    assert not any(name.split(".")[0] in {"ortools", "highspy", "numpy", "scipy"} for name in sys.modules)
    result.update(seconds=time.monotonic()-started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(directory / "report.json", result)
    return result


def owned(mode, configuration, directory, preparation, run_directory):
    config = load(configuration)
    directory.mkdir(parents=True, exist_ok=False)
    if mode == "cold":
        command = [sys.executable, str(ROOT / COLD_PATH), "--configuration", str(configuration),
                   "--run-directory", str(run_directory), "--output", str(directory / "report.json")]
        limit = LIMITS["cold_owner_seconds"]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
                   "--configuration", str(configuration), "--directory", str(directory)]
        if preparation is not None:
            command += ["--preparation", str(preparation)]
        limit = LIMITS["preparation_owner_seconds" if mode == "prepare" else "main_owner_seconds"]
    sys.path.insert(0, str(ROOT / WORK))
    supervisor = module(config["sources"]["supervisor"], "mod4_reused_supervisor")
    stage = supervisor.owned(command, directory, limit, mode, new_group=True)
    record = {"mode": mode, "configuration": reference(configuration), "source_sha256": config["sources"]["producer"]["sha256"],
              "supervision": stage, "report_accepted": False, "optimizer_calls": 0, "automatic_retries": 0}
    expected = {"prepare": "PASS_MOD4_SOURCE_BINDINGS_DOMAIN_AND_SMALL_CONTROLS",
                "run": "COMPLETE_EXACT_MOD4_SHARED_PROJECTION_AWAITING_INDEPENDENT_COLD",
                "cold": "PASS_INDEPENDENT_ALL_MOD4_OBLIGATIONS_AND_GRAM_MEMBERSHIP"}[mode]
    if supervisor.success(stage) and (directory / "report.json").exists():
        result = json.loads((directory / "report.json").read_bytes())
        assert result["configuration"] == reference(configuration)
        assert result["seconds"] < LIMITS[{"prepare": "preparation_seconds", "run": "main_seconds", "cold": "cold_seconds"}[mode]]
        record.update(report=reference(directory / "report.json"), report_accepted=result["status"] == expected)
    record["status"] = "OWNED_MOD4_PHASE_ACCEPTED" if record["report_accepted"] else "UNKNOWN_MOD4_PHASE_FAILURE"
    write(directory / "owner.json", record)
    return record


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("configuration", "prepare", "run", "cold", "_prepare", "_run"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--run-directory", type=Path)
    args = parser.parse_args()
    configuration = args.configuration.resolve()
    if args.mode == "configuration":
        result = write(configuration, definition())
    elif args.mode.startswith("_"):
        try:
            result = worker(args.mode[1:], configuration, args.directory.resolve(), args.preparation.resolve() if args.preparation else None)
        except Exception as error:
            write(args.directory.resolve() / "error.json", {"type": type(error).__name__, "message": str(error), "complete_result_accepted": False})
            raise
    else:
        assert args.directory is not None
        assert args.mode != "run" or args.preparation is not None
        assert args.mode != "cold" or args.run_directory is not None
        result = owned(args.mode, configuration, args.directory.resolve(), args.preparation.resolve() if args.preparation else None,
                       args.run_directory.resolve() if args.run_directory else None)
    print(json.dumps({"status": result.get("status"), "artifact": result.get("path"), "report_accepted": result.get("report_accepted")}), flush=True)
