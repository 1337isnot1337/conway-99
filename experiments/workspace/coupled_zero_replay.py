"""Replay the eleven necessary Z-forest types without calling a SAT solver.

The saved witnesses realize only H/Z incidence and common-neighbor upper
bounds.  They do not give complete graphs, or low-class incidences.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path

from coupled_zero_structure import forests, graph, verify


EXCLUDED = {
    'e1_a1_b1_c1_d0',
    'e1_a3_b0_c0_d1',
    'e1_a3_b0_c1_d0',
    'e1_a4_b1_c0_d0',
}


def classify(edges):
    Z = graph(edges, 11)
    left = set(range(11)); counts = Counter()
    while left:
        seed = min(left); part = {seed}
        while True:
            more = part | {w for z in part for w in Z[z]}
            if more == part:
                break
            part = more
        left -= part
        degrees = tuple(sorted(len(Z[z]) for z in part))
        name = {
            (0,): 'isolate', (1, 1): 'edge', (1, 1, 2): 'p3',
            (1, 1, 1, 3): 'star3', (1, 1, 2, 2): 'p4',
        }[degrees]
        counts[name] += 1
    e = len(edges) - 5
    a, b, c, d = [counts[name] for name in ('edge', 'p3', 'star3', 'p4')]
    ident = f'e{e}_a{a}_b{b}_c{c}_d{d}'
    return ident, counts


def overlap(high):
    sig = [set(p) | {n + 8 for n in nn} for p, nn in high]
    return [[0 if i == j else len(a & b) for j, b in enumerate(sig)]
            for i, a in enumerate(sig)]


def check_high_edge_triangle(w):
    if not w['high_edges']:
        return
    x, y = w['endpoints']
    Z = graph(w['edges'], 11)
    shared = [z for z in range(11)
              if (w['masks'][x] >> z) & (w['masks'][y] >> z) & 1]
    assert len(shared) == 1 and not Z[shared[0]]
    assert w['common'][x][y] == 0


def from_old(record, block):
    old = record['edges']; orbit = block['orbits'][record['orbit']]
    ze = [[i - 8, j - 8] for i, j in old if i >= 8]
    ident, _ = classify(ze)
    forest = next(f for f in forests() if f['id'] == ident)
    endpoints = next(([i, j] for i, j in old if j < 8), [])
    masks = [sum(1 << (j - 8) for i, j in old if i == h and j >= 8)
             for h in range(8)]
    return dict(forest, edges=ze, endpoints=endpoints, masks=masks,
                common=overlap(orbit['high']), source_core=block['core'],
                source_orbit=record['orbit'], source='saved high/low witness')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--old-witnesses', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-low-all.json'))
    p.add_argument('--witnesses', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-zero-witnesses.json'))
    p.add_argument('--generate', action='store_true')
    a = p.parse_args()
    data = json.loads(a.orbits.read_text()); blocks = {b['core']: b for b in data}
    old = json.loads(a.old_witnesses.read_text())
    representatives = {}; census = Counter()
    for r in old:
        if r['status'] != 'sat':
            continue
        w = from_old(r, blocks[r['core']])
        verify(w, w['masks'], w['common'], w['endpoints'])
        check_high_edge_triangle(w)
        assert w['id'] not in EXCLUDED
        census[w['id']] += 1
        representatives.setdefault(w['id'], w)
    print('Saved high/low partial witnesses:', sum(census.values()))
    for ident, count in sorted(census.items()):
        print(ident, count)
    if a.generate:
        for name in ('star-p3', 'two-p4'):
            path = a.witnesses.parent / f'coupled-zero-overlap-{name}.json'
            w = json.loads(path.read_text())[-1]
            assert w['status'] == 'sat'
            w['source'] = 'fixed actual overlap matrix'
            representatives.setdefault(w['id'], w)
        a.witnesses.write_text(json.dumps(list(representatives.values()), indent=2) + '\n')
    witnesses = json.loads(a.witnesses.read_text())
    all_types = {f['id'] for f in forests()}
    expected = all_types - EXCLUDED
    assert len(all_types) == 15 and len(expected) == 11
    assert len(witnesses) == 11
    assert {w['id'] for w in witnesses} == expected
    for w in witnesses:
        block = blocks[w['source_core']]
        o = block['orbits'][w['source_orbit']]
        assert w['common'] == overlap(o['high'])
        assert classify(w['edges'])[0] == w['id']
        verify(w, w['masks'], w['common'], w['endpoints'])
        check_high_edge_triangle(w)
        print('Verified forest:', w['id'], 'core', w['source_core'],
              'orbit', w['source_orbit'])
    print('PASS: eleven exact H/Z witnesses, each using an actual core overlap matrix.')
    print('Scope: these witnesses do not choose low/zero or low/low edges.')


if __name__ == '__main__':
    main()
