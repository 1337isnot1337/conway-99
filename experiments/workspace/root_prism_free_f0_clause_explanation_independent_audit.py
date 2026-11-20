"""Independent exact checks of the generic clause rule and saved F0 pilot.

No subject module is imported. The generic mathematics is reviewed in
research/root_prism_free_lazy_pb_clauses_review.md. This source directly
checks the pilot's literal lists, exact minima and cardinality premise.
"""

import gzip
import hashlib
import json
from pathlib import Path
import time


ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'experiments/workspace'
LOGS=ROOT/'experiments/logs/root-prism-free'
GENERIC=WORK/'integer_cut_clause_explanations.py'
PILOT=WORK/'root_prism_free_f0_clause_explanation_pilot.py'
RESULT=LOGS/'f0-clause-explanation-pilot.json'
BINDINGS={
    GENERIC:'f57d51b8be3fefd7a5d1035c52cc5758c719adb6a79d16a0909f1a54fdaa59f3',
    PILOT:'b6f701949f31a09892d8b2211e9fc64d1fb7d1fa9a2ed6775185542980c350c4',
    RESULT:'f06b7658ea4447bd785bab8fe2b4df87472c97944b85703ef7491dc54460b455',
    LOGS/'integer-cut-clause-controls.json':'5624e7489bc290d34a7466ad6a8ea97300adf86c5d10dcd320177faf7a3ef309'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def fixed_values(clause):
    assert all(type(lit) is int and lit!=0 for lit in clause)
    assert len({abs(lit) for lit in clause})==len(clause)
    return {abs(lit):int(lit<0) for lit in clause}


def cardinality_minimum(coefficients,fixed,population):
    assert set(fixed)<=set(range(1,481))
    residual=population-sum(fixed.values())
    free=[coefficients.get(i,0) for i in range(1,481) if i not in fixed]
    assert 0<=residual<=len(free)
    return sum(coefficients.get(i,0)*value for i,value in fixed.items())+sum(sorted(free)[:residual])


def audit():
    started=time.monotonic()
    for path,sha in BINDINGS.items():
        assert digest(path)==sha
    pilot=read(RESULT)
    for name,sha in pilot['frozen_inputs'].items():
        assert digest(LOGS/name)==sha
    assert pilot['source_sha256']==BINDINGS[PILOT] and pilot['helper_sha256']==BINDINGS[GENERIC]
    generic_controls=read(LOGS/'integer-cut-clause-controls.json')
    assert generic_controls['source_sha256']==BINDINGS[GENERIC]
    assert generic_controls['explicit_boolean_semantic_checks']==112000
    domain=read(LOGS/'f0-exterior-row-domains02.json.gz')
    model=read(LOGS/'f0-incidence-case00-model.json')
    repaired=read(LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz')
    core,triples=domain['component_core_rows'],domain['signature_domain']
    assert len(triples)==480 and all(len(h)==3 for h in triples)
    gram=[[12*int(i==j)+2-(core[i+3]&core[j+3]).bit_count()-((core[i+3]>>(j+3))&1)
           for j in range(18)] for i in range(18)]
    assert [gram[i][i] for i in range(18)]==[10]*18
    coverage=model['formula']['Gram_position_coverage']
    assert [(i,j) for i,j,*_ in coverage]==[(i,j) for i in range(18) for j in range(i,18)]
    for i,j,quota,members,_ in coverage:
        assert quota==gram[i][j] and members==sum(i in h and j in h for h in triples)
    assert sum(gram[i][i] for i in range(18))==3*60
    population=pilot['population_premise']
    assert population['value']==60 and population['Gram_diagonal_equations']==18
    assert population['each_diagonal_margin']==10 and population['each_selector_multiplicity_in_diagonal_sum']==3

    identity=tuple(range(21))
    group,queue={identity},[identity]
    while queue:
        old=queue.pop()
        for generator in domain['core_generators']:
            image=tuple(generator[old[i]] for i in range(21))
            assert sorted(image)==list(range(21)) and set(image[:3])=={0,1,2}
            assert all(((core[i]>>j)&1)==((core[image[i]]>>image[j])&1) for i in range(21) for j in range(21))
            if image not in group:
                group.add(image);queue.append(image)
    assert len(group)==len(pilot['records'])==12
    positions={tuple(h):i for i,h in enumerate(triples)}
    lift=repaired['universal_selector_lift']
    selected=lift['selected_signature_ids_for_allocation_only']
    counts={'plain_literals':0,'population_literals':0,'deletion_bounds_checked':0}
    outcomes=[]
    for index,(image,record) in enumerate(zip(sorted(group),pilot['records'])):
        assert record['core_action_index']==index
        action=[positions[tuple(sorted(image[i+3]-3 for i in h))] for h in triples]
        assert sorted(action)==list(range(480))
        chosen={action[a]+1 for a in selected}
        assert len(chosen)==60 and record['transported_selected_columns']==sorted(i-1 for i in chosen)
        cut=lift['transported_cuts'][index]
        assert hashlib.sha256(canonical(cut)).hexdigest()==record['proved_signed_cut_sha256']
        coefficients={a+1:c for a,c in cut['signed_coefficients']}
        assert set(coefficients)==set(range(1,481))
        value=sum(coefficients[i] for i in chosen)
        assert value==26
        plain,card=record['independent_explanation'],record['cardinality_explanation']
        for explanation in (plain,card):
            fixed=fixed_values(explanation['clause'])
            assert all(v==int(i in chosen) for i,v in fixed.items())
            assert explanation['violating_assignment_value']==value
        fixed=fixed_values(plain['clause'])
        bound=sum(coefficients[i]*fixed[i] if i in fixed else min(0,coefficients[i]) for i in range(1,481))
        assert bound==plain['minimum_if_clause_is_false']==plain['strict_integer_margin']>0
        baseline=sum(min(0,c) for c in coefficients.values())
        gains=sorted((abs(c) for i,c in coefficients.items() if (i in chosen)==(c>0)),reverse=True)
        k=len(fixed)
        assert baseline==plain['independent_baseline']
        assert baseline+sum(gains[:k])==bound and baseline+sum(gains[:max(0,k-1)])<=0
        assert plain['largest_k_minus_one_gains_bound']==baseline+sum(gains[:k-1])
        assert plain['minimum_explanation_literal_count']==k and plain['cardinality_premise'] is None

        fixed={i:1 for i in chosen}
        order=sorted(fixed,key=lambda i:(abs(coefficients.get(i,0)),i))
        assert [step['variable'] for step in card['deletion_checks']]==order
        for step in card['deletion_checks']:
            trial={i:v for i,v in fixed.items() if i!=step['variable']}
            trial_bound=cardinality_minimum(coefficients,trial,60)
            assert trial_bound==step['minimum_without_variable']
            assert step['removed']==(trial_bound>0)
            if step['removed']:
                fixed=trial
            counts['deletion_bounds_checked']+=1
        assert fixed==fixed_values(card['clause'])
        bound_card=cardinality_minimum(coefficients,fixed,60)
        assert bound_card==card['minimum_if_clause_is_false']==card['strict_integer_margin']>0
        assert card['cardinality_premise']==60 and card['full_universe']==list(range(1,481))
        assert all(lit<0 for lit in card['clause']) and len(card['clause'])<=60
        for i in fixed:
            assert cardinality_minimum(coefficients,{j:v for j,v in fixed.items() if j!=i},60)<=0
        counts['plain_literals']+=len(plain['clause']);counts['population_literals']+=len(card['clause'])
        outcomes.append({'core_action_index':index,'plain_width':k,'plain_strict_margin':bound,
                         'population_width':len(card['clause']),'population_strict_margin':bound_card})
    assert counts=={'plain_literals':5352,'population_literals':720,'deletion_bounds_checked':720}
    assert all(x['plain_width']==446 and x['population_width']==60 for x in outcomes)
    report={'status':'PASS: independent generic source/mathematics gate and all 24 saved pilot clause certificates',
        'audit_source_sha256':digest(Path(__file__)),'generic_source_sha256':BINDINGS[GENERIC],
        'pilot_source_sha256':BINDINGS[PILOT],'pilot_certificate_sha256':BINDINGS[RESULT],
        'generic_owner_controls_bound_but_not_rerun':generic_controls,
        'exact_clause_certificates_checked':24,'all_12_core_actions_checked':True,
        'complete_population_premise_rederived':True,'full_free_universe_includes_zero_coefficients':True,
        'counts':counts,'clause_outcomes':outcomes,
        'generic_source_review':[
            'Duplicate coefficients are combined before selecting gains or calculating bounds.',
            'Literal falsifying values are correctly fixed to one for negative literals and zero for positive literals.',
            'The independent rule chooses the largest helpful gains and proves minimum literal count with the k-1 bound.',
            'The cardinality rule uses every variable in the complete universe, including absent zero coefficients.',
            'Greedy cardinality deletion is exactly rechecked and asserts single-deletion irredundancy, without claiming minimum width.',
            'Strict inequalities and arbitrary-precision integer arithmetic are retained; zero-width contradictions are valid only after the same exact gate.'],
        'pilot_scope':'Twelve exact consequences of the proved repaired-ray inequalities; no formula is changed.',
        'all_population_clauses_still_fix_the_full_60_selected_variables':True,
        'no_stronger_population_subclause_found_by_the_pilot':True,
        'subject_modules_imported':False,'solver_or_optimizer_called':False,'CNF_rebuilt':False,
        'component_excluded':False,'seconds':time.monotonic()-started}
    output=LOGS/'f0-clause-explanation-pilot-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('output_sha256',digest(output))


if __name__=='__main__':
    audit()
