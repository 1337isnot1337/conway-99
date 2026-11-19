"""Frozen complete case4 CNF plus exactly85 proved-zero selector units.

All old439604 clause lines are unchanged. No numerical candidate, basis,
symmetry condition, or auxiliary is introduced. Preparation/cold replay
call no solver. The old full formula is rebuilt and hash-checked first.
"""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import tempfile
import time

import complement_rook_35core_case0004_coordinate_cover_query as old
import rook_case4_transportation_seed as seed

ROOT = Path(__file__).resolve().parents[2]
OLD_SOURCE_SHA = "eb352386f55c5a1fd6ddb9c692ad934d8eef87904c00e86122172dc1ebc1f9d8"
SEED_SOURCE_SHA = "9eedacb4b62db8ad7058e291d04f83141fca306971ed278a58548ead4cd1e8a1"
SEED_PATH = "experiments/logs/grids-and-triangles/rook-case4-transportation-seed-certificate.json"
SEED_SHA = "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"
VARIABLES, OLD_CLAUSES, NEW_CLAUSES = 134852, 439604, 439689
OLD_LITERALS, NEW_LITERALS = 13546364, 13546449
BASE_SHA = "5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2"
BASE_BYTES = 57873863


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save_new(path, value):
    path = Path(path)
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def bindings():
    assert digest(old.__file__) == OLD_SOURCE_SHA
    assert digest(seed.__file__) == SEED_SOURCE_SHA
    answer = old.source_hashes()
    answer[Path(seed.__file__).name] = SEED_SOURCE_SHA
    answer[Path(seed.short.__file__).name] = seed.SHORT_SHA
    answer[Path(__file__).name] = digest(__file__)
    return dict(sorted(answer.items()))


def unit_provenance():
    bindings()
    base = old.checked_model(False)
    raw = (ROOT/SEED_PATH).read_bytes()
    assert sha(raw) == SEED_SHA
    proof = seed.prove(ROOT)
    assert canonical(proof) == canonical(json.loads(raw))
    original = base["formula"]["cover_unit_target_columns"]
    zeros = proof["seed_zero_columns"]
    assert len(original) == 14 and len(zeros) == 99 and set(original) <= set(zeros)
    added = sorted(set(zeros)-set(original))
    assert len(added) == 85
    short = json.loads((ROOT/seed.SHORT_CERT).read_bytes())
    reasons = []
    for a in added:
        reason = proof["seed_reasons"][str(a)]
        assert reason["seed_kind"] == "short_row_combination"
        step = short["steps"][reason["step"]]
        assert a in step["new_zero_columns"] and step["all1214_coefficients"][a] == 1
        reasons.append({"column": a, "DIMACS_unit": [-a-1], "short_proof_step": reason["step"]})
    return {"seed_certificate": SEED_PATH, "seed_sha256": SEED_SHA,
            "short_certificate": seed.SHORT_CERT, "short_sha256": seed.SHORT_CERT_SHA,
            "native_inventory_sha256": proof["primary_inventory_sha256"],
            "old_explicit_zero_columns": original, "all99_zero_columns": zeros,
            "added85_zero_columns": added, "unit_implications": reasons,
            "all_six_signed_row_identities_and_prior_zero_premises_replayed": True,
            "all14_existing_empty_covers_reproved": True, "candidate_or_basis_used": False}


def extend(base_path, target_path, variables, old_count, units):
    """Generic exact suffix writer, also used by the tiny Boolean controls."""
    assert not target_path.exists()
    assert units == sorted(set(units)) and all(0 <= a < variables for a in units)
    old_header = f"p cnf {variables} {old_count}\n".encode()
    header = f"p cnf {variables} {old_count+len(units)}\n".encode()
    base_hash, body_hash, suffix_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    body_bytes = body_lines = 0
    with base_path.open("rb") as source, target_path.open("wb") as target:
        assert source.readline() == old_header
        base_hash.update(old_header); target.write(header)
        for chunk in iter(lambda: source.read(1 << 20), b""):
            base_hash.update(chunk); body_hash.update(chunk)
            body_bytes += len(chunk); body_lines += chunk.count(b"\n")
            target.write(chunk)
        assert body_lines == old_count
        for a in units:
            line = f"{-a-1} 0\n".encode()
            target.write(line); suffix_hash.update(line)
    return {"base_sha256": base_hash.hexdigest(), "base_clause_body_sha256": body_hash.hexdigest(),
            "base_clause_body_bytes": body_bytes, "base_clause_lines": body_lines,
            "unit_suffix_sha256": suffix_hash.hexdigest(), "unit_suffix_lines": len(units),
            "variables": variables, "clauses": old_count+len(units),
            "CNF_sha256": digest(target_path), "CNF_bytes": target_path.stat().st_size}


