"""Separate exact dyadic proposals against the complete frozen r8,s1 cache.

Numerical eigensystems propose directions only. Every accepted direction,
count-form contraction, and 550-coordinate cut is checked with integers.
Only rows proved exactly zero at the current point are removed.
"""

from fractions import Fraction
from functools import reduce
import gzip
import json
from math import gcd, isfinite, lcm
from pathlib import Path
import pickle
import signal
import time

import numpy as np
from scipy import sparse

import grid_free_order10_scaled as counts
import grid_free_order10_r8s1 as construction


CACHE_SHA = 'aecf7411230f718c8c3879c38ad39dcdb041ed07c58a799f8b044ebd0ab5028d'
CONSTRUCTION_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def exact_point(proposal):
    saved = json.loads(proposal.read_text())
    assert saved['case_index'] == 1 and not saved['fixed_order_nine_point']
    real = saved['real_proposal']
    active = real['active_coordinates']
    assert active == [j for j in range(1, 550) if j not in (56, 57)]
    point = [0.0]*550
    point[0] = 1.0
    for j, value in zip(active, real['ordinary_core_values'], strict=True):
        point[j] = float(value)
    assert all(isfinite(value) for value in point)
    ratios = [value.as_integer_ratio() for value in point]
    denominator = lcm(*(d for _, d in ratios))
    numerators = [n*(denominator//d) for n, d in ratios]
    return point, numerators, denominator


class FullScanner:
    def __init__(self, data, raw, scale, cache_path, reduced_cache_sha):
        assert counts.digest(cache_path) == CACHE_SHA
        assert counts.digest(Path(construction.__file__)) == CONSTRUCTION_SHA
        cache = pickle.loads(gzip.decompress(cache_path.read_bytes()))
        assert cache['format'] == 2 and cache['point_independent']
        assert cache['complete_root_family'] and not cache['zero_flags_or_roots_removed']
        assert cache['construction_source_sha256'] == CONSTRUCTION_SHA
        self.data, self.raw, self.scale = data, raw, scale
        self.cache_path, self.reduced_cache_sha = cache_path, reduced_cache_sha
        self.blocks = cache['blocks']
        assert len(self.blocks) == 916
        assert [root for root, _, _ in self.blocks] == data[1][8]
        for root, masks, tensor in self.blocks:
            assert masks == [mask for mask, _ in data[3][root] if mask.bit_count() >= 3]
            assert tensor.shape == ((len(masks)+1)*(len(masks)+2)//2, 48965)
            assert tensor.data.dtype.kind == 'i' and all(v > 0 for v in tensor.data)
            assert max(np.asarray(tensor.sum(axis=1)).ravel(), default=0) <= 2
        assert raw.shape == (48965, 550) and not np.any(raw % scale)
        self.forms = sparse.csr_matrix(raw//scale)
        self.lookup = {root: (masks, tensor) for root, masks, tensor in self.blocks}

    def count_numerators(self, point_numerators):
        T = self.forms
        return [sum(int(T.data[k])*point_numerators[int(T.indices[k])]
                    for k in range(T.indptr[i], T.indptr[i+1]))
                for i in range(T.shape[0])]

    @staticmethod
    def matrix(tensor, order, embeddings):
        values = [sum(int(tensor.data[k])*embeddings[int(tensor.indices[k])]
                      for k in range(tensor.indptr[i], tensor.indptr[i+1]))
                  for i in range(tensor.shape[0])]
        M = np.empty((order, order), dtype=object)
        lower = np.tril_indices(order)
        M[lower] = values
        M[(lower[1], lower[0])] = values
        return M

    @staticmethod
    def negative(matrix):
        n = len(matrix)
        zero, active = [], []
        for i in range(n):
            diagonal = int(matrix[i, i])
            if diagonal < 0:
                vector = [0]*n
                vector[i] = 1
                return vector, diagonal, None, 0
            if diagonal == 0:
                nonzero = [j for j in range(n) if matrix[i, j]]
                if nonzero:
                    j = nonzero[0]
                    entry = int(matrix[i, j])
                    vector = [0]*n
                    vector[i] = max(1, int(matrix[j, j])//(2*abs(entry))+1)
                    vector[j] = -1 if entry > 0 else 1
                    v = np.array(vector, dtype=object)
                    value = int(v@matrix@v)
                    assert value < 0
                    return vector, value, None, len(zero)
                zero.append(i)
            else:
                active.append(i)
        assert all(not any(matrix[i, j] for j in range(n)) for i in zero)
        if not active:
            return None, None, 0.0, len(zero)
        reduced = matrix[np.ix_(active, active)]
        scales = np.sqrt(np.array([float(reduced[i, i]) for i in range(len(active))]))
        normalized = np.asarray(reduced, dtype=float)/scales[:, None]/scales[None, :]
        eigenvalues, eigenvectors = np.linalg.eigh(normalized)
        smallest = float(eigenvalues[0])
        if smallest >= -1e-8:
            return None, None, smallest, len(zero)
        direction = eigenvectors[:, 0]/scales
        direction /= max(abs(direction))
        for power in (8, 12, 20, 28, 36):
            vector = [0]*n
            for i, value in zip(active, direction):
                vector[i] = int(round(value*(2**power)))
            divisor = reduce(gcd, [abs(v) for v in vector], 0)
            if not divisor:
                continue
            vector = [v//divisor for v in vector]
            v = np.array(vector, dtype=object)
            value = int(v@matrix@v)
            if value < 0:
                return vector, value, smallest, len(zero)
        return None, None, smallest, len(zero)

    def scan(self, proposal, output, seconds=180):
        assert 0 < seconds <= 180
        started = time.monotonic()
        point, numerators, denominator = exact_point(proposal)
        result = {'source_sha256': counts.digest(Path(__file__)),
                  'proposal_path': str(proposal), 'proposal_sha256': counts.digest(proposal),
                  'full_cache_path': str(self.cache_path), 'full_cache_sha256': CACHE_SHA,
                  'reduced_cache_sha256': self.reduced_cache_sha,
                  'point_float': point, 'point_numerators': numerators, 'point_denominator': denominator,
                  'required_zero_coordinate_numerators': [[j, numerators[j]] for j in (1, 56, 57)],
                  'root_blocks_total': 916, 'blocks_scanned': 0, 'negative_blocks': [],
                  'unique_core_cuts': [], 'unconfirmed_numeric_negatives': [],
                  'exact_zero_rows_removed': 0, 'optimizer_called': False,
                  'PSD_feasibility_certified': False}
        known, timed_out = {}, False

        def deadline(_signum, _frame):
            raise TimeoutError('bounded complete r8s1 separation')

        previous = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            count_numerators = self.count_numerators(numerators)
            result['negative_exact_induced_forms'] = sum(value < 0 for value in count_numerators)
            result['minimum_exact_induced_numerator'] = min(count_numerators)
            embeddings = [value*a for value, a in zip(count_numerators, self.data[2])]
            for root, masks, tensor in self.blocks:
                matrix = self.matrix(tensor, len(masks)+1, embeddings)
                vector, quadratic, smallest, removed = self.negative(matrix)
                result['exact_zero_rows_removed'] += removed
                if vector is not None:
                    terms, divisor = construction.induced_form(tensor, vector, self.data[2])
                    value = sum(coefficient*count_numerators[index] for index, coefficient in terms)
                    assert value*divisor == quadratic < 0
                    core, core_gcd = construction.reduced_form(terms, self.raw, self.scale)
                    core_numerator = sum(a*x for a, x in zip(core, numerators))
                    assert core_numerator*core_gcd == value < 0
                    fraction = Fraction(core_numerator, denominator)
                    key = tuple(core)
                    if key not in known:
                        known[key] = len(result['unique_core_cuts'])
                        result['unique_core_cuts'].append({'coefficients': core,
                            'exact_value_at_proposal': [fraction.numerator, fraction.denominator],
                            'new_coordinate_support': [j for j in range(58, 550) if core[j]]})
                    result['negative_blocks'].append({'root_type': root, 'order': len(masks)+1,
                        'integer_vector': vector, 'quadratic_numerator': quadratic,
                        'primitive_induced_count_form': terms, 'induced_form_gcd': divisor,
                        'primitive_induced_numerator': value, 'core_form_gcd': core_gcd,
                        'core_cut_index': known[key], 'smallest_numeric_eigenvalue': smallest})
                elif smallest is not None and smallest < -1e-8:
                    result['unconfirmed_numeric_negatives'].append({'root_type': root, 'eigenvalue': smallest})
                result['blocks_scanned'] += 1
                if result['blocks_scanned'] % 128 == 0:
                    counts.save(output, result)
        except TimeoutError:
            timed_out = True
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
        result.update(status='exact r8s1 separators found' if result['negative_blocks'] else
                             'no exact separator in scanned blocks; PSD not certified',
                      timed_out=timed_out, complete_scan=result['blocks_scanned'] == 916 and not timed_out,
                      exact_negative_block_count=len(result['negative_blocks']),
                      unique_integer_cut_count=len(result['unique_core_cuts']),
                      seconds=time.monotonic()-started)
        counts.save(output, result)
        print(json.dumps({key: result[key] for key in ('status', 'blocks_scanned', 'complete_scan',
              'exact_negative_block_count', 'unique_integer_cut_count', 'seconds')}, indent=2), flush=True)
        return result

    def replay(self, certificate):
        result = json.loads(certificate.read_text())
        assert result['source_sha256'] == counts.digest(Path(__file__))
        assert result['full_cache_sha256'] == CACHE_SHA
        assert result['reduced_cache_sha256'] == self.reduced_cache_sha
        proposal = Path(result['proposal_path'])
        assert counts.digest(proposal) == result['proposal_sha256']
        point, numerators, denominator = exact_point(proposal)
        assert point == result['point_float'] and numerators == result['point_numerators']
        assert denominator == result['point_denominator']
        count_numerators = self.count_numerators(numerators)
        embeddings = [value*a for value, a in zip(count_numerators, self.data[2])]
        used = set()
        for block in result['negative_blocks']:
            masks, tensor = self.lookup[block['root_type']]
            matrix = self.matrix(tensor, len(masks)+1, embeddings)
            vector = block['integer_vector']
            assert len(vector) == len(masks)+1 and all(type(v) is int for v in vector)
            v = np.array(vector, dtype=object)
            quadratic = int(v@matrix@v)
            assert quadratic == block['quadratic_numerator'] < 0
            terms, divisor = construction.induced_form(tensor, vector, self.data[2])
            assert terms == block['primitive_induced_count_form'] and divisor == block['induced_form_gcd']
            value = sum(c*count_numerators[i] for i, c in terms)
            assert value == block['primitive_induced_numerator'] and value*divisor == quadratic
            core, common = construction.reduced_form(terms, self.raw, self.scale)
            assert common == block['core_form_gcd']
            index = block['core_cut_index']
            saved = result['unique_core_cuts'][index]
            assert core == saved['coefficients']
            exact = Fraction(sum(a*x for a, x in zip(core, numerators)), denominator)
            assert [exact.numerator, exact.denominator] == saved['exact_value_at_proposal']
            assert exact < 0
            used.add(index)
        assert len(result['negative_blocks']) == result['exact_negative_block_count']
        assert used == set(range(result['unique_integer_cut_count']))
        return {'status': 'exact full-cache r8s1 separator replay PASS',
                'negative_blocks': len(result['negative_blocks']),
                'unique_integer_cuts': len(used), 'optimizer_called': False,
                'numerical_eigensystems_recomputed': False}
