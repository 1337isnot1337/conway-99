"""Read-only exact inspection of archived prism-count relaxation witnesses.

No catalogue is regenerated and no solver is called. The archived count
witnesses are re-evaluated in the existing exact order-nine reduction.
The old theta log is identified separately from a fresh coefficient replay.
"""

import argparse
import ast
import gzip
import hashlib
from itertools import combinations
import json
from math import comb
from numbers import Integral
from pathlib import Path
import pickle

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal_after(path, marker):
    matches = [line.split(marker, 1)[1] for line in path.read_text().splitlines() if marker in line]
    assert len(matches) == 1
    return ast.literal_eval(matches[0])


def generate():
    paths = {
        'cache': ROOT/'experiments/workspace/moments-order9.pickle',
        'order8_log': ROOT/'experiments/logs/moments-and-counts/core8.log',
        'order9_log': ROOT/'experiments/logs/moments-and-counts/core9.log',
        'theta_log': ROOT/'experiments/logs/eigenlattices/nine-max-integrality.log',
        'grid_free_certificate': ROOT/'experiments/logs/moments-and-counts/grid-free-core9-certificate.json.gz',
    }
    with paths['cache'].open('rb') as stream:
        graphs, levels, automorphisms, cores, scale, inj, induced = pickle.load(stream)
    assert len(graphs) == 6535 and len(cores) == 57
    assert all(isinstance(c, Integral) for matrix in (inj, induced) for c in matrix.flat)
    inj, induced = inj.astype(object), induced.astype(object)
    prism_index = cores[0]
    prism = graphs[prism_index]
    assert len(prism) == 6 and all(row.bit_count() == 3 for row in prism)
    triangles = [triple for triple in combinations(range(6), 3)
                 if all(prism[a] >> b & 1 for a, b in combinations(triple, 2))]
    assert len(triangles) == 2 and set(triangles[0]).isdisjoint(triangles[1])
    assert list(inj[prism_index]) == [0, automorphisms[prism_index]]+[0]*56
    assert list(induced[prism_index]) == [0, scale]+[0]*56

    def check(point, order):
        x = np.array(point, dtype=object)
        assert len(x) == 58 and x[0] == 1 and all(type(v) is int for v in point)
        raw, embeddings = induced@x, inj@x
        indices = [i for i, graph in enumerate(graphs) if len(graph) <= order]
        assert all(raw[i] >= 0 and raw[i] % scale == 0 for i in indices)
        assert all(embeddings[i] >= 0 and embeddings[i] % automorphisms[i] == 0 for i in indices)
        for n, level in enumerate(levels[:order+1]):
            assert sum(raw[i]//scale for i in level) == comb(99, n)
        assert raw[prism_index]//scale == embeddings[prism_index]//automorphisms[prism_index] == point[1]
        return {'order': order, 'cached_induced_forms_checked': len(indices),
                'nonnegative_integral_induced_counts': True,
                'ordinary_count_divisibility': True, 'subset_totals_exact': True,
                'prism_count': point[1]}

    old8 = literal_after(paths['order8_log'], 'core counts ')
    old9 = literal_after(paths['order9_log'], 'core counts ')
    assert len(old8) == 9 and len(old9) == 57
    assert [i for i in cores if len(graphs[i]) <= 8] == cores[:9]
    checks8 = check([1]+old8+[0]*48, 8)
    checks9 = check([1]+old9, 9)
    assert checks8['prism_count'] == checks9['prism_count'] == 0
    current = json.loads(gzip.decompress(paths['grid_free_certificate'].read_bytes()))
    current_point = current['core_point_with_constant']
    assert current_point[1] == 326
    current_count = check(current_point, 9)
    theta = literal_after(paths['theta_log'], 'free integer counts ')
    assert theta['prism'] == 0 and theta['$constant'] == 1
    return {'status': 'archived base count witnesses permit zero prisms',
            'input_sha256': {key: digest(path) for key, path in paths.items()},
            'source_sha256': digest(Path(__file__)),
            'prism_core_index': prism_index, 'prism_core_rows': list(prism),
            'ordinary_and_induced_prism_coordinate_agree': True,
            'order8': checks8, 'order9': checks9,
            'order9_nonzero_core_coordinates': [[i, value] for i, value in enumerate(old9) if value],
            'current_grid_free_count_point': current_count,
            'current_grid_free_point_is_not_a_prism_lower_bound': True,
            'theta_archived_free_integer_coordinates': theta,
            'theta_current_coefficient_replay_performed': False,
            'theta_scope': 'archived order20 maximal single-coordinate relaxation; existing log records exact integer verification with prism=0',
            'limitations': 'Cached count forms were replayed, not the extension catalogue or all flag/PSD blocks; no new theta system was reconstructed.',
            'solver_called': False, 'catalogue_regenerated': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = generate()
    if args.write:
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert json.loads(args.certificate.read_text()) == result
    print(json.dumps(result), flush=True)
