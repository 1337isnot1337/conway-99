"""Check the remaining 6+1 endpoint component by its fifteen integer norm budgets."""
from dataclasses import dataclass
from itertools import combinations, product


PAIRS = list(combinations(range(6), 2))
FULL = (1 << len(PAIRS))-1


@dataclass(frozen=True)
class Event:
    endpoints: tuple
    center: int
    raised: tuple
    ones: int
    twos: int

    @property
    def cost(self):
        return self.ones.bit_count()+2*self.twos.bit_count()


def events():
    for pair in PAIRS:
        for center in sorted(set(range(7))-set(pair)):
            outside = sorted(set(range(6))-set(pair)-{center})
            for size in range(1, len(outside)+1):
                for raised in combinations(outside, size):
                    ones = twos = 0
                    for j, (a, b) in enumerate(PAIRS):
                        m = [2*int(i == center)+int(i in pair) for i in (a, b)]
                        k = [int(i in raised) for i in (a, b)]
                        old = m[0]-m[1]
                        new = old+4*(k[0]-k[1])
                        excess = new*new-old*old
                        assert excess in (0, 8, 16)
                        ones |= int(excess == 8) << j
                        twos |= int(excess == 16) << j
                    yield Event(pair, center, raised, ones, twos)


def orientations(chosen):
    balanced = symmetric = 0
    for signs in product((-1, 1), repeat=len(chosen)):
        vk = [[0]*6 for _ in range(6)]
        for sign, event in zip(signs, chosen):
            p, q = event.endpoints
            for j in event.raised:
                vk[p][j] += sign
                vk[q][j] -= sign
        if any(sum(row) for row in vk):
            continue
        balanced += 1
        symmetric += all(vk[i][j] == vk[j][i] for i, j in PAIRS)
    return balanced, symmetric


def verify():
    all_events = list(events())
    assert len(all_events) == 645 and min(e.cost for e in all_events) == 6
    results = {}
    for first in all_events:
        if first.endpoints != (0, 1) or first.center not in (2, 6):
            continue
        start = 3 if first.center == 2 else 2
        if first.raised != tuple(range(start, start+len(first.raised))):
            continue
        available = [[e for e in all_events if e.cost <= first.cost
                      and (e.ones | e.twos) & (1 << j)] for j in range(len(PAIRS))]
        counts = [0, 0, 0]

        def extend(chosen, used_once, full):
            if full == FULL:
                balanced, symmetric = orientations(chosen)
                counts[0] += 1
                counts[1] += balanced
                counts[2] += symmetric
                return
            if len(chosen) == 5:
                return
            unfilled = FULL ^ full
            pivot = (unfilled & -unfilled).bit_length()-1
            for e in available[pivot]:
                if (e.ones | e.twos) & full or e.twos & used_once:
                    continue
                extend(chosen+[e], used_once ^ e.ones, full | e.twos | (used_once & e.ones))

        extend([first], first.ones, first.twos)
        results[first.center, len(first.raised)] = tuple(counts)
    assert results == {(2, 1): (20, 40, 0), (2, 2): (0, 0, 0), (2, 3): (84, 168, 0),
                       (6, 1): (0, 0, 0), (6, 2): (0, 0, 0), (6, 3): (0, 0, 0),
                       (6, 4): (0, 0, 0)}, results
    print('Six-axis norm budgets: 104 terminal choices, 208 balanced orientations, zero symmetric.')


if __name__ == '__main__':
    verify()
