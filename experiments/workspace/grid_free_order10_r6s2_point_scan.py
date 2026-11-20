"""Reusable exact separator for immutable r6s2 tensor caches.

FullScanner(data, raw, scale, cache_path, reduced_hash) accepts either a
single cache or the combined manifest. scan(proposal,path,seconds) and
replay(path) use the same550-coordinate cut schema as the r8s1 scanner.
Coverage of the stored cache, the selected55 roots, and all62 roots is
reported separately. No binary diagonal formula is imposed.
"""

from fractions import Fraction
import gzip
import json
from pathlib import Path
import pickle
import signal
import time

import numpy as np
import pynauty
from scipy import sparse

import grid_free_order10_r6s2 as family
import grid_free_order10_r8s1 as forms
import grid_free_order10_r8s1_scan as directions
import grid_free_order10_scaled as counts
from subgraph_counts import nauty


FAMILY_SHA = '3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d'
PREPARATION_SHA = '1ff172888ebdd1a139710cb25e0a0f29c8044a1d81ba4972c0085f9827d691ea'
DIRECTION_SHA = '71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'
FORM_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'
OLD_SOURCE_SHA = 'ca16071dd21b7d0eed9e41d7bd08678cf5ea7b7863b8cac98a2969d230d088bd'
OLD_CACHE_SHA = '84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c'
REMAINING_SOURCE_SHA = '71a26e498ca70c9cf232a2d37b136e4c5c98b6b179800127de8161690ab530f1'
FAMILY_PREPARATION = Path(__file__).resolve().parents[1]/'logs/moments-and-counts/prism-zero-order10-r6s2-preparation.json'


