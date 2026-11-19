"""Point-independent triangle-projector conditioning on a core triangle.

For roots 14 and 15 the root has one triangle T. The kernel
120 Q(U,V) - Q(T,U) Q(T,V) is PSD by per-embedding Schur conditioning.
All full triangle classes are retained. Literal induced-subset coefficients
are reconstructed directly; no aggregated Q tensor is divided or reused.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import isqrt
from pathlib import Path
import time

import pynauty
import triangle_incidence_projector_moments as base
import triangle_incidence_projector_full_classes as full

BASE_SOURCE_SHA = '1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9'
FULL_SOURCE_SHA = 'd26499a0eec07c2c80a28818f0a40319fc0b14f54140a28253c820eb00d44f2a'
FULL_PREPARATION_SHA = '48a3788a0ca55dd445971f71dba46be49f4291b0ddd6b920beebb5de87e66fb7'
FULL_MODEL_SHA = '819aa1954ce038865404433995eb401ad7111cad0a21992f4ba8c42e3e04687c'
FULL_GZIP_SHA = '9305dffa83a024f574321dd5843244724d3cd82b569c0749d2ed135ccdc01938'

def load_full(directory):
    assert base.digest(Path(base.__file__).read_bytes()) == BASE_SOURCE_SHA
    assert base.digest(Path(full.__file__).read_bytes()) == FULL_SOURCE_SHA
    preparation_raw = (directory/'preparation.json').read_bytes()
    assert base.digest(preparation_raw) == FULL_PREPARATION_SHA
    preparation = json.loads(preparation_raw)
    compressed = (directory/'model.json.gz').read_bytes()
    raw = gzip.decompress(compressed)
    assert base.digest(compressed) == FULL_GZIP_SHA == preparation['model_gzip_sha256']
    assert base.digest(raw) == FULL_MODEL_SHA == preparation['model_raw_sha256']
    assert preparation['source_sha256'] == FULL_SOURCE_SHA
    specification = json.loads(raw)
    domains = [d for d in specification['domains'] if len(base.triangles(d['root_rows'])) == 1]
    assert [d['root_type'] for d in domains] == [14, 15]
    assert [len(d['classes']) for d in domains] == [41, 34]
    result = []
    for d in domains:
        fixed = base.triangles(d['root_rows'])[0]
        values = []
        fixed_class = None
        for i, c in enumerate(d['classes']):
            literal = full.extension(d['root_rows'], c['root_intersection_mask'], c['outside_masks'])
            assert literal is not None and base.cap_valid(literal)
            triangle = tuple(j for j in range(4) if c['root_intersection_mask'] >> j & 1) + tuple(range(4, len(literal)))
            assert triangle in base.triangles(literal)
            value = base.kernel(literal, fixed, triangle)
            values.append(value)
            if triangle == fixed:
                assert fixed_class is None
                fixed_class = i
                assert value == 120
        assert fixed_class is not None
        result.append(dict(d, fixed_triangle=list(fixed),
            fixed_triangle_class=fixed_class, fixed_triangle_cross_values=values))
    return result

def root_maps(domains):
    maps = {}
    for code in range(64):
        rows = tuple(sum(((code >> k) & 1) << (b if i == a else a)
                         for k, (a, b) in enumerate(base.ROOT_EDGES) if i in (a, b))
                     for i in range(4))
        hits = []
        for d in domains:
            transports = [p for p in permutations(range(4)) if base.induced(rows, p) == tuple(d['root_rows'])]
            if transports:
                assert len(transports) == d['root_automorphisms']
                hits.append((d['root_type'], transports))
        assert len(hits) <= 1
        if hits:
            maps[code] = hits[0]
    assert len(maps) == 16 and sum(len(p) for _, p in maps.values()) == 48
    return maps

def conditioned(rows, fixed, left, right):
    return 120*base.kernel(rows, left, right) - base.kernel(rows, fixed, left)*base.kernel(rows, fixed, right)

def construct(data, domains, deadline):
    graphs, levels, _, _ = data
    maps = root_maps(domains)
    by_root = {d['root_type']: d for d in domains}
    classes = {d['root_type']: {full.class_key(c): i for i,c in enumerate(d['classes'])} for d in domains}
    tensors = {d['root_type']: Counter() for d in domains}
    census = Counter()
    samples = {}
    values_checked = 0
    for order in range(4, 11):
        for graph_id in levels[order]:
            if graph_id % 128 == 0:
                base.check_time(deadline)
            rows = graphs[graph_id]
            ts = base.triangles(rows)
            for i, left in enumerate(ts):
                for right in ts[:i+1]:
                    union = set(left) | set(right)
                    extra_count = 4+len(union)-order
                    if extra_count < 0 or extra_count > min(4, len(union)):
                        continue
                    rest = tuple(v for v in range(order) if v not in union)
                    for extra in combinations(sorted(union), extra_count):
                        root = tuple(sorted(rest+extra))
                        assert len(root) == 4 and set(root) | union == set(range(order))
                        key = base.graph_code(base.induced(rows, root))
                        if key not in maps:
                            continue
                        root_id, transports = maps[key]
                        fixed_local = base.triangles(base.induced(rows, root))
                        assert len(fixed_local) == 1
                        fixed = tuple(root[j] for j in fixed_local[0])
                        q_left, q_right = base.kernel(rows, fixed, left), base.kernel(rows, fixed, right)
                        value = conditioned(rows, fixed, left, right)
                        if left == fixed or right == fixed:
                            assert value == 0
                        kind = 'diagonal' if left == right else 'intersection' if len(set(left)&set(right)) == 1 else 'disjoint_'+str((base.kernel(rows,left,right)+6)//7)
                        tag = str(root_id)+':'+kind+':'+('negative' if value<0 else 'positive' if value>0 else 'zero')
                        samples.setdefault(tag, graph_id)
                        census[tag] += 1
                        for p in transports:
                            labelled = tuple(root[j] for j in p)
                            a = classes[root_id][full.full_classify(rows, left, labelled)]
                            b = classes[root_id][full.full_classify(rows, right, labelled)]
                            assert by_root[root_id]['fixed_triangle_cross_values'][a] == q_left
                            assert by_root[root_id]['fixed_triangle_cross_values'][b] == q_right
                            values_checked += 2
                            if a < b:
                                a, b = b, a
                            multiplier = 2 if left != right and a == b else 1
                            tensors[root_id][(a*(a+1)//2+b, graph_id)] += multiplier*value
                            census['root_labelled_decompositions'] += 1
    blocks = []
    zero_positions = 0
    for d in domains:
        root_id = d['root_type']
        n = len(d['classes'])
        terms = [[entry, graph, coefficient] for (entry,graph),coefficient in sorted(tensors[root_id].items()) if coefficient]
        assert all(0 <= entry < n*(n+1)//2 for entry,_,_ in terms)
        fixed = d['fixed_triangle_class']
        for entry,_,_ in terms:
            row = (isqrt(8*entry+1)-1)//2
            column = entry-row*(row+1)//2
            assert fixed not in (row, column)
        zero_positions += n
        blocks.append({'root_type':root_id,'order':n,'lower_entries':n*(n+1)//2,'terms':terms})
    assert zero_positions == 75
    return {
        'schema':'conway99.triangle-projector-core-triangle-conditioning.v1',
        'catalogue_sha256':base.CATALOGUE_SHA,
        'parent_full_class_model_raw_sha256':FULL_MODEL_SHA,
        'domains':domains,'blocks':blocks,
        'kernel':'120*Q(U,V)-Q(T,U)*Q(T,V), with the unique triangle T contained in the labelled four-root',
        'kernel_projector_scale':25200,'kernel_global_rank':131,
        'normalization':'Actual unlabelled triangle sets inside each induced graph and every labelled root isomorphism; unordered distinct pairs contribute twice only on a class diagonal. Multiply coefficients by unlabelled induced counts.',
        'census':dict(sorted(census.items())),'control_graph_ids':samples,
        'literal_class_cross_values_checked':values_checked,
        'fixed_triangle_rows_zero_coefficientwise':True,'zero_row_positions_checked':zero_positions,
        'all_full_class_domains_retained':True,
        'aggregated_parent_Q_tensors_used':False,
        'count_point_loaded':False,'optimizer_called':False,
    }, maps

def direct_host(rows, specification, maps):
    domains = {d['root_type']:d for d in specification['domains']}
    class_maps = {k:{full.class_key(c):i for i,c in enumerate(d['classes'])} for k,d in domains.items()}
    matrices = {k:[[0]*len(d['classes']) for _ in d['classes']] for k,d in domains.items()}
    ts = base.triangles(rows)
    for root in combinations(range(len(rows)), 4):
        code = base.graph_code(base.induced(rows, root))
        if code not in maps:
            continue
        root_id, transports = maps[code]
        fixed_local = base.triangles(base.induced(rows, root))
        assert len(fixed_local) == 1
        fixed = tuple(root[i] for i in fixed_local[0])
        for p in transports:
            labelled = tuple(root[i] for i in p)
            labels = [class_maps[root_id][full.full_classify(rows, t, labelled)] for t in ts]
            matrix = matrices[root_id]
            for i, left in enumerate(ts):
                for j, right in enumerate(ts):
                    matrix[labels[i]][labels[j]] += conditioned(rows, fixed, left, right)
    return matrices

def controls(data, specification, maps, deadline):
    graphs, levels, _, _ = data
    selected = sorted(set(specification['control_graph_ids'].values()))
    lookup = {(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i for n in range(4,10) for i in levels[n]}
    checks=[]
    for graph_id in selected:
        base.check_time(deadline)
        rows=graphs[graph_id]
        counts=[0]*len(graphs)
        for n in range(4,len(rows)+1):
            for subset in combinations(range(len(rows)),n):
                pos=graph_id if n==len(rows) else lookup[n,pynauty.certificate(base.nauty(base.induced(rows,subset)))]
                counts[pos]+=1
        direct=direct_host(rows,specification,maps)
        contracted=base.contract(specification,counts)
        assert direct==contracted,(graph_id,'direct induced-subset normalization')
        checks.append({'host_type':graph_id,'order':len(rows),'ordered_triangle_pairs':True,'both_full_class_blocks_equal':True})
    return checks

def prepare(args):
    start=time.monotonic()
    deadline=start+args.seconds
    assert 0<args.seconds<=60 and not args.directory.exists()
    domains=load_full(args.full_preparation)
    data=base.load_catalogue(args.catalogue)
    specification,maps=construct(data,domains,deadline)
    checks=controls(data,specification,maps,deadline)
    raw=base.canonical(specification)
    compressed=gzip.compress(raw,mtime=0)
    report={
        'status':'COMPLETE_POINT_INDEPENDENT_CORE_TRIANGLE_CONDITIONED_PREPARATION',
        'source_sha256':base.digest(Path(__file__).read_bytes()),
        'base_source_sha256':BASE_SOURCE_SHA,'full_class_source_sha256':FULL_SOURCE_SHA,
        'full_class_preparation_sha256':FULL_PREPARATION_SHA,
        'parent_full_class_model_raw_sha256':FULL_MODEL_SHA,
        'catalogue_sha256':base.CATALOGUE_SHA,
        'model_raw_sha256':base.digest(raw),'model_gzip_sha256':base.digest(compressed),
        'model_raw_bytes':len(raw),'model_gzip_bytes':len(compressed),
        'root_types':[14,15],'block_orders':[41,34],
        'classes':75,'lower_entries':1456,
        'tensor_nonzeros':sum(len(b['terms']) for b in specification['blocks']),
        'literal_class_cross_values_checked':specification['literal_class_cross_values_checked'],
        'census':specification['census'],'small_host_controls':checks,
        'fixed_triangle_rows_zero_coefficientwise':True,
        'all_full_class_domains_retained':True,
        'point_query_requires_separate_gate':True,'count_point_loaded':False,'optimizer_called':False,
        'seconds':time.monotonic()-start,
    }
    base.check_time(deadline)
    args.directory.mkdir(parents=True)
    (args.directory/'model.json.gz').write_bytes(compressed)
    (args.directory/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,required=True)
    parser.add_argument('--full-preparation',type=Path,required=True)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=60)
    args=parser.parse_args()
    prepare(args)

if __name__=='__main__':
    main()
