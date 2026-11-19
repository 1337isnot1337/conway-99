"""Save every high-graph decoration in the independently counted domain."""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import signal
import time

import numpy as np

import grid_free_order10_high_mask_graph_audit as literal
import grid_free_order10_high_mask_graph_patterns as patterns


ROOT, LOGS = patterns.ROOT, patterns.LOGS
PATTERNS = LOGS / 'order10-high-mask-graph-patterns.json'
PATTERNS_SHA = '86248876874c7b3ded078aec9e189de6f9728302137bb857ffe1500ad519400b'
PATTERN_SOURCE_SHA = '9e5714d7570536c347159072456aae2b6bf2d6e90c71a0ae2e58a018f69ca829'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enumerate_graphs(masks):
    rows = patterns.adjacency(masks, 0)
    assert literal.valid(rows)
    pairs = [(a, b) for a, b in combinations(range(len(masks)), 2)
             if (masks[a] & masks[b]).bit_count() <= 1]
    codes = []

    def search(at, code):
        if at == len(pairs):
            codes.append(code)
            return
        search(at+1, code)
        a, b = pairs[at]
        rows[6+a] |= 1 << (6+b)
        rows[6+b] |= 1 << (6+a)
        if literal.valid(rows):
            search(at+1, code | (1 << at))
        rows[6+a] &= ~(1 << (6+b))
        rows[6+b] &= ~(1 << (6+a))

    search(0, 0)
    assert len(codes) == len(set(codes))
    assert all(0 <= code < (1 << len(pairs)) for code in codes)
    return pairs, sorted(codes)


def prepare(output, arrays_path):
    assert not output.exists() and not arrays_path.exists()
    started = time.monotonic()
    assert sha(PATTERNS) == PATTERNS_SHA
    assert sha(Path(patterns.__file__)) == PATTERN_SOURCE_SHA
    assert sha(Path(literal.__file__)) == patterns.LITERAL_SOURCE_SHA
    for path, expected in ((patterns.SCOPE, patterns.SCOPE_SHA), (patterns.RAW, patterns.RAW_SHA),
                           (patterns.AUDIT, patterns.AUDIT_SHA)):
        assert sha(path) == expected
    scope = json.loads(patterns.SCOPE.read_text())
    raw = json.loads(patterns.RAW.read_text())
    all_codes, offsets, records = [], [0], []
    edge_tables = np.full((249, 30, 2), 255, dtype=np.uint8)
    for atom, counted in zip(scope['representatives'], raw['records']):
        identifier = atom['atom_orbit']
        assert identifier == len(records) == counted['atom_orbit']
        pairs, codes = enumerate_graphs(atom['selected_high_masks'])
        assert len(pairs) == atom['eligible_edge_count'] == counted['eligible_edges']
        histogram = Counter(code.bit_count() for code in codes)
        assert [histogram[e] for e in range(len(pairs)+1)] == counted['edge_histogram']
        assert len(codes) == counted['graphs']
        if pairs:
            edge_tables[identifier, :len(pairs)] = pairs
        all_codes.extend(codes)
        offsets.append(len(all_codes))
        records.append({'atom_orbit': identifier, 'graphs': len(codes),
                        'offset_start': offsets[-2], 'offset_end': offsets[-1],
                        'eligible_edge_count': len(pairs),
                        'selected_high_masks': atom['selected_high_masks']})
        if len(records) % 32 == 0:
            print(json.dumps({'atom_orbits_saved': len(records), 'graph_codes': len(all_codes),
                              'seconds': time.monotonic()-started}), flush=True)
    assert len(records) == 249 and len(all_codes) == raw['graphs'] == 157711
    arrays = {'graph_codes': np.asarray(all_codes, dtype='<u4'),
              'atom_offsets': np.asarray(offsets, dtype='<u4'),
              'edge_tables': edge_tables}
    np.savez_compressed(arrays_path, **arrays)
    report = {'status': 'complete explicit high-graph domain; all per-atom counts match both censuses',
              'complete': True, 'source_sha256': sha(Path(__file__)),
              'pattern_source_sha256': PATTERN_SOURCE_SHA, 'patterns_sha256': PATTERNS_SHA,
              'scope_sha256': patterns.SCOPE_SHA, 'count_sha256': patterns.RAW_SHA,
              'independent_count_sha256': patterns.AUDIT_SHA,
              'literal_adjacency_source_sha256': patterns.LITERAL_SOURCE_SHA,
              'atom_orbits': 249, 'graph_decorations': 157711, 'records': records,
              'graph_code_order': 'lexicographic eligible unordered high pairs; increasing code within each atom',
              'pair_table_padding': 255,
              'all_graphs_distinct_within_each_atom': True,
              'every_graph_satisfies_all_literal_induced_degree_and_common_neighbor_caps': True,
              'per_atom_complete_census_counts_and_all_edge_histograms_match': True,
              'arrays': {'path': str(arrays_path.resolve().relative_to(ROOT)),
                         'bytes': arrays_path.stat().st_size, 'sha256': sha(arrays_path)},
              'array_sha256': {name: hashlib.sha256(array.tobytes(order='C')).hexdigest()
                               for name, array in arrays.items()},
              'atom_stabilizer_graph_quotient_applied': False,
              'exterior_completion_proved': False, 'optimizer_or_solver_called': False,
              'seconds': time.monotonic()-started}
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'records'}, indent=2))
    print('result_sha256', sha(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arrays', type=Path, required=True)
    args = parser.parse_args()
    def deadline(_signum, _frame):
        raise TimeoutError('complete graph-domain enumeration exceeded sixty seconds')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        prepare(args.output, args.arrays)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
