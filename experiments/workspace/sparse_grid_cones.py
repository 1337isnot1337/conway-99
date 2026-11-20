"""Exact exterior Gram checks with four missing cells opposite a rooted grid."""

import argparse
from pathlib import Path
import subprocess
from tempfile import TemporaryFile

from flint import fmpz_mat
import numpy as np

from central_grid_neighborhood import CHARACTERS, PAIRS, gram_possible
from two_missing_grid_neighbors import representatives


# Missing pairs, labeled grid assignments, symmetry classes, simultaneous near labelings.
SHAPES = {
    'cycle': (((0, 1), (1, 2), (2, 3), (0, 3)), 8009, 409, 120),
    'star': (((0, 1), (0, 2), (0, 3), (0, 4)), 97336, 1757, 1136),
    'paw': (((0, 1), (0, 2), (1, 2), (0, 3)), 29544, 4233, 206),
    'path': (((0, 1), (1, 2), (2, 3), (3, 4)), 19411, 2947, 980),
    'triangle and edge': (((0, 1), (1, 2), (0, 2), (3, 4)), 59100, 1596, 32),
    'fork': (((0, 1), (0, 2), (0, 3), (3, 4)), 22600, 3253, 196),
}


def full_adjacency(fields, pairs):
    assert len(fields) == 50
    bits = np.arange(44, dtype=np.uint64)
    full = np.zeros((59, 59), dtype=np.int64)
    rows = np.array(fields[1:45], dtype=np.uint64)
    full[:44, :44] = (rows[:, None] >> bits) & 1
    for a, mask in enumerate(fields[45:]):
        positive = (np.uint64(mask) >> bits) & np.uint64(1)
        full[:44, 44+2*a] = positive
        for i, e in enumerate(pairs):
            if a in e:
                full[4*i:4*i+4, 45+2*a] = 1-positive[4*i:4*i+4]
    for a in range(2):
        for x, sign in enumerate(CHARACTERS[a+1]):
            full[40+x, 54+2*a+int(sign < 0)] = 1
    full[44:58, :44] = full[:44, 44:58].T
    for a in range(44, 58, 2):
        full[a, a+1] = full[a+1, a] = 1
    full[44:58, 58] = full[58, 44:58] = 1
    assert np.array_equal(full, full.T) and not np.any(np.diag(full))
    return full


def verify(executable, name):
    missing, assignments, classes, expected_labelings = SHAPES[name]
    pairs = missing + tuple(e for e in PAIRS if e not in missing)
    neighbors = [tuple(j for j, other in enumerate(pairs) if not set(e) & set(other))
                 for e in pairs]
    slots = tuple(range(len(missing)))
    cases = representatives(pairs, neighbors, assignments, missing=slots)
    with TemporaryFile(mode='w+') as source:
        print(*(a for e in pairs for a in e), file=source)
        count = 0
        for case in cases:
            print(count, *(p for row in case[len(missing):] for p in row), file=source)
            count += 1
        assert count == classes
        source.seek(0)
        command = [str(executable), str(len(missing))]
        if name == 'cycle':
            command.append('--four-cycle')
        if name in ('cycle', 'path', 'star', 'triangle and edge'):
            command.append('--signs-first')
        with subprocess.Popen(command, stdin=source, stdout=subprocess.PIPE, text=True) as run:
            labelings = 0
            for line in run.stdout:
                fields = list(map(int, line.split()))
                case = fields[0]
                if name == 'cycle':
                    case, profile = divmod(case, 19)
                    assert profile == 9  # Only zero deviation reaches the Gram test.
                assert 0 <= case < count
                full = full_adjacency(fields, pairs)
                residual = 12*np.eye(59, dtype=np.int64)+2-full-full@full
                if gram_possible(residual):
                    assert fmpz_mat(residual.tolist()).rank() > 40, (name, fields[0])
                labelings += 1
            if run.wait():
                raise RuntimeError('the cone enumerator failed')
    assert labelings == expected_labelings
    print(f'{name}: {assignments} assignments, {classes} classes, {labelings} near labelings, '
          'no extension.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('enumerator', type=Path)
    parser.add_argument('--shape', choices=SHAPES)
    args = parser.parse_args()
    for shape in ([args.shape] if args.shape else SHAPES):
        verify(args.enumerator.resolve(), shape)
