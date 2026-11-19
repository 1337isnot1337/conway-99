"""Literal reconstruction of the eight binary C4 flag moments.

This uses direct labelled graph products, without the cached product
constructor or core reduction. It checks a 29-pattern Boolean moment
representation of one saved count point, not a graph realization.
"""

import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import pickle
import time

import grid_free_order10_r6s2_independent_audit as oracle


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(catalogue, output):
    started = time.monotonic()
    assert not output.exists()
    result_path = LOGS/'order10-higher-flags-c4-integer-cuts.json'
    witness_path = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
    cache_path = LOGS/'order10-higher-flags-r4s3-blocks.pickle.gz'
    expected = {result_path: '1bd5949db47d251eae086e54e0ddd03ce0458cc26c98ef00e31fa1af95b8be8d',
                witness_path: '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df',
                cache_path: '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943',
                catalogue: '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057',
                Path(oracle.__file__): '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'}
    for path, sha in expected.items():
        assert digest(path) == sha
    saved = json.loads(result_path.read_text())
    assert saved['complete'] and saved['candidate_count'] == 265720
    assert not saved['negative_candidates']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    induced = json.loads(witness_path.read_text())['induced_counts']
    payload = pickle.loads(gzip.decompress(cache_path.read_bytes()))
    _, flags, tensor = next(b for b in payload['blocks'] if b[0] == 16)
    binary = saved['eight_binary_flags']
    assert binary == [6, 7, 9, 10, 11, 12, 13, 14]
    indices = [0]+binary
    ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
    moments, products = {}, {}
    for i in indices:
        for j in indices:
            if j > i:
                continue
            terms, _ = oracle.direct_product(4, tuple(flags[i]['rows']), tuple(flags[j]['rows']), ids)
            row = i*(i+1)//2+j
            cached = {int(tensor.indices[k]): int(tensor.data[k])
                      for k in range(tensor.indptr[row], tensor.indptr[row+1])}
            assert terms == cached
            products[i, j] = terms
            moments[i, j] = sum(c*data[2][t]*induced[t] for t, c in terms.items())
    assert len(products) == 45
    for i in binary:
        assert products[i, i] == products[i, 0] == {307: 1}
        assert flags[i]['stabilizer'] == 1
    weights = dict(saved['boolean_pattern_multiplicities'])
    assert len(weights) == 29 and all(type(m) is int and 0 <= m < 256 for m in weights)
    assert all(type(w) is int and w > 0 for w in weights.values())
    assert all(m.bit_count() <= 2 for m in weights)
    assert sum(weights.values()) == moments[0, 0] == 16632
    for a, i in enumerate(binary):
        assert sum(w for m, w in weights.items() if m >> a & 1) == moments[i, 0]
        for b, j in enumerate(binary[:a+1]):
            assert sum(w for m, w in weights.items() if m >> a & 1 and m >> b & 1) == moments[i, j]
    report = {'status': 'literal products, binary diagonal identities, and Boolean moment representation PASS',
              'source_sha256': digest(Path(__file__)), 'integer_scan_sha256': digest(result_path),
              'witness_sha256': digest(witness_path), 'literal_oracle_sha256': digest(Path(oracle.__file__)),
              'literal_entries_reconstructed': len(products), 'binary_identities_checked': len(binary),
              'positive_Boolean_patterns': len(weights), 'total_pattern_multiplicity': sum(weights.values()),
              'all_first_and_second_moments_match': True,
              'joint_four_nonbinary_flags_included': False, 'graph_constructed': False,
              'integer_scan_enumeration_repeated': False, 'optimizer_called': False,
              'seconds': time.monotonic()-started}
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.catalogue, args.output)
