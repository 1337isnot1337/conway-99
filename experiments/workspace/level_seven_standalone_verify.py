"""Standalone, zero-assert, stdlib-only exact rational verifier for level-7 theta certificates.

Independently checks (with zero floats, zero NumPy, zero Z3, and zero bare `assert` statements so
every check remains active under `python3 -O`):
  1. Weight-22 Gamma_0(7) eta-quotient basis `f_j = theta * eta(z)^(49-4j) * eta(7z)^(4j-7)`
     through arbitrary Fourier order `n`.
  2. Five rank-44 positive control lattices (`theta^6 * E_4^(4-s) * E_{4,7}^s`, `s = 0..4`)
     and their Fricke involution transforms.
  3. All 35 Fano-complement triples generating the 14-vertex core under same-side closure.
  4. All committed `level-seven-certificate-{28,30,32}.json` files on disk AND the unified
     order-10 exact integer dual functional matching `lean/Conway99LevelSeven.lean` across
     every even rank `r <= 30` (from base floors) and `r = 32` (from 5-site sparse floors).
"""

from __future__ import annotations

import json
from fractions import Fraction
from itertools import combinations
from math import comb, isqrt
from pathlib import Path
from typing import Mapping


ZERO = Fraction(0)
ONE = Fraction(1)

BASE_DUAL_FLOORS: dict[int, int] = {0: 1, 1: 0, 2: 462, 3: 24948, 4: 1386, 5: 0, 6: 0}
SPARSE_DUAL_FLOORS: dict[int, int] = {
    0: 1,
    1: 0,
    2: 462,
    3: 24948,
    4: 1398474,
    5: 18001368,
    6: 86356116,
}

# Unified order-10 exact integer dual weights matching `lean/Conway99LevelSeven.lean`
UNIFIED_WL: dict[int, int] = {
    0: -56706285,
    1: -16133402,
    2: -4305675,
    3: -1064463,
    4: -239525,
    5: -47795,
    6: -8100,
    7: -1075,
    8: -89,
    10: 1,
}
UNIFIED_WK: dict[int, int] = {
    0: 932253,
    1: 246829,
    2: 37963,
    3: 4071,
    4: 292,
    5: 11,
}


def poly_mul(a: list[int], b: list[int]) -> list[int]:
    n = len(a)
    return [sum(a[j] * b[i - j] for j in range(i + 1)) for i in range(n)]


def poly_pow(a: list[int], exp: int) -> list[int]:
    out = [1] + [0] * (len(a) - 1)
    for _ in range(exp):
        out = poly_mul(out, a)
    return out


