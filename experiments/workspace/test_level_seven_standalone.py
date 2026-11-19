"""Tests for the standalone zero-assert level-7 theta certificate verifier."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

WORKSPACE = Path(__file__).resolve().parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from level_seven_standalone_verify import (  # noqa: E402
    compute_level7_eta_basis,
    run_all_checks,
    verify_certificate_dict,
)


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_standalone_verifier_has_no_floats_or_bare_asserts() -> None:
    src = (WORKSPACE / "level_seven_standalone_verify.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            raise AssertionError("Found forbidden bare assert in level_seven_standalone_verify.py")
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"Found forbidden float literal {node.value!r}")


def test_committed_certificates_unified_dual_and_tamper_rejection() -> None:
    res = run_all_checks(WORKSPACE)
    check(res["positive_controls"]["controls_verified"] == 5, "Expected 5 rank-44 controls.")
    check(res["fano_closure"]["triples_checked"] == 35, "Expected 35 Fano triples.")
    certs = res["committed_certificates"]
    for fname in (
        "level-seven-certificate-28.json",
        "level-seven-certificate-30.json",
        "level-seven-certificate-32.json",
    ):
        check(fname in certs and certs[fname]["verified"] is True, f"Failed on {fname}")

    uni = res["unified_order10_dual"]
    check(uni["all_even_ranks_0_to_30_excluded"] is True, "Expected all even ranks 0..30 excluded.")
    check(uni["rank_28_gap_int"] == 772043163, f"Unexpected rank-28 gap {uni['rank_28_gap_int']}")
    check(uni["rank_30_gap_int"] == 49408089, f"Unexpected rank-30 gap {uni['rank_30_gap_int']}")
    check(uni["rank_32_gap_int"] == 229186293, f"Unexpected rank-32 gap {uni['rank_32_gap_int']}")

    _th, _e4, _e47, basis = compute_level7_eta_basis(14)
    cert30 = json.loads((WORKSPACE / "level-seven-certificate-30.json").read_text(encoding="utf-8"))

    # Tampered weight fails closed
    tampered = dict(cert30)
    tampered_weights = dict(tampered["weights"])
    tampered_weights["L10"] = "2/49408089"
    tampered["weights"] = tampered_weights
    with pytest.raises(ValueError):
        verify_certificate_dict(tampered, basis)

    # Odd, negative, and boolean ranks fail closed
    for bad_rank in (29, -2, True):
        bad_cert = dict(cert30)
        bad_cert["rank"] = bad_rank
        with pytest.raises(ValueError):
            verify_certificate_dict(bad_cert, basis)