def audit_stream(path, units):
    """Recover the old full-file hash from the unchanged new prefix."""
    old_header = f"p cnf {VARIABLES} {OLD_CLAUSES}\n".encode()
    old_hash, body_hash, suffix_hash = hashlib.sha256(old_header), hashlib.sha256(), hashlib.sha256()
    literals = largest = body_bytes = 0
    with path.open("rb") as stream:
        assert stream.readline() == f"p cnf {VARIABLES} {NEW_CLAUSES}\n".encode()
        for index in range(OLD_CLAUSES):
            line = stream.readline()
            assert line.endswith(b"\n")
            old_hash.update(line); body_hash.update(line); body_bytes += len(line)
            values = list(map(int, line.split()))
            assert values and values[-1] == 0 and all(values[:-1])
            assert all(abs(v) <= VARIABLES for v in values[:-1])
            literals += len(values)-1
            largest = max(largest, max(map(abs, values[:-1]), default=0))
        for a in units:
            line = stream.readline()
            assert line == f"{-a-1} 0\n".encode()
            suffix_hash.update(line)
        assert stream.read(1) == b""
    assert old_hash.hexdigest() == BASE_SHA
    assert len(old_header)+body_bytes == BASE_BYTES
    assert literals == OLD_LITERALS and largest == VARIABLES
    return {"old_full_CNF_sha256_recovered": BASE_SHA,
            "old_clause_body_sha256": body_hash.hexdigest(), "old_literal_occurrences": literals,
            "unit_suffix_sha256": suffix_hash.hexdigest(), "unit_suffix_clauses": len(units),
            "total_literal_occurrences": literals+len(units), "all_old_clause_bytes_preserved": True,
            "only_certified85_negative_units_appended": True}


def controls():
    assignments = streams = 0
    with tempfile.TemporaryDirectory(prefix="rook99-unit-controls-") as directory:
        directory = Path(directory)
        clauses = [[1, -2], [2, 3], [-3, 4], [-1, -4]]
        base = directory/"base.cnf"
        base.write_text("p cnf 4 4\n"+"".join(" ".join(map(str, c))+" 0\n" for c in clauses))
        for bits in range(16):
            units = [a for a in range(4) if bits >> a & 1]
            output = directory/f"extended{bits}.cnf"
            record = extend(base, output, 4, 4, units)
            parsed = [list(map(int, line.split()))[:-1] for line in output.read_text().splitlines()[1:]]
            assert parsed == clauses+[[-a-1] for a in units]
            assert record["base_sha256"] == digest(base)
            streams += 1
            for values in product((False, True), repeat=4):
                truth = lambda c: any(values[abs(v)-1] == (v > 0) for v in c)
                assert all(map(truth, parsed)) == (all(map(truth, clauses)) and not any(values[a] for a in units))
                assignments += 1
    return {"status": "PASS: exact suffix and complete Boolean unit controls", "streams": streams,
            "assignments": assignments, "solver_or_optimizer_called": False}


