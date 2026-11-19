"""Replay integer deficient-neighbor certificates for exterior signatures."""
import argparse
import json
from pathlib import Path
import numpy as np

from broken_grid import canonical_cases
from completion_constraints_packing import signatures


def prepare(B, domains):
    N = np.array([[int(i in S) for i in range(len(B))] for S in domains], dtype=np.int16)
    assert min(map(len, domains)) >= 2
    Q = N @ (B + np.eye(len(B), dtype=int))
    assert np.max(Q) <= 2
    return N, Q


def possible_neighbors(N, Q, source, live):
    return live & (N @ N[source] <= 1) & ((Q == 2) @ N[source] == 0) & (N @ (Q[source] == 2) == 0)


def replay(record):
    B = list(canonical_cases())[record['case']][2]
    domains = signatures(B)
    assert len(domains) == record['candidate_signatures']
    N, Q = prepare(B, domains)
    live = np.ones(len(domains), dtype=bool)
    for certificate in record['certificates']:
        source = certificate['source']
        assert live[source] and list(domains[source]) == certificate['signature']
        possible = possible_neighbors(N, Q, source, live)
        h = certificate['coordinate']
        if h < 0:
            need = 14 - len(domains[source])
            available = int(possible.sum())
        else:
            need = int(2 - Q[source, h])
            available = int(N[possible, h].sum())
        assert need == certificate['required'] and available == certificate['available']
        assert available < need
        # Each candidate neighbor can occur at most once: two copies would
        # share the source and at least two core sites.
        live[source] = False
    assert int(live.sum()) == record['survivors']
    return len(record['certificates'])


def control():
    from triangle_ball import golay
    G, B, core = golay()
    outside = sorted(set(range(len(G))) - set(core))
    domains = [tuple(map(int, np.flatnonzero(G[x, core]))) for x in outside]
    assert len(set(domains)) == len(domains)
    N, Q = prepare(B, domains)
    live = np.ones(len(domains), dtype=bool)
    for source, vertex in enumerate(outside):
        possible = possible_neighbors(N, Q, source, live)
        assert np.all(possible[G[vertex, outside].astype(bool)])
        assert np.all(N[possible].sum(0) >= 2 - Q[source])
        assert possible.sum() >= 22 - len(domains[source])
    print(json.dumps({'positive_control': 'Golay', 'triangle_core_vertices': len(core),
                      'exterior_rows_retained': len(domains), 'status': 'exact pass'}), flush=True)
    from patch_layers import patch
    from percolation_layers import seed
    P = patch(3)
    inverse = [0, 1, 5, 3, 2, 6, 7, 4]
    assert np.array_equal(P[np.ix_(inverse, inverse)], seed(2))
    assert list(np.flatnonzero(P[8])) == [2, 4]
    assert not P[8, 6] and not P[8, 7]
    print(json.dumps({'P3_cell_trigger': 'exact eight-grid isomorphism checked'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', action='store_true')
    p.add_argument('--replay', type=Path)
    args = p.parse_args()
    if args.control:
        control()
    if args.replay:
        records = json.loads(args.replay.read_text())
        total = 0
        for record in records:
            count = replay(record)
            total += count
            print(json.dumps({'case': record['case'], 'exact_signature_exclusions': count,
                              'survivors': record['survivors']}), flush=True)
        print(json.dumps({'total_exact_signature_exclusions': total}), flush=True)
