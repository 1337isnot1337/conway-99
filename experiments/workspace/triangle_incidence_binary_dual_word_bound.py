"""Strengthen the frozen binary-code dual with forced triangle words.

No optimizer, original builder, or model imports. All arithmetic is exact.
The combinatorial lower bounds are proved in the accompanying note.
"""
import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path

RESULT_SHA = "80c87653eb52286cd90633823dfa8e07166e65531eba938b69f9b6957e287e5f"
WEIGHTS = [36, 40, 44, 48, 52, 56, 60]
LOWER = {3: 231, 4: 2079, 6: 24486}


def krawtchouk(j, w):
    return sum((-1)**i * comb(w, i) * comb(99-w, j-i)
               for i in range(max(0, j-(99-w)), min(w, j)+1))


def small_host_control():
    # The nine-vertex rook graph, constructed directly from coordinates.
    vertices = list(range(9))
    def edge(a, b):
        return a != b and (a//3 == b//3 or a%3 == b%3)
    triangles = [sum(1 << a for a in t) for t in combinations(vertices, 3)
                 if all(edge(a, b) for a, b in combinations(t, 2))]
    assert len(triangles) == 6
    words = {4: set(), 6: set()}
    counts = {4: 0, 6: 0}
    for t, u in combinations(triangles, 2):
        intersection = (t & u).bit_count()
        assert intersection in (0, 1)
        word = t ^ u
        weight = word.bit_count()
        assert weight == (4 if intersection else 6)
        words[weight].add(word)
        counts[weight] += 1
    assert counts == {4: 9, 6: 6}
    assert {w: len(v) for w, v in words.items()} == counts
    return {"host": "three by three rook graph", "triangles": 6,
            "distinct_intersecting_pair_words": 9,
            "distinct_disjoint_pair_words": 6}


def verify(path):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RESULT_SHA
    result = json.loads(raw)
    y = list(map(Fraction, result["exact_dual"]))
    assert len(y) == 99 and all(value >= 0 for value in y)
    for w in WEIGHTS:
        assert -sum(y[j-1]*krawtchouk(j, w) for j in range(1, 100)) == 1
    old_upper = 1 + sum(y[j-1]*comb(99, j) for j in range(1, 100))
    assert old_upper == Fraction(5834276864000, 755087)
    assert LOWER == {3: 99*7//3, 4: 99*comb(7, 2), 6: comb(231, 2)-99*comb(7, 2)}
    factor = 1 + sum(y[j-1]*lower for j, lower in LOWER.items())
    new_y = [value/factor for value in y]
    for w in WEIGHTS:
        assert sum(new_y[j-1]*(LOWER.get(j, 0)-krawtchouk(j, w))
                   for j in range(1, 100)) == 1
    upper = 1 + sum(new_y[j-1]*(comb(99, j)-LOWER.get(j, 0)) for j in range(1, 100))
    assert upper == old_upper/factor == Fraction(1166855372800, 7799881)
    assert 2**17 <= upper < 2**18
    return {"status": "PASS_EXACT_FORCED_DUAL_WORD_CODE_BOUND",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "base_dual_result_sha256": RESULT_SHA,
            "forced_dual_word_lower_bounds": LOWER,
            "old_exact_bound": str(old_upper), "dual_rescaling_factor": str(factor),
            "exact_code_size_upper_bound": str(upper),
            "integer_code_size_upper_bound": upper.numerator//upper.denominator,
            "binary_kernel_dimension_upper_bound": 17,
            "binary_incidence_rank_lower_bound": 82,
            "positive_rescaled_dual": [[j, str(new_y[j-1])] for j in range(1, 100) if new_y[j-1]],
            "all_99_dual_signs_and_seven_dual_columns_checked": True,
            "small_host_control": small_host_control(),
            "stronger_LP_optimum_claimed": False,
            "optimizer_called": False, "unrestricted_graph_existence_resolved": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("result", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    report = verify(a.result)
    assert not a.output.exists()
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