def compute_level7_eta_basis(order: int) -> tuple[list[int], list[int], list[int], list[list[int]]]:
    """Compute exact integer q-expansions of theta, E_4, E_{4,7}, and f_0..f_14 through `q^order`."""
    if order < 14:
        raise ValueError(f"order must be >= 14 to span all 15 basis forms, got {order}.")
    th = [0] * (order + 1)
    for y in range(-isqrt(4 * order // 7), isqrt(4 * order // 7) + 1):
        rem = 4 * order - 7 * y * y
        if rem < 0:
            continue
        for z in range(-isqrt(rem), isqrt(rem) + 1):
            if (y - z) % 2 == 0:
                th[(7 * y * y + z * z) // 4] += 1

    e4 = [1] + [240 * sum(d * d * d for d in range(1, i + 1) if i % d == 0) for i in range(1, order + 1)]
    e47 = [e4[i // 7] if i % 7 == 0 else 0 for i in range(order + 1)]

    basis: list[list[int]] = []
    for j in range(15):
        q_ser = th.copy()
        for step_t, exp in ((1, 49 - 4 * j), (7, 4 * j - 7)):
            for k in range(step_t, order + 1, step_t):
                v = [0] * (order + 1)
                for i in range(order // k + 1):
                    if exp >= 0:
                        v[k * i] = ((-1) ** i) * (comb(exp, i) if i <= exp else 0)
                    else:
                        v[k * i] = comb(i - exp - 1, i)
                q_ser = poly_mul(q_ser, v)
        basis.append(([0] * j + q_ser)[: order + 1])
    return th, e4, e47, basis


def verify_rank44_positive_controls(order: int = 28) -> dict[str, object]:
    th, e4, e47, basis = compute_level7_eta_basis(order)
    th6 = poly_pow(th, 6)
    for s in range(5):
        lat_l = poly_mul(th6, poly_mul(poly_pow(e4, 4 - s), poly_pow(e47, s)))
        lat_k = poly_mul(th6, poly_mul(poly_pow(e4, s), poly_pow(e47, 4 - s)))
        rank = 6 + 8 * s
        residue = lat_l.copy()
        coords: list[int] = []
        for j, bj in enumerate(basis):
            x_j = residue[j]
            coords.append(x_j)
            residue = [a_v - x_j * c_v for a_v, c_v in zip(residue, bj)]
        if any(residue):
            raise ValueError(f"Rank-44 positive control s={s} failed basis reconstruction.")
        for i in range(order + 1):
            fricke_i = sum(
                (Fraction(7) ** (3 + rank // 2 - 2 * j)) * coords[j] * basis[14 - j][i]
                for j in range(15)
            )
            if fricke_i != Fraction(lat_k[i], 1):
                raise ValueError(f"Fricke mismatch at s={s}, order={i}: {fricke_i} != {lat_k[i]}.")
    return {"order": order, "controls_verified": 5}


def verify_fano_35_triples_closure() -> dict[str, object]:
    blocks = [{(s + j) % 7 for j in (2, 4, 5, 6)} for s in range(7)]
    adj = [{7 + i for i, blk in enumerate(blocks) if x in blk} for x in range(7)] + blocks
    checked = 0
    for triple in combinations(range(7), 3):
        seen = set(triple)
        while True:
            added: set[int] = set()
            for x, y in combinations(seen, 2):
                if x // 7 == y // 7:
                    added |= adj[x] & adj[y]
            if added <= seen:
                break
            seen |= added
        if len(seen) != 14:
            raise ValueError(f"Triple {triple} generated only {len(seen)} vertices.")
        checked += 1
    if checked != 35:
        raise ValueError(f"Expected 35 triples, checked {checked}.")
    return {"triples_checked": checked, "core_size": 14}


def verify_certificate_dict(cert: Mapping[str, object], basis: list[list[int]]) -> dict[str, object]:
    rank_raw = cert["rank"]
    if isinstance(rank_raw, bool) or not isinstance(rank_raw, int):
        raise ValueError(f"Certificate rank must be an even integer, got {rank_raw!r}.")
    rank = rank_raw
    if rank < 0 or rank % 2 != 0:
        raise ValueError(f"Certificate rank must be a non-negative even integer, got {rank}.")
    sparse = bool(cert.get("sparse", False))
    limits_raw = cert["limits"]
    weights_raw = cert["weights"]
    if not isinstance(limits_raw, Mapping) or not isinstance(weights_raw, Mapping):
        raise TypeError("Certificate limits and weights must be mappings.")
    limits = {str(k): int(v) for k, v in limits_raw.items()}
    floors = SPARSE_DUAL_FLOORS if sparse else BASE_DUAL_FLOORS

    rows = [ZERO] * 15
    rhs = ZERO
    for tag, w_str in weights_raw.items():
        w = Fraction(str(w_str))
        if w < ZERO:
            raise ValueError(f"Negative certificate weight on {tag}: {w}")
        if tag in ("mass_L", "mass_L_rev", "mass_K", "mass_K_rev"):
            side = tag[5]
            idx = 0
            val = 1
            sign = -1 if tag.endswith("rev") else 1
        elif tag.startswith(("zero_L", "bound_L")):
            side = "L"
            idx = int(tag.split("L")[1])
            val = limits.get(str(idx), 0)
            sign = -1
        elif tag[0] in ("K", "L") and tag[1:].isdigit():
            side = tag[0]
            idx = int(tag[1:])
            val = floors.get(idx, 0) if side == "K" else 0
            sign = 1
        else:
            raise ValueError(f"Unrecognized certificate tag {tag!r}.")

        for j in range(15):
            coeff = (
                Fraction(basis[j][idx], 1)
                if side == "L"
                else (Fraction(7) ** (3 + rank // 2 - 2 * j)) * basis[14 - j][idx]
            )
            rows[j] += w * sign * coeff
        rhs += w * sign * val

    if any(r_val != ZERO for r_val in rows):
        raise ValueError(f"Rank-{rank} certificate failed basis cancellation.")
    if rhs != ONE:
        raise ValueError(f"Rank-{rank} certificate RHS expected 1, got {rhs}.")
    return {"rank": rank, "sparse": sparse, "terms": len(weights_raw), "rhs": str(rhs), "verified": True}


def verify_unified_dual_all_ranks(basis: list[list[int]]) -> dict[str, object]:
    """Verify the unified order-10 integer dual vector across all even ranks `r = 0..30` and `r = 32`."""
    p7_10 = 7 ** 10
    for j in range(15):
        s_l = sum(w * basis[j][i] for i, w in UNIFIED_WL.items())
        s_k = sum(w * basis[14 - j][i] for i, w in UNIFIED_WK.items())
        if p7_10 * s_l + (7 ** (28 - 2 * j)) * s_k != 0:
            raise ValueError(f"Unified dual basis cancellation failed at j={j}.")

    l_rhs = UNIFIED_WL[0] * 1 + UNIFIED_WL[7] * 990 + UNIFIED_WL[8] * 148995
    k_base = sum(w * BASE_DUAL_FLOORS[i] for i, w in UNIFIED_WK.items())
    k_sparse = sum(w * SPARSE_DUAL_FLOORS[i] for i, w in UNIFIED_WK.items())

    even_ranks_le_30: dict[int, int] = {}
    for p in range(16):
        gap = (7 ** (15 - p)) * k_base + l_rhs
        if gap <= 0:
            raise ValueError(f"Unified dual failed at r={2 * p}: gap={gap}")
        even_ranks_le_30[2 * p] = gap

    gap_32 = k_sparse + 7 * l_rhs
    if gap_32 <= 0:
        raise ValueError(f"Unified dual failed at r=32: gap={gap_32}")

    return {
        "max_fourier_order": 10,
        "l_rhs_int": l_rhs,
        "k_base_int": k_base,
        "k_sparse_int": k_sparse,
        "rank_28_gap_int": even_ranks_le_30[28],
        "rank_30_gap_int": even_ranks_le_30[30],
        "rank_32_gap_int": gap_32,
        "all_even_ranks_0_to_30_excluded": len(even_ranks_le_30) == 16,
    }


def run_all_checks(cert_dir: Path | None = None) -> dict[str, object]:
    workspace = cert_dir if cert_dir is not None else Path(__file__).resolve().parent
    _th, _e4, _e47, basis = compute_level7_eta_basis(14)
    controls = verify_rank44_positive_controls(28)
    fano = verify_fano_35_triples_closure()

    cert_paths = sorted(workspace.glob("level-seven-certificate-*.json"))
    if not cert_paths:
        raise FileNotFoundError(f"No level-seven-certificate-*.json files found in {workspace}.")
    committed_results: dict[str, dict[str, object]] = {}
    for path in cert_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        committed_results[path.name] = verify_certificate_dict(data, basis)

    unified = verify_unified_dual_all_ranks(basis)
    return {
        "positive_controls": controls,
        "fano_closure": fano,
        "committed_certificates": committed_results,
        "unified_order10_dual": unified,
    }


if __name__ == "__main__":
    print(json.dumps(run_all_checks(), indent=2))
