"""Five high-mask signed integer sums at every six-vertex root.

For L=sum(sign_i X_i), integrality gives E[(L-k)(L-k-1)]>=0.
All five-subsets and all sixteen signs up to global negation are retained.
The minimum over every integer shift is evaluated exactly, without LP.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations, islice, product
import json
from math import comb, gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np

import grid_free_order10_four_boolean_domains as domain


ROOT = domain.ROOT
LOGS = ROOT/'experiments/logs/moments-and-counts'
DOMAINS = LOGS/'order10-four-boolean-domains.json.gz'
DOMAINS_SHA = '5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35'
CACHE = ROOT/'experiments/workspace/induced-moments-6-1-512.pickle'
CACHE_SHA = '13808003e8f24bd47b8da6169c65a1eccc205b2bc9c3be1c8b57b588a2ba37c5'
POINT = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
SIGNS = [(1,)+tail for tail in product((-1, 1), repeat=4)]
PAIR_POSITIONS = list(combinations(range(5), 2))
LIMIT = (1 << 63)-1


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def load_domains():
    assert domain.digest(DOMAINS) == DOMAINS_SHA
    ledger = read(DOMAINS)
    assert ledger['all_allowed_high_masks_retained'] and not ledger['point_or_zero_pruning']
    assert domain.digest(CACHE) == CACHE_SHA and domain.digest(domain.CATALOGUE) == domain.CATALOGUE_SHA
    catalogue = pickle.loads(domain.CATALOGUE.read_bytes())
    blocks = {int(r): (f, t) for r, f, t in pickle.loads(CACHE.read_bytes())}
    assert len(blocks) == 55
    for record in ledger['roots']:
        root, high = record['root_type'], record['high_masks']
        if high:
            flags, tensor = blocks[root]
            rows = tuple(catalogue[0][root])
            assert [tuple(flag) for flag in flags] == [rows]+[domain.attach(rows, mask) for mask in high]
            n = len(high)+1
            assert tensor.shape == (n*(n+1)//2, 6535)
            assert max((int(i) for i in tensor.indices), default=-1) < 1224
        else:
            assert root not in blocks
    return ledger, catalogue, blocks


def controls():
    count = 0
    for signs in SIGNS:
        for bits in product((0, 1), repeat=5):
            L = sum(s*x for s, x in zip(signs, bits))
            for k in range(-6, 7):
                assert (L-k)*(L-k-1) >= 0
                assert (L-k)*(L-k-1) == L*L-(2*k+1)*L+k*(k+1)
                count += 1
    # Exact mixtures check the minimizer and negative-L normalization.
    mixtures = [([0, 1], [1, 1]), ([-4, 1, 5], [2, 5, 3]), ([2, 3], [7, 4])]
    for values, weights in mixtures:
        g = sum(weights); p = sum(v*w for v, w in zip(values, weights))
        q = sum(v*v*w for v, w in zip(values, weights)); k = p//g
        value = q-(2*k+1)*p+k*(k+1)*g
        assert value == min(q-(2*j+1)*p+j*(j+1)*g for j in range(-8, 9))
        minus = (-p)//g
        assert value == q+(2*minus+1)*p+minus*(minus+1)*g
    return {'literal_integer_polynomials_checked': count,
            'exact_mixtures_checking_all_shift_minimum_and_negation': len(mixtures)}


def preparation(ledger):
    rows = [{'root_type': r['root_type'], 'high_masks': r['high_masks'],
             'five_subsets': comb(len(r['high_masks']), 5) if len(r['high_masks']) >= 5 else 0}
            for r in ledger['roots']]
    total = sum(r['five_subsets'] for r in rows)
    assert total == 4543737
    return {'status': 'complete five-high-mask integer-sum family prepared without a point scan',
        'source_sha256': domain.digest(Path(__file__)), 'domain_certificate_sha256': DOMAINS_SHA,
        'scalar_cache_sha256': CACHE_SHA, 'catalogue_sha256': domain.CATALOGUE_SHA,
        'root_count': 62, 'high_masks': 829, 'five_subsets': total,
        'signs_up_to_global_negation': [list(s) for s in SIGNS],
        'integer_functionals': 16*total, 'all_integer_shifts_covered_by_exact_minimizer': True,
        'roots': rows, 'controls': controls(), 'maximum_seconds': 60, 'batch_size': 50000,
        'root_or_flag_pruning': False, 'count_point_loaded': False,
        'optimizer_or_eigensystem_called': False, 'new_product_tensors_generated': False}


def exact_matrix(root, high, blocks, embeddings):
    n = len(high)+1
    if not high:
        return np.asarray([[embeddings[root]]], dtype=np.int64)
    _, tensor = blocks[root]
    values = [sum(int(tensor.data[k])*embeddings[int(tensor.indices[k])]
                  for k in range(tensor.indptr[i], tensor.indptr[i+1])) for i in range(tensor.shape[0])]
    assert min(values) >= 0 and 256*max(values, default=0) <= LIMIT
    M = np.empty((n, n), dtype=np.int64)
    lower = np.tril_indices(n); M[lower] = values; M[lower[1], lower[0]] = values
    assert np.array_equal(np.diag(M)[1:], M[0, 1:])
    assert all(0 <= int(M[0, i]) <= int(M[0, 0]) for i in range(1, n))
    return M


def negative_form(root, subset, signs, k, M, blocks, automorphisms, counts, expected):
    positions = [i+1 for i in subset]
    p = sum(s*int(M[0, i]) for i, s in zip(positions, signs))
    q = sum(s*t*int(M[i, j]) for i, s in zip(positions, signs) for j, t in zip(positions, signs))
    assert q-(2*k+1)*p+k*(k+1)*int(M[0, 0]) == expected < 0
    row_coefficients = Counter({0: k*(k+1)})
    for i, s in zip(positions, signs):
        row_coefficients[domain.lower(i, 0)] += 1-(2*k+1)*s
    for (i, s), (j, t) in combinations(zip(positions, signs), 2):
        row_coefficients[domain.lower(i, j)] += 2*s*t
    tensor = blocks[root][1]
    form = Counter()
    for row, coefficient in row_coefficients.items():
        for at in range(tensor.indptr[row], tensor.indptr[row+1]):
            index = int(tensor.indices[at])
            form[index] += coefficient*int(tensor.data[at])*automorphisms[index]
    form = {i: c for i, c in sorted(form.items()) if c}
    assert sum(c*counts[i] for i, c in form.items()) == expected
    divisor = gcd(*(abs(c) for c in form.values()))
    return {'root_type': root, 'high_mask_positions': list(subset), 'signs': list(signs), 'integer_shift': k,
        'primitive_induced_count_form': [[i, c//divisor] for i, c in form.items()],
        'coefficient_gcd': divisor, 'exact_value': expected, 'primitive_value': expected//divisor,
        'independent_literal_replay_complete': False, 'optimizer_eligible': False}


def scan(prepared, output, seconds):
    started = time.monotonic()
    ledger, catalogue, blocks = load_domains()
    assert prepared == preparation(ledger)
    assert domain.digest(POINT) == POINT_SHA
    counts = read(POINT)['induced_counts']
    assert len(counts) == 48965 and all(type(c) is int and c >= 0 for c in counts)
    automorphisms = [int(a) for a in catalogue[2]]
    embeddings = [a*c for a, c in zip(automorphisms, counts)]
    result = {'source_sha256': domain.digest(Path(__file__)), 'integer_count_point_sha256': POINT_SHA,
        'preparation': prepared, 'root_records': [], 'negative_certificates': [],
        'optimizer_or_eigensystem_called': False, 'graph_existence_resolved': False}
    current, error, timeout = None, None, False
    def alarm(_sig, _frame):
        raise TimeoutError('bounded five-Boolean integer-sum scan')
    previous = signal.signal(signal.SIGALRM, alarm); signal.setitimer(signal.ITIMER_REAL, seconds)
    scan_started = time.monotonic()
    try:
        for r in prepared['roots']:
            root, high = r['root_type'], r['high_masks']; current = root
            M = exact_matrix(root, high, blocks, embeddings); g = int(M[0, 0])
            checked = negatives = zeros = 0; minimum = None; root_cuts = []
            if g == 0:
                assert not np.any(M)
                checked = zeros = 16*r['five_subsets']; minimum = 0 if checked else None
            else:
                iterator = iter(combinations(range(len(high)), 5))
                while True:
                    tuples = list(islice(iterator, prepared['batch_size']))
                    if not tuples:
                        break
                    indices = np.asarray(tuples, dtype=np.int64)+1
                    first = M[0, indices]
                    pair = [M[indices[:, i], indices[:, j]] for i, j in PAIR_POSITIONS]
                    diagonal = first.sum(axis=1)
                    for signs in SIGNS:
                        p = sum(s*first[:, i] for i, s in enumerate(signs))
                        q = diagonal.copy()
                        for values, (i, j) in zip(pair, PAIR_POSITIONS):
                            q += (2*signs[i]*signs[j])*values
                        k = p//g
                        assert np.all((-4 <= k)&(k <= 5))
                        values = q-(2*k+1)*p+k*(k+1)*g
                        least = int(values.min()); minimum = least if minimum is None else min(minimum, least)
                        checked += len(values); negatives += int(np.count_nonzero(values < 0)); zeros += int(np.count_nonzero(values == 0))
                        if least < 0 and len(root_cuts) < 4:
                            i = int(values.argmin())
                            cut = negative_form(root, tuples[i], signs, int(k[i]), M, blocks,
                                                automorphisms, counts, least)
                            cut['selected_high_masks'] = [high[j] for j in tuples[i]]
                            root_cuts.append(cut)
            assert checked == 16*r['five_subsets']
            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
            try:
                result['root_records'].append({'root_type': root, 'high_masks': len(high),
                    'five_subsets': r['five_subsets'], 'integer_functionals': checked,
                    'negative_minima': negatives, 'zero_minima': zeros, 'minimum': minimum,
                    'all_integer_shifts_covered': True, 'zero_root_matrix_checked': g == 0})
                result['negative_certificates'].extend(root_cuts); current = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    except TimeoutError:
        timeout = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)
    complete = len(result['root_records']) == 62 and not error and not timeout
    totals = {key: sum(r[key] for r in result['root_records']) for key in
              ('five_subsets', 'integer_functionals', 'negative_minima', 'zero_minima')}
    if complete:
        assert totals['integer_functionals'] == prepared['integer_functionals']
    result.update(status='complete exact five-Boolean integer-sum scan' if complete else 'UNKNOWN: incomplete integer-sum scan',
        complete_family=bool(complete), summary=totals, error=error, timed_out=timeout,
        unfinished_root=current, scan_seconds=time.monotonic()-scan_started,
        total_seconds=time.monotonic()-started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('preparation', 'root_records', 'negative_certificates')}, indent=2), flush=True)
    print('output_sha256', domain.digest(output), flush=True)
    return int(error is not None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path); parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args(); assert 0 < args.seconds <= 60
    if args.prepare:
        assert not args.preparation.exists()
        ledger, _, _ = load_domains(); prepared = preparation(ledger)
        args.preparation.write_text(json.dumps(prepared, indent=2)+'\n')
        print(json.dumps({k: v for k, v in prepared.items() if k != 'roots'}, indent=2))
    else:
        assert args.output and not args.output.exists()
        raise SystemExit(scan(read(args.preparation), args.output, args.seconds))
