"""Replay the seventeen four-high counting certificates with Python integers.

This verifier does not import the census, graph canonicalizer, or SAT solver.
"""
from collections import Counter
from itertools import combinations
import argparse
import json
from pathlib import Path


def verify(record):
    rows = record['core_rows']
    assert len(rows) == 8 and all(0 <= r < 256 and r.bit_count() == 4 for r in rows)
    columns = [sum(((rows[p] >> n) & 1) << p for p in range(8)) for n in range(8)]
    assert all(c.bit_count() == 4 for c in columns)
    for side in (rows, columns):
        assert all((side[i] & side[j]).bit_count() <= 2 for i, j in combinations(range(8), 2))
    high = record['high']
    assert len(high) == 8
    masks = []
    for pp, nn in high:
        assert len(pp) == len(nn) == 2
        assert len(set(pp)) == len(set(nn)) == 2
        assert all(0 <= p < 8 for p in pp + nn)
        assert all(sum((rows[p] >> n) & 1 for n in nn) <= 1 for p in pp)
        assert all(sum((rows[p] >> n) & 1 for p in pp) <= 1 for n in nn)
        masks.append(sum(1 << p for p in pp) + sum(1 << (n+8) for n in nn))
    for side, part in ((rows, 0), (columns, 1)):
        actual = Counter(tuple(sorted(h[part])) for h in high)
        expected = {pair: 2-(side[pair[0]] & side[pair[1]]).bit_count()
                    for pair in combinations(range(8), 2)}
        assert all(actual[pair] == value for pair, value in expected.items())
    for p in range(8):
        for n in range(8):
            used = sum(p in pp and n in nn for pp, nn in high)
            assert used <= 2-((rows[p] >> n) & 1)
    common = {(i, j): (masks[i] & masks[j]).bit_count()
              for i, j in combinations(range(8), 2)}
    assert max(common.values()) <= 2
    certificate = record['certificate']
    selected = certificate['vertices']
    assert len(selected) == len(set(selected)) == 4
    assert all(0 <= h < 8 for h in selected)
    pair_sum = sum(common[tuple(sorted(pair))] for pair in combinations(selected, 2))
    lower, upper = 4*len(selected), 11 + 2*6 - pair_sum
    assert certificate['core_pair_sum'] == pair_sum
    assert certificate['incidence_lower'] == lower
    assert certificate['incidence_upper'] == upper
    assert lower > upper


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('path', type=Path, nargs='?', default=Path(__file__).resolve().parents[1]
                   / 'logs/eigenlattices/coupled-shells-counting-certificates.json')
    args = p.parse_args()
    data = json.loads(args.path.read_text())
    identifiers = [(r['core'], r['orbit']) for r in data]
    assert len(set(identifiers)) == len(data) == 17
    for record in data:
        verify(record)
    counts = Counter(r['core'] for r in data)
    assert [counts[i] for i in range(5)] == [2, 3, 0, 12, 0]
    print('17 integer counting certificates verified; core counts 2 3 0 12 0')


if __name__ == '__main__':
    main()