def rebuild(cnf, progress=None):
    sources = bindings()
    base = old.checked_model(False)
    proof = unit_provenance()
    with tempfile.TemporaryDirectory(prefix="rook99-old-complete-") as directory:
        prior = Path(directory)/"base.cnf"
        _, ledger, formula = old.overlay.build(prior, progress)
        assert old.normalized(formula) == base["formula"]
        assert old.normalized(ledger) == base["cover_ledger_check"]
        assert digest(prior) == BASE_SHA and prior.stat().st_size == BASE_BYTES
        appended = extend(prior, cnf, VARIABLES, OLD_CLAUSES, proof["added85_zero_columns"])
    assert appended["base_sha256"] == BASE_SHA
    checked = audit_stream(cnf, proof["added85_zero_columns"])
    assert checked["total_literal_occurrences"] == NEW_LITERALS
    assert appended["unit_suffix_sha256"] == checked["unit_suffix_sha256"]
    return {"source_hashes": sources, "old_model_sha256": old.MODEL_SHA, "old_cold_sha256": old.COLD_SHA,
            "case": base["case"], "domain_record_sha256": base["domain_record_sha256"],
            "column_domain_sha256": base["column_domain_sha256"], "Gram_sha256": base["Gram_sha256"],
            "unit_provenance": proof, "formula": appended, "byte_audit": checked,
            "original_primary_columns": 1214, "remaining_primary_columns": 1115,
            "original_Gram_positions": 630, "original_signature_rows": 186,
            "all_triple_capacities": 1365, "Gram_conflicts": 30,
            "uncapped_row_cuts": 60, "complete_coordinate_covers": 178533,
            "new_auxiliary_variables": 0, "all_previous_primary_constraints_retained": True,
            "full_exterior_adjacency_variables": 0, "case_index": 4,
            "only_proved_zero_units_added": True, "candidate_basis_or_symmetry_restriction": False}


def prepare(directory, cnf):
    assert not directory.exists() and not cnf.exists()
    directory.mkdir(parents=True); cnf.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    def progress(phase, values):
        record = {"phase": phase, "values": values, "elapsed_seconds": time.monotonic()-started,
                  "source_hashes": bindings(), "production_solver_calls": 0}
        (directory/"progress.json").write_text(json.dumps(record, indent=2)+"\n")
        print(json.dumps({"phase": phase, "elapsed_seconds": record["elapsed_seconds"]}), flush=True)
    progress("starting_old_formula_reconstruction", {})
    tiny = controls()
    model = rebuild(cnf, progress)
    model.update(status="PASS: unchanged complete case4 CNF plus85 proved units prepared; no query",
                 complete=True, controls=tiny, cnf_path=str(cnf.resolve()),
                 production_solver_calls=0, optimizer_calls=0, elapsed_seconds=time.monotonic()-started)
    save_new(directory/"model.json", model)
    return model


def checked_model(directory, require_cnf=False):
    model = json.loads((directory/"model.json").read_bytes())
    assert model["complete"] and model["source_hashes"] == bindings()
    assert model["old_model_sha256"] == old.MODEL_SHA and model["old_cold_sha256"] == old.COLD_SHA
    assert model["production_solver_calls"] == model["optimizer_calls"] == 0
    assert model["unit_provenance"] == unit_provenance()
    assert model["formula"]["variables"] == VARIABLES and model["formula"]["clauses"] == NEW_CLAUSES
    assert model["byte_audit"]["total_literal_occurrences"] == NEW_LITERALS
    if require_cnf:
        path = Path(model["cnf_path"])
        assert digest(path) == model["formula"]["CNF_sha256"]
        assert path.stat().st_size == model["formula"]["CNF_bytes"]
    return model


def cold(directory, output):
    assert not output.exists()
    started = time.monotonic(); model = checked_model(directory)
    with tempfile.TemporaryDirectory(prefix="rook99-overlay-cold-") as temporary:
        rebuilt = rebuild(Path(temporary)/"full.cnf")
        assert all(model[key] == value for key, value in rebuilt.items())
    report = {"status": "PASS: full original CNF and all85 unit implications cold-replayed",
              "source_hashes": bindings(), "model_sha256": digest(directory/"model.json"),
              "CNF_sha256": model["formula"]["CNF_sha256"], "clauses": NEW_CLAUSES,
              "variables": VARIABLES, "optimizer_or_solver_called": False,
              "elapsed_seconds": time.monotonic()-started}
    save_new(output, report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--cnf", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if a.mode == "prepare":
        assert a.cnf is not None
        result = prepare(a.directory, a.cnf)
    else:
        assert a.output is not None
        result = cold(a.directory, a.output)
    print(json.dumps({k: result[k] for k in ("status", "elapsed_seconds") if k in result}, indent=2))


if __name__ == "__main__":
    main()
