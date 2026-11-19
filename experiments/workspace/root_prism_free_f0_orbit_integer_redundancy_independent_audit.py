"""Direct original-row audit of the sole shifted-orbit candidate's redundancy."""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "proof_source": ("experiments/workspace/root_prism_free_f0_orbit_integer_redundancy.py", "24a0b0a7954f198e52084c75f010fe6473f82bc14674d11e062492043d08443c"),
    "proof": (BASE + "f0-orbit-integer-quadratics-scan01-redundancy.json", "495eec0bde8b61da031b10a8fe0657df72bf1822f7e04d639e74480fc9cdc88b"),
    "scan": (BASE + "f0-orbit-integer-quadratics-scan01.json.gz", "5491abae33fb6faa79b006fe8b789df801ad289ec42167d3c53ec9041627aa51"),
    "baseline": (BASE + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": (BASE + "f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "reduced": (BASE + "f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "parent": (BASE + "f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT / name).read_bytes()
        assert digest(raw) == expected
        if key != "proof_source":
            data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    proof, scan = data["proof"], data["scan"]
    assert len(scan["cuts"]) == 1 and len(scan["attempts"]) == 1764
    candidate = scan["cuts"][0]
    assert candidate["form"] == [[6, 1], [7, 1]] and candidate["k"] == 3
    expected_multipliers = [[3, "6"], [1481, "6"], [1494, "6"], [1611, "6"], [1624, "6"]]
    assert proof["parent_equality_multipliers"] == expected_multipliers
    total = [0] * 15200
    rhs = 0
    equations = data["parent"]["matrix"]["equalities"]
    for row_id, scalar in expected_multipliers:
        scalar = int(scalar)
        for j, c in equations[row_id]["terms"]:
            total[j] += scalar * c
        rhs += scalar * equations[row_id]["rhs"]
    target = dict(candidate["row"]["terms"])
    assert total == [target.get(j, 0) for j in range(15200)]
    assert rhs == candidate["row"]["rhs"] == 6
    domain = data["baseline"]["validation"]
    triples, orbits = domain["triples"], domain["selector_orbits"]
    xof = {a: i for i, members in enumerate(orbits) for a in members}
    support = sorted(orbits[6] + orbits[7])
    core_pairs = [(0, 5), (1, 3), (2, 4)]
    supports = [[a for a, h in enumerate(triples) if i in h and j in h] for i, j in core_pairs]
    assert [len(s) for s in supports] == [8, 8, 8]
    assert sorted(a for s in supports for a in s) == support and len(support) == 24
    for pair, members in zip(core_pairs, supports):
        matches = [r for r in data["moments"]["original_selector_equalities"]
                   if r.get("core_pair") == list(pair)]
        assert len(matches) == 1 and matches[0]["quota"] == 1 and matches[0]["support"] == members
    reverse = {old: new for new, old in enumerate(data["reduced"]["kept_original_variables"])}
    def zcoord(a, b):
        if a == b:
            return xof[a]
        a, b = sorted((a, b))
        pair_id = a * (959 - a) // 2 + b - a - 1
        return reverse.get(5847 + data["moments"]["pair_to_orbit"][pair_id])
    L, P, R = Counter(xof[a] for a in support), Counter(), Counter()
    for a, b in combinations(support, 2):
        j = zcoord(a, b)
        if j is not None:
            P[j] += 1
    for members in supports:
        for a in support:
            R[xof[a]] -= 1
            for b in members:
                j = zcoord(a, b)
                if j is not None:
                    R[j] += 1
    for j in range(15200):
        assert R[j] == 2 * P[j] - 2 * L[j]
        assert target.get(j, 0) == 3 * L[j] - P[j]
    report = {
        "status": "PASS: five existing equality rows reproduce the full candidate exactly",
        "audit_source_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": s} for k, (p, s) in INPUTS.items()},
        "parent_equality_multipliers": expected_multipliers,
        "all_coefficient_positions_checked": 15200, "right_hand_side": 6,
        "independent_literal_Gram_supports": supports,
        "literal_lifted_rows_reconstructed": 72,
        "identities": ["L=3", "R=L^2-3L=2P-2L", "3L-P-6=2*(L-3)-R/2"],
        "complete_both_mathematical_sources_read": True,
        "full_finite_family_or_point_scan_repeated": False,
        "subject_imports": False, "matrix_rebuilt": False, "optimizer_calls": 0,
        "nonredundant_candidate_rows": 0,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
