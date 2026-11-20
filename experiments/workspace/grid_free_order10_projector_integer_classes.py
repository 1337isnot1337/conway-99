"""Exact optimal shifted-integer inequalities for every outside class size.

Recover each second moment coefficientwise from the two raw projector
blocks, then test E[(n-k)(n-k-1)] at the integer minimizing shift. All
68,176 masks are retained. This uses no eigensystem or dense reduction.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import time

import grid_free_order10_projector_probe as construction
import grid_free_order10_projector_domains as domains
import grid_free_order10_projector_literal as literal
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT/'experiments/logs/moments-and-counts/order10-eight-root-projector-full01-cache/manifest.json'
CACHE_SHA = '434454d319468262ca384e00b3a251a672262c5e73f2bd7f655bfccad23794ce'
SCAN = ROOT/'experiments/logs/moments-and-counts/order10-eight-root-projector-full01.json'
SCAN_SHA = 'f56fb300b440d660a5a542b181fd44e7f6c2f331bb8f28a85e16f2fcca44c0d9'
PROBE_SHA = '0af37fafb7db4e68963fa602800e7aa3256b9cf56ef8ffd1ce4b06a48da16e7a'


def preparation():
    assert files.digest(CACHE) == CACHE_SHA and files.digest(SCAN) == SCAN_SHA
    assert files.digest(Path(construction.__file__)) == PROBE_SHA
    records, counts = construction.inputs()
    cache = json.loads(CACHE.read_text())
    assert cache['complete_root_family'] and cache['complete_block_count'] == 3664
    assert cache['root_types_completed'] == sorted(records)
    return {
        'source_sha256': files.digest(Path(__file__)),
        'cache_manifest_sha256': CACHE_SHA, 'full_scan_result_sha256': SCAN_SHA,
        'construction_source_sha256': PROBE_SHA,
        'domain_source_sha256': construction.DOMAIN_SOURCE_SHA,
        'domain_certificate_sha256': construction.DOMAIN_SHA,
        'literal_oracle_source_sha256': files.digest(Path(literal.__file__)),
        'catalogue_sha256': domains.CATALOGUE_SHA,
        'integer_witness_sha256': construction.WITNESS_SHA,
        'root_count': len(records), 'class_count': sum(r['classes'] for r in records.values()),
        'all_integer_shifts_covered_by_exact_minimizer': True,
        'zero_roots_and_all_mask_degrees_retained': True,
        'coefficientwise_division_by_seven_checked': True,
        'no_numerical_eigensystem': True, 'no_dense_reduction': True, 'no_optimizer': True,
    }


def second_moment(minus, plus, position, one):
    """N = 99 diag(p) - (11 D_minus + 9 D_plus)/7, as type forms."""
    weighted = Counter()
    for block, coefficient in ((minus, 11), (plus, 9)):
        for index, value in construction.tensor_entry(block['tensor'], position, position).items():
            weighted[index] += coefficient*value
    assert all(value % 7 == 0 for value in weighted.values())
    result = Counter({one: 99})
    for index, value in weighted.items():
        result[index] -= value//7
    result = {index: value for index, value in result.items() if value}
    assert result.get(one) == 1 and all(value == 1 for value in result.values())
    assert 1 <= len(result) <= 3
    return result


def polynomial(second, one, root, shift):
    result = Counter(second)
    result[one] -= 2*shift+1
    result[root] += shift*(shift+1)
    return {index: value for index, value in result.items() if value}


def primitive(form, automorphisms):
    terms = [[index, value*automorphisms[index]] for index, value in sorted(form.items()) if value]
    divisor = reduce(gcd, (abs(value) for _, value in terms), 0)
    assert divisor > 0
    return [[index, value//divisor] for index, value in terms], divisor


def literal_polynomial(record, mask, shift, oracle):
    rows, root = record['root_rows'], record['root_type']
    one = oracle.type_id(literal.extend(rows, [mask]))
    assert one is not None
    result = Counter({root: shift*(shift+1), one: -2*shift})
    for edge in (0, 1):
        index = oracle.type_id(literal.extend(rows, [mask, mask], edge))
        if index is not None:
            result[index] += 1
    return {index: value for index, value in result.items() if value}


def run(args, prepared):
    started = time.monotonic()
    assert prepared == preparation()
    records, counts = construction.inputs()
    assert files.digest(args.catalogue) == domains.CATALOGUE_SHA
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    assert data[1][8] == sorted(records)
    embeddings = [int(a)*c for a, c in zip(data[2], counts)]
    cache = json.loads(CACHE.read_text())
    completed, class_records, negatives = [], [], []
    shifts, outcomes, degrees = Counter(), Counter(), Counter()
    identically_zero, divisions, zero_root_classes, point_zero_classes = 0, 0, 0, 0
    oracle = None
    for part in cache['parts']:
        path = CACHE.parent/part['path']
        assert files.digest(path) == part['sha256']
        payload = pickle.loads(gzip.decompress(path.read_bytes()))
        assert payload['point_independent'] and not payload['zero_flags_or_roots_removed']
        assert payload['construction_source_sha256'] == PROBE_SHA
        assert payload['domain_certificate_sha256'] == construction.DOMAIN_SHA
        assert payload['catalogue_sha256'] == domains.CATALOGUE_SHA
        assert payload['root_types'] == part['root_types'] and payload['all_four_blocks_per_root']
        by_root = {}
        for block in payload['blocks']:
            root = block['root_type']
            record = records[root]
            assert block['masks'] == record['masks']
            expected_order = len(record['masks'])+(8 if block['family'] == 'spectral' else 0)
            assert block['order'] == expected_order
            assert block['tensor'].shape == (expected_order*(expected_order+1)//2, 48965)
            key = block['family'], block['projector']
            assert key not in by_root.setdefault(root, {})
            by_root[root][key] = block
        assert sorted(by_root) == part['root_types']
        for root in part['root_types']:
            record, blocks = records[root], by_root[root]
            assert set(blocks) == {(family, sign) for family in ('spectral','schur') for sign in ('minus','plus')}
            minus, plus = blocks['spectral','minus'], blocks['spectral','plus']
            one_types = dict(data[3][root])
            assert sorted(one_types) == record['masks']
            g = embeddings[root]
            rows = []
            assert sum(embeddings[one_types[mask]] for mask in record['masks']) == 91*g
            for position, mask in enumerate(record['masks'], 8):
                one = one_types[mask]
                second = second_moment(minus, plus, position, one)
                divisions += 1
                assert len(data[0][one]) == 9
                assert all(index == one or len(data[0][index]) == 10 for index in second)
                p = embeddings[one]
                n2 = sum(coefficient*embeddings[index] for index, coefficient in second.items())
                assert p >= 0 and n2 >= p
                if g:
                    shift = p//g
                    # The two neighboring shifts establish the global minimum
                    # of this convex quadratic over all integer shifts.
                    assert 2*((shift+1)*g-p) >= 0 and 2*(p-shift*g) >= 0
                else:
                    assert p == n2 == 0
                    shift = 0
                    zero_root_classes += 1
                form = polynomial(second, one, root, shift)
                value = n2-(2*shift+1)*p+shift*(shift+1)*g
                assert value == sum(coefficient*embeddings[index] for index, coefficient in form.items())
                degree = mask.bit_count()
                degrees[degree] += 1
                shifts[shift] += 1
                outcomes['negative' if value < 0 else 'zero' if value == 0 else 'positive'] += 1
                identically_zero += not form
                point_zero_classes += p == 0
                if value < 0:
                    if oracle is None:
                        oracle = literal.Oracle(data)
                    direct = literal_polynomial(record, mask, shift, oracle)
                    assert direct == form
                    terms, divisor = primitive(form, data[2])
                    exact = sum(coefficient*counts[index] for index, coefficient in terms)
                    assert exact*divisor == value < 0
                    negatives.append({'root_type': root, 'mask': mask, 'shift': shift,
                        'root_embedding_count': g, 'first_moment': p, 'second_moment': n2,
                        'unscaled_value': value, 'primitive_induced_count_form': terms,
                        'induced_form_gcd': divisor, 'primitive_value_at_witness': exact,
                        'independent_literal_products_rebuilt': True,
                        'core_form_reduced': False, 'optimizer_eligible': False})
                rows.append([mask, shift, p, n2, value])
            completed.append(root)
            class_records.append({'root_type': root, 'root_embedding_count': g,
                                  'class_columns': ['mask','shift','first_moment','second_moment','shifted_value'],
                                  'classes': rows})
    assert completed == data[1][8] and divisions == 68176
    table = {'format': 1, 'source_sha256': files.digest(Path(__file__)),
             'preparation_sha256': files.digest(args.preparation),
             'integer_witness_sha256': construction.WITNESS_SHA,
             'complete_root_family': True, 'complete_class_count': divisions,
             'roots': class_records}
    args.records.write_bytes(gzip.compress(json.dumps(table,separators=(',',':')).encode(),compresslevel=9,mtime=0))
    result = {
        'status': 'exact shifted-integer class inequalities passed' if not negatives else 'exact shifted-integer class separators found',
        'source_sha256': files.digest(Path(__file__)), 'preparation_sha256': files.digest(args.preparation),
        'cache_manifest_sha256': CACHE_SHA, 'integer_witness_sha256': construction.WITNESS_SHA,
        'root_count': len(completed), 'class_count': divisions, 'complete_scan': True,
        'coefficientwise_seven_divisions_checked': divisions,
        'all_integer_shifts_covered': True, 'outcomes': dict(sorted(outcomes.items())),
        'shift_histogram': dict(sorted(shifts.items())), 'mask_degree_histogram': dict(sorted(degrees.items())),
        'identically_zero_polynomials': identically_zero,
        'classes_at_zero_root_counts': zero_root_classes, 'classes_with_zero_first_moment': point_zero_classes,
        'negative_inequalities': negatives,
        'class_table_path': str(args.records), 'class_table_sha256': files.digest(args.records),
        'class_table_bytes': args.records.stat().st_size,
        'all_arithmetic_is_unbounded_Python_integer': True,
        'eigensystems_computed': False, 'dense_reduction_loaded': False, 'optimizer_called': False,
        'PSD_feasibility_claimed': False, 'graph_constructed': False,
        'seconds': time.monotonic()-started, 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    files.save(args.output, result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--records', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    if args.prepare:
        assert args.preparation is None and args.records is None
        prepared = preparation()
        files.save(args.output, prepared)
        print(json.dumps(prepared, indent=2), flush=True)
    else:
        assert args.preparation and args.records and not args.records.exists()
        run(args, json.loads(args.preparation.read_text()))
