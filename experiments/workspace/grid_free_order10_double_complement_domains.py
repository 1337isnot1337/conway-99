"""Complete six-root double-absence domains and exact conditional lifts.

For distinct binary high classes a,b the necessary localizer is
M - C_a - C_b + C_ab.  The two selected rows vanish coefficientwise.
This preparation uses no count point, optimizer, or eigensystem.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations, permutations
import json
from pathlib import Path
import pickle
import resource
import time

import grid_free_order10_complement_domains as seven
import grid_free_order10_projector_domains as direct
import grid_free_order10_projector_literal as literal
import grid_free_order10_r8s1 as transport
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/workspace/induced-moments-6-1-512.pickle'
BASE_SHA = '13808003e8f24bd47b8da6169c65a1eccc205b2bc9c3be1c8b57b588a2ba37c5'


def entry(blocks, root, i, j):
    if root not in blocks:
        assert i == j == 0
        return {root: 1}
    return seven.entry(blocks[root][1], i, j)


def lifted_entry(blocks, lift, i, j):
    result = Counter()
    for a in lift['sparse_rows'][i]:
        for b in lift['sparse_rows'][j]:
            result.update(entry(blocks, lift['child_root_type'], a, b))
    return dict(result)


class Lifts:
    def __init__(self, data, children7, children8):
        self.data = data
        self.builder = transport.Builder(data)
        self.children = {7: children7, 8: children8}

    def conditional(self, root, high, selected, cross_edge=None):
        rows = tuple(self.data[0][root])
        assert len(rows) == 6 and len(selected) in (1, 2)
        current, actual = root, rows
        mapping = list(range(6))
        for position, mask in enumerate(selected):
            actual_mask = mask | ((int(cross_edge) << 6) if position else 0)
            child_mask = transport.transported_mask(actual_mask, mapping)
            child = self.builder.child_map(current).get(child_mask)
            if child is None:
                return None
            actual = transport.attach(actual, actual_mask)
            mapping = self.builder.transport(actual, child)
            current = child
        r = 6 + len(selected)
        child_masks = [mask for mask, _ in self.data[3][current] if mask.bit_count() >= 3]
        if current in self.children[r]:
            assert child_masks == self.children[r][current][0]
        else:
            assert not child_masks
        positions = {mask: i+1 for i, mask in enumerate(child_masks)}
        sparse = [[0]]
        for mask in high:
            choices = []
            for bits in range(1 << len(selected)):
                moved = transport.transported_mask(mask | (bits << 6), mapping)
                if moved in positions:
                    choices.append(positions[moved])
            if mask in selected:
                assert not choices
                choices = [0]
            assert len(choices) == len(set(choices)) and len(choices) <= 4
            sparse.append(choices)
        return {'child_root_type': current, 'selected_masks': list(selected),
                'mutual_edge': cross_edge, 'actual_child_rows': list(actual),
                'actual_to_child_map': mapping, 'child_high_masks': child_masks,
                'child_base_order': len(child_masks)+1, 'sparse_rows': sparse}


def root_actions(rows, high):
    n = len(rows)
    actions = []
    for move in permutations(range(n)):
        if any(rows[i].bit_count() != rows[move[i]].bit_count() for i in range(n)):
            continue
        if all(transport.transported_mask(rows[i], move) == rows[move[i]] for i in range(n)):
            images = [transport.transported_mask(mask, move) for mask in high]
            assert sorted(images) == sorted(high)
            actions.append({'vertex_image': list(move), 'high_mask_image': images})
    assert actions and len({tuple(a['vertex_image']) for a in actions}) == len(actions)
    return actions


def literal_control(lifts, high, selected, free_masks, edges):
    root = lifts.data[1][6][0]
    rows = tuple(lifts.data[0][root])
    assert rows == (0,)*6
    host = literal.extend(rows, free_masks, edges)
    assert literal.valid(host)
    counts = Counter(free_masks)
    X = [1]+[counts[mask] for mask in high]
    assert all(value in (0, 1) for value in X)

    def contribution(masks):
        result = [[0]*len(X) for _ in X]
        chosen = [6+free_masks.index(mask) for mask in masks if mask in free_masks]
        if len(chosen) != len(masks):
            return result
        edge = (host[chosen[0]] >> chosen[1] & 1) if len(chosen) == 2 else None
        lift = lifts.conditional(root, high, masks, edge)
        assert lift is not None
        actual_vertices = list(range(6))+chosen
        actual_rows = tuple(sum((host[a] >> b & 1) << j for j,b in enumerate(actual_vertices)) for a in actual_vertices)
        assert list(actual_rows) == lift['actual_child_rows']
        positions = {m: i+1 for i,m in enumerate(lift['child_high_masks'])}
        Y = [1]+[0]*len(positions)
        for vertex in range(6, len(host)):
            if vertex in chosen:
                continue
            mask = sum((host[vertex] >> a & 1) << i for i,a in enumerate(actual_vertices))
            moved = transport.transported_mask(mask, lift['actual_to_child_map'])
            if moved in positions:
                Y[positions[moved]] += 1
        image = [sum(Y[k] for k in row) for row in lift['sparse_rows']]
        assert image == X
        return [[a*b for b in image] for a in image]

    ca, cb, cab = (contribution([selected[0]]), contribution([selected[1]]), contribution(selected))
    factor = (1-counts[selected[0]])*(1-counts[selected[1]])
    localizer = [[a*b-ca[i][j]-cb[i][j]+cab[i][j] for j,b in enumerate(X)] for i,a in enumerate(X)]
    assert localizer == [[factor*a*b for b in X] for a in X]
    return {'root_type': root, 'host_rows': list(host), 'selected_masks': selected,
            'outside_masks': free_masks, 'outside_edge_bits': edges, 'factor': factor,
            'literal_single_and_double_lift_identity': True, 'literal_localizer_identity': True,
            'scope': 'Literal cap-compatible host, not an SRG(99) assertion.'}


def build(catalogue):
    started = time.monotonic()
    assert files.digest(catalogue) == direct.CATALOGUE_SHA
    assert files.digest(BASE) == BASE_SHA
    assert files.digest(seven.BASE) == seven.BASE_SHA
    assert files.digest(seven.CHILD) == seven.CHILD_SHA
    assert files.digest(Path(transport.__file__)) == seven.TRANSPORT_SHA
    data = pickle.loads(catalogue.read_bytes())
    bases = {r: (f,t) for r,f,t in pickle.loads(BASE.read_bytes())}
    seven_blocks = {r: ([flag[-1] for flag in f[1:]],t)
                    for r,f,t in pickle.loads(seven.BASE.read_bytes())}
    child_saved = pickle.loads(gzip.decompress(seven.CHILD.read_bytes()))
    eight_blocks = {r: (m,t) for r,m,t in child_saved['blocks']}
    assert len(bases) == 55 and len(seven_blocks) == 203 and len(eight_blocks) == 916
    assert child_saved['point_independent'] and not child_saved['zero_flags_or_roots_removed']
    lifts = Lifts(data, seven_blocks, eight_blocks)
    totals, records = Counter(), []
    for root in data[1][6]:
        rows = tuple(data[0][root])
        allowed = direct.masks_for(rows)
        assert allowed == [mask for mask, _ in data[3][root]]
        high = [mask for mask in allowed if mask.bit_count() >= 3]
        n = len(high)+1
        if high:
            flags, tensor = bases[root]
            assert [tuple(f) for f in flags] == [rows]+[transport.attach(rows,m) for m in high]
        else:
            assert root not in bases
        positions = {m: i+1 for i,m in enumerate(high)}
        residuals = [[i,j,2-(rows[i] >> j & 1)-(rows[i]&rows[j]).bit_count()]
                     for i,j in combinations(range(6),2)]
        witnesses = {}
        q2 = []
        for mask in high:
            pairs = [(i,j,q) for i,j,q in residuals if mask >> i & 1 and mask >> j & 1]
            assert all(q in (1,2) for i,j,q in pairs)
            one = [(i,j) for i,j,q in pairs if q == 1]
            if one:
                i,j = one[0]
                bits = (1 << i)|(1 << j)
                others = [m for m in allowed if m != mask and m & bits == bits]
                assert bits in others
                witnesses[mask] = {'residual_pair': [i,j,1], 'positive_sum_other_masks': others}
            else:
                q2.append(mask)
        singles = {mask: lifts.conditional(root, high, [mask]) for mask in q2}
        assert all(lift is not None for lift in singles.values())
        pairs, incompatible = [], []
        for a,b in combinations(q2,2):
            children = [lifts.conditional(root,high,[a,b],edge) for edge in (0,1)]
            children = [child for child in children if child is not None]
            if not children:
                assert (a&b).bit_count() >= 3
                incompatible.append([a,b])
                continue
            assert (a&b).bit_count() <= 2
            for chosen in (a,b):
                i = positions[chosen]
                for j in range(n):
                    terms = Counter(entry(bases,root,i,j))
                    terms.subtract(lifted_entry(seven_blocks,singles[a],i,j))
                    terms.subtract(lifted_entry(seven_blocks,singles[b],i,j))
                    for child in children:
                        terms.update(lifted_entry(eight_blocks,child,i,j))
                    assert all(value == 0 for value in terms.values())
                    totals['coefficientwise_selected_row_checks'] += 1
            pairs.append({'masks': [a,b], 'selected_base_positions': [positions[a],positions[b]],
                          'double_conditional_lifts': children, 'quotient_order': n-2,
                          'quotient_lower_entries': (n-2)*(n-1)//2,
                          'both_selected_rows_vanish_coefficientwise': True})
        actions = root_actions(rows,high) if pairs else []
        candidate_pairs = {tuple(p['masks']) for p in pairs}
        pending, orbits = set(candidate_pairs), []
        while pending:
            representative = min(pending)
            orbit = sorted({tuple(sorted(transport.transported_mask(m,action['vertex_image']) for m in representative)) for action in actions})
            assert set(orbit) <= candidate_pairs and set(orbit) <= pending
            pending.difference_update(orbit)
            orbits.append({'representative': list(representative), 'members': [list(p) for p in orbit],
                           'size': len(orbit)})
        totals.update(root_types=1,high_masks=len(high),all_high_pairs=len(high)*(len(high)-1)//2,
                      all_residual_two_masks=len(q2),all_residual_two_pairs=len(q2)*(len(q2)-1)//2,
                      quota_one_redundant_pairs=len(high)*(len(high)-1)//2-len(q2)*(len(q2)-1)//2,
                      incompatible_redundant_pairs=len(incompatible),candidate_pairs=len(pairs),
                      candidate_roots=int(bool(pairs)),candidate_pair_orbits=len(orbits),
                      representative_quotient_lower_entries=len(orbits)*(n-2)*(n-1)//2,
                      full_quotient_lower_entries=len(pairs)*(n-2)*(n-1)//2,
                      checked_root_automorphisms=len(actions))
        records.append({'root_type':root,'root_rows':list(rows),'allowed_masks':allowed,'high_masks':high,
                        'base_order':n,'residual_pairs':residuals,'quota_one_mask_witnesses':witnesses,
                        'all_residual_two_masks':q2,'incompatible_pairs':incompatible,
                        'single_conditional_lifts':[{'mask':m,**singles[m]} for m in q2],
                        'candidate_pairs':pairs,'root_automorphisms':actions,'pair_orbits':orbits})
    assert totals['root_types'] == 62 and totals['high_masks'] == 829
    assert totals['all_high_pairs'] == 9118 and totals['all_residual_two_pairs'] == 1591
    assert totals['candidate_pairs'] == 1112 and totals['candidate_roots'] == 16
    first_high = records[0]['high_masks']
    controls = [literal_control(lifts,first_high,[7,56],masks,edges)
                for masks,edges in (([11],0),([7,11],0),([56,11],0),([7,56,11],0),([7,56],1))]
    return {'status':'complete six-root double-complement preparation',
            'source_sha256':files.digest(Path(__file__)),'catalogue_sha256':direct.CATALOGUE_SHA,
            'six_root_cache_sha256':BASE_SHA,'seven_root_cache_sha256':seven.BASE_SHA,
            'eight_root_cache_sha256':seven.CHILD_SHA,'transport_source_sha256':seven.TRANSPORT_SHA,
            'summary':dict(sorted(totals.items())),'roots':records,'literal_controls':controls,
            'complete_root_and_mask_domains':True,'point_dependent_pruning':False,
            'count_point_loaded':False,'optimizer_called':False,'new_product_tensors_generated':False,
            'zero_rows_are_unrestricted_coefficient_identities':True,
            'redundancy_scope':'Quota-one pairs are positive congruence sums of seven-root clique complements. '
                               'Incompatible pairs are six-root clique complements, obtained by summing '
                               'their seven-root extension localizers and dividing by93.',
            'seconds':time.monotonic()-started,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    result = build(args.catalogue)
    if args.replay:
        saved = json.loads(gzip.decompress(args.replay.read_bytes()))
        for key in ('seconds','peak_rss_kib'):
            saved.pop(key,None)
        assert saved == {k:v for k,v in result.items() if k not in ('seconds','peak_rss_kib')}
        result = {'status':'exact double-complement domain and coefficient replay PASS',
                  'source_sha256':files.digest(Path(__file__)),'certificate_sha256':files.digest(args.replay),
                  'summary':result['summary'],'seconds':result['seconds']}
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,mtime=0) if args.output.suffix == '.gz' else content)
    print(json.dumps({k:v for k,v in result.items() if k not in ('roots','literal_controls')},indent=2),flush=True)
