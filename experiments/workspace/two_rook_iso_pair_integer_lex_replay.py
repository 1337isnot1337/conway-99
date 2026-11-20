"""Solver-free replay of the fixed-tip lex continuation transcript."""

import argparse
import hashlib
import json
from pathlib import Path

from two_rook_iso_pair_integer_replay import replay as replay_points_and_cuts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(record):
    metadata = record['metadata']
    source = Path(__file__).with_name('two_rook_iso_pair_integer_lex.py')
    assert digest(source) == metadata['source_sha256']
    seed_path = Path(metadata['seed_record'])
    if not seed_path.is_absolute():
        seed_path = Path(__file__).resolve().parents[2]/seed_path
    assert digest(seed_path) == metadata['seed_record_sha256']
    seed = json.loads(seed_path.read_text())
    assert metadata['base_source_sha256'] == seed['metadata']['source_sha256']
    assert record['initial_cuts'] == seed['necessary_cuts']
    assert metadata['lex_clauses'] == 252 and metadata['orbit_equalities'] == 0
    for point in record['points']:
        selected = {tuple(edge) for edge in point['selected_edges']}
        for a in range(9, 81, 2):
            first = tuple(int((tip, a) in selected) for tip in range(9))
            second = tuple(int((tip, a+1) in selected) for tip in range(9))
            assert first >= second
    combined = {'metadata': seed['metadata'], 'points': seed['points']+record['points'],
                'necessary_cuts': record['initial_cuts']+record['necessary_cuts'],
                'status': record['status']}
    checked = replay_points_and_cuts(combined)
    result = {'status': 'fixed-tip lex ordering, partial points, and necessary cuts verified',
              'seed_points': len(seed['points']), 'new_points': len(record['points']),
              'new_cuts': len(record['necessary_cuts']), 'all_cuts': checked['necessary_cuts'],
              'search_status': record['status']}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    replay(json.loads(args.record.read_text()))
