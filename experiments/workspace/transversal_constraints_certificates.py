"""Integer Farkas certificates for the four universal-axis h=20 patterns.

No LP solver or floating arithmetic is used by this replay.
"""

import argparse
import json
from pathlib import Path
import numpy as np

from transversal_constraints_incidence import build, cases


DIRECTORY = Path(__file__).resolve().parents[1] / 'logs' / 'independent-sets'


def certificate(edges):
    degrees = [sum(i in e for e in edges) for i in range(7)]
    axis = degrees.index(6)
    A, b, labels, _ = build(edges, spectral=False)
    anchor_weights = np.array([5 if a == 2*axis else 3 if a % 2 == 0 else 1 for a in range(14)])
    # Use -floor, not floor of a negative number, for an odd square.
    multipliers = [-((int(anchor_weights[a]+anchor_weights[b])+1)**2//4) for a, b in labels]
    multipliers += list(map(int, np.tile(anchor_weights, 13)))
    multipliers += [-2] * 78
    y = np.array(multipliers, dtype=np.int64)
    products = A.T @ y
    assert max(products) <= 0 and b @ y == 4
    return {'h': 20, 'edges': [list(e) for e in edges], 'universal_axis': axis, 'multiplier': multipliers,
            'rows': A.shape[0], 'columns': A.shape[1], 'dot_rhs': int(b @ y),
            'max_column': int(max(products)), 'spectral_filter': False}


def run(write=False):
    count = 0
    for case, (atlas, edges) in enumerate(cases(20)):
        if not any(sum(i in e for e in edges) == 6 for i in range(7)):
            continue
        result = certificate(edges)
        result.update(case=case, atlas=atlas)
        path = DIRECTORY / f'transversal-certificate20-case{case}.json'
        if write:
            path.write_text(json.dumps(result, indent=2)+'\n')
        else:
            assert json.loads(path.read_text()) == result
        print(json.dumps({k: v for k, v in result.items() if k not in ('edges', 'multiplier')}), flush=True)
        count += 1
    assert count == 4


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    run(args.write)
