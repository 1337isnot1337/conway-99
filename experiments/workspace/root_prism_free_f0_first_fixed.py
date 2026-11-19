"""Fix the first checked component incidence, leaving all second triples free.

This is a 5,472-column incidence model, not an exterior-edge completion.
Preparation, streamed CNF construction, replay, and primary inspection
call no SAT solver. The saved rational point checks the linear primary
specification only; it is not a Boolean or CNF witness.
"""

import argparse
from collections import Counter, defaultdict
import gzip
from itertools import combinations
import json
from pathlib import Path
import tempfile
import time

import root_prism_free_f0_pair_gram_model as complete
import root_prism_free_f0_pair_gram_build as streamed
import root_prism_free_f0_coupling as coupling


ROOT, LOGS = complete.ROOT, complete.LOGS
COUPLING = LOGS/'f0-coupling-certificate.json.gz'
COUPLING_SHA = 'bbe73089b6ae19b25ebb43597195ee81682202e3139e627fbc75db427a5c4cc7'
SOURCE_NAMES = ('root_prism_free_f0_first_fixed.py',
                'root_prism_free_f0_pair_gram_model.py',
                'root_prism_free_f0_pair_gram_build.py',
                'root_prism_free_f0_pair_gram.py',
                'root_prism_free_f0_coupling.py',
                'root_prism_free_f0_components.py',
                'root_prism_free_f0_pair_clauses.py')
digest, canonical = complete.digest, complete.canonical
sha = complete.components.sha


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def sources():
    return {name:digest(Path(__file__).with_name(name)) for name in SOURCE_NAMES}


def load():
    assert digest(COUPLING) == COUPLING_SHA
    saved = json.loads(gzip.decompress(COUPLING.read_bytes()))
    assert saved['source_sha256'] == digest(Path(coupling.__file__))
    assert digest(coupling.RESULT) == coupling.RESULT_SHA == saved['fixed_incidence_result_sha256']
    first = json.loads(coupling.RESULT.read_text())
    assert first['case'] == 0 and first['status'].startswith('SAT;')
    domain,core,gram,_,_,conflicts,_ = complete.load()
    selected = saved['first_selected_domain_indices']
    assert selected == first['incidence_witness']['selected_columns']
    assert selected == sorted(set(selected)) and len(selected) == 60
    coupling.check_design(domain,selected,conflicts)
    triples = domain['signature_domain']
    design = [triples[i] for i in selected]
    assert saved['fixed_design'] == design
    assert core == list(map(int,saved['joined39_core_rows'])) and gram == saved['joined39_Gram']
    pairs = [(a,b) for a,h in enumerate(design) for b,k in enumerate(triples)
             if all(x+y == 2 for x,y in zip(coupling.profile(h),coupling.profile(k)))]
    assert len(pairs) == 5472
    columns = [[3+i for i in design[a]]+[21+j for j in triples[b]] for a,b in pairs]
    assert len({tuple(h) for h in columns}) == len(columns)
    for h in columns:
        assert len(h) == 6 and h == sorted(set(h))
        mask = sum(1 << i for i in h)
        assert all(gram[i][j] > 0 for i,j in combinations(h,2))
        assert all(((row | (1 << i))&mask).bit_count() <= 2 for i,row in enumerate(core))
    return domain,selected,design,pairs,columns,core,gram,conflicts,saved


