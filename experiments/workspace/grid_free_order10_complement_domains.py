"""Complete seven-root Boolean-complement domain and sparse child lifts.

The 4,478 quota-one cases have explicit positive child-sum witnesses.
The remaining 737 cases retain their full domains and sparse transports.
No product tensor, count reduction, eigensystem or optimizer is generated.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations
import json
from pathlib import Path
import pickle
import resource
import time

import grid_free_order10_projector_domains as direct
import grid_free_order10_projector_literal as literal
import grid_free_order10_r8s1 as transport
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/workspace/induced-moments-7-1-512.pickle'
BASE_SHA = '1b97bf97c8565c929061a6a795f4224c8f808f80a1e59daf48b055a5594f58bc'
CHILD = ROOT/'experiments/logs/moments-and-counts/order10-r8s1-full-blocks.pickle.gz'
CHILD_SHA = 'aecf7411230f718c8c3879c38ad39dcdb041ed07c58a799f8b044ebd0ab5028d'
TRANSPORT_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def entry(tensor, i, j):
    i, j = max(i, j), min(i, j)
    row = i*(i+1)//2+j
    return {int(tensor.indices[k]): int(tensor.data[k])
            for k in range(tensor.indptr[row], tensor.indptr[row+1])}


class Lifts:
    def __init__(self, data, child_blocks):
        self.data = data
        self.children = child_blocks
        self.builder = transport.Builder(data)

    def build(self, root, selected, high):
        rows = self.data[0][root]
        child = self.builder.child_map(root)[selected]
        mapping = self.builder.transport(transport.attach(rows, selected), child)
        child_masks, _ = self.children[child]
        positions = {mask: i+1 for i, mask in enumerate(child_masks)}
        extra_bit = 1 << mapping[7]
        lift = [[0]]
        for mask in high:
            translated = transport.transported_mask(mask, mapping)
            choices = [positions[value] for value in (translated, translated | extra_bit)
                       if value in positions]
            assert all(value.bit_count() >= 3 for value in (translated, translated | extra_bit))
            if mask == selected:
                assert not choices
                lift.append([0])
            else:
                lift.append(choices)
        assert all(len(row) <= 2 and len(row) == len(set(row)) for row in lift)
        return {'child_root_type': child, 'actual_to_child_vertex_map': mapping,
                'child_high_masks': child_masks, 'child_base_order': len(child_masks)+1,
                'sparse_rows': lift}


def literal_redundant_control(data, all_domains, lifts, root_rows, free_masks, edge):
    """A fixed literal embedding, including a size-two selected child class."""
    root_ids = {literal.canonical(tuple(data[0][root])): root for root in data[1][7]}
    root = root_ids[literal.canonical(tuple(root_rows))]
    root_map = lifts.builder.transport(tuple(root_rows), root)
    masks = [transport.transported_mask(mask, root_map) for mask in free_masks]
    rows = tuple(data[0][root])
    host = literal.extend(rows, masks, edge)
    assert literal.valid(host)
    domain = all_domains[root]
    high = domain['high_masks']
    actual = Counter(masks)
    assert all(actual[mask] <= 1 for mask in high)
    chosen = None
    for flag in domain['flags']:
        if flag['classification'] != 'quota_one_redundant' or actual[flag['mask']]:
            continue
        for i, j, residual in domain['residual_pairs']:
            pair = (1 << i) | (1 << j)
            if residual == 1 and flag['mask'] & pair == pair:
                if sum(count for mask, count in actual.items() if mask & pair == pair) == 1:
                    chosen = flag['mask'], i, j
                    break
        if chosen is not None:
            break
    assert chosen is not None
    selected, i, j = chosen
    pair = (1 << i) | (1 << j)
    X = [1]+[actual[mask] for mask in high]
    assert any(X[1:]) and actual[selected] == 0
    rhs = [[0]*len(X) for _ in X]
    selected_children = []
    for outside, mask in enumerate(masks, 7):
        if mask == selected or mask & pair != pair:
            continue
        child = lifts.build(root, mask, high)
        mapping = child['actual_to_child_vertex_map']
        child_positions = {m: k+1 for k, m in enumerate(child['child_high_masks'])}
        Y = [1]+[0]*len(child_positions)
        remaining = [v for v in range(7, len(host)) if v != outside]
        for vertex in remaining:
            old_mask = sum(((host[vertex] >> k) & 1) << k for k in range(7))
            if (host[vertex] >> outside) & 1:
                old_mask |= 1 << 7
            moved = transport.transported_mask(old_mask, mapping)
            if moved in child_positions:
                Y[child_positions[moved]] += 1
        image = [sum(Y[k] for k in row) for row in child['sparse_rows']]
        assert image == X
        for a in range(len(X)):
            for b in range(len(X)):
                rhs[a][b] += image[a]*image[b]
        selected_children.append({'mask': mask, 'degree': mask.bit_count(),
                                  'child_root_type': child['child_root_type'],
                                  'lifted_vector_equals_parent': True})
    lhs = [[(1-actual[selected])*a*b for b in X] for a in X]
    assert lhs == rhs
    return {'root_type': root, 'root_rows': list(rows), 'host_rows': list(host),
            'absent_high_mask': selected, 'quota_one_pair': [i,j],
            'actual_outside_masks': masks, 'parent_base_order': len(X),
            'nonzero_parent_coordinates': [k for k, value in enumerate(X) if value],
            'selected_child_classes': selected_children,
            'pointwise_full_redundant_sum_identity': True,
            'scope': 'Literal cap-compatible host with the selected residual pair saturated; no SRG(99) assertion about this host.'}


def build(catalogue):
    started = time.monotonic()
    assert files.digest(catalogue) == direct.CATALOGUE_SHA
    assert files.digest(BASE) == BASE_SHA and files.digest(CHILD) == CHILD_SHA
    assert files.digest(Path(transport.__file__)) == TRANSPORT_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    base_list = pickle.loads(BASE.read_bytes())
    child_saved = pickle.loads(gzip.decompress(CHILD.read_bytes()))
    assert child_saved['point_independent'] and child_saved['complete_root_family']
    assert not child_saved['zero_flags_or_roots_removed']
    assert child_saved['construction_source_sha256'] == TRANSPORT_SHA
    bases = {root: (flags, tensor) for root, flags, tensor in base_list}
    children = {root: (masks, tensor) for root, masks, tensor in child_saved['blocks']}
    assert len(bases) == len(base_list) == 203
    assert sorted(children) == data[1][8]
    for root, (masks, tensor) in children.items():
        assert masks == [mask for mask, _ in data[3][root] if mask.bit_count() >= 3]
        n = len(masks)+1
        assert tensor.shape == (n*(n+1)//2, 48965)
    lifts = Lifts(data, children)
    domains, new_masks, redundant_masks = [], 0, 0
    zero_row_checks, sparse_product_terms = 0, 0
    candidate_roots, used_children = set(), set()
    for root in data[1][7]:
        rows = tuple(data[0][root])
        allowed = direct.masks_for(rows)
        assert allowed == [mask for mask, _ in data[3][root]]
        high = [mask for mask in allowed if mask.bit_count() >= 3]
        n = len(high)+1
        if high:
            flags, tensor = bases[root]
            assert [tuple(f) for f in flags] == [rows]+[transport.attach(rows, mask) for mask in high]
            assert tensor.shape == (n*(n+1)//2, 6535)
        else:
            assert root not in bases
        residuals = [[i,j,2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count()]
                     for i in range(7) for j in range(i)]
        flags = []
        for position, mask in enumerate(high, 1):
            contained = [(i,j,q) for i,j,q in residuals if mask >> i & 1 and mask >> j & 1]
            assert all(q in (1,2) for _,_,q in contained)
            witnesses = [(i,j) for i,j,q in contained if q == 1]
            if witnesses:
                i,j = witnesses[0]
                pair = (1 << i) | (1 << j)
                others = [b for b in allowed if b != mask and b & pair == pair]
                assert pair in others and pair.bit_count() == 2
                flag = {'mask': mask, 'base_position': position,
                        'classification': 'quota_one_redundant',
                        'residual_pair_witness': [i,j,1], 'other_allowed_masks_in_positive_sum': others}
                redundant_masks += 1
            else:
                assert all(q == 2 for _,_,q in contained)
                assert all(not ((rows[i] >> j) & 1) and not (rows[i] & rows[j]) for i,j,_ in contained)
                lift = lifts.build(root, mask, high)
                assert lift['sparse_rows'][position] == [0]
                child_tensor = children[lift['child_root_type']][1]
                parent_tensor = bases[root][1]
                for j, row in enumerate(lift['sparse_rows']):
                    conditional = Counter()
                    for column in row:
                        conditional.update(entry(child_tensor, 0, column))
                    assert dict(conditional) == entry(parent_tensor, position, j)
                    zero_row_checks += 1
                lengths = [len(row) for j,row in enumerate(lift['sparse_rows']) if j != position]
                bound = (sum(lengths)**2+sum(x*x for x in lengths))//2
                sparse_product_terms += bound
                flag = {'mask': mask, 'base_position': position,
                        'classification': 'new_complement_candidate',
                        'all_contained_pair_residuals_are_two': True,
                        'quotient_order_after_zero_Xa_row': n-1,
                        'quotient_lower_entries': (n-1)*n//2,
                        'conditional_sparse_product_placements_upper_bound': bound,
                        'conditional_Xa_row_equals_parent_coefficientwise': True,
                        **lift}
                new_masks += 1
                candidate_roots.add(root)
                used_children.add(lift['child_root_type'])
            flags.append(flag)
        domains.append({'root_type': root, 'root_rows': list(rows),
                        'allowed_masks': allowed, 'high_masks': high, 'base_order': n,
                        'base_cache_has_nonconstant_block': bool(high),
                        'residual_pairs': residuals, 'flags': flags})
    assert len(domains) == 208 and new_masks == 737 and redundant_masks == 4478
    assert new_masks+redundant_masks == 5215 and len(candidate_roots) == 82
    lower = sum(flag['quotient_lower_entries'] for root in domains for flag in root['flags']
                if flag['classification'] == 'new_complement_candidate')
    assert lower == 1903068
    all_domains = {r['root_type']: r for r in domains}
    controls = [literal_redundant_control(data, all_domains, lifts,
                    (4,4,3,0,0,0,0), [3,56], 0)]
    assert any(child['degree'] == 2 for control in controls for child in control['selected_child_classes'])
    summary = {
        'root_types': len(domains), 'high_mask_domains': 5215,
        'quota_one_redundant_masks': redundant_masks, 'explicit_residual_pair_witnesses': redundant_masks,
        'new_complement_candidates': new_masks, 'candidate_root_types': len(candidate_roots),
        'distinct_child_root_types_used_by_candidates': len(used_children),
        'largest_parent_base_order': max(r['base_order'] for r in domains),
        'largest_candidate_quotient_order': max(f['quotient_order_after_zero_Xa_row'] for r in domains for f in r['flags'] if f['classification'] == 'new_complement_candidate'),
        'candidate_quotient_lower_entries': lower,
        'conditional_sparse_product_placements_upper_bound': sparse_product_terms,
        'coefficientwise_conditional_zero_row_checks': zero_row_checks,
        'literal_redundant_sum_controls': len(controls),
        'size_two_selected_child_control_included': True,
        'base_cache_nonconstant_roots': len(bases), 'constant_only_roots_in_full_ledger': len(domains)-len(bases),
        'no_point_dependent_pruning': True,
    }
    return {
        'status': 'complete Boolean-complement domains and exact sparse lifts',
        'source_sha256': files.digest(Path(__file__)),
        'catalogue_sha256': direct.CATALOGUE_SHA, 'base_cache_sha256': BASE_SHA,
        'child_cache_sha256': CHILD_SHA, 'transport_source_sha256': TRANSPORT_SHA,
        'direct_mask_source_sha256': files.digest(Path(direct.__file__)),
        'literal_control_source_sha256': files.digest(Path(literal.__file__)),
        'summary': summary, 'roots': domains, 'literal_controls': controls,
        'new_product_tensors_generated': False, 'dense_reduction_loaded': False,
        'point_scanned': False, 'optimizer_called': False,
        'seconds': time.monotonic()-started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def read(path):
    content = path.read_bytes()
    return json.loads(gzip.decompress(content) if path.suffix == '.gz' else content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    result = build(args.catalogue)
    if args.replay:
        saved = read(args.replay)
        assert {k:v for k,v in result.items() if k not in ('seconds','peak_rss_kib')} == {k:v for k,v in saved.items() if k not in ('seconds','peak_rss_kib')}
        result = {'status': 'exact complete-domain and lift replay PASS',
                  'source_sha256': files.digest(Path(__file__)),
                  'certificate_sha256': files.digest(args.replay),
                  'summary': result['summary'], 'seconds': result['seconds']}
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix == '.gz' else content)
    print(json.dumps({k:v for k,v in result.items() if k not in ('roots','literal_controls')},indent=2),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
