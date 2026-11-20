"""Bounded exact integer-valued tests of the fifteen-flag C4 moment.

For integer L and k, (L-k)(L-k-1) is nonnegative. Every flag counts
labelled assignments, so every integer linear combination L is integer.
This checks all nonzero {-1,0,1} combinations of the twelve nonzero
nonconstant flags, up to sign. It does not describe the integer cone.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import hashlib
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path
import pickle
import time

from grid_free_order10_r8s1_scan import FullScanner


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
CACHE = LOGS/'order10-higher-flags-r4s3-blocks.pickle.gz'
WITNESS = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
EXPECTED = {CACHE: '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943',
            WITNESS: '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def form(tensor, vector, k, automorphisms):
    weights = Counter()
    def add(i, j, coefficient):
        i, j = max(i, j), min(i, j)
        row = i*(i+1)//2+j
        for p in range(tensor.indptr[row], tensor.indptr[row+1]):
            index = int(tensor.indices[p])
            weights[index] += coefficient*int(tensor.data[p])*automorphisms[index]
    support = [i for i, a in enumerate(vector) if a]
    for i in support:
        add(i, 0, -(2*k+1)*vector[i])
        for j in support:
            if j <= i:
                add(i, j, vector[i]*vector[j]*(1 if i == j else 2))
    add(0, 0, k*(k+1))
    divisor = reduce(gcd, (abs(x) for x in weights.values()), 0)
    assert divisor > 0
    return [[i, a//divisor] for i, a in sorted(weights.items()) if a], divisor


def run(catalogue, output, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    for path, expected in EXPECTED.items():
        assert digest(path) == expected
    assert digest(catalogue) == '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    point = json.loads(WITNESS.read_text())
    induced = point['induced_counts']
    payload = pickle.loads(gzip.decompress(CACHE.read_bytes()))
    root, flags, tensor = next(block for block in payload['blocks'] if block[0] == 16)
    assert len(flags) == 15 and all(flag['stabilizer'] == 1 for flag in flags)
    M = FullScanner.matrix(tensor, 15, [a*b for a, b in zip(induced, data[2])]).tolist()
    assert all(type(x) is int for row in M for x in row)
    active = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    assert all(M[i][j] == 0 for i in (1, 2) for j in range(15))
    g = M[0][0]
    assert g > 0
    checked, minimum, negatives = 0, None, []
    by_support = Counter()
    complete = True
    for size in range(1, len(active)+1):
        for support in combinations(active, size):
            for tail in product((-1, 1), repeat=size-1):
                coefficients = (1,)+tail
                first = sum(a*M[0][i] for i, a in zip(support, coefficients))
                second = sum(a*b*M[i][j] for i, a in zip(support, coefficients)
                             for j, b in zip(support, coefficients))
                k = first//g
                value = second-(2*k+1)*first+k*(k+1)*g
                minimum = value if minimum is None else min(minimum, value)
                checked += 1
                by_support[size] += 1
                if value < 0:
                    vector = [0]*15
                    for i, a in zip(support, coefficients):
                        vector[i] = a
                    terms, divisor = form(tensor, vector, k, data[2])
                    assert sum(a*induced[i] for i, a in terms)*divisor == value
                    negatives.append({'coefficients': vector, 'integer_shift': k,
                                      'value': value, 'positive_gcd': divisor,
                                      'primitive_induced_count_form': terms})
                if checked % 1024 == 0 and time.monotonic()-started > seconds:
                    complete = False
                    break
            if not complete:
                break
        if not complete:
            break
    if complete:
        assert checked == (3**12-1)//2 == 265720

    # This represents just the eight binary first/second moments exactly.
    # Each pair contributes its cross moment; remaining mass is singleton
    # or zero. No joint representation of the four other flags is claimed.
    binary = [6, 7, 9, 10, 11, 12, 13, 14]
    weights = {0: g-sum(M[0][i] for i in binary)
               +sum(M[i][j] for i, j in combinations(binary, 2))}
    for a, i in enumerate(binary):
        assert M[i][i] == M[0][i]
        weights[1 << a] = M[0][i]-sum(M[i][j] for j in binary if j != i)
        for b, j in enumerate(binary[:a]):
            weights[(1 << a) | (1 << b)] = M[i][j]
    boolean_control = all(value >= 0 for value in weights.values())
    if boolean_control:
        assert sum(weights.values()) == g
        for a, i in enumerate(binary):
            assert sum(w for mask, w in weights.items() if mask >> a & 1) == M[0][i]
            for b, j in enumerate(binary):
                assert sum(w for mask, w in weights.items()
                           if mask >> a & 1 and mask >> b & 1) == M[i][j]
    result = {'status': 'exact integer separators found' if negatives else
                       'no separator in the checked bounded integer family',
              'source_sha256': digest(Path(__file__)),
              'cache_sha256': EXPECTED[CACHE], 'witness_sha256': EXPECTED[WITNESS],
              'catalogue_sha256': digest(catalogue), 'root_type': root,
              'active_flag_indices': active, 'coefficients_allowed': [-1, 0, 1],
              'first_nonzero_coefficient_positive': True,
              'shift_rule': 'floor(E[L]/E[1]); the minimizing integer shift',
              'candidate_count': checked, 'complete': complete,
              'counts_by_support': dict(sorted(by_support.items())),
              'minimum_exact_value': minimum, 'negative_candidates': negatives,
              'eight_binary_flags': binary, 'boolean_first_second_moments_realized': boolean_control,
              'boolean_pattern_multiplicities': [[m, w] for m, w in sorted(weights.items()) if w],
              'joint_all_flag_distribution_constructed': False,
              'all_arithmetic_is_unbounded_Python_integer': True,
              'full_integer_moment_cone_exhausted': False, 'optimizer_called': False,
              'graph_constructed': False, 'seconds': time.monotonic()-started}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ['negative_candidates', 'boolean_pattern_multiplicities']}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=60)
    args = parser.parse_args()
    run(args.catalogue, args.output, args.seconds)