def specification(data):
    domain,selected,design,pairs,columns,core,gram,conflicts,_ = data
    triples = domain['signature_domain']
    n = len(pairs)
    second_ids = [n+1+b for b in range(480)]
    first_members = [[] for _ in range(60)]
    second_members = [[] for _ in range(480)]
    cross_members = [[[] for _ in range(18)] for _ in range(18)]
    triple_members = defaultdict(list)
    for variable,((a,b),h) in enumerate(zip(pairs,columns),1):
        first_members[a].append(variable)
        second_members[b].append(variable)
        for i in design[a]:
            for j in triples[b]:
                cross_members[i][j].append(variable)
        for sites in combinations(h,3):
            triple_members[sites].append(variable)
    specs = []
    def add(kind,label,encoding,literals,quota):
        assert literals and len({abs(x) for x in literals}) == len(literals)
        assert encoding in ('equals','atmost') and 0 <= quota <= len(literals)
        specs.append({'kind':kind,'label':label,'encoding':encoding,
                      'literals':literals,'quota':quota})
    for a,members in enumerate(first_members):
        add('fixed first row',[a],'equals',members,1)
    for b,members in enumerate(second_members):
        # sum(x)+(1-v)=1 is equivalent to sum(x)=v, including at most one.
        add('second component link',[b],'equals',members+[-second_ids[b]],1)
    local_coverage,seen = [],{}
    for i in range(18):
        for j in range(i,18):
            members = [second_ids[b] for b,h in enumerate(triples) if i in h and j in h]
            quota = gram[21+i][21+j]
            key = tuple(members),quota
            if key not in seen:
                seen[key] = None
                if members:
                    seen[key] = len(specs)
                    add('second component Gram',[i,j],'equals',members,quota)
                else:
                    assert quota == 0
            local_coverage.append([i,j,quota,len(members),seen[key]])
    for i in range(18):
        for j in range(18):
            add('cross Gram',[i,j],'equals',cross_members[i][j],gram[3+i][21+j])
    motifs = sorted({tuple(item['columns']) for family in ('F_conflicts','prism_conflicts')
                     for item in conflicts[family]})
    assert len(motifs) == 90
    chosen = set(selected)
    assert all(not {a,b} <= chosen for a,b in motifs)
    direct = [[-second_ids[a],-second_ids[b]] for a,b in motifs]
    packing_coverage = []
    first_position = {tuple(h):a for a,h in enumerate(design)}
    second_position = {tuple(h):b for b,h in enumerate(triples)}
    for sites in combinations(range(3,39),3):
        members = triple_members.get(sites,[])
        if len(members) <= 1:
            reason = 'at most one candidate'
        elif sites[-1] < 21:
            a = first_position[tuple(i-3 for i in sites)]
            assert members == first_members[a]
            reason = 'fixed first row at most one'
        elif sites[0] >= 21:
            b = second_position[tuple(i-21 for i in sites)]
            assert members == second_members[b]
            reason = 'second component link at most one'
        elif any(gram[i][j] == 1 for i,j in combinations(sites,2)):
            # First-side quota-one rows hold identically once first row
            # quotas hold; second/cross quota-one rows are explicit.
            reason = 'quota-one Gram pair'
        else:
            assert all(gram[i][j] == 2 for i,j in combinations(sites,2))
            reason = 'explicit mixed triple capacity'
            add('mixed triple packing',list(sites),'atmost',members,1)
        packing_coverage.append([list(sites),len(members),reason])
    assert len(packing_coverage) == 7140 and len(local_coverage) == 171
    assert sum(map(len,first_members)) == sum(map(len,second_members)) == n
    assert sum(len(row) for table in cross_members for row in table) == 9*n
    first_gram = [[sum(i in h and j in h for h in design) for j in range(18)] for i in range(18)]
    assert first_gram == [row[3:21] for row in gram[3:21]]
    return specs,direct,{'first_component_Gram':first_gram,
                         'first_component_Gram_follows_from_60_row_equalities':True,
                         'second_component_Gram_positions':local_coverage,
                         'cross_Gram_positions':324,'zero_central_Gram_positions':114,
                         'all_shell_core_triple_positions':packing_coverage,
                         'second_selector_ids':second_ids,
                         'first_component_motif_pairs_checked':90,
                         'second_component_motif_pairs_imposed':90,
                         'motif_family_sizes':{name:len(conflicts[name]) for name in ('F_conflicts','prism_conflicts')}}


def counts(specs,direct,n):
    answer = complete.formula_counts(specs,direct,n,480)
    for key in ('optional_two_population_rows_extra_variables','optional_two_population_rows_extra_clauses'):
        del answer[key]
    answer['population_60_follows_from_component_Gram_diagonal_sum'] = True
    answer['population_60_follows_from_fixed_first_row_quotas'] = True
    return answer


def fractional_control(data,specs,direct):
    domain,selected,design,pairs,columns,core,gram,conflicts,saved = data
    fraction = saved['fractional_control']
    denominator = fraction['denominator']
    assert denominator == 144
    index = {pair:i for i,pair in enumerate(pairs)}
    values = [0]*(len(pairs)+480)
    for a,b,weight in fraction['weights']:
        assert type(weight) is int and 0 < weight <= denominator
        i = index[a,b]
        assert values[i] == 0
        values[i] = weight
        values[len(pairs)+b] += weight
    assert all(0 <= v <= denominator for v in values)
    for item in specs:
        total = sum(values[lit-1] if lit > 0 else denominator-values[-lit-1]
                    for lit in item['literals'])
        if item['encoding'] == 'equals':
            assert total == denominator*item['quota']
        else:
            assert total <= denominator*item['quota']
    assert all(sum(values[-lit-1] for lit in clause) <= denominator for clause in direct)
    actual = [[0]*39 for _ in range(39)]
    for weight,h in zip(values,columns):
        for i in h:
            for j in h:
                actual[i][j] += weight
    assert actual == [[denominator*v for v in row] for row in gram]
    return {'status':'exact rational primary-specification control passed',
            'common_denominator':denominator,'positive_column_weights':sum(v > 0 for v in values[:len(pairs)]),
            'second_triples_with_positive_weight':sum(v > 0 for v in values[len(pairs):]),
            'all_constraint_rows_checked':len(specs),'all90_second_motif_inequalities_checked':True,
            'full39_Gram_entries_checked':1521,
            'Boolean_or_CNF_witness':False,'additional_constraint_imposed_from_fractional_point':False}


