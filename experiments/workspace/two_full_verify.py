"""Replay every interface of the two-full-axis core. A surviving core is an error."""
import argparse
from collections import Counter
from math import isqrt
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

from spoke_core_rank import core, independent_columns


def determinant(matrix):
    # Fraction-free elimination with row pivoting, on ordinary Python integers.
    a = matrix.tolist()
    sign = previous = 1
    for k in range(len(a)-1):
        pivot = next((i for i in range(k, len(a)) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign = -sign
        v = a[k][k]
        for i in range(k+1, len(a)):
            for j in range(k+1, len(a)):
                numerator = v*a[i][j]-a[i][k]*a[k][j]
                quotient, remainder = divmod(numerator, previous)
                assert remainder == 0
                a[i][j] = quotient
        previous = v
    return sign*a[-1][-1]


def reject(interface):
    matrix = core(interface)
    residual = 12*np.eye(59, dtype=int)+2-matrix-matrix@matrix
    if residual.min() < 0:
        return 'quota'
    gram = 27*np.eye(59, dtype=int)-9*matrix+1
    basis = independent_columns(gram, 1009)
    if len(basis) > 44:
        return 'rank'
    if len(basis) == 44:
        det = determinant(gram[np.ix_(basis, basis)])
        if det < 0 or isqrt(det)**2 != det:
            return 'nonsquare'
    raise AssertionError(f'Unexcluded two-full-axis interface: {interface}')


def audit_output(output):
    counts = Counter()
    summary = None
    for line in output.splitlines():
        if line.startswith('survivor '):
            neg, pos, *perms = map(int, line.split()[1:])
            assert len(perms) == 25 and neg <= 13 and pos <= 14
            counts[reject(perms)] += 1
        else:
            assert summary is None
            summary = re.fullmatch(r'(\d+) templates; retained prefixes ((?:\d+ ){4}\d+); rank survivors (\d+)', line)
            assert summary
    assert summary and int(summary[3]) == sum(counts.values())
    return (int(summary[1]), int(summary[2].split()[-1]), int(summary[3]),
            counts['quota'], counts['rank'], counts['nonsquare'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    p.add_argument('--sizes', type=int, nargs='+', default=list(range(0, 21, 2)))
    args = p.parse_args()
    script = Path(__file__).with_name('mixed_spoke_templates.py')
    print('mixed templates psd rank_pass quota rank nonsquare', flush=True)
    for size in args.sizes:
        with subprocess.Popen([sys.executable, str(script), '--group-rows', str(size)],
                              stdout=subprocess.PIPE) as source:
            result = subprocess.run([str(args.binary.resolve()), '--rank-survivors'],
                                    stdin=source.stdout, capture_output=True, text=True, check=True)
            source.stdout.close()
            if source.wait() != 0:
                raise RuntimeError('Template generation failed')
        print(size, *audit_output(result.stdout), flush=True)


if __name__ == '__main__':
    main()
