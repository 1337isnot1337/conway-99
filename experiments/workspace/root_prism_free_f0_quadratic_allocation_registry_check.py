"""Put the three new shared-family detections in full-registry context.

No optimizer, source import, CNF build, or formula modification.  This
does not re-prove the old individual cuts; their complete frozen registry
is hash-bound.  Every reported candidate value is recomputed with ints.
"""

import argparse
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
INPUTS = {
    'f0-quadratic-allocation-preparation.json.gz': '7ab2ec935cdbbb7035a0fd95d5a7ca514aed508b7d5efbe953c5265176733589',
    'f0-quadratic-allocation-scan.json.gz': 'ba2e83a0ae513bce846f9e7765b527584b342bdd5f8d382e2625da38fad99399',
    'f0-bounded-lazy-continuation-run01/result.json': '88c4858aa36aaf3af15f4b53ce41be5c1fee3d8f2c237a49e2df026f1228bd86'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def calculate():
    loaded = {}
    for name, expected in INPUTS.items():
        assert digest(LOGS/name) == expected
        loaded[name] = read(LOGS/name)
    preparation = loaded['f0-quadratic-allocation-preparation.json.gz']
    scan = loaded['f0-quadratic-allocation-scan.json.gz']
    parent = loaded['f0-bounded-lazy-continuation-run01/result.json']
    path = ROOT/parent['individual-registry']
    assert digest(path) == parent['individual-registry_sha256']
    individual = read(path)
    assert len(individual) == 2640
    normalized_old = set()
    for cut in individual:
        terms = {cut['target']: cut['demand']}
        for a, weight in cut['weights']:
            terms[a] = terms.get(a, 0)-weight
        divisor = gcd(*(abs(c) for c in terms.values()))
        normalized_old.add(tuple(sorted((a, c//divisor) for a, c in terms.items() if c)))
    records = []
    for cut in scan['new_endpoint_allocation_cuts']:
        selected = set(cut['selected_signature_ids'])
        assert sorted(selected) == preparation['saved_candidates'][cut['candidate_index']]['selected_signature_ids']
        violations = []
        for index, old in enumerate(individual):
            value = old['demand']*int(old['target'] in selected)-sum(w for a, w in old['weights'] if a in selected)
            if value > 0:
                violations.append({'registry_index': index, 'exact_signed_value': value,
                    'normalized_predicate_sha256': old['normalized_predicate_sha256']})
        assert violations
        records.append({'candidate_index': cut['candidate_index'], 'family_index': cut['family_index'],
            'core_action_index': cut['core_action_index'], 'new_cut_predicate_sha256': cut['predicate_sha256'],
            'exact_new_cut_value': sum(c for a, c in cut['signed_coefficients'] if a in selected),
            'already_violated_individual_cuts': violations,
            'new_linear_predicate_identical_to_retained_individual_predicate':
                tuple(map(tuple, cut['signed_coefficients'])) in normalized_old})
    assert len(records) == 3 and [len(r['already_violated_individual_cuts']) for r in records] == [2, 2, 3]
    return {'status': 'exact full-registry context check PASS', 'source_sha256': digest(Path(__file__)),
        'input_hashes': INPUTS, 'individual_registry_sha256': parent['individual-registry_sha256'],
        'individual_registry_count': 2640, 'records': records,
        'historical_candidate_exclusions_added_beyond_full_retained_registry': 0,
        'strict_improvement_is_over_fixed_shared_allocations': True,
        'no_future_throughput_or_component_exclusion_claim': True, 'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_bytes(canonical(report)+b'\n')
    print(json.dumps(report, indent=2), flush=True)
