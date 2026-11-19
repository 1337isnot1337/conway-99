"""Original-Gram combination proofs for signed-population equalities."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "character_replay": ("f0-character-populations01-cold.json", "1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    filename, expected = INPUTS[name]
    raw = (LOGS / filename).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if filename.endswith(".gz") else raw)


def build():
    chars, replay, domains, moments = [read(name) for name in INPUTS]
    assert replay["status"].startswith("PASS")
    actions, original = domains["signature_actions"], moments["original_selector_equalities"]
    assert len(original) == 172 and actions == moments["selector_actions"]
    row_index = {}
    for i, row in enumerate(original):
        row_index.setdefault((tuple(row["support"]), row["quota"]), i)
    equations, mapping, ranks = [], [], []
    from flint import fmpz_mat
    for character in chars["nontrivial_characters"]:
        ci, chi = character["character"], character["values"]
        assert sum(chi) == 0
        populations = [p for p in chars["signed_populations"] if p["character"] == ci]
        unique, dense_rows = {}, []
        for ri, row in enumerate(original):
            multipliers = Counter()
            for move, sign in zip(actions, chi):
                transported = tuple(sorted(move[a] for a in row["support"]))
                target = row_index[transported, row["quota"]]
                multipliers[target] += sign
            multipliers = {i: v for i, v in multipliers.items() if v}
            expanded = [0]*480
            rhs = 0
            for i, v in multipliers.items():
                rhs += v*original[i]["quota"]
                for a in original[i]["support"]:
                    expanded[a] += v
            assert rhs == 0
            support = set(row["support"])
            coefficients, restored = [], [0]*480
            for p in populations:
                c = (12//len(p["literal_selectors"]))*sum(w for a, w in zip(p["literal_selectors"], p["signs"])
                                                         if a in support)
                coefficients.append(c)
                for a, w in zip(p["literal_selectors"], p["signs"]):
                    restored[a] = c*w
            assert expanded == restored
            if not any(coefficients):
                mapping.append({"character": ci, "original_Gram_row": ri, "disposition": "zero_identity"})
                continue
            divisor = math.gcd(*coefficients)
            if next(c for c in coefficients if c) < 0:
                divisor = -divisor
            primitive = tuple(c//divisor for c in coefficients)
            if primitive not in unique:
                equation_id = len(equations)
                unique[primitive] = equation_id
                dense_rows.append(list(primitive))
                equations.append({"equation": equation_id, "character": ci,
                                  "signed_population_terms": [[p["signed_population"], c]
                                                              for p, c in zip(populations, primitive) if c],
                                  "rhs": 0, "representative_original_Gram_row": ri,
                                  "original_Gram_integer_combination": sorted(map(list, multipliers.items())),
                                  "primitive_signed_divisor": divisor,
                                  "original_literal_coefficients_checked": 480,
                                  "original_rhs_checked": rhs})
            mapping.append({"character": ci, "original_Gram_row": ri,
                            "disposition": "retained_primitive_equation", "equation": unique[primitive],
                            "primitive_signed_divisor": divisor})
        ranks.append({"character": ci, "signed_populations": len(populations),
                      "distinct_equations": len(dense_rows), "exact_rational_rank": fmpz_mat(dense_rows).rank(),
                      "dense_primitive_matrix": dense_rows})
    assert len(mapping) == 516 and len(equations) == 32
    assert [r["exact_rational_rank"] for r in ranks] == [9, 9, 10]
    return {"schema": "conway99.f0-character-Gram-equalities.v1",
            "status": "EXACT_ORIGINAL_ROW_COMBINATIONS",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+v[0], "sha256": v[1]}
                       for k, v in INPUTS.items()},
            "equations": equations, "original_row_projection_map": mapping,
            "character_ranks": ranks, "retained_equations": len(equations),
            "original_character_row_combinations_checked": len(mapping),
            "literal_coefficient_comparisons": len(mapping)*480,
            "validity": "For each nontrivial character, sum the12 transported original equations with its signs. Their quotas are unchanged and the character sums to zero. The resulting480-coordinate row is expanded exactly as a linear combination of the compatible orbit signings. Division by its signed gcd gives each recorded homogeneous equation.",
            "graph_automorphism_assumed": False, "optimizer_calls": 0, "solver_calls": 0,
            "F0_excluded": False, "global_incidence_claimed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = build()
    if args.mode == "replay":
        raw = args.record.read_bytes()
        assert json.loads(raw) == result
        result = {"status": "PASS: all516 character-weighted original rows and32 primitive equations replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()), "record_sha256": sha(raw),
                  "literal_coefficient_comparisons": 247680, "solver_calls": 0,
                  "seconds": time.monotonic()-started}
    raw = canonical(result)+b"\n"
    with args.output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"status": result["status"], "sha256": sha(raw),
                      "seconds": time.monotonic()-started}, indent=2))
