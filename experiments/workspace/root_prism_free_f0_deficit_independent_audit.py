"""Read-only source/provenance audit of the 384-cut deficit continuation."""

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
SOURCE=WORK/'root_prism_free_f0_deficit_row_loop.py'
HELPER=WORK/'root_prism_free_f0_shared_deficit_separator.py'
WRAPPER=WORK/'root_prism_free_f0_deficit_row_loop_certificate.py'
PREP=LOGS/'f0-deficit-row-loop-preparation.json.gz'
BINDINGS={
    SOURCE:'27b10330125ca5586512e2a4d3f8a297cf203dbb05e246bda4820240d03e940e',
    HELPER:'6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf',
    WRAPPER:'f023da2322053bd15c844f6c8c3c63d54feb3e5ed8ed51b1df0f6cb18319d419',
    PREP:'8884d196447a51e6104e473794a402cd2c0ab54465207355face9f20041faa08',
    LOGS/'f0-exterior-row-domains02.json.gz':'665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    LOGS/'f0-carry-row-loop-run01-shared-ray-repair-independent-audit.json':'e67e932377d757928b12b0d4e4612afceff2141e92c827e919bd0f59ce4b5df1'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def normalize(terms,demand):
    merged=Counter()
    for variable,weight in terms:
        assert type(variable) is int and 1<=abs(variable)<=480
        assert type(weight) is int and weight>0
        merged[variable]+=weight
    capped=sorted((variable,min(weight,demand)) for variable,weight in merged.items())
    divisor=gcd(*(weight for _,weight in capped)) if capped else 1
    return [[variable,weight//divisor] for variable,weight in capped],(demand+divisor-1)//divisor,divisor


class StatusOnly(ast.NodeTransformer):
    VALUES={
        'RUNNING: free480 carry/deficit individual/shared-row loop':'RUNNING: free480 carry-encoded individual/shared-row loop',
        'conway-f0-deficit-initial-':'conway-f0-carry-initial-',
        'conway-f0-deficit-final-':'conway-f0-carry-final-',
        'cold complete carry/deficit formula, all384 proved cuts, prior prefixes and separate repair replay PASS':
            'cold complete carry formula, all192 proved cuts and prior exact candidate prefixes replay PASS',
        'cold complete carry/deficit final formula, candidate prefixes, exact individual/shared witnesses and lifts replay PASS':
            'cold complete carry final formula, candidate prefixes, exact individual/shared witnesses and lifts replay PASS'}

    def visit_Constant(self,node):
        if isinstance(node.value,str) and node.value in self.VALUES:
            return ast.copy_location(ast.Constant(self.VALUES[node.value]),node)
        return node


def functions(path,normalize_strings=False):
    tree=ast.parse(path.read_text())
    if normalize_strings:
        tree=StatusOnly().visit(tree)
    return {node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,ast.FunctionDef)}


def audit():
    started=time.monotonic()
    for path,sha in BINDINGS.items():
        assert digest(path)==sha
    prepared=read(PREP)
    for name,sha in prepared['dependency_source_hashes'].items():
        assert digest(WORK/name)==sha
    for name,sha in prepared['parent_terminal_bindings'].items():
        assert digest(ROOT/name)==sha
    old_functions=functions(WORK/'root_prism_free_f0_carry_row_loop.py')
    new_functions=functions(SOURCE,True)
    identical=['add_individual','signed_cut','add_signed','signed_outcomes','inspect',
               'checked_preparation','counters','append_individual','symmetric_candidates','run','reconstruct']
    assert all(old_functions[name]==new_functions[name] for name in identical)
    assert functions(WRAPPER)==functions(WORK/'root_prism_free_f0_carry_row_loop_certificate.py')
    old_helper=functions(WORK/'root_prism_free_f0_shared_row_separator.py')
    new_helper=functions(HELPER)
    unchanged_helper=['save','domain','inventory','lift','seed_control']
    assert all(old_helper[name]==new_helper[name] for name in unchanged_helper)

    parent=read(LOGS/'f0-carry-row-loop-run01/result.json')
    repaired=read(LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz')
    rows,signed=prepared['initial_individual_cuts'],prepared['initial_symmetric_cuts']
    old_rows=read(ROOT/parent['individual-registry'])
    old_signed=read(ROOT/parent['symmetric-registry'])
    assert digest(ROOT/parent['individual-registry'])==parent['individual-registry_sha256']
    assert digest(ROOT/parent['symmetric-registry'])==parent['symmetric-registry_sha256']
    assert rows==old_rows and len(rows)==348
    assert signed[:24]==old_signed and len(signed)==36
    assert len({cut['normalized_predicate_sha256'] for cut in rows})==348
    keys={cut['predicate_sha256']:i for i,cut in enumerate(old_signed)}
    reconstructed=list(old_signed)
    maps=[]
    for transport in repaired['universal_selector_lift']['transported_cuts']:
        terms=transport['signed_coefficients']
        divisor=gcd(*(abs(c) for _,c in terms))
        normalized=[[a,c//divisor] for a,c in terms]
        origin={'kind':'separate exact-deficit repair of frozen parent UNKNOWN',
                'repair_certificate_sha256':digest(LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz'),
                'core_action_index':transport['core_action_index']}
        key=hashlib.sha256(canonical(normalized)).hexdigest()
        assert key not in keys
        keys[key]=len(reconstructed)
        reconstructed.append({'signed_coefficients':normalized,'origin':origin,'predicate_sha256':key})
        maps.append({'origin':origin,'registry_index':keys[key],'new_cut':True})
    assert reconstructed==signed and len(maps)==12 and len(keys)==36
    controls=prepared['dynamic_shared_helper_control']
    assert maps==controls['all_twelve_separate_repair_transports']
    assert controls['parent_UNKNOWN_status_unchanged']==parent['status']
    assert controls['separate_repair_exact_ray_check']==repaired['exact_ray_check']
    helper_control=controls['new_deficit_helper_reproduces_repair']
    assert helper_control['exact_ray_check']==repaired['exact_ray_check']
    assert helper_control['normalized_gap']==26 and helper_control['transports']==12

    domain=read(LOGS/'f0-exterior-row-domains02.json.gz')
    triples,targets,neighbors=domain['signature_domain'],domain['row_targets'],domain['possible_neighbor_signature_ids']
    encodings=prepared['initial_individual_encodings']+prepared['initial_symmetric_encodings']
    assert len(encodings)==384
    for index,(cut,encoding) in enumerate(zip(rows,prepared['initial_individual_encodings'])):
        vector,target=cut['integer_vector'],cut['target']
        demand=sum(a*b for a,b in zip(vector,targets[target]))
        weights=[[b,sum(vector[i] for i in triples[b])] for b in neighbors[target]]
        weights=[[b,w] for b,w in weights if w>0]
        assert demand==cut['demand']>0 and weights==cut['weights']
        terms=[[b+1,w] for b,w in weights]
        normalized,bound,divisor=normalize(terms,demand)
        assert encoding['cut_index']==index and encoding['guard']==target+1
        assert encoding['original_terms']==terms and encoding['original_demand']==demand
        assert encoding['normalized_terms']==normalized and encoding['normalized_demand']==bound
        assert encoding['weight_gcd']==divisor
        predicate={'target':target+1,'demand':bound,'terms':normalized}
        assert hashlib.sha256(canonical(predicate)).hexdigest()==cut['normalized_predicate_sha256']
    for index,(cut,encoding) in enumerate(zip(signed,prepared['initial_symmetric_encodings'])):
        assert encoding['cut_index']==index
        terms=[[-(a+1) if c>0 else a+1,abs(c)] for a,c in cut['signed_coefficients']]
        demand=sum(c for _,c in cut['signed_coefficients'] if c>0)
        assert encoding['signed_terms']==[[a+1,c] for a,c in cut['signed_coefficients']]
        assert encoding['positive_weighted_literals']==terms and encoding['positive_literal_threshold']==demand
        underlying=encoding['underlying_carry_threshold']
        normalized,bound,divisor=normalize(terms,demand)
        assert underlying['original_terms']==terms and underlying['original_demand']==demand
        assert underlying['normalized_terms']==normalized and underlying['normalized_demand']==bound
        assert underlying['weight_gcd']==divisor and underlying['guard'] is None
    top,clause=28308,56994
    for encoding in encodings:
        assert encoding['initial_top']==top and encoding['clause_start']==clause
        assert encoding['final_top']==top+encoding['auxiliary_variables']
        top=encoding['final_top'];clause+=encoding['clauses']
    assert top==prepared['formula']['variables']==208836
    assert clause==prepared['formula']['clauses']==1476450
    assert digest(Path(prepared['cnf']))==prepared['cnf_sha256']

    rejected=[]
    for step in parent['iterations']:
        path=ROOT/step['candidate']
        assert digest(path)==step['candidate_sha256']
        chosen=set(read(path)['selected_signature_ids'])
        row_failures=sum(sum(w for b,w in cut['weights'] if b in chosen) <
                         cut['demand']*int(cut['target'] in chosen) for cut in rows)
        signed_failures=sum(sum(c for a,c in cut['signed_coefficients'] if a in chosen)>0 for cut in signed)
        assert row_failures or signed_failures
        rejected.append({'parent_iteration':step['iteration'],'violated_individual_cut_count':row_failures,
                         'violated_signed_cut_count':signed_failures})
    assert rejected==controls['all_nine_parent_selections_rejected_by_proved_cuts']
    report={'status':'PASS: independent 384-cut provenance and deficit-helper/loop/proof source gate',
        'audit_source_sha256':digest(Path(__file__)),'source_sha256':BINDINGS[SOURCE],
        'helper_sha256':BINDINGS[HELPER],'proof_wrapper_sha256':BINDINGS[WRAPPER],
        'preparation_sha256':BINDINGS[PREP],
        'inherited_individual_cuts':348,'inherited_signed_cuts':24,'separate_exact_repair_transports_added':12,
        'total_weighted_cuts':384,'individual_potential_forms_recomputed':348,
        'encoding_input_and_normalization_records_checked':384,'fresh_auxiliary_interval_records_checked':384,
        'parent_candidates_rejected':rejected,'variables':top,'clauses':clause,
        'existing_CNF_sha256_checked':prepared['cnf_sha256'],
        'unchanged_loop_functions_after_explicit_status_string_changes':identical,
        'unchanged_shared_helper_functions':unchanged_helper,
        'all_four_proof_wrapper_functions_AST_unchanged':True,
        'source_review':[
            'Only free equality multipliers are rounded; exact upper deficits give both nonnegative dual column blocks.',
            'Each accepted ray passes the unchanged complete integer sign and strict RHS verifier.',
            'The last proposal scales by the largest dyadic denominator, a common denominator for every finite binary float.',
            'Replay reconstructs the exact recorded orientation/scale recipe before checking the ray and potentials.',
            'The parent UNKNOWN and every actual candidate prefix are preserved; the repair remains a separate proof artifact.',
            'Universal allocation and all 12 transports use the unchanged reviewed lift function.',
            'Candidate handling, stop conditions, partial terminal prefixes and fresh proof gates are unchanged.'],
        'subject_modules_imported':False,'nested_reconstruction_called':False,
        'CNF_regenerated':False,'new_solver_or_optimizer_called':False,'DRAT_checked':False,
        'whole_component_excluded':False,'seconds':time.monotonic()-started}
    output=LOGS/'f0-deficit-row-loop-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('output_sha256',digest(output))


if __name__=='__main__':
    audit()
