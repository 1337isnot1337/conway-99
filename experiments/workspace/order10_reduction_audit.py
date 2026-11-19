"""Check all original order-ten equations after exact ordinary-core reduction.

The cached reduction is reused. Fixed-width arithmetic is allowed only
after exact divisibility and overflow guards. This test can expose new
linear equalities that a nonnegativity-only search would otherwise omit.
"""

import argparse
from functools import reduce
import hashlib
import json
from math import gcd
from pathlib import Path
import pickle
import time

import numpy as np

from subgraph_counts import identities


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def audit(cache):
    started = time.monotonic()
    with cache.open('rb') as stream:
        data, cores, scale, inj, induced = pickle.load(stream)
    assert len(data[0]) == 48965 and len(cores) == 549 and scale == 3628800
    assert inj.shape == induced.shape == (48965, 550)
    integral_induced = True
    ordinary_nonintegral_rows = []
    for first in range(0, len(data[0]), 256):
        last = min(len(data[0]), first+256)
        if np.any(induced[first:last] % scale):
            integral_induced = False
        remainder = inj[first:last] % np.array(data[2][first:last], dtype=object)[:, None]
        ordinary_nonintegral_rows.extend(first+int(i) for i in np.flatnonzero(np.any(remainder != 0, axis=1)))
    assert integral_induced, 'Fractional coefficient forms require a different audit path.'
    assert not ordinary_nonintegral_rows, 'Nontrivial ordinary-count congruences need explicit export.'
    del inj
    counts = (induced//scale).astype(np.int64)
    # This cast is checked against the original arbitrary-precision values.
    for first in range(0, len(data[0]), 256):
        last = min(len(data[0]), first+256)
        assert np.array_equal(counts[first:last].astype(object)*scale, induced[first:last])
    del induced
    maximum_coefficient = max(abs(int(counts.min())), abs(int(counts.max())))
    reduced_equations = set()
    checked = 0
    worst_guard = 0
    for equation in identities(data, 99, 14):
        guard = sum(abs(int(value)) for index, value in equation.items() if index)*maximum_coefficient
        guard += abs(int(equation.get(0, 0)))
        assert guard < (1 << 63)
        worst_guard = max(worst_guard, guard)
        residual = np.zeros(550, dtype=np.int64)
        for index, value in equation.items():
            if index:
                residual += int(value)*counts[index-1]
            else:
                residual[0] += int(value)
        if np.any(residual):
            values = [int(x) for x in residual]
            common = reduce(gcd, map(abs, values), 0)
            values = [x//common for x in values]
            if next(x for x in values if x) < 0:
                values = [-x for x in values]
            reduced_equations.add(tuple(values))
        checked += 1
    assert checked == 180445
    return {
        'status': 'exact order-ten reduction audit completed',
        'source_sha256': digest(Path(__file__)), 'cache_sha256': digest(cache),
        'catalogue_types': len(data[0]), 'core_coordinates': len(cores),
        'induced_count_forms_integral_coefficientwise': integral_induced,
        'ordinary_count_forms_integral_coefficientwise': not ordinary_nonintegral_rows,
        'original_equations_checked': checked,
        'distinct_nonzero_reduced_equations': len(reduced_equations),
        'nonzero_reduced_equations': [list(row) for row in sorted(reduced_equations)],
        'maximum_absolute_integer_count_coefficient': maximum_coefficient,
        'largest_per_equation_absolute_sum_bound': worst_guard,
        'fixed_width_limit': (1 << 63)-1,
        'elapsed_seconds': time.monotonic()-started,
        'scope': 'Algebraic consistency of the exact reduction, not feasibility or graph existence.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
