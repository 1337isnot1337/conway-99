"""Exact principal-projector filtering of the saved complete high-graph domain.

Every removal carries an integer negative vector in a literal principal
matrix. A partial scan retains every unvisited column. No count optimizer
or graph enumeration runs here.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd, lcm
from pathlib import Path
import random
import resource
import time

from flint import fmpz_mat
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
DOMAIN = LOGS / 'order10-high-mask-graph-domain.json'
DOMAIN_SHA = '39fb9f237327616f83917a15644c36a2f397d5c938720b4dff9278d4262d94f8'
MAX_SECONDS = 60


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def save(path, value):
    assert not path.exists()
    raw = json.dumps(value, indent=2).encode()+b'\n'
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def load_domain():
    assert digest(DOMAIN) == DOMAIN_SHA
    record = read(DOMAIN)
    path = ROOT / record['arrays']['path']
    assert digest(path) == record['arrays']['sha256']
    with np.load(path, allow_pickle=False) as saved:
        arrays = {name: saved[name] for name in saved.files}
    assert set(arrays) == set(record['array_sha256'])
    for name, array in arrays.items():
        assert hashlib.sha256(array.tobytes(order='C')).hexdigest() == record['array_sha256'][name]
    assert record['complete'] and len(arrays['graph_codes']) == 157711
    assert len(record['records']) == 249
    assert list(map(int, arrays['atom_offsets'])) == [r['offset_start'] for r in record['records']]+[157711]
    return record, arrays


def graph(record, arrays, full):
    atom = int(np.searchsorted(arrays['atom_offsets'], full, side='right')-1)
    item = record['records'][atom]
    masks = item['selected_high_masks']
    code = int(arrays['graph_codes'][full])
    edges = [(int(a), int(b)) for bit, (a, b) in enumerate(
        arrays['edge_tables'][atom, :item['eligible_edge_count']]) if code >> bit & 1]
    rows = [0]*(6+len(masks))
    for a, mask in enumerate(masks):
        for i in range(6):
            if mask >> i & 1:
                rows[i] |= 1 << (6+a)
                rows[6+a] |= 1 << i
    for a, b in edges:
        rows[6+a] |= 1 << (6+b)
        rows[6+b] |= 1 << (6+a)
    return atom, masks, edges, rows


def principal(rows, kind):
    n = len(rows)
    if kind == 0:
        return [[27*int(i == j)-9*((rows[i] >> j) & 1)+1 for j in range(n)] for i in range(n)]
    return [[44*int(i == j)+11*((rows[i] >> j) & 1)-2 for j in range(n)] for i in range(n)]


def schur(masks, edges, kind):
    k = len(masks)
    degrees = [m.bit_count() for m in masks]
    if kind == 0:
        Q = [[297*int(a == b)+9+3*(degrees[a]+degrees[b])
              -33*(masks[a] & masks[b]).bit_count()+degrees[a]*degrees[b]
              for b in range(k)] for a in range(k)]
        edge_coefficient = -99
    else:
        Q = [[256*int(a == b)-16-16*(masks[a] & masks[b]).bit_count()
              +4*(degrees[a]+degrees[b])-degrees[a]*degrees[b]
              for b in range(k)] for a in range(k)]
        edge_coefficient = 64
    for a, b in edges:
        Q[a][b] += edge_coefficient
        Q[b][a] += edge_coefficient
    return Q


def quadratic(Q, vector):
    return sum(x*y*Q[i][j] for i, x in enumerate(vector) for j, y in enumerate(vector))


def primitive(vector):
    scale = lcm(*(v.denominator for v in vector))
    values = [int(v*scale) for v in vector]
    divisor = gcd(*(abs(v) for v in values)) or 1
    return [v//divisor for v in values]


def exact_psd(Q):
    """Fraction-free Schur elimination with explicit treatment of zero pivots."""
    n = len(Q)
    if not n:
        return {'psd': True, 'rank': 0, 'pivots': []}
    ones = [1]*n
    value = quadratic(Q, ones)
    if value < 0:
        return {'psd': False, 'negative_vector': ones, 'quadratic_value': value}
    B, previous, eliminations, pivots = [r[:] for r in Q], 1, [], []
    for i in range(n):
        pivot = B[i][i]
        y = None
        if pivot < 0:
            y = [Fraction(0)]*n
            y[i] = Fraction(1)
        elif pivot == 0:
            j = next((j for j in range(i+1, n) if B[i][j]), None)
            if j is not None:
                off = B[i][j]
                y = [Fraction(0)]*n
                y[i] = Fraction(abs(B[j][j])//(2*abs(off))+1)
                y[j] = Fraction(-1 if off > 0 else 1)
            else:
                continue
        if y is not None:
            for at, diagonal, row in reversed(eliminations):
                y[at] = -sum(Fraction(row[j], diagonal)*y[j] for j in range(at+1, n))
            vector = primitive(y)
            value = quadratic(Q, vector)
            assert value < 0
            return {'psd': False, 'negative_vector': vector, 'quadratic_value': value}
        assert pivot > 0 and previous > 0
        eliminations.append((i, pivot, B[i][:]))
        pivots.append(pivot)
        for a in range(i+1, n):
            for b in range(a, n):
                numerator = pivot*B[a][b]-B[a][i]*B[i][b]
                assert numerator % previous == 0
                B[a][b] = B[b][a] = numerator//previous
        previous = pivot
    return {'psd': True, 'rank': len(pivots), 'pivots': pivots}


def full_vector(masks, z, kind):
    s = sum(z)
    D = sum(mask.bit_count()*value for mask, value in zip(masks, z))
    u = [sum(value for mask, value in zip(masks, z) if mask >> i & 1) for i in range(6)]
    if kind == 0:
        return [33*v-3*s-D for v in u]+[99*v for v in z]
    return [-16*v+4*s-D for v in u]+[64*v for v in z]


def controls(record, arrays):
    rng = random.Random(990610)
    matrices = [[], [[0]], [[1]], [[-1]], [[0, 1], [1, 0]], [[1, 1], [1, 1]]]
    for _ in range(200):
        n = rng.randrange(1, 6)
        Q = [[0]*n for _ in range(n)]
        for i in range(n):
            for j in range(i, n):
                Q[i][j] = Q[j][i] = rng.randrange(-4, 5)
        matrices.append(Q)
    for _ in range(100):
        n, rank = rng.randrange(1, 6), rng.randrange(1, 5)
        V = [[rng.randrange(-3, 4) for _ in range(rank)] for _ in range(n)]
        matrices.append([[sum(a*b for a, b in zip(V[i], V[j])) for j in range(n)] for i in range(n)])
    minors = 0
    for Q in matrices:
        all_nonnegative = True
        for size in range(1, len(Q)+1):
            for subset in combinations(range(len(Q)), size):
                determinant = int(fmpz_mat([[Q[i][j] for j in subset] for i in subset]).det())
                minors += 1
                all_nonnegative &= determinant >= 0
        assert exact_psd(Q)['psd'] == all_nonnegative
    selected = sorted({0, 157710} | {int(v) for v in arrays['atom_offsets'][:-1]})
    entries = lifts = 0
    for full in selected:
        _, masks, edges, rows = graph(record, arrays, full)
        for kind in (0, 1):
            P, Q = principal(rows, kind), schur(masks, edges, kind)
            for a in range(len(masks)):
                for b in range(len(masks)):
                    x, y = [P[i][6+a] for i in range(6)], [P[i][6+b] for i in range(6)]
                    if kind == 0:
                        subtraction = Fraction(sum(u*v for u, v in zip(x, y)), 27)-Fraction(sum(x)*sum(y), 891)
                        expected = Fraction(Q[a][b], 11)
                    else:
                        subtraction = Fraction(sum(u*v for u, v in zip(x, y)), 44)+Fraction(sum(x)*sum(y), 704)
                        expected = Fraction(11*Q[a][b], 64)
                    assert P[6+a][6+b]-subtraction == expected
                    entries += 1
            z = [rng.randrange(-3, 4) for _ in masks]
            v = full_vector(masks, z, kind)
            assert quadratic(P, v) == (891 if kind == 0 else 704)*quadratic(Q, z)
            lifts += 1
    rook = [sum(1 << j for j in range(9) if i != j and (i//3 == j//3 or i%3 == j%3)) for i in range(9)]
    assert all(exact_psd(principal(rook, kind))['psd'] for kind in (0, 1))
    K5 = [31 ^ (1 << i) for i in range(5)]
    assert quadratic(principal(K5, 0), [1]*5) == -20
    return {'independent_principal_minor_matrices': len(matrices), 'literal_principal_minors': minors,
            'exact_schur_entries': entries, 'full_integer_lifts': lifts,
            'rook_both_projectors_psd': True, 'K5_positive_projector_negative': True,
            'production_domain_scan_called': False}


def prepare(output):
    started = time.monotonic()
    record, arrays = load_domain()
    result = {'status': 'principal-projector domain filter prepared; no full scan',
              'source_sha256': digest(Path(__file__)), 'domain_sha256': DOMAIN_SHA,
              'domain_arrays_sha256': record['arrays']['sha256'], 'full_columns': 157711,
              'maximum_schur_order': 10, 'projectors': ['27I-9B+J', '44I+11B-2J'],
              'scaled_schur_forms': ['297I-99H+9J+3(d1T+1dT)-33M^TM+ddT',
                                     '256I+64H-16J-16M^TM+4(d1T+1dT)-ddT'],
              'maximum_scan_seconds': MAX_SECONDS,
              'unvisited_columns_retained_on_timeout': True,
              'every_removed_column_requires_full_integer_negative_vector': True,
              'controls': controls(record, arrays), 'optimizer_called': False,
              'seconds': time.monotonic()-started}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    print('preparation_sha256', digest(output), flush=True)


def scan(preparation, output):
    prepared = read(preparation)
    assert prepared['source_sha256'] == digest(Path(__file__)) and prepared['domain_sha256'] == DOMAIN_SHA
    assert prepared['maximum_scan_seconds'] == MAX_SECONDS
    record, arrays = load_domain()
    started = time.monotonic()
    rejects, ranks, checked = [], [[0]*11, [0]*11], 0
    for full in range(157711):
        if time.monotonic()-started >= MAX_SECONDS:
            break
        atom, masks, edges, rows = graph(record, arrays, full)
        for kind in (0, 1):
            check = exact_psd(schur(masks, edges, kind))
            if check['psd']:
                ranks[kind][check['rank']] += 1
                continue
            z = check['negative_vector']
            v = full_vector(masks, z, kind)
            value = quadratic(principal(rows, kind), v)
            assert value == (891 if kind == 0 else 704)*check['quadratic_value'] < 0
            rejects.append({'full_column': full, 'atom_orbit': atom, 'projector': kind,
                            'integer_schur_vector': z, 'schur_quadratic': check['quadratic_value'],
                            'full_quadratic': value})
            break
        checked += 1
        if checked % 8192 == 0:
            print(json.dumps({'checked': checked, 'removed': len(rejects), 'seconds': time.monotonic()-started}), flush=True)
    removed = {r['full_column'] for r in rejects}
    kept = [j for j in range(157711) if j not in removed]
    result = {'status': 'complete exact principal-projector filter' if checked == 157711 else 'partial exact filter; unvisited columns retained',
              'complete': checked == 157711, 'source_sha256': digest(Path(__file__)),
              'preparation_sha256': digest(preparation), 'domain_sha256': DOMAIN_SHA,
              'domain_arrays_sha256': record['arrays']['sha256'], 'checked_full_columns': checked,
              'rejected_full_columns': len(rejects), 'retained_full_columns': len(kept),
              'unvisited_columns_retained': 157711-checked, 'retained_columns': kept,
              'rejection_witnesses': rejects, 'accepted_projector_rank_histograms': ranks,
              'optimizer_called': False, 'unrestricted_nonexistence_proved': False,
              'seconds': time.monotonic()-started, 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('retained_columns', 'rejection_witnesses')}, indent=2), flush=True)
    print('result_sha256', digest(output), flush=True)


def replay(preparation, result_path, output):
    prepared, result = read(preparation), read(result_path)
    assert prepared['source_sha256'] == result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation)
    assert result['domain_sha256'] == DOMAIN_SHA
    record, arrays = load_domain()
    rejected = set()
    for item in result['rejection_witnesses']:
        full, kind = item['full_column'], item['projector']
        assert type(full) is int and full not in rejected and 0 <= full < result['checked_full_columns']
        assert kind in (0, 1)
        atom, masks, edges, rows = graph(record, arrays, full)
        assert atom == item['atom_orbit']
        z = item['integer_schur_vector']
        assert len(z) == len(masks) and all(type(v) is int for v in z)
        v = full_vector(masks, z, kind)
        value = quadratic(principal(rows, kind), v)
        assert value == item['full_quadratic'] == (891 if kind == 0 else 704)*item['schur_quadratic'] < 0
        rejected.add(full)
    assert len(rejected) == result['rejected_full_columns']
    kept = [j for j in range(157711) if j not in rejected]
    assert kept == result['retained_columns'] and len(kept) == result['retained_full_columns']
    assert set(range(result['checked_full_columns'], 157711)) <= set(kept)
    report = {'status': 'PASS: every removed graph has a literal full-matrix integer negative vector',
              'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
              'result_sha256': digest(result_path), 'removed_graphs_checked': len(rejected),
              'retained_graphs': len(kept), 'unvisited_graphs_retained': result['unvisited_columns_retained'],
              'all_actual_graphs_remain_covered_by_necessary_projector_condition': True,
              'positive_classification_repeated': False, 'optimizer_called': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'scan', 'replay'))
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output)
    elif args.command == 'scan':
        scan(args.preparation, args.output)
    else:
        replay(args.preparation, args.result, args.output)
