"""Find and exactly replay a finite integer distribution for C4 moments.

The eight binary coordinates use the saved zero/singleton/pair patterns.
The four other coordinates range from zero to a bounded integer maximum.
This finite moment representation has no graph-realization claim.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations_with_replacement, product
import json
from pathlib import Path
import pickle
import time

import numpy as np
from scipy.optimize import linprog
import sympy as sp
from threadpoolctl import threadpool_limits

from grid_free_order10_r8s1_scan import FullScanner


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    started = time.monotonic()
    assert not args.output.exists() and args.maximum in (3, 5)
    catalogue = Path('/tmp/conway99-order10-catalogue.pickle')
    witness = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
    scan = LOGS/'order10-higher-flags-c4-integer-cuts.json'
    cache = LOGS/'order10-higher-flags-r4s3-blocks.pickle.gz'
    expected = {catalogue: '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057',
                witness: '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df',
                scan: '1bd5949db47d251eae086e54e0ddd03ce0458cc26c98ef00e31fa1af95b8be8d',
                cache: '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943'}
    for path, value in expected.items():
        assert digest(path) == value
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    counts = json.loads(witness.read_text())['induced_counts']
    payload = pickle.loads(gzip.decompress(cache.read_bytes()))
    _, flags, tensor = next(block for block in payload['blocks'] if block[0] == 16)
    M = FullScanner.matrix(tensor, len(flags), [a*b for a, b in zip(data[2], counts)]).tolist()
    boolean = json.loads(scan.read_text())
    binary = boolean['eight_binary_flags']
    patterns = boolean['boolean_pattern_multiplicities']
    nonbinary = [3, 4, 5, 8]
    grid = list(product(range(args.maximum+1), repeat=4))
    count = len(patterns)*len(grid)
    monomials = [(i,) for i in range(4)]
    monomials += list(combinations_with_replacement(range(4), 2))
    cross = list(product(range(4), range(8)))
    rows = len(patterns)+len(monomials)+len(cross)
    assert rows == 75
    matrix = np.zeros((rows, count), dtype=np.int64)
    target = [weight for _, weight in patterns]
    target += [M[nonbinary[item[0]]][0] if len(item) == 1 else
               M[nonbinary[item[0]]][nonbinary[item[1]]] for item in monomials]
    target += [M[nonbinary[i]][binary[j]] for i, j in cross]
    for p, (mask, _) in enumerate(patterns):
        for q, point in enumerate(grid):
            column = p*len(grid)+q
            matrix[p, column] = 1
            for j, item in enumerate(monomials, len(patterns)):
                matrix[j, column] = point[item[0]] if len(item) == 1 else point[item[0]]*point[item[1]]
            for j, (i, b) in enumerate(cross, len(patterns)+len(monomials)):
                matrix[j, column] = point[i]*((mask >> b) & 1)
    result = {'source_sha256': digest(Path(__file__)), 'witness_sha256': digest(witness),
              'cache_sha256': digest(cache), 'binary_patterns_sha256': digest(scan),
              'rows': rows, 'columns': count, 'matrix_bytes': matrix.nbytes,
              'nonbinary_flag_indices': nonbinary, 'nonbinary_integer_maximum': args.maximum,
              'binary_flag_indices': binary, 'seconds_limit': 30,
              'exact_distribution_found': False, 'graph_constructed': False,
              'actual_root_configurations_enumerated': False}
    solve_started = time.monotonic()
    with threadpool_limits(limits=1):
        numerical = linprog(np.zeros(count), A_eq=matrix, b_eq=target,
                            bounds=(0, None), method='highs-ds',
                            options={'time_limit': 30, 'presolve': True})
    result.update(numerical_status=int(numerical.status), numerical_message=numerical.message,
                  numerical_seconds=time.monotonic()-solve_started)
    if numerical.success:
        support = np.flatnonzero(numerical.x > 1e-8).tolist()
        result['numerical_positive_support'] = len(support)
        exact_matrix = sp.Matrix(matrix[:, support].tolist())
        try:
            weights, parameters = exact_matrix.gauss_jordan_solve(sp.Matrix(target))
            assert parameters.rows == 0
            rational = [Fraction(int(w.p), int(w.q)) for w in weights]
            assert all(w > 0 for w in rational)
            atoms = []
            for column, weight in zip(support, rational):
                p, q = divmod(column, len(grid))
                mask = patterns[p][0]
                vector = [0]*15
                vector[0] = 1
                for i, value in zip(nonbinary, grid[q]):
                    vector[i] = value
                for b, i in enumerate(binary):
                    vector[i] = (mask >> b) & 1
                atoms.append({'flag_values': vector,
                              'weight': [weight.numerator, weight.denominator]})
            for i in range(15):
                for j in range(15):
                    assert sum(w*atom['flag_values'][i]*atom['flag_values'][j]
                               for w, atom in zip(rational, atoms)) == M[i][j]
            result.update(exact_distribution_found=True, atoms=atoms,
                          exact_moment_entries_checked=225,
                          total_weight=[sum(rational).numerator, sum(rational).denominator],
                          scope='all fifteen C4 flag first/second moments as an integer-valued mixture, not actual local graphs')
        except (ValueError, AssertionError) as error:
            result['exact_reconstruction_failed'] = type(error).__name__+': '+str(error)
    result['status'] = 'exact finite integer moment distribution verified' if result['exact_distribution_found'] else 'no exact distribution certificate obtained for this bounded support'
    result['seconds'] = time.monotonic()-started
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'atoms'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--maximum', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
