"""Independently reconstruct the three cuts from the first full-family loop.

The literal graph oracle constructs every supported product. Saved tensors
are comparison targets only. The induced forms are reduced afresh with
Python integers and evaluated at the exact dyadic proposal.
"""

import argparse
from collections import Counter
from fractions import Fraction
from functools import reduce
import gzip
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_r6s2_independent_audit as oracle
import grid_free_order10_scaled as counts


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
CERTIFICATE = LOGS/'prism-zero-order10-r6s2-loop01-round0-r6s2-separation.json'
CERTIFICATE_SHA = 'fccbd4eeebba92b34f1f1fe69343633a59562f3e32817fc839aa29c490b65c19'
CACHE = LOGS/'prism-zero-order10-r6s2-blocks.pickle.gz'
CACHE_SHA = '84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c'
ORACLE_SHA = '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'
REDUCED_SHA = '0ad45482ea273b3412e8d308d47eabab366678f4a7e446e4a9f32791c563af65'
COUNTS_SHA = '12409f5ea1932d549cb69d9ca83e8cd4bd53d173b1a6ef136f9cdee6c095fc16'


def run(reduced_cache, output, seconds=120):
    assert 0 < seconds <= 300 and not output.exists()
    started = time.monotonic()
    bindings = [(CERTIFICATE, CERTIFICATE_SHA), (CACHE, CACHE_SHA),
                (Path(oracle.__file__), ORACLE_SHA), (Path(counts.__file__), COUNTS_SHA),
                (reduced_cache, REDUCED_SHA)]
    for path, expected in bindings:
        assert counts.digest(path) == expected, str(path)
    saved = json.loads(CERTIFICATE.read_text())
    proposal_path = Path(saved['proposal_path'])
    assert counts.digest(proposal_path) == saved['proposal_sha256']
    proposal = json.loads(proposal_path.read_text())['real_proposal']
    floats = [0.0]*550
    floats[0] = 1.0
    for coordinate, value in zip(proposal['active_coordinates'], proposal['ordinary_core_values']):
        floats[coordinate] = value
    assert floats == saved['point_float']
    fractions = [Fraction(value) for value in floats]
    denominator = max(value.denominator for value in fractions)
    assert all(denominator % value.denominator == 0 for value in fractions)
    numerators = [value.numerator*(denominator//value.denominator) for value in fractions]
    assert numerators == saved['point_numerators'] and denominator == saved['point_denominator']
    assert saved['exact_negative_block_count'] == saved['unique_integer_cut_count'] == 3
    data, cores, scale, raw = counts.load_reduced(reduced_cache)
    assert len(cores) == 549 and scale == 3628800
    payload = pickle.loads(gzip.decompress(CACHE.read_bytes()))
    blocks = {root: (flags, tensor) for root, flags, tensor in payload['blocks']}
    needed = sum(sum(value != 0 for value in block['integer_vector'])*
                 (sum(value != 0 for value in block['integer_vector'])+1)//2
                 for block in saved['negative_blocks'])
    assert needed == 15979
    result = {'status': 'independent product reconstruction incomplete',
              'source_sha256': counts.digest(Path(__file__)),
              'input_sha256': {str(path): sha for path, sha in bindings},
              'proposal_sha256': saved['proposal_sha256'],
              'required_blocks': 3, 'required_supported_entries': needed,
              'completed_blocks': [], 'complete': False, 'maximum_seconds': seconds,
              'producer_product_builder_called': False,
              'saved_tensor_used_only_for_comparison': True,
              'reduced_forms_reconstructed_with_Python_integers': True,
              'optimizer_called': False, 'eigensystems_computed': False,
              'PSD_feasibility_certified': False, 'graph_constructed': False}
    counts.save(output, result)

    def deadline(_signum, _frame):
        raise TimeoutError('bounded direct product reconstruction')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    timed_out = False
    try:
        ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
        assert len(ids) == 48965
        for block in saved['negative_blocks']:
            root = block['root_type']
            flags, tensor = blocks[root]
            vector = block['integer_vector']
            assert len(flags) == len(vector) == block['order']
            assert all(type(value) is int for value in vector)
            support = [i for i, value in enumerate(vector) if value]
            for i in support:
                flag = flags[i]
                graph = oracle.add_free(data[0][root], tuple(flag['masks']), flag['edge'])
                assert graph == tuple(flag['rows']) and oracle.valid(graph)
            weights = Counter()
            checked = 0
            for i in support:
                for j in support:
                    if j > i:
                        continue
                    terms, _ = oracle.direct_product(6, tuple(flags[i]['rows']), tuple(flags[j]['rows']), ids)
                    position = i*(i+1)//2+j
                    target = {int(tensor.indices[k]): int(tensor.data[k])
                              for k in range(tensor.indptr[position], tensor.indptr[position+1])}
                    assert terms == target
                    multiplier = vector[i]*vector[j]*(1 if i == j else 2)
                    for graph, multiplicity in terms.items():
                        weights[graph] += multiplier*multiplicity*data[2][graph]
                    checked += 1
            assert checked == len(support)*(len(support)+1)//2
            terms = [[index, value] for index, value in sorted(weights.items()) if value]
            common = reduce(gcd, [abs(value) for _, value in terms], 0)
            assert common == block['induced_form_gcd'] > 0
            primitive = [[index, value//common] for index, value in terms]
            assert primitive == block['primitive_induced_count_form']
            reduced = [sum(value*int(raw[index, j]) for index, value in primitive)
                       for j in range(550)]
            assert all(value % scale == 0 for value in reduced)
            reduced = [value//scale for value in reduced]
            core_gcd = reduce(gcd, map(abs, reduced), 0)
            assert core_gcd == block['core_form_gcd'] > 0
            coefficients = [value//core_gcd for value in reduced]
            cut = saved['unique_core_cuts'][block['core_cut_index']]
            assert coefficients == cut['coefficients']
            core_numerator = sum(a*x for a, x in zip(coefficients, numerators))
            assert core_numerator*core_gcd == block['primitive_induced_numerator'] < 0
            assert core_numerator*core_gcd*common == block['quadratic_numerator']
            value = Fraction(core_numerator, denominator)
            assert [value.numerator, value.denominator] == cut['exact_value_at_proposal']
            record = {'root_type': root, 'supported_flags': len(support),
                      'products_reconstructed': checked, 'induced_terms': len(primitive),
                      'exact_primitive_core_value': [value.numerator, value.denominator],
                      'all_supported_tensor_entries_match': True,
                      'induced_form_matches': True, 'core_form_matches': True,
                      'exact_negative_value_matches': True}
            result['completed_blocks'].append(record)
            counts.save(output, result)
            print(json.dumps(record), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    complete = len(result['completed_blocks']) == 3
    result.update(status='independent fresh product and core reduction replay PASS' if complete
                         else 'bounded independent replay incomplete',
                  complete=complete, timed_out=timed_out,
                  products_reconstructed=sum(item['products_reconstructed'] for item in result['completed_blocks']),
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'completed_blocks'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reduced-cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=120)
    args = parser.parse_args()
    run(args.reduced_cache, args.output, args.seconds)
