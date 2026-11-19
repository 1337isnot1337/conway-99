"""Exclude three missing passive cells and the remaining twelve-grid supports."""

import argparse
from collections import Counter
from pathlib import Path
import subprocess
from tempfile import TemporaryFile

import numpy as np
from flint import fmpz_mat

from central_grid_neighborhood import PAIRS, gram_possible
from root_cell_profiles import AXIS_PAIRS, RootCells
from thirteen_grid_supports import bipartite_components, unlabelled_graphs
from two_missing_grid_neighbors import near_completions, representatives


SHAPES = {
    'star': (((0, 1), (0, 2), (0, 3)), 141696, 6376, 19471),
    'triangle': (((0, 1), (0, 2), (1, 2)), 177300, 4636, 11560),
    'path': (((0, 1), (1, 2), (2, 3)), 45993, 6840, 164653),
    'separate edge': (((0, 1), (0, 2), (3, 4)), 41060, 3167, 23068),
}


def possible_gram(matrix):
    if np.any(matrix < 0):
        return False
    values, vectors = np.linalg.eigh(matrix)
    if values[0] >= -1e-8:
        return True
    # The numerical direction only proposes a witness. Reject on its integer
    # quadratic form, falling back to an exact polynomial if rounding fails.
    for scale in (8, 32, 128, 512, 2048, 8192, 32768):
        x = np.rint(scale*vectors[:, 0]).astype(np.int64)
        if sum(int(a)*int(b) for a, b in zip(x, matrix@x)) < 0:
            return False
    return gram_possible(matrix)


def far_graphs(executable, cases, pairs):
    with TemporaryFile(mode='w+') as source:
        print(*(a for pair in pairs for a in pair), file=source)
        for i, case in enumerate(cases):
            print(i, *(value for row in case[3:] for value in row), file=source)
        source.seek(0)
        with subprocess.Popen([str(executable)], stdin=source, stdout=subprocess.PIPE, text=True) as run:
            shifts = np.arange(44, dtype=np.uint64)
            for line in run.stdout:
                fields = line.split()
                assert len(fields) == 45
                masks = np.array(fields[1:], dtype=np.uint64)
                matrix = ((masks[:, None] >> shifts) & 1).astype(np.int64)
                yield cases[int(fields[0])], matrix
            if run.wait() != 0:
                raise RuntimeError('the far-graph enumerator failed')


def verify_shape(executable, name):
    missing, assignments, classes, expected = SHAPES[name]
    pairs = missing+tuple(pair for pair in PAIRS if pair not in missing)
    neighbors = [tuple(i for i, other in enumerate(pairs) if not set(pair) & set(other))
                 for pair in pairs]
    cases = list(representatives(pairs, neighbors, assignments, missing=(0, 1, 2)))
    assert len(cases) == classes
    count = Counter()
    for case, matrix in far_graphs(executable, cases, pairs):
        count['far graphs'] += 1
        quota = 12*np.eye(44, dtype=int)+2-matrix-matrix@matrix
        for full in near_completions(case, matrix, quota, pairs, missing_count=3,
                                     gram_test=possible_gram):
            count['near labelings'] += 1
            residual = 12*np.eye(59, dtype=int)+2-full-full@full
            if possible_gram(residual) and gram_possible(residual):
                assert fmpz_mat(residual.tolist()).rank() > 40
    assert count['far graphs'] == expected
    print(f'{name}: {assignments} assignments, {classes} classes, {dict(count)}, no extension.',
          flush=True)


def verify_twelve_supports():
    counts = Counter()
    for edges in unlabelled_graphs():
        if len(edges) != 9:
            continue
        counts['missing graphs'] += 1
        missing = tuple(sorted(edges))
        if any(sum(not set(e) & set(f) for f in missing) < 4 for e in set(AXIS_PAIRS)-set(missing)):
            continue
        counts['four disjoint missing'] += 1
        if len({v for e in missing for v in e}) < 6:
            continue
        components = bipartite_components(missing)
        if any(bipartite_components(missing[:i]+missing[i+1:]) != components for i in range(9)):
            continue
        counts['supports'] += 1
        model = RootCells(missing)
        assert any(not model.cell_options(i) for i in range(21))
    assert counts == {'missing graphs': 131, 'four disjoint missing': 11, 'supports': 2}
    print('Both remaining twelve-grid supports have an empty four-vertex cell domain.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('enumerator', type=Path)
    parser.add_argument('--shape', choices=SHAPES)
    args = parser.parse_args()
    for shape in ([args.shape] if args.shape else SHAPES):
        verify_shape(args.enumerator.resolve(), shape)
    if not args.shape:
        verify_twelve_supports()
