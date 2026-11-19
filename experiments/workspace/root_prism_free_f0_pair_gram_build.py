"""Stream and replay the complete unfixed component0-pair incidence CNF.

No SAT solver is imported or called. The inspector checks a full primary
assignment directly as a39-core incidence and reports visible forbidden
motifs. The sixty-vertex exterior adjacency remains unspecified.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import tempfile
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

import root_prism_free_f0_pair_gram_model as preparation
import root_prism_free_f0_pair_gram as gram_screen
import root_prism_free_f0_components as components
import root_prism_free_f0_pair_clauses as motifs


ROOT, LOGS = preparation.ROOT, preparation.LOGS
PREPARATION = LOGS/'f0-pair-gram-model-preparation.json.gz'
PREPARATION_SHA = '7b870a9df98c855f75fcd0191b5fe03589d9458ad1e3f985ba77edb066be0c59'
SOURCE_NAMES = ('root_prism_free_f0_pair_gram_build.py',
                'root_prism_free_f0_pair_gram_model.py',
                'root_prism_free_f0_pair_gram.py',
                'root_prism_free_f0_components.py',
                'root_prism_free_f0_pair_clauses.py')
digest, canonical = preparation.digest, preparation.canonical


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def load_specification():
    assert digest(PREPARATION) == PREPARATION_SHA
    saved = json.loads(gzip.decompress(PREPARATION.read_bytes()))
    assert saved['source_sha256'] == digest(Path(preparation.__file__))
    assert saved['Gram_source_sha256'] == digest(Path(gram_screen.__file__))
    data = preparation.load()
    domain, rows, gram, pairs, columns, conflicts, _ = data
    specs, direct, coverage = preparation.supports(domain, gram, pairs, columns, conflicts)
    assert coverage == saved['coverage']
    formula = preparation.formula_counts(specs, direct, len(pairs), 960)
    assert formula == saved['formula']
    assert formula['projected_total_variables'] == 1478076
    assert formula['projected_total_clauses'] == 3173640
    assert len(specs) == 2160 and len(direct) == 180
    assert saved['column_order_sha256'] == components.sha(canonical(columns))
    return data, specs, direct, saved


def stream_cnf(path, specs, direct, expected):
    """Write one counter at a time, with one shared monotone auxiliary pool."""
    assert not path.exists()
    initial = expected['independent_column_variables']+expected['derived_component_selection_variables']
    pool = IDPool(start_from=initial+1)
    predicted_variables, predicted_clauses = expected['projected_total_variables'], expected['projected_total_clauses']
    total_clauses, literal_count, max_variable = 0, 0, initial
    full_hash = hashlib.sha256()
    blocks = []
    current = None
    header = f'p cnf {predicted_variables} {predicted_clauses}\n'.encode()
    with path.open('xb') as output:
        output.write(header)
        full_hash.update(header)
        def start_group(kind):
            nonlocal current
            if current is not None and current['kind'] == kind:
                return
            if current is not None:
                current['body_sha256'] = current.pop('_hash').hexdigest()
                current['last_auxiliary_variable'] = pool.top
                blocks.append(current)
            current = {'kind':kind, 'first_clause_number':total_clauses+1,
                       'counter_rows':0, 'clauses':0, 'literal_occurrences':0,
                       'first_new_auxiliary_variable':pool.top+1, '_hash':hashlib.sha256()}
        def write_clause(clause):
            nonlocal total_clauses, literal_count, max_variable
            assert clause and all(type(v) is int and v for v in clause)
            line = (' '.join(map(str,clause))+' 0\n').encode()
            output.write(line)
            full_hash.update(line)
            current['_hash'].update(line)
            total_clauses += 1
            literal_count += len(clause)
            max_variable = max(max_variable,*(abs(v) for v in clause))
            current['clauses'] += 1
            current['literal_occurrences'] += len(clause)
        for item in specs:
            start_group(item['kind'])
            before = pool.top
            method = CardEnc.equals if item['encoding'] == 'equals' else CardEnc.atmost
            assert item['encoding'] in ('equals','atmost')
            cnf = method(item['literals'],item['quota'],vpool=pool,encoding=EncType.seqcounter)
            statistics = preparation.encoding_size(item['encoding'],len(item['literals']),item['quota'])
            assert pool.top-before == statistics['variables']
            assert len(cnf.clauses) == statistics['clauses']
            assert sum(map(len,cnf.clauses)) == statistics['literal_occurrences']
            current['counter_rows'] += 1
            for clause in cnf.clauses:
                write_clause(clause)
        start_group('component motif')
        for clause in direct:
            assert len(clause) == 2 and all(-initial <= v < -expected['independent_column_variables'] for v in clause)
            write_clause(clause)
        current['body_sha256'] = current.pop('_hash').hexdigest()
        current['last_auxiliary_variable'] = pool.top
        blocks.append(current)
    assert pool.top == max_variable == predicted_variables
    assert total_clauses == predicted_clauses
    assert literal_count == expected['projected_literal_occurrences']
    assert path.stat().st_size <= expected['safe_DIMACS_byte_upper_bound']
    assert digest(path) == full_hash.hexdigest()
    return {'variables':max_variable,'clauses':total_clauses,'literal_occurrences':literal_count,
            'cnf_sha256':full_hash.hexdigest(),'cnf_bytes':path.stat().st_size,
            'clause_blocks':blocks,'counter_rows':len(specs),'direct_clauses':len(direct),
            'initial_primary_and_derived_variables':initial,
            'all_auxiliaries_allocated_by_one_IDPool':True,
            'formula_streamed_one_counter_at_a_time':True,
            'full_formula_list_kept_in_memory':False}


def incidence_check(core, gram, columns, degree):
    n, m = len(core), len(columns)
    assert len({tuple(h) for h in columns}) == m
    actual = [[0]*n for _ in range(n)]
    masks = []
    for h in columns:
        assert h == sorted(set(h)) and all(0 <= i < n for i in h)
        masks.append(sum(1 << i for i in h))
        for i in h:
            for j in h:
                actual[i][j] += 1
    assert actual == gram
    assert all(((row | (1 << i))&mask).bit_count() <= 2
               for mask in masks for i,row in enumerate(core))
    assert all((masks[a]&masks[b]).bit_count() <= 2 for a,b in combinations(range(m),2))
    packing = Counter(t for h in columns for t in combinations(h,3))
    assert max(packing.values(),default=0) <= 1
    rows = list(core)+[0]*m
    for outside,h in enumerate(columns,n):
        for i in h:
            components.edge(rows,outside,i)
    assert [row.bit_count() for row in rows[:n]] == [degree]*n
    assert [row.bit_count() for row in rows[n:]] == [len(h) for h in columns]
    assert components.caps(rows)
    return rows, packing


def all_chords_forbidden(rows):
    assert components.caps(rows)
    for a,b in combinations(range(len(rows)),2):
        if not rows[a] >> b & 1:
            extra = list(rows)
            components.edge(extra,a,b)
            assert not components.caps(extra)


def visible_motifs(rows):
    triangles = [t for t in combinations(range(len(rows)),3)
                 if all(rows[a] >> b & 1 for a,b in combinations(t,2))]
    prisms = []
    for a,b in combinations(triangles,2):
        if set(a)&set(b):
            continue
        if all(sum(rows[u] >> v & 1 for v in b) == 1 for u in a) and all(
               sum(rows[v] >> u & 1 for u in a) == 1 for v in b):
            sites = list(a+b)
            induced = motifs.induced(rows,sites)
            assert motifs.is_prism(induced)
            all_chords_forbidden(induced)
            prisms.append(sorted(sites))
    found = []
    for u,v in combinations(range(len(rows)),2):
        if not rows[u] >> v & 1:
            continue
        left = [a for a in range(len(rows)) if a != v and rows[u] >> a & 1 and not rows[v] >> a & 1]
        right = [a for a in range(len(rows)) if a != u and rows[v] >> a & 1 and not rows[u] >> a & 1]
        le = [(a,b) for a,b in combinations(left,2) if rows[a] >> b & 1]
        re = [(a,b) for a,b in combinations(right,2) if rows[a] >> b & 1]
        for l1,l2 in combinations(le,2):
            if set(l1)&set(l2):
                continue
            for r1,r2 in combinations(re,2):
                if set(r1)&set(r2):
                    continue
                sites = [u,v,*l1,*l2,*r1,*r2]
                induced = motifs.induced(rows,sites)
                if motifs.is_F(induced):
                    all_chords_forbidden(induced)
                    found.append(sites)
    return {'visible_prism_count':len(prisms),'visible_prism_supports':prisms,
            'visible_F_count':len(found),'visible_F_supports':found,
            'each_visible_motif_missing_chord_forbidden_by_caps':True,
            'absence_of_future_motifs_not_claimed':True}


def inspect(true_primary, data, specs, direct, saved):
    domain, core, gram, pairs, columns, conflicts, _ = data
    n, initial = len(pairs), len(pairs)+960
    assert true_primary == sorted(set(true_primary))
    assert all(type(v) is int and 1 <= v <= initial for v in true_primary)
    truth = set(true_primary)
    for item in specs:
        count = sum((lit in truth) if lit > 0 else (-lit not in truth) for lit in item['literals'])
        assert count == item['quota'] if item['encoding'] == 'equals' else count <= item['quota']
    assert all(any((lit in truth) if lit > 0 else (-lit not in truth) for lit in clause) for clause in direct)
    selected = [v-1 for v in true_primary if v <= n]
    assert len(selected) == 60
    chosen = [pairs[i] for i in selected]
    component_selected = [sorted(a[side] for a in chosen) for side in range(2)]
    assert all(len(set(row)) == 60 for row in component_selected)
    for side in range(2):
        expected = {n+1+480*side+i for i in component_selected[side]}
        actual = {v for v in truth if n+1+480*side <= v < n+1+480*(side+1)}
        assert expected == actual
    paired = [columns[i] for i in selected]
    assert all(len(h) == 6 and all(sum((v-3 if v<21 else v-21)//6 == f for v in h) == 2
                                 for f in range(3)) for h in paired)
    rows, packing = incidence_check(core,gram,paired,14)
    assert len(rows) == 99 and [row.bit_count() for row in rows] == [14]*39+[6]*60
    visible = visible_motifs(rows)
    return {'status':'exact full39-core incidence and primary constraints checked; exterior edges unspecified',
            'true_primary_variables':true_primary,'selected_column_indices':selected,
            'selected_component_triple_indices':component_selected,
            'selected_pairs':[list(p) for p in chosen],'six_neighbor_columns':paired,
            'full39_Gram_entries_checked':1521,'outside_pair_caps_checked':1770,
            'known_partial_graph_caps_checked':4851,'core_triple_packing_max':max(packing.values()),
            'both_component_motif_clause_families_hold':True,
            'partial99_rows':[str(row) for row in rows],'visible_motifs':visible,
            'satisfies_all_checked_visible_PF_restrictions':not(visible['visible_prism_count'] or visible['visible_F_count']),
            'exterior_edges_still_required':240,'full_graph_completion':False,
            'fixed_component_incidence_designs':False}


def controls():
    rook = lambda a,b:a != b and (a//3 == b//3 or a%3 == b%3)
    sites = [0,1,3,4]
    core = [sum(int(rook(v,w)) << j for j,w in enumerate(sites)) for v in sites]
    columns = [[i for i,w in enumerate(sites) if rook(v,w)] for v in range(9) if v not in sites]
    gram = [[2*int(i == j)+2-(core[i]&core[j]).bit_count()-(core[i] >> j & 1)
             for j in range(4)] for i in range(4)]
    rows, _ = incidence_check(core,gram,columns,4)
    assert len(rows) == 9
    rejected = 0
    for modified in (columns[1:], columns+[columns[0]]):
        try:
            incidence_check(core,gram,modified,4)
        except AssertionError:
            rejected += 1
    assert rejected == 2
    prism = [0]*6
    for a,b in ((0,1),(0,2),(1,2),(3,4),(3,5),(4,5),(0,3),(1,4),(2,5)):
        components.edge(prism,a,b)
    assert motifs.is_prism(prism)
    all_chords_forbidden(prism)
    f = [0]*10
    components.edge(f,0,1)
    # Eight-cycle with repeated color sequence0011; same-color cycle
    # edges are the two side matchings, and opposite colors are cross edges.
    for i in range(8):
        components.edge(f,2+i,2+(i+1)%8)
        components.edge(f,0 if i%4 < 2 else 1,2+i)
    # Reorder the two four-point sides to the is_F convention.
    order = [0,1]+[2+i for i in range(8) if i%4 < 2]+[2+i for i in range(8) if i%4 >= 2]
    f = list(components.permute(f,order))
    assert motifs.is_F(f)
    all_chords_forbidden(f)
    return {'rook9_actual_incidence_positive_control':True,
            'deleted_or_repeated_actual_column_controls_rejected':rejected,
            'prism_chords_checked':6,'F_chords_checked':28,
            'full_model_solved':False,'solver_called':False}


def prepare(model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    control = controls()
    data, specs, direct, saved = load_specification()
    actual = stream_cnf(cnf_path,specs,direct,saved['formula'])
    model = {'status':'complete unfixed incidence CNF built; no solver called',
             'scope':saved['scope'],'source_hashes':{name:digest(Path(__file__).with_name(name)) for name in SOURCE_NAMES},
             'preparation':portable(PREPARATION),'preparation_sha256':PREPARATION_SHA,
             'Gram_certificate_sha256':preparation.GRAM_SHA,
             'component_motif_certificate_sha256':preparation.PAIR_SHA,
             'full_specification_sha256':saved['formula']['full_specification_sha256'],
             'column_order_sha256':saved['column_order_sha256'],
             'core_rows_sha256':components.sha(canonical(data[1])),
             'Gram_sha256':components.sha(canonical(data[2])),
             'formula':actual,'cnf':str(cnf_path),'cnf_sha256':actual['cnf_sha256'],
             'controls':control,'fixed_incidence_designs':False,'graph_symmetry_constraints':False,
             'full_primary_assignment_inspector':True,'exterior_adjacency_variables':0,
             'SAT_scope':'sixty-column incidence candidate; all exterior adjacency remains unmodeled',
             'UNSAT_scope':'complete component0 pair with identity relative fiber alignment only',
             'solver_called':False,'elapsed_seconds':time.monotonic()-started}
    model_path.write_text(json.dumps(model,indent=2)+'\n')
    print(json.dumps(model,indent=2),flush=True)


def checked_model(path):
    model = json.loads(path.read_text())
    for name,value in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == value
    assert model['preparation_sha256'] == PREPARATION_SHA
    assert model['fixed_incidence_designs'] is False and model['graph_symmetry_constraints'] is False
    return model


def replay(model_path, output):
    assert not output.exists()
    model = checked_model(model_path)
    data, specs, direct, saved = load_specification()
    with tempfile.TemporaryDirectory(prefix='conway-f0-pair-gram-replay-') as directory:
        actual = stream_cnf(Path(directory)/'rebuilt.cnf',specs,direct,saved['formula'])
    assert actual == model['formula']
    assert actual['cnf_sha256'] == model['cnf_sha256']
    assert components.sha(canonical(data[1])) == model['core_rows_sha256']
    assert components.sha(canonical(data[2])) == model['Gram_sha256']
    report = {'status':'cold complete domain, constraints and streamed CNF replay passed',
              'model_sha256':digest(model_path),'cnf_sha256':actual['cnf_sha256'],
              'variables':actual['variables'],'clauses':actual['clauses'],
              'fixed_incidence_designs':False,'solver_called':False}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    control = commands.add_parser('controls')
    control.add_argument('--output',type=Path,required=True)
    build = commands.add_parser('prepare')
    build.add_argument('--model',type=Path,required=True)
    build.add_argument('--cnf',type=Path,required=True)
    check = commands.add_parser('replay')
    check.add_argument('--model',type=Path,required=True)
    check.add_argument('--output',type=Path,required=True)
    point = commands.add_parser('inspect')
    point.add_argument('--model',type=Path,required=True)
    point.add_argument('--assignment',type=Path,required=True)
    point.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'controls':
        assert not args.output.exists()
        result = {'source_sha256':digest(Path(__file__)),**controls()}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2),flush=True)
    elif args.command == 'prepare':
        prepare(args.model.resolve(),args.cnf.resolve())
    elif args.command == 'replay':
        replay(args.model.resolve(),args.output.resolve())
    else:
        assert not args.output.exists()
        model = checked_model(args.model.resolve())
        data,specs,direct,saved = load_specification()
        assert saved['formula']['full_specification_sha256'] == model['full_specification_sha256']
        assignment = json.loads(args.assignment.read_text())
        result = inspect(assignment['true_primary_variables'],data,specs,direct,saved)
        result.update(model_sha256=digest(args.model),assignment_sha256=digest(args.assignment))
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('partial99_rows','six_neighbor_columns')},indent=2),flush=True)
