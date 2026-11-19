"""Finite independent semantic controls for signed integer cut normalization."""
import argparse
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBJECT = ROOT / "experiments/workspace/root_prism_free_f0_direct_master_registry_v2.py"
EXPECTED = "a14fbdbfce9badeee748930d2f501ecde9bc5ca77bb866d4878a9b53096286c8"


def controls():
    assert hashlib.sha256(SUBJECT.read_bytes()).hexdigest() == EXPECTED
    spec = importlib.util.spec_from_file_location("registry_under_semantic_controls", SUBJECT)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    checks = 0
    for coefficients in product(range(-2, 3), repeat=3):
        if not any(coefficients):
            continue
        for rhs in range(-3, 4):
            row = helper.normalized(list(enumerate(coefficients)), rhs)
            for bits in product((0, 1), repeat=3):
                old = sum(c * x for c, x in zip(coefficients, bits)) <= rhs
                new = sum(c * bits[j] for j, c in row["terms"]) <= row["rhs"]
                assert old == new
                checks += 1
    first = ({"terms": [[0, 1], [1, -1]], "rhs": 0}, {"test": 0})
    stronger = ({"terms": [[0, 1], [1, -1]], "rhs": -1}, {"test": 1})
    registry, additions = helper.add_rows([], [first, stronger, first])
    assert len(registry) == len(additions) == 2
    saved = helper.canonical(registry)
    valid = ({"terms": [[2, 1]], "rhs": 0}, {"test": 2})
    invalid = ({"terms": [[3, 1], [4, 1 << 63]], "rhs": 0}, {"test": 3})
    try:
        helper.add_rows(registry, [valid, invalid])
    except OverflowError:
        pass
    else:
        raise AssertionError("unsafe batch accepted")
    assert helper.canonical(registry) == saved
    return {"status": "PASS_EXACT_BOOLEAN_EQUIVALENCE_AND_BATCH_CONTROLS",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "subject_sha256": EXPECTED, "signed_boolean_truth_checks": checks,
            "RHS_is_in_deduplication_key": True, "unsafe_batch_does_not_mutate_registry": True,
            "subject_small_controls": helper.controls(), "model_or_domain_builds": 0,
            "optimizer_calls": 0, "production_candidates": 0}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls()
    args.output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(report, sort_keys=True))
