"""Independent literal check of all25 held-direction integer refinements."""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "source": ("experiments/workspace/root_prism_free_f0_selector_integer_refinement.py", "eb0c41c0448b43a4bd684c791d468e37b9c805c888b86383fb36b33da75560d5"),
    "record": (BASE + "f0-selector-integer-refinements01.json.gz", "68d5ea0ca4a9906e74319770924eb91f880e46cec0c3ed2ab269bb1debe7b339"),
    "old": (BASE + "f0-selector-psd-cuts-scan01.json.gz", "5c74497bb70d44bf2fac7002ed16b4657500c4af2518cab196684c9346449e79"),
    "new": (BASE + "f0-joint-psd-zero-scan02.json.gz", "43e590c801ccb85e385253cc475ce6f6bdc09874d10b9c7571170cb2bd06d9a3"),
    "cache": (BASE + "f0-joint-psd-cache01.json.gz", "6d293340386e77e0bf0b0a7b006744523d75eb7e90ef0fd371c3eed5eb82801e"),
    "proposal": (BASE + "f0-schur-path-query-run01/numerical.json", "bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    values = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT / name).read_bytes()
        assert digest(raw) == expected
        if key != "source":
            values[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    record = values["record"]
    assert record["source_sha256"] == INPUTS["source"][1]
    domain = values["cache"]["domain"]
    assert digest(canonical(domain)) == values["cache"]["domain_sha256"]
    reverse = {old: new for new, old in enumerate(domain["kept"])}
    assert len(reverse) == 15200
    point = [float.fromhex(v).as_integer_ratio() for v in values["proposal"]["col_value_hex"]]
    assert len(point) == 15200
    den = max(b for a, b in point)
    assert den > 0 and den & (den - 1) == 0
    nums = [a * (den // b) for a, b in point]
    assert all(den % b == 0 for a, b in point)
    directions = {("old", i): c for i, c in enumerate(values["old"]["cuts"])}
    directions.update({("new", i): c for i, c in enumerate(values["new"]["cuts"]) if c["family"] == "selector"})
    assert len(directions) == record["held_directions"] == 48
    by_direction = {}
    for r in record["refinements"]:
        key = r["source"], r["index"]
        assert (key, r["k"]) not in by_direction
        by_direction[key, r["k"]] = r
    zero_means, implication_count, row_checks = 0, 0, []
    for key, held in directions.items():
        vector = held["certificate"]["vector"]
        assert len(vector) == 481 and vector[0] == 0 and all(type(v) is int for v in vector)
        weights = vector[1:]
        mean = Counter()
        for a, w in enumerate(weights):
            mean[domain["xmap"][a]] += w
        mean = {j: c for j, c in mean.items() if c}
        if not mean:
            zero_means += 1
            assert not any(k == key for k, shift in by_direction)
            continue
        # Direct Boolean expansion at k=0: diagonal w(1-w)/2,
        # and one coefficient -w_a*w_b for every unordered pair.
        base = Counter()
        for a, w in enumerate(weights):
            assert (w - w * w) % 2 == 0
            base[domain["xmap"][a]] += (w - w * w) // 2
        for p, (a, b) in enumerate(domain["pairs"]):
            old = 5847 + domain["pmap"][p]
            if old in reverse:
                base[reverse[old]] -= weights[a] * weights[b]
        base = {j: c for j, c in base.items() if c}
        mean_num = sum(c * nums[j] for j, c in mean.items())
        expected_shifts = {-1, 0, mean_num // den}
        assert {shift for k, shift in by_direction if k == key} == expected_shifts
        raw_rows = {}
        for shift in sorted(expected_shifts):
            raw = {j: base.get(j, 0) + shift * mean.get(j, 0) for j in set(base) | set(mean)}
            raw = {j: c for j, c in raw.items() if c}
            rhs = shift * (shift + 1) // 2
            factor = math.gcd(abs(rhs), *(abs(c) for c in raw.values())) or 1
            row = {"terms": [[j, c // factor] for j, c in sorted(raw.items())], "rhs": rhs // factor}
            saved = by_direction[key, shift]
            assert row == saved["row"] and factor == saved["positive_normalization"]
            assert digest(canonical(row)) == saved["row_sha256"]
            gap_num = sum(c * nums[j] for j, c in row["terms"]) - row["rhs"] * den
            gap = Fraction(gap_num, den)
            assert gap == Fraction(saved["exact_proposal_gap"]) and gap > 0
            assert saved["strict_nonredundancy_in_full_parent_proved"] is False
            raw_rows[shift] = raw
            row_checks.append({"source": key[0], "index": key[1], "k": shift,
                               "row_sha256": saved["row_sha256"], "exact_gap": str(gap)})
        old_row = dict(held["certificate"]["row"]["terms"])
        old_factor = held["certificate"]["positive_divisor"]
        assert old_factor > 0 and held["certificate"]["row"]["rhs"] == 0
        assert all(raw_rows[-1].get(j, 0) + raw_rows[0].get(j, 0) == old_factor * old_row.get(j, 0) for j in range(15200))
        implication_count += 1
        assert time.monotonic() - started < 60
    assert zero_means == 37 and implication_count == 11 and len(row_checks) == 25
    report = {
        "status": "PASS: all25 literal integer rows/gaps and11 held-PSD implications independently checked",
        "source_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "complete_mathematical_source_read": True,
        "all48_integer_vectors_checked": True, "identically_zero_orbit_mean_directions": zero_means,
        "literal_nonzero_mean_directions_reexpanded": implication_count,
        "all15200_positions_checked_per_held_row_implication": True,
        "rows": row_checks,
        "scope": "Validity and exact old-proposal gaps only. No strict nonredundancy relative to all parent rows, current-model feasibility or graph exclusion is claimed.",
        "subject_imported": False, "old_controls_repeated": False,
        "new_direction_search": False, "optimizer_calls": 0, "eigendecompositions": 0,
        "seconds": time.monotonic() - started,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
