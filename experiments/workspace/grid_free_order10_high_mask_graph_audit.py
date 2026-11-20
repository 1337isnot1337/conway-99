"""Independent literal-adjacency census of all high-mask graph decorations.

The C++ census updates only affected constraints. This checker builds the
complete core-plus-high adjacency matrix and checks every pair after each
included edge. It uses a different edge order and branch order.
"""

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
import signal
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
SCOPE = LOGS / 'order10-high-mask-graph-scope.json'
PREPARATION = LOGS / 'order10-high-mask-graph-count01-preparation.json'
RAW = LOGS / 'order10-high-mask-graph-count01-raw.json'
SOURCE = ROOT / 'experiments/workspace/grid_free_order10_high_mask_graph_count.cpp'
SCOPE_SHA = '9733b52563e5b1937937b196ad9edeb738c141c2ca8041c27e501ca3f5cc2c94'
SOURCE_SHA = 'f0d73f1661629dc72998668dc16d74aa309f1bdb75c0b6b1b7b3e0d53e0e2e79'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid(rows):
    if any(row.bit_count() > 14 for row in rows):
        return False
    for a in range(len(rows)):
        for b in range(a):
            cap = 1 if rows[a] >> b & 1 else 2
            if (rows[a] & rows[b]).bit_count() > cap:
                return False
    return True


def count(masks):
    n = 6 + len(masks)
    rows = [0] * n
    for a, mask in enumerate(masks):
        rows[6+a] = mask
        for i in range(6):
            if mask >> i & 1:
                rows[i] |= 1 << (6+a)
    assert valid(rows)
    edges = [(6+a, 6+b) for a, b in combinations(range(len(masks)), 2)
             if (rows[6+a] & rows[6+b]).bit_count() <= 1]
    histogram = [0] * (len(edges)+1)
    visited = 0

    def search(at, chosen):
        nonlocal visited
        visited += 1
        if at == len(edges):
            histogram[chosen] += 1
            return
        search(at+1, chosen)
        a, b = edges[at]
        rows[a] |= 1 << b
        rows[b] |= 1 << a
        if valid(rows):
            search(at+1, chosen+1)
        rows[a] &= ~(1 << b)
        rows[b] &= ~(1 << a)

    search(0, 0)
    return histogram, visited


def controls():
    rook = [sum(1 << b for b in range(9)
                if a != b and (a//3 == b//3 or a % 3 == b % 3)) for a in range(9)]
    assert valid(rook)
    # The four-clique has two common neighbors on each edge.
    assert not valid([14, 13, 11, 7])
    # Three common neighbors on one nonedge violate the nonedge cap.
    assert not valid([28, 28, 3, 3, 3])
    return {'rook9_accepted': True, 'four_clique_rejected': True,
            'three_common_neighbors_on_a_nonedge_rejected': True}


def audit(output):
    assert not output.exists()
    started = time.monotonic()
    assert sha(SCOPE) == SCOPE_SHA and sha(SOURCE) == SOURCE_SHA
    prepared = json.loads(PREPARATION.read_text())
    assert prepared['source_sha256'] == SOURCE_SHA and prepared['scope_sha256'] == SCOPE_SHA
    assert sha(ROOT / prepared['input']) == prepared['input_sha256']
    scope, raw = (json.loads(path.read_text()) for path in (SCOPE, RAW))
    assert raw['complete'] and raw['completed_atom_orbits'] == 249
    assert len(raw['records']) == len(scope['representatives']) == 249
    report = {'status': 'independent literal census active', 'complete': False,
              'source_sha256': sha(Path(__file__)), 'count_source_sha256': SOURCE_SHA,
              'scope_sha256': SCOPE_SHA, 'raw_result_sha256': sha(RAW),
              'preparation_sha256': sha(PREPARATION), 'controls': controls()}
    records = []
    for atom, expected in zip(scope['representatives'], raw['records']):
        assert atom['atom_orbit'] == expected['atom_orbit'] == len(records)
        assert expected['complete']
        histogram, visited = count(atom['selected_high_masks'])
        assert histogram == expected['edge_histogram']
        assert sum(histogram) == expected['graphs']
        assert histogram[0] == 1
        records.append({'atom_orbit': atom['atom_orbit'], 'graphs': sum(histogram),
                        'edge_histogram': histogram, 'independent_visited_nodes': visited})
        if len(records) % 32 == 0:
            print(json.dumps({'completed_atom_orbits': len(records),
                              'seconds': time.monotonic()-started}), flush=True)
    assert sum(record['graphs'] for record in records) == raw['graphs']
    report.update(status='PASS: independent full literal-adjacency census agrees', complete=True,
                  atom_orbits=249, graph_decorations=raw['graphs'], records=records,
                  all_edge_histograms_equal=True,
                  independent_visited_nodes=sum(record['independent_visited_nodes'] for record in records),
                  graph_decorations_quotiented_by_atom_stabilizers=False,
                  exterior_completion_proved=False, optimizer_or_solver_called=False,
                  seconds=time.monotonic()-started)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'records'}, indent=2))
    print('result_sha256', sha(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    def deadline(_signum, _frame):
        raise TimeoutError('independent graph census exceeded sixty seconds')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        audit(args.output)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
