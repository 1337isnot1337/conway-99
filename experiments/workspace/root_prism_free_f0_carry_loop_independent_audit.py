"""Read-only standard-library audit of the carry loop's inherited predicates.

No subject imports, CNF regeneration, optimizer, SAT call or proof checker.
The compact carry encoder has a separate independent audit.
"""

import ast
from collections import Counter
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import time


ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'experiments/workspace'
LOGS=ROOT/'experiments/logs/root-prism-free'
SOURCE=WORK/'root_prism_free_f0_carry_row_loop.py'
WRAPPER=WORK/'root_prism_free_f0_carry_row_loop_certificate.py'
PREPARATION=LOGS/'f0-carry-row-loop-preparation.json.gz'
BINDINGS={
    SOURCE:'ec85c752a5d3c5538250e0099286dcbad674e23ef9572f72bbd3ca72fb5ef403',
    WRAPPER:'6ed58e8656b5a46a8dd14e6064495dbfe2960d8916bdabc85b54ec22cd3d557a',
    PREPARATION:'b43aedd6dda33b3b0415865831fb48e87610815f4f3659d7a59f8c5c84b0eb9e',
    LOGS/'f0-symmetric-row-loop-preparation.json.gz':'ac320bcd92d1e801fc027ca7776ad97ebe978628b530caa67ceb5d770c992a55',
    LOGS/'f0-symmetric-row-loop-run01/result.json':'03c7cfa9cfde1a23df0e3b3b2ffe6e1650801eaf5daf9e79a0403f45574fd20b',
    LOGS/'f0-symmetric-row-loop-run01-cold-replay.json':'fb5cde46be5506f4edb30323f3a17ce2a96f929c631dc8662b02d50ae1d655ec',
    LOGS/'f0-incidence-case00-model.json':'16deda266149f5123a1db3833cfebf22d6bdfe4426b1424fcc51ccbfdc38f0a1',
    LOGS/'f0-first-design-exterior-row-certificate.json.gz':'3b5c302f9a9e3bfce6175de7c73cb835cc89f88e63148de15d59085b1da974c0'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def normal_terms(terms,demand):
    merged=Counter()
    for literal,weight in terms:
        assert type(literal) is int and 1<=abs(literal)<=480
        assert type(weight) is int and weight>0
        merged[literal]+=weight
    capped=sorted((literal,min(weight,demand)) for literal,weight in merged.items())
    divisor=gcd(*(weight for _,weight in capped)) if capped else 1
    return [[literal,weight//divisor] for literal,weight in capped],(demand+divisor-1)//divisor,divisor


class StatusOnly(ast.NodeTransformer):
    VALUES={
        'RUNNING: free480 carry-encoded individual/shared-row loop':'RUNNING: free480 individual/shared-row loop',
        'conway-f0-carry-initial-':'conway-f0-symmetric-initial-',
        'conway-f0-carry-final-':'conway-f0-symmetric-final-',
        'cold complete carry formula, all192 proved cuts and prior exact candidate prefixes replay PASS':
            'cold complete initial incidence/signed-cut formula and dynamic shared helper replay PASS',
        'cold complete carry final formula, candidate prefixes, exact individual/shared witnesses and lifts replay PASS':
            'cold complete final formula, candidate prefixes, exact individual/shared witnesses and lifts replay PASS'}

    def visit_Constant(self,node):
        if isinstance(node.value,str) and node.value in self.VALUES:
            return ast.copy_location(ast.Constant(self.VALUES[node.value]),node)
        return node


def functions(path,normalize=False):
    tree=ast.parse(path.read_text())
    if normalize:
        tree=StatusOnly().visit(tree)
    return {node.name:ast.dump(node,include_attributes=False)
            for node in tree.body if isinstance(node,ast.FunctionDef)}


def audit():
    started=time.monotonic()
    for path,sha in BINDINGS.items():
        assert digest(path)==sha
    prepared=read(PREPARATION)
    for name,sha in prepared['dependency_source_hashes'].items():
        assert digest(WORK/name)==sha
    for name,sha in prepared['parent_terminal_bindings'].items():
        assert digest(ROOT/name)==sha
    old_source=WORK/'root_prism_free_f0_symmetric_row_loop.py'
    old_wrapper=WORK/'root_prism_free_f0_symmetric_row_loop_certificate.py'
    old_functions,new_functions=functions(old_source),functions(SOURCE,True)
    unchanged=['signed_cut','signed_outcomes','inspect','counters','symmetric_candidates','run','reconstruct']
    assert all(new_functions[name]==old_functions[name] for name in unchanged)
    wrapper_functions=functions(WRAPPER)
    assert wrapper_functions==functions(old_wrapper)

    parent=read(LOGS/'f0-symmetric-row-loop-run01/result.json')
    old_rows=read(ROOT/parent['individual-registry'])
    old_signed=read(ROOT/parent['symmetric-registry'])
    assert digest(ROOT/parent['individual-registry'])==parent['individual-registry_sha256']
    assert digest(ROOT/parent['symmetric-registry'])==parent['symmetric-registry_sha256']
    rows,signed=prepared['initial_individual_cuts'],prepared['initial_symmetric_cuts']
    assert rows==old_rows and len(rows)==168
    assert signed[:20]==old_signed and len(signed)==24
    assert len({cut['normalized_predicate_sha256'] for cut in rows})==168
    assert len({cut['predicate_sha256'] for cut in signed})==24
    last=parent['iterations'][-1]
    lifted=read(ROOT/last['symmetric_lift'])
    assert digest(ROOT/last['symmetric_lift'])==last['symmetric_lift_sha256']
    reconstructed=list(old_signed)
    by_key={cut['predicate_sha256']:i for i,cut in enumerate(reconstructed)}
    maps=[]
    for transport in lifted['transported_cuts']:
        terms=transport['signed_coefficients']
        divisor=gcd(*(abs(c) for _,c in terms))
        normalized=[[a,c//divisor] for a,c in terms]
        origin={'kind':'loop exact shared-row lift','iteration':last['iteration'],
                'shared_result_sha256':last['shared_rows_sha256'],'core_action_index':transport['core_action_index']}
        key=hashlib.sha256(canonical(normalized)).hexdigest()
        cut={'signed_coefficients':normalized,'origin':origin,'predicate_sha256':key}
        added=key not in by_key
        if added:
            by_key[key]=len(reconstructed);reconstructed.append(cut)
        maps.append({'origin':origin,'registry_index':by_key[key],'new_cut':added})
    assert reconstructed==signed and len(maps)==12
    assert [m['new_cut'] for m in maps]==[False]*8+[True]*4
    assert maps==prepared['dynamic_shared_helper_control']['all_twelve_last_shared_transports']
    rejected=[]
    for step in parent['iterations']:
        candidate=ROOT/step['candidate']
        assert digest(candidate)==step['candidate_sha256']
        chosen=set(read(candidate)['selected_signature_ids'])
        failures=sum(sum(weight for b,weight in cut['weights'] if b in chosen) <
                     cut['demand']*int(cut['target'] in chosen) for cut in rows)
        signed_failures=sum(sum(c for a,c in cut['signed_coefficients'] if a in chosen)>0 for cut in signed)
        assert failures or signed_failures
        rejected.append({'parent_iteration':step['iteration'],'violated_individual_cut_count':failures,
                         'violated_signed_cut_count':signed_failures})
    assert rejected==prepared['dynamic_shared_helper_control']['all_five_parent_selections_rejected_by_proved_cuts']

    encodings=prepared['initial_individual_encodings']+prepared['initial_symmetric_encodings']
    assert len(encodings)==192
    for index,(cut,encoding) in enumerate(zip(rows,prepared['initial_individual_encodings'])):
        assert encoding['cut_index']==index and encoding['guard']==cut['target']+1
        terms=[[b+1,weight] for b,weight in cut['weights']]
        assert encoding['original_terms']==terms and encoding['original_demand']==cut['demand']
        normalized,demand,divisor=normal_terms(terms,cut['demand'])
        assert encoding['normalized_terms']==normalized and encoding['normalized_demand']==demand
        assert encoding['weight_gcd']==divisor
        predicate={'target':cut['target']+1,'demand':demand,'terms':normalized}
        assert hashlib.sha256(canonical(predicate)).hexdigest()==cut['normalized_predicate_sha256']
    for index,(cut,encoding) in enumerate(zip(signed,prepared['initial_symmetric_encodings'])):
        assert encoding['cut_index']==index
        assert encoding['signed_terms']==[[a+1,c] for a,c in cut['signed_coefficients']]
        terms=[[-(a+1) if c>0 else a+1,abs(c)] for a,c in cut['signed_coefficients']]
        demand=sum(c for _,c in cut['signed_coefficients'] if c>0)
        assert encoding['positive_weighted_literals']==terms and encoding['positive_literal_threshold']==demand
        inner=encoding['underlying_carry_threshold']
        assert inner['guard'] is None and inner['original_terms']==terms and inner['original_demand']==demand
        normalized,bound,divisor=normal_terms(terms,demand)
        assert inner['normalized_terms']==normalized and inner['normalized_demand']==bound
        assert inner['weight_gcd']==divisor

    formula=prepared['formula']
    base=read(LOGS/'f0-incidence-case00-model.json')
    direct=read(LOGS/'f0-first-design-exterior-row-certificate.json.gz')['row_certificate']['all_guarded_clauses']
    cnf_path=Path(prepared['cnf'])
    assert digest(cnf_path)==prepared['cnf_sha256']
    base_hash=hashlib.sha256(b'p cnf 28308 56550\n')
    counts,literals,current=0,0,0
    buffer=[]
    top=28308
    start=56994
    for encoding in encodings:
        assert encoding['initial_top']==top and encoding['clause_start']==start
        assert encoding['final_top']==top+encoding['auxiliary_variables']
        top=encoding['final_top'];start+=encoding['clauses']
    assert top==formula['variables']==100296 and start==formula['clauses']==620370
    with cnf_path.open('rb') as stream:
        assert stream.readline()==b'p cnf 100296 620370\n'
        for line in stream:
            values=list(map(int,line.split()))
            assert values[-1]==0 and all(values[:-1])
            clause=values[:-1]
            literals+=len(clause)
            if counts<56550:
                base_hash.update(line)
            elif counts<56994:
                assert clause==direct[counts-56550]
            else:
                encoding=encodings[current]
                assert all(abs(v)<=480 or encoding['initial_top']<abs(v)<=encoding['final_top'] for v in clause)
                buffer.append(clause)
                if len(buffer)==encoding['clauses']:
                    assert hashlib.sha256(canonical(buffer)).hexdigest()==encoding['clause_body_sha256']
                    assert sum(map(len,buffer))==encoding['literal_occurrences']
                    buffer=[];current+=1
            counts+=1
    assert not buffer and current==192 and counts==620370
    assert literals==formula['literal_occurrences']==2404476
    assert base_hash.hexdigest()==base['cnf_sha256']
    result={'status':'PASS: independent inherited-cut, actual-CNF and loop/proof semantic audit',
        'audit_source_sha256':digest(Path(__file__)),
        'loop_source_sha256':BINDINGS[SOURCE],'proof_wrapper_sha256':BINDINGS[WRAPPER],
        'preparation_sha256':BINDINGS[PREPARATION],
        'subject_dependencies_checked':prepared['dependency_source_hashes'],
        'parent_terminal_bindings_checked':prepared['parent_terminal_bindings'],
        'inherited_individual_cuts':168,'inherited_signed_cuts':20,'new_previously_unencoded_transports':4,
        'all_last_transports_checked':12,'all_weighted_cuts':192,
        'old_primary_incidence_prefix_clauses_hash_checked':56550,
        'old_direct_guarded_clauses_checked':444,'new_encoded_clause_blocks_hash_checked':192,
        'fresh_auxiliary_intervals_checked':192,
        'formula_variables':top,'formula_clauses':counts,'formula_literals':literals,
        'formula_sha256':prepared['cnf_sha256'],'parent_selections_rejected':rejected,
        'functions_AST_identical_after_explicit_status_string_changes':unchanged,
        'proof_wrapper_functions_AST_identical_to_previous':sorted(wrapper_functions),
        'mathematical_review':[
            'All row potentials are revalidated on the complete signature and neighbor domain before encoding.',
            'The prior complete reconstruction checks every actual candidate against its exact cut prefix before any terminal registry is inherited.',
            'The last shared ray and all 12 transported global predicates are replayed; eight deduplicate and four are newly encoded.',
            'Only a complete 60-row exact rational box pass permits the shared-edge query.',
            'Resource failure appends no partial cut; replay accepts only the recorded terminal prefix.',
            'Incremental UNSAT remains uncertified until a fresh complete reconstruction, proof-enabled solve, retained-clause inclusion and separate cold DRAT check.',
            'The second component remains unrestricted; no visitation block or hypothetical graph symmetry is introduced.'],
        'compact_carry_gate_truth_tables_reaudited':False,
        'subject_modules_imported':False,'CNF_rebuilt':False,'optimizer_or_SAT_called':False,
        'DRAT_checked':False,'whole_component_excluded':False,
        'scope':'Component 0 in the globally P=F=0 split 18+18 case only.',
        'seconds':time.monotonic()-started}
    output=LOGS/'f0-carry-row-loop-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print('output_sha256',digest(output))


if __name__=='__main__':
    audit()
