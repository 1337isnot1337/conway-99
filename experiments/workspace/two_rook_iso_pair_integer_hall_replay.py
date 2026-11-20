"""Solver-free Hall certificates, clause transport, and continuation replay."""

import argparse
from collections import deque
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path

from two_rook_iso_completion import core, rook, check_incidence, allowed_edges
from two_rook_iso_pair_integer_lex_replay import replay as replay_lex
from two_rook_tip_hall_audit import verify as verify_hall, translate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else Path(__file__).resolve().parents[2]/path


def read_artifact(path):
    packed = path.read_bytes()
    if path.name.endswith('.json.gz'):
        manifest = json.loads(path.with_name(path.name[:-8]+'-artifact.json').read_text())
        assert manifest['format'] == 'gzip-json' and manifest['compressed_file'] == path.name
        raw = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == manifest['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest() == manifest['uncompressed_sha256']
        assert len(packed) == manifest['compressed_bytes'] and len(raw) == manifest['uncompressed_bytes']
    else:
        raw = packed
    return json.loads(raw)


def replay(record):
    metadata = record['metadata']
    assert digest(Path(__file__).with_name('two_rook_iso_pair_integer_hall.py')) == metadata['source_sha256']
    assert digest(Path(__file__).with_name('two_rook_tip_hall_audit.py')) == metadata['hall_verifier_sha256']
    certificate_path = resolve(metadata['hall_certificate'])
    assert digest(certificate_path) == metadata['hall_certificate_sha256']
    certificate = json.loads(certificate_path.read_text())
    checked = verify_hall(certificate)
    assert metadata['hall_replay'] == {k: checked[k] for k in metadata['hall_replay']}
    assert metadata['hall_clauses'] == 1377 and metadata['tip_psd_cuts'] == 0

    # Reconstruct actual primary IDs independently of the SAT builder.
    rows = core()
    signatures = [(i, 9+i) for i in range(9)]
    signatures += [(i, 9+j) for i, j in product(range(9), repeat=2)
                   if i != j and not rook(i, j) for copy in range(2)]
    need = check_incidence(rows, signatures)
    variables = {edge: index+1 for index, edge in enumerate(allowed_edges(signatures, need))}
    clauses = []
    for tip in range(9):
        for mask in certificate['forbidden_masks']:
            clause = []
            for canonical in range(1, 9):
                original = 3*((canonical//3+tip//3) % 3)+(canonical % 3+tip % 3) % 3
                assert translate(original, tip) == canonical
                variable = variables[tuple(sorted((tip, original)))]
                clause.append(-variable if mask >> (canonical-1) & 1 else variable)
            clauses.append(clause)
    assert len(clauses) == 1377
    cnf_checked = False
    initial = Path(metadata['initial_cnf'])
    if initial.exists():
        assert digest(initial) == metadata['initial_cnf_sha256']
        last, count = deque(maxlen=1377), 0
        for line in initial.read_text().splitlines():
            if line.startswith(('c', 'p')) or not line.strip():
                continue
            values = [int(x) for x in line.split()]
            assert values[-1] == 0
            last.append(values[:-1])
            count += 1
        assert count == metadata['clauses'] and list(last) == clauses
        cnf_checked = True
    final_checked = False
    final = Path(record['final_cnf'])
    if cnf_checked and final.exists():
        assert digest(final) == record['final_cnf_sha256']
        assert record['final_clauses'] == metadata['clauses']+len(record['necessary_cuts'])
        with initial.open() as before, final.open() as after:
            old_header, new_header = before.readline().split(), after.readline().split()
            assert old_header[:3] == new_header[:3] == ['p', 'cnf', str(metadata['variables_with_auxiliaries'])]
            assert int(old_header[3]) == metadata['clauses']
            assert int(new_header[3]) == record['final_clauses']
            for line in before:
                assert after.readline() == line
            for cut in record['necessary_cuts']:
                a, b = cut['pair']
                terms = [variables[a, b]] if cut['edge'] else []
                for c in cut['via']:
                    terms += [variables[tuple(sorted((a, c)))], variables[tuple(sorted((b, c)))]]
                expected = sorted({-v for v in terms})+[0]
                assert [int(x) for x in after.readline().split()] == expected
            assert not after.read().strip()
        final_checked = True

    admitted = set(certificate['admitted_masks'])
    for point in record['points']:
        edges = {tuple(edge) for edge in point['tip_edges']}
        for tip in range(9):
            mask = 0
            for other in range(9):
                if other != tip and tuple(sorted((tip, other))) in edges:
                    mask |= 1 << (translate(other, tip)-1)
            assert mask in admitted
    proxy = dict(record)
    proxy['metadata'] = dict(metadata)
    proxy['metadata']['source_sha256'] = metadata['lex_source_sha256']
    replay_lex(proxy)
    result = {'status': 'Hall certificates, transported clauses, lex ordering, points, and cuts verified',
              'hall_clauses': len(clauses), 'actual_initial_cnf_checked': cnf_checked,
              'actual_final_cnf_checked': final_checked,
              'new_points': len(record['points']), 'new_cuts': len(record['necessary_cuts']),
              'search_status': record['status']}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    replay(read_artifact(args.record))
