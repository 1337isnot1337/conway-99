"""Replay a C4 integer moment distribution from literal graph products.

No distribution finder, optimizer, eigensystem, or reduced core matrix is
imported. All 120 distinct matrix entries are reconstructed independently.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import time

import grid_free_order10_r6s2_independent_audit as oracle


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(args):
    started = time.monotonic()
    assert not args.output.exists() and digest(args.distribution) == args.sha256
    saved = json.loads(args.distribution.read_text())
    assert saved['exact_distribution_found'] is True
    catalogue = Path('/tmp/conway99-order10-catalogue.pickle')
    witness = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
    cache = LOGS/'order10-higher-flags-r4s3-blocks.pickle.gz'
    assert digest(witness) == saved['witness_sha256'] == '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
    assert digest(cache) == saved['cache_sha256'] == '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943'
    assert digest(catalogue) == '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
    assert digest(Path(oracle.__file__)) == '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    counts = json.loads(witness.read_text())['induced_counts']
    payload = pickle.loads(gzip.decompress(cache.read_bytes()))
    root, flags, tensor = next(block for block in payload['blocks'] if block[0] == 16)
    assert len(flags) == 15 and flags[0]['size'] == 0
    binary, nonbinary = saved['binary_flag_indices'], saved['nonbinary_flag_indices']
    assert sorted([0, 1, 2]+binary+nonbinary) == list(range(15))
    weights, atoms = [], []
    for atom in saved['atoms']:
        vector, pair = atom['flag_values'], atom['weight']
        assert len(vector) == 15 and all(type(x) is int and x >= 0 for x in vector)
        assert vector[0] == 1 and vector[1] == vector[2] == 0
        assert all(vector[i] in (0, 1) for i in binary)
        assert all(vector[i] <= saved['nonbinary_integer_maximum'] for i in nonbinary)
        assert len(pair) == 2 and all(type(x) is int and x > 0 for x in pair)
        weight = Fraction(*pair)
        assert [weight.numerator, weight.denominator] == pair
        weights.append(weight)
        atoms.append(vector)
    assert len(atoms) == len(set(map(tuple, atoms))) == 75
    ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
    entries = 0
    for i in range(15):
        for j in range(i+1):
            terms, _ = oracle.direct_product(4, tuple(flags[i]['rows']), tuple(flags[j]['rows']), ids)
            row = i*(i+1)//2+j
            cached = {int(tensor.indices[k]): int(tensor.data[k])
                      for k in range(tensor.indptr[row], tensor.indptr[row+1])}
            assert terms == cached
            expected = sum(c*data[2][t]*counts[t] for t, c in terms.items())
            assert sum(w*v[i]*v[j] for w, v in zip(weights, atoms)) == expected
            entries += 1
    assert entries == 120 and sum(weights) == 16632
    result = {'status': 'independent literal reconstruction and exact full C4 integer distribution replay PASS',
              'source_sha256': digest(Path(__file__)), 'distribution_sha256': args.sha256,
              'witness_sha256': digest(witness), 'literal_oracle_sha256': digest(Path(oracle.__file__)),
              'positive_integer_valued_atoms': len(atoms), 'total_weight': [16632, 1],
              'distinct_literal_matrix_entries_reconstructed': entries,
              'full_symmetric_moment_entries_verified': 225,
              'weights_are_positive_rationals': True,
              'all_fifteen_flag_moments_included': True,
              'actual_root_configurations_enumerated': False,
              'integer_root_multiplicities_asserted': False,
              'graph_constructed': False, 'optimizer_called': False,
              'finder_imported': False, 'dense_reduction_loaded': False,
              'seconds': time.monotonic()-started}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--distribution', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    replay(parser.parse_args())
