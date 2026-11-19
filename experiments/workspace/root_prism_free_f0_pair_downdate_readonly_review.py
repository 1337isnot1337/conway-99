"""Cheap non-author source/coverage review; no pair census or solver.

Check the complete saved type-table coverage and reversal weights, scalar
overflow bounds, and the recorded allowed-minimum witness. The native and
independent NumPy classification loops were reviewed as source. This file
does not rerun their33,578,176 type combinations or certify their category
counts independently of the saved runs.
"""

import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
EXPECTED = {
    'experiments/workspace/root_prism_free_f0_pair_downdate.py':
        'a17b7c8f8a7526398fc0da6ead18da2228e27e89a85b759ff0c3b6076da9b979',
    'experiments/workspace/root_prism_free_f0_pair_downdate.cpp':
        'b4cc2fc3d2a9c363d9d14c719741d725da8e9337f40bbe1fcbfbf1e79e2fa802',
    'experiments/workspace/root_prism_free_f0_pair_downdate_independent_audit.py':
        '58b4ed968093153817b849621f97a50b838753cb6e9f8dbd30df8d7192ab0065',
    'experiments/logs/root-prism-free/f0-pair-gram-model-preparation.json.gz':
        '7b870a9df98c855f75fcd0191b5fe03589d9458ad1e3f985ba77edb066be0c59',
    'experiments/logs/root-prism-free/f0-pair-downdate-bounds.json':
        '443c87ca561fa28c343d0446afa6d65ad87ad7d1f754a54a1756e5fcca7b6dfb',
    'experiments/logs/root-prism-free/f0-pair-downdate-run01/certificate.json':
        'fe09cb1f9a6544006f05646599258e6b806e2b8156cd6a8d8e4d43695b8826b6',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(t):
    return (tuple(t[0]), tuple(t[1]), t[2], t[3], t[4], tuple(t[5]), t[6], t[7])


def review():
    for path, expected in EXPECTED.items():
        assert digest(ROOT/path) == expected
    prepared = json.loads(gzip.decompress((LOGS/'f0-pair-gram-model-preparation.json.gz').read_bytes()))
    bounds = json.loads((LOGS/'f0-pair-downdate-bounds.json').read_text())
    subject = json.loads((LOGS/'f0-pair-downdate-run01/certificate.json').read_text())
    independent_path = LOGS/'f0-pair-downdate-independent-audit.json'
    independent = json.loads(independent_path.read_text())
    assert independent['subject_certificate_sha256'] == EXPECTED['experiments/logs/root-prism-free/f0-pair-downdate-run01/certificate.json']
    assert independent['audit_source_sha256'] == EXPECTED['experiments/workspace/root_prism_free_f0_pair_downdate_independent_audit.py']
    types = prepared['bilinear_table_preparation']['type_histogram']
    lookup = {key(t): t[-1] for t in types}
    assert len(lookup) == len(types) == 36134 and sum(lookup.values()) == 480**2
    groups = defaultdict(list)
    for t in types:
        p, q = tuple(t[0]), tuple(t[1])
        assert sum(p) == sum(q) == 3 and all(0 <= x <= 2 for x in p+q)
        assert all(0 <= x <= 2 for x in t[5]) and sum(t[5]) <= 3
        groups[p, q].append(t)
        reverse = (q, p, t[3], t[2], t[4], tuple(t[5]), t[6], t[7])
        assert lookup[reverse] == t[-1]
    assert len(groups) == 49
    combinations = weighted = self_count = 0
    for (p, q), first in groups.items():
        second = groups[tuple(2-x for x in p), tuple(2-x for x in q)]
        combinations += len(first)*len(second)
        weighted += sum(t[-1] for t in first)*sum(t[-1] for t in second)
        self_count += sum(t[-1] for t in first if sum(t[5]) == 3)*sum(t[-1] for t in second if sum(t[5]) == 3)
    assert combinations == 33578176 and weighted == 39168**2 and self_count == 39168
    assert (weighted-self_count)//2 == 767046528
    native = subject['native']['native_summary']
    assert native['status'] == 'COMPLETE' and native['groups_finished'] == 49
    assert sum(native['all_nonself_ordered_counts_by_mask'])+self_count == weighted
    assert all(value % 2 == 0 for value in native['all_nonself_ordered_counts_by_mask'])
    negative = native['negative_nonself_ordered_counts_by_mask']
    assert all(value % 2 == 0 for value in negative) and sum(negative)//2 == 866448
    assert all(value == 0 for mask, value in enumerate(negative) if not mask & 2)
    D = 4577040
    low, high = -342896, 858218
    cross = [4*low-D//60-2*(D//36), 4*high-D//60+2*(D//36)]
    bound = max(map(abs, cross))**2+(D-2240036)**2
    assert cross == [-1702148, 3610868] == bounds['direct_cross_numerator_range']
    assert bound == 18499955409440 == bounds['conservative_determinant_absolute_upper'] < 2**63
    assert max(t[-1] for t in types) == 24 and 24**2*combinations < 2**63
    ia, ib = independent['allowed_pair_minimum_type_ids']
    a, b = types[ia], types[ib]
    assert all(x+y == 2 for x, y in zip(a[0], b[0]))
    assert all(x+y == 2 for x, y in zip(a[1], b[1]))
    assert sum(a[5])+sum(b[5]) <= 2
    p, q = a[0], a[1]
    nh = 2*(a[2]+b[2])+D//15-(D//36)*sum(x*x for x in p)
    nk = 2*(a[3]+b[3])+D//15-(D//36)*sum(x*x for x in q)
    cross_value = 2*(a[4]+b[4])+D//15-(D//36)*sum(x*y for x, y in zip(p, q))
    determinant = (D-nh)*(D-nk)-cross_value**2
    assert determinant == independent['allowed_pair_minimum_determinant_numerator'] == 613323123456
    assert independent['allowed_pair_zero_determinant_unordered_count'] == 0
    predicates = ROOT/subject['predicate_file']
    assert digest(predicates) == subject['predicate_file_sha256'] and gzip.decompress(predicates.read_bytes()) == b''
    return {
        'status': 'PASS: read-only source review and cheap exact coverage/overflow/witness checks',
        'review_source_sha256': digest(Path(__file__)), 'checked_hashes': EXPECTED,
        'independent_census_report_sha256': digest(independent_path),
        'component_types': len(types), 'component_ordered_pairs': 480**2,
        'complementary_profile_groups': len(groups), 'type_combinations_recounted': combinations,
        'represented_full_ordered_pairs': weighted, 'self_columns': self_count,
        'represented_distinct_unordered_pairs': (weighted-self_count)//2,
        'signed_int64_determinant_absolute_bound': bound,
        'recorded_allowed_minimum_witness_type_ids': [ia, ib],
        'recorded_witness_exact_determinant_numerator': determinant,
        'source_review': [
            'all full-column pairs correspond exactly to products of complementary component-pair types',
            'component overlap3 means equal triples; self columns are removed before division by2',
            'centered and homogeneous bilinear formulas agree because every profile sums to3',
            'intersection-profile dot product detects same-fiber cross quota-one pairs',
            'native and NumPy loops use bounded exact integer products and weighted reductions',
            'NumPy allowed means full intersection at most2, so its positive minimum is stronger than mask0 positivity',
            'empty new predicate archive yields no new constraints or component exclusion',
        ],
        'full_type_classification_rerun': False, 'global_minimum_independently_recomputed': False,
        'native_executable_called': False, 'CNF_rebuilt': False, 'solver_called': False,
        'scope': 'review of the saved component0+component0 identity-alignment census only',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = review()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