def cache_contents(data, cache_path):
    """Validate full flag domains and return all cached immutable tensors."""
    assert counts.digest(Path(family.__file__)) == FAMILY_SHA
    assert counts.digest(FAMILY_PREPARATION) == PREPARATION_SHA
    prepared = json.loads(FAMILY_PREPARATION.read_text())
    assert prepared['source_sha256'] == FAMILY_SHA
    full_roots = set(data[1][6])
    assert len(data[0]) == 48965 and len(full_roots) == 62
    records = {record['root_type']: record for record in prepared['all_62_root_domains']}
    assert set(records) == full_roots
    selected55 = set(prepared['selected_root_types'])
    assert len(selected55) == 55
    combined = None
    if cache_path.suffix == '.json':
        combined = json.loads(cache_path.read_text())
        assert combined['format'] == 1 and combined['family_source_sha256'] == FAMILY_SHA
        assert combined['source_sha256'] == REMAINING_SOURCE_SHA
        assert combined['catalogue_sha256'] == family.CATALOGUE_SHA
        assert combined['point_independent_tensors'] and not combined['root_or_flag_zero_pruning']
        parts = [(Path(part['path']), part['sha256'], set(part['root_types'])) for part in combined['cache_parts']]
    else:
        parts = [(cache_path, counts.digest(cache_path), None)]
    blocks, bindings, seen_roots = [], [], set()
    ids = {(len(rows), pynauty.certificate(nauty(rows))): i
           for i, rows in enumerate(data[0]) if 6 <= len(rows) <= 8}
    for path, expected_hash, expected_roots in parts:
        assert counts.digest(path) == expected_hash
        payload = pickle.loads(gzip.decompress(path.read_bytes()))
        assert payload['format'] == 1 and payload['family_source_sha256'] == FAMILY_SHA
        assert payload['catalogue_sha256'] == family.CATALOGUE_SHA
        assert payload['point_independent_tensors'] and not payload['root_or_flag_zero_pruning']
        if payload['source_sha256'] == OLD_SOURCE_SHA:
            assert expected_hash == OLD_CACHE_SHA
            assert set(payload['selected_root_types']) == selected55
        else:
            assert payload['source_sha256'] == REMAINING_SOURCE_SHA
            assert counts.digest(Path(__file__).with_name('grid_free_order10_r6s2_remaining.py')) == REMAINING_SOURCE_SHA
            assert set(payload['selected_root_types']) == full_roots-selected55
        part_roots = []
        for root, flags, tensor in payload['blocks']:
            assert root in full_roots and root not in seen_roots
            assert list(data[0][root]) == records[root]['root_rows']
            assert len(flags) == records[root]['flags']
            assert tensor.format == 'csr' and tensor.has_canonical_format
            assert tensor.shape == (len(flags)*(len(flags)+1)//2, 48965)
            assert tensor.data.dtype.kind == 'i'
            assert np.all((tensor.data > 0) & (tensor.data <= 26))
            assert max(np.diff(tensor.indptr), default=0) <= 26
            assert max(np.asarray(tensor.sum(axis=1)).ravel(), default=0) <= 26
            keys = set()
            for i, flag in enumerate(flags):
                size, masks, edge = flag['size'], tuple(flag['masks']), flag['edge']
                assert size in (0, 1, 2) and len(masks) == size and edge in (0, 1)
                assert size == 2 or edge == 0
                assert all(0 <= mask < 64 for mask in masks)
                if size == 2:
                    assert masks[0] < masks[1]
                graph = list(data[0][root])+[0]*size
                for outside, mask in enumerate(masks, 6):
                    graph[outside] = mask
                    for vertex in range(6):
                        if mask >> vertex & 1:
                            graph[vertex] |= 1 << outside
                if edge:
                    graph[6] |= 1 << 7
                    graph[7] |= 1 << 6
                assert tuple(graph) == tuple(flag['rows']) and family.caps(graph)
                assert all(row.bit_count() >= 3 for row in graph[6:])
                assert ids[len(graph), pynauty.certificate(nauty(graph))] == flag['type']
                key = size, masks, edge
                assert key not in keys
                keys.add(key)
                position = i*(i+1)//2
                start, end = tensor.indptr[position], tensor.indptr[position+1]
                assert end-start == 1 and int(tensor.indices[start]) == flag['type']
                assert int(tensor.data[start]) == 1
            assert flags[0]['size'] == 0 and flags[0]['type'] == root
            seen_roots.add(root)
            part_roots.append(root)
            blocks.append((root, flags, tensor))
        assert set(part_roots) == set(payload['completed_root_types'])
        assert len(part_roots) == len(set(part_roots))
        if expected_roots is not None:
            assert set(part_roots) == expected_roots
        bindings.append({'path': str(path), 'sha256': expected_hash,
                         'producer_source_sha256': payload['source_sha256'],
                         'root_types': sorted(part_roots)})
    if combined is not None:
        assert sorted(seen_roots) == combined['all_cached_root_types']
        assert len(seen_roots) == combined['cached_root_count']
        assert combined['covers_full62_family'] == (seen_roots == full_roots)
    blocks.sort(key=lambda item: (len(item[1]), item[0]))
    coverage = {'cached_root_count': len(blocks), 'cache_root_types': sorted(seen_roots),
                'selected55_root_types': sorted(selected55), 'full62_root_types': sorted(full_roots),
                'covers_complete55_subfamily': selected55 <= seen_roots,
                'covers_full62_family': seen_roots == full_roots,
                'cached_lower_entries': sum(tensor.shape[0] for _, _, tensor in blocks),
                'cached_tensor_nonzeros': sum(tensor.nnz for _, _, tensor in blocks),
                'maximum_flag_count': max(len(flags) for _, flags, _ in blocks),
                'point_dependent_root_or_flag_pruning': False,
                'flag_domain_completeness_check': 'distinct admissible flags equal the exact prepared domain cardinality'}
    return blocks, coverage, bindings


class FullScanner(directions.FullScanner):
    def __init__(self, data, raw, scale, cache_path, reduced_hash):
        assert counts.digest(Path(directions.__file__)) == DIRECTION_SHA
        assert counts.digest(Path(forms.__file__)) == FORM_SHA
        self.data, self.raw, self.scale = data, raw, scale
        self.cache_path = Path(cache_path)
        self.cache_sha256 = counts.digest(self.cache_path)
        self.reduced_cache_sha = reduced_hash
        self.blocks, self.coverage, self.cache_parts = cache_contents(data, self.cache_path)
        self.lookup = {root: (flags, tensor) for root, flags, tensor in self.blocks}
        assert raw.shape == (48965, 550) and not np.any(raw % scale)
        self.forms = sparse.csr_matrix(raw//scale)

    @staticmethod
    def _synchronize(result, records):
        negative, cuts, unconfirmed, known = [], [], [], {}
        for record in records:
            cut = record['negative']
            if cut is not None:
                key = tuple(cut['coefficients'])
                if key not in known:
                    known[key] = len(cuts)
                    cuts.append({'coefficients': cut['coefficients'],
                                 'exact_value_at_proposal': cut['exact_value_at_proposal'],
                                 'new_coordinate_support': [j for j in range(58, 550) if cut['coefficients'][j]]})
                block = {key: value for key, value in cut.items()
                         if key not in ('coefficients', 'exact_value_at_proposal')}
                block['core_cut_index'] = known[key]
                negative.append(block)
            elif record['smallest'] is not None and record['smallest'] < -1e-8:
                unconfirmed.append({'root_type': record['root'], 'eigenvalue': record['smallest']})
        result.update(blocks_scanned=len(records), root_types_scanned=[record['root'] for record in records],
                      negative_blocks=negative, unique_core_cuts=cuts,
                      unconfirmed_numeric_negatives=unconfirmed,
                      exact_zero_rows_removed=sum(record['removed'] for record in records))

    def scan(self, proposal, path, seconds=180):
        assert 0 < seconds <= 180
        proposal, path = Path(proposal), Path(path)
        point, numerators, denominator = directions.exact_point(proposal)
        result = {'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
                  'proposal_path': str(proposal), 'proposal_sha256': counts.digest(proposal),
                  'cache_path': str(self.cache_path), 'cache_sha256': self.cache_sha256,
                  'cache_parts': self.cache_parts, 'coverage': self.coverage,
                  'reduced_cache_sha256': self.reduced_cache_sha,
                  'point_float': point, 'point_numerators': numerators, 'point_denominator': denominator,
                  'root_blocks_total': len(self.blocks), 'full_family_root_blocks': 62,
                  'blocks_scanned': 0, 'negative_blocks': [], 'unique_core_cuts': [],
                  'unconfirmed_numeric_negatives': [], 'exact_zero_rows_removed': 0,
                  'binary_diagonal_shortcut_used': False, 'optimizer_called': False,
                  'PSD_feasibility_certified': False}
        records, timed_out = [], False
        started = time.monotonic()

        def deadline(_signum, _frame):
            raise TimeoutError('bounded r6s2 exact separation')

        previous = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            induced_numerators = self.count_numerators(numerators)
            result['negative_exact_induced_forms'] = sum(value < 0 for value in induced_numerators)
            result['minimum_exact_induced_numerator'] = min(induced_numerators)
            embeddings = [value*aut for value, aut in zip(induced_numerators, self.data[2])]
            for root, flags, tensor in self.blocks:
                matrix = self.matrix(tensor, len(flags), embeddings)
                vector, quadratic, smallest, removed = self.negative(matrix)
                negative = None
                if vector is not None:
                    terms, divisor = forms.induced_form(tensor, vector, self.data[2])
                    value = sum(coefficient*induced_numerators[index] for index, coefficient in terms)
                    assert value*divisor == quadratic < 0
                    core, common = forms.reduced_form(terms, self.raw, self.scale)
                    core_value = sum(a*x for a, x in zip(core, numerators))
                    assert core_value*common == value < 0
                    fraction = Fraction(core_value, denominator)
                    negative = {'root_type': root, 'order': len(flags), 'integer_vector': vector,
                                'quadratic_numerator': quadratic, 'primitive_induced_count_form': terms,
                                'induced_form_gcd': divisor, 'primitive_induced_numerator': value,
                                'core_form_gcd': common, 'coefficients': core,
                                'exact_value_at_proposal': [fraction.numerator, fraction.denominator],
                                'smallest_numeric_eigenvalue': smallest}
                records.append({'root': root, 'negative': negative, 'smallest': smallest, 'removed': removed})
                if len(records) % 8 == 0:
                    self._synchronize(result, records)
                    counts.save(path, result)
        except TimeoutError:
            timed_out = True
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
        self._synchronize(result, records)
        scanned = {record['root'] for record in records}
        complete = len(records) == len(self.blocks) and not timed_out
        result.update(status='exact r6s2 separators found' if result['negative_blocks'] else
                             'no exact separator in scanned cached blocks; PSD not certified',
                      timed_out=timed_out, complete_scan=complete,
                      complete_cached_family_scan=complete,
                      complete_selected55_scan=set(self.coverage['selected55_root_types']) <= scanned,
                      complete_full62_scan=set(self.coverage['full62_root_types']) <= scanned,
                      exact_negative_block_count=len(result['negative_blocks']),
                      unique_integer_cut_count=len(result['unique_core_cuts']),
                      seconds=time.monotonic()-started)
        counts.save(path, result)
        print(json.dumps({key: result[key] for key in ('status', 'blocks_scanned', 'complete_cached_family_scan',
              'complete_selected55_scan', 'complete_full62_scan', 'exact_negative_block_count',
              'unique_integer_cut_count', 'seconds')}, indent=2), flush=True)
        return result

    def replay(self, path):
        path = Path(path)
        result = json.loads(path.read_text())
        assert result['source_sha256'] == counts.digest(Path(__file__))
        assert result['family_source_sha256'] == FAMILY_SHA
        assert result['cache_sha256'] == self.cache_sha256 and result['cache_parts'] == self.cache_parts
        assert result['coverage'] == self.coverage
        assert result['reduced_cache_sha256'] == self.reduced_cache_sha
        proposal = Path(result['proposal_path'])
        assert counts.digest(proposal) == result['proposal_sha256']
        point, numerators, denominator = directions.exact_point(proposal)
        assert point == result['point_float'] and numerators == result['point_numerators']
        assert denominator == result['point_denominator']
        induced_numerators = self.count_numerators(numerators)
        embeddings = [value*aut for value, aut in zip(induced_numerators, self.data[2])]
        used = set()
        for block in result['negative_blocks']:
            flags, tensor = self.lookup[block['root_type']]
            assert len(flags) == block['order']
            vector = block['integer_vector']
            assert len(vector) == len(flags) and all(type(value) is int for value in vector)
            matrix = self.matrix(tensor, len(flags), embeddings)
            v = np.array(vector, dtype=object)
            quadratic = int(v@matrix@v)
            assert quadratic == block['quadratic_numerator'] < 0
            terms, divisor = forms.induced_form(tensor, vector, self.data[2])
            assert terms == block['primitive_induced_count_form'] and divisor == block['induced_form_gcd']
            value = sum(coefficient*induced_numerators[index] for index, coefficient in terms)
            assert value == block['primitive_induced_numerator'] and value*divisor == quadratic
            core, common = forms.reduced_form(terms, self.raw, self.scale)
            assert common == block['core_form_gcd']
            index = block['core_cut_index']
            cut = result['unique_core_cuts'][index]
            assert core == cut['coefficients']
            fraction = Fraction(sum(a*x for a, x in zip(core, numerators)), denominator)
            assert [fraction.numerator, fraction.denominator] == cut['exact_value_at_proposal']
            assert fraction < 0
            used.add(index)
        assert len(result['negative_blocks']) == result['exact_negative_block_count']
        assert used == set(range(result['unique_integer_cut_count']))
        return {'status': 'exact cached r6s2 separator replay PASS',
                'source_sha256': counts.digest(Path(__file__)), 'cache_sha256': self.cache_sha256,
                'negative_blocks': len(result['negative_blocks']), 'unique_integer_cuts': len(used),
                'coverage': self.coverage, 'optimizer_called': False,
                'numerical_eigensystems_recomputed': False, 'tensor_construction_rebuilt': False,
                'PSD_feasibility_certified': False}