def calculate():
    started = time.monotonic()
    data = load()
    domain,selected,design,pairs,columns,core,gram,conflicts,_ = data
    specs,direct,coverage = specification(data)
    return data,specs,direct,{'status':'complete fixed-first/full-second incidence preparation; no solver',
            'source_hashes':sources(),'coupling_certificate_sha256':COUPLING_SHA,
            'Gram_certificate_sha256':complete.GRAM_SHA,'motif_certificate_sha256':complete.PAIR_SHA,
            'first_incidence_result_sha256':coupling.RESULT_SHA,
            'scope':'component0 paired with component0, identity fibers; only first saved60-triple design fixed',
            'first_selected_domain_indices':selected,'first_design':design,
            'second_domain_triples':domain['signature_domain'],'pairs':[list(p) for p in pairs],
            'core_rows':[str(row) for row in core],'Gram':gram,
            'column_order_sha256':sha(canonical(columns)),
            'pair_order_sha256':sha(canonical(pairs)),
            'full_second_domain_size':480,'full_paired_domain_size':5472,
            'first_profile_counts':[[list(p),count] for p,count in sorted(Counter(map(coupling.profile,design)).items())],
            'coverage':coverage,'formula':counts(specs,direct,len(pairs)),
            'fractional_control':fractional_control(data,specs,direct),
            'controls':{'counter_and_link':complete.controls(),'rook_and_inspector':streamed.controls()},
            'second_incidence_fixed':False,'graph_symmetry_constraints':False,
            'exterior_adjacency_variables':0,'solver_called':False,
            'elapsed_seconds_for_information_only':time.monotonic()-started}


def saved_specification(path):
    saved = json.loads(gzip.decompress(path.read_bytes()))
    for name,value in saved['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == value
    data,specs,direct,actual = calculate()
    actual['elapsed_seconds_for_information_only'] = saved['elapsed_seconds_for_information_only']
    assert actual == saved
    return data,specs,direct,saved


def inspect(true_primary,data,specs,direct):
    domain,selected,design,pairs,columns,core,gram,conflicts,_ = data
    n = len(pairs)
    assert true_primary == sorted(set(true_primary))
    assert all(type(v) is int and 1 <= v <= n+480 for v in true_primary)
    truth = set(true_primary)
    for item in specs:
        total = sum(lit in truth if lit > 0 else -lit not in truth for lit in item['literals'])
        assert total == item['quota'] if item['encoding'] == 'equals' else total <= item['quota']
    assert all(any(lit in truth if lit > 0 else -lit not in truth for lit in clause) for clause in direct)
    chosen = [i-1 for i in true_primary if i <= n]
    assert len(chosen) == 60
    selected_pairs = [pairs[i] for i in chosen]
    assert sorted(a for a,b in selected_pairs) == list(range(60))
    seconds = sorted(b for a,b in selected_pairs)
    assert len(set(seconds)) == 60
    assert {v for v in truth if v > n} == {n+1+b for b in seconds}
    paired = [columns[i] for i in chosen]
    rows,packing = streamed.incidence_check(core,gram,paired,14)
    assert len(rows) == 99 and [row.bit_count() for row in rows] == [14]*39+[6]*60
    visible = streamed.visible_motifs(rows)
    return {'status':'exact fixed-first/full-second39-core incidence checked; exterior edges unspecified',
            'true_primary_variables':true_primary,'selected_column_indices':chosen,
            'selected_pairs':[list(p) for p in selected_pairs],
            'first_selected_domain_indices':selected,'second_selected_domain_indices':seconds,
            'six_neighbor_columns':paired,'full39_Gram_entries_checked':1521,
            'known_partial_graph_caps_checked':4851,'outside_pair_caps_checked':1770,
            'core_triple_packing_max':max(packing.values()),
            'both_component_motif_families_hold':True,
            'partial99_rows':[str(row) for row in rows],'visible_motifs':visible,
            'satisfies_all_checked_visible_PF_restrictions':not(visible['visible_prism_count'] or visible['visible_F_count']),
            'exterior_edges_still_required':240,'full_graph_completion':False,
            'only_first_saved_incidence_fixed':True,'second_domain_restricted_to_saved_design':False}


def build(preparation_path,model_path,cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    data,specs,direct,saved = saved_specification(preparation_path)
    formula = streamed.stream_cnf(cnf_path,specs,direct,saved['formula'])
    model = {'status':'fixed-first/full-second incidence CNF built; no solver',
             'source_hashes':sources(),'preparation':portable(preparation_path),
             'preparation_sha256':digest(preparation_path),'scope':saved['scope'],
             'formula':formula,'cnf':str(cnf_path),'cnf_sha256':formula['cnf_sha256'],
             'full_specification_sha256':saved['formula']['full_specification_sha256'],
             'column_order_sha256':saved['column_order_sha256'],'pair_order_sha256':saved['pair_order_sha256'],
             'core_rows_sha256':sha(canonical(data[5])),'Gram_sha256':sha(canonical(data[6])),
             'only_first_saved_incidence_fixed':True,'second_incidence_fixed':False,
             'graph_symmetry_constraints':False,'full_primary_assignment_inspector':True,
             'SAT_scope':'sixty-column incidence candidate with all exterior adjacency still unspecified',
             'UNSAT_scope':'only the specified first60-triple design with component0 partner and identity alignment',
             'solver_called':False,'elapsed_seconds':time.monotonic()-started}
    model_path.write_text(json.dumps(model,indent=2)+'\n')
    print(json.dumps(model,indent=2),flush=True)


def checked_model(path):
    model = json.loads(path.read_text())
    for name,value in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == value
    preparation_path = ROOT/model['preparation']
    assert digest(preparation_path) == model['preparation_sha256']
    assert model['only_first_saved_incidence_fixed'] is True and model['second_incidence_fixed'] is False
    assert model['graph_symmetry_constraints'] is False
    data,specs,direct,saved = saved_specification(preparation_path)
    assert saved['formula']['full_specification_sha256'] == model['full_specification_sha256']
    assert saved['column_order_sha256'] == model['column_order_sha256']
    assert saved['pair_order_sha256'] == model['pair_order_sha256']
    assert sha(canonical(data[5])) == model['core_rows_sha256'] and sha(canonical(data[6])) == model['Gram_sha256']
    return model,data,specs,direct,saved


def replay(model_path,output):
    assert not output.exists()
    model,data,specs,direct,saved = checked_model(model_path)
    with tempfile.TemporaryDirectory(prefix='conway-f0-first-fixed-replay-') as directory:
        actual = streamed.stream_cnf(Path(directory)/'replay.cnf',specs,direct,saved['formula'])
    assert actual == model['formula'] and actual['cnf_sha256'] == model['cnf_sha256']
    report = {'status':'cold complete fixed-first/full-second domain and CNF replay passed',
              'model_sha256':digest(model_path),'cnf_sha256':actual['cnf_sha256'],
              'variables':actual['variables'],'clauses':actual['clauses'],
              'full_paired_domain_size':5472,'only_first_saved_incidence_fixed':True,
              'second_incidence_fixed':False,'solver_called':False}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--output',type=Path,required=True)
    prepare.add_argument('--replay',action='store_true')
    assemble = commands.add_parser('build')
    assemble.add_argument('--preparation',type=Path,required=True)
    assemble.add_argument('--model',type=Path,required=True)
    assemble.add_argument('--cnf',type=Path,required=True)
    verify = commands.add_parser('replay')
    verify.add_argument('--model',type=Path,required=True)
    verify.add_argument('--output',type=Path,required=True)
    point = commands.add_parser('inspect')
    point.add_argument('--model',type=Path,required=True)
    point.add_argument('--assignment',type=Path,required=True)
    point.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        if args.replay:
            _,_,_,saved = saved_specification(args.output)
        else:
            assert not args.output.exists()
            _,_,_,saved = calculate()
            args.output.write_bytes(gzip.compress(canonical(saved)+b'\n',mtime=0))
        print(json.dumps({k:v for k,v in saved.items() if k not in ('coverage','formula','pairs','core_rows','Gram','second_domain_triples')}
                         | {'formula':{k:v for k,v in saved['formula'].items() if k != 'constraint_support_summaries'}},indent=2),flush=True)
    elif args.command == 'build':
        build(args.preparation.resolve(),args.model.resolve(),args.cnf.resolve())
    elif args.command == 'replay':
        replay(args.model.resolve(),args.output.resolve())
    else:
        assert not args.output.exists()
        model,data,specs,direct,_ = checked_model(args.model.resolve())
        assignment = json.loads(args.assignment.read_text())
        result = inspect(assignment['true_primary_variables'],data,specs,direct)
        result.update(model_sha256=digest(args.model),assignment_sha256=digest(args.assignment))
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('partial99_rows','six_neighbor_columns')},indent=2),flush=True)
