"""Independent integer audit of the saved repaired shared-row certificate.

Only standard-library arithmetic and frozen data arrays are used. No
subject imports, formula rebuild, optimizer, SAT call or proof checker.
"""

from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations,product
import json
from math import gcd
from pathlib import Path
import time


ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'experiments/workspace'
LOGS=ROOT/'experiments/logs/root-prism-free'
SOURCE=WORK/'root_prism_free_f0_shared_ray_repair.py'
CERT=LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz'
DOMAIN=LOGS/'f0-exterior-row-domains02.json.gz'
BINDINGS={
    SOURCE:'4a214635d5ba1ec73477a3acdfd36c30cb65be3c4c4fb662ee19a615388c07d3',
    CERT:'96e945d1211147e2ad13ed3468f51d72bd3ef87319ca33153eda6248e0b5c7c5',
    DOMAIN:'665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4'}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def nearest_even(value):
    quotient,remainder=divmod(value.numerator,value.denominator)
    if 2*remainder>value.denominator or (2*remainder==value.denominator and quotient%2):
        quotient+=1
    return quotient


def allocate(signatures,targets,edges,potentials,support,ordering):
    demand=[sum(a*b for a,b in zip(v,q)) for v,q in zip(potentials,targets)]
    coefficient=list(demand)
    positive=[]
    for a,b in edges:
        weight=sum(potentials[a][i] for i in signatures[b])+sum(potentials[b][i] for i in signatures[a])
        if weight<=0:
            continue
        assert a in support or b in support
        if a in support and b in support:
            endpoint=a if ordering[a]<ordering[b] else b
            kind='internal'
        else:
            endpoint=b if a in support else a
            kind='boundary'
        coefficient[endpoint]-=weight
        positive.append({'edge':[a,b],'weight':weight,'allocated_endpoint':endpoint,'kind':kind})
    return demand,coefficient,positive


def audit():
    started=time.monotonic()
    for path,sha in BINDINGS.items():
        assert digest(path)==sha
    certificate,saved=read(CERT),read(DOMAIN)
    assert certificate['source_sha256']==BINDINGS[SOURCE]
    for name,sha in certificate['dependency_source_hashes'].items():
        assert digest(WORK/name)==sha
    result_path=ROOT/certificate['frozen_terminal_result']
    candidate_path=ROOT/certificate['candidate']
    numerical_path=ROOT/certificate['numerical_shared_result']
    for path,key in ((result_path,'frozen_terminal_result_sha256'),(candidate_path,'candidate_sha256'),
                     (numerical_path,'numerical_shared_result_sha256')):
        assert digest(path)==certificate[key]
    result,candidate,numerical=read(result_path),read(candidate_path),read(numerical_path)
    assert result['status']==certificate['frozen_terminal_status_unchanged']
    assert result['iterations'][-1]['iteration']==8
    selected=candidate['selected_signature_ids']
    assert selected==sorted(set(selected)) and len(selected)==60

    core=saved['component_core_rows']
    assert len(core)==21 and all((core[i]>>i)&1==0 for i in range(21))
    assert all(((core[i]>>j)&1)==((core[j]>>i)&1) for i in range(21) for j in range(21))
    adjacency=[(row>>3)&((1<<18)-1) for row in core[3:]]
    gram=[[12*int(i==j)+2-(core[i+3]&core[j+3]).bit_count()-((core[i+3]>>(j+3))&1)
           for j in range(18)] for i in range(18)]
    signatures=[]
    for h in combinations(range(18),3):
        if max(sum(i//6==f for i in h) for f in range(3))>2:
            continue
        if any(gram[i][j]==0 for i,j in combinations(h,2)):
            continue
        if any(sum(int(i==j or (adjacency[i]>>j)&1) for j in h)>2 for i in range(18)):
            continue
        signatures.append(list(h))
    assert signatures==saved['signature_domain'] and len(signatures)==480
    targets=[[2-int(i in h)-sum((adjacency[i]>>j)&1 for j in h) for i in range(18)] for h in signatures]
    assert targets==saved['row_targets'] and all(sum(q)==24 for q in targets)
    assert [[sum(i in signatures[a] and j in signatures[a] for a in selected) for j in range(18)]
            for i in range(18)]==gram
    masks=[sum(1<<i for i in h) for h in signatures]
    edges=[]
    neighbors=[[] for _ in signatures]
    for a,b in combinations(range(480),2):
        allowed=(masks[a]&masks[b]).bit_count()<=1
        allowed=allowed and all(targets[a][i]>0 for i in signatures[b]) and all(targets[b][i]>0 for i in signatures[a])
        if allowed:
            edges.append([a,b]);neighbors[a].append(b);neighbors[b].append(a)
    assert neighbors==saved['possible_neighbor_signature_ids'] and len(edges)==68394
    fixed_edges=[[a,b] for a in range(60) for b in range(a) if selected[b] in neighbors[selected[a]]]
    incident=[[] for _ in selected]
    for e,(a,b) in enumerate(fixed_edges):
        incident[a].append((b,e));incident[b].append((a,e))
    rows=[]
    for a in range(60):
        rows.append({'kind':'degree','vertex':a,'support':sorted(e for _,e in incident[a]),'rhs':8})
        for i in range(18):
            rows.append({'kind':'mixed','vertex':a,'core_vertex':i,
                'support':sorted(e for b,e in incident[a] if i in signatures[selected[b]]),
                'rhs':targets[selected[a]][i]})
    n,m=len(fixed_edges),len(rows)
    assert (n,m)==(1228,1140)
    data={'design':[signatures[a] for a in selected],'targets':[targets[a] for a in selected],
          'edge_domain':fixed_edges,'selected_signature_ids':selected}
    assert hashlib.sha256(canonical(rows)).hexdigest()==certificate['inventory']['rows_sha256']
    assert hashlib.sha256(canonical(data)).hexdigest()==certificate['inventory']['data_sha256']
    assert len(numerical['numerical_ray_hex'])==m+n
    free=[nearest_even(-Fraction(float.fromhex(value))) for value in numerical['numerical_ray_hex'][:m]]
    columns=[0]*n
    for row,value in zip(rows,free):
        for edge in row['support']:
            columns[edge]+=value
    upper=[max(0,-value) for value in columns]
    raw=free+upper
    divisor=gcd(*raw)
    assert divisor>0
    ray=[value//divisor for value in raw]
    assert ray==certificate['integer_ray']
    equality,upper=ray[:m],ray[m:]
    columns=[0]*n
    for row,value in zip(rows,equality):
        for edge in row['support']:
            columns[edge]+=value
    assert upper==[max(0,-value) for value in columns]
    primary=[a+b for a,b in zip(columns,upper)]
    assert min(primary)>=0 and min(upper)>=0
    rhs=sum(row['rhs']*value for row,value in zip(rows,equality))+sum(upper)
    check={'rhs_dot_product':rhs,'minimum_primary_coefficient':min(primary),
        'minimum_upper_slack_coefficient':min(upper),
        'nonzero_row_multipliers':sum(value!=0 for value in ray),'maximum_absolute_multiplier':max(map(abs,ray)),
        'orientation':'E^T ray>=0 and rhs^T ray<0 for every nonnegative primary and upper slack'}
    assert check==certificate['exact_ray_check'] and rhs==-26

    local=[[-equality[19*a]-3*equality[19*a+1+i] for i in range(18)] for a in range(60)]
    potential=certificate['fixed_capacity_potentials']
    assert local==potential['integer_potentials60_by18']
    demand=sum(sum(v*q for v,q in zip(local[a],targets[selected[a]])) for a in range(60))
    fixed_weights=[sum(local[a][i] for i in signatures[selected[b]])+
                   sum(local[b][i] for i in signatures[selected[a]]) for a,b in fixed_edges]
    assert fixed_weights==[-3*c for c in columns]
    capacity=sum(max(0,w) for w in fixed_weights)
    assert capacity==3*sum(upper)==potential['complete_internal_positive_edge_capacity']==21765
    assert demand==potential['total_weighted_demand']==21843
    assert demand-capacity==potential['strict_gap']==-3*rhs==78
    potentials=[[0]*18 for _ in range(480)]
    for a,vector in zip(selected,local):
        potentials[a]=vector
    support=set(selected)
    delta,coefficient,positive=allocate(signatures,targets,edges,potentials,support,list(range(480)))
    lifted=certificate['universal_selector_lift']
    assert hashlib.sha256(canonical(edges)).hexdigest()==lifted['global_edge_sha256']
    assert hashlib.sha256(canonical(positive)).hexdigest()==lifted['positive_edge_allocation_sha256']
    assert len(positive)==lifted['positive_edge_count']==7217
    assert dict(Counter(entry['kind'] for entry in positive))==lifted['positive_edge_type_counts']
    assert sum(delta[a] for a in selected)==lifted['total_target_demand_at_saved_selection']==demand
    assert sum(coefficient[a] for a in selected)==lifted['raw_gap']==78
    divisor=gcd(*(abs(value) for value in coefficient))
    assert divisor==lifted['coefficient_gcd']==3 and lifted['normalized_gap']==26

    identity=tuple(range(21))
    group,frontier={identity},[identity]
    while frontier:
        permutation=frontier.pop()
        for generator in saved['core_generators']:
            image=tuple(generator[permutation[i]] for i in range(21))
            assert sorted(image)==list(range(21)) and set(image[:3])==set(range(3))
            assert all(((core[i]>>j)&1)==((core[image[i]]>>image[j])&1) for i in range(21) for j in range(21))
            if image not in group:
                group.add(image);frontier.append(image)
    assert len(group)==len(lifted['transported_cuts'])==12
    positions={tuple(h):i for i,h in enumerate(signatures)}
    for action_index,permutation in enumerate(sorted(group)):
        move=[permutation[i+3]-3 for i in range(18)]
        image=[positions[tuple(sorted(move[i] for i in h))] for h in signatures]
        assert sorted(image)==list(range(480))
        assert all(targets[a][i]==targets[image[a]][move[i]] for a in range(480) for i in range(18))
        assert all(sorted(image[b] for b in neighbors[a])==neighbors[image[a]] for a in range(480))
        inverse=[0]*480
        moved=[[0]*18 for _ in range(480)]
        for a in range(480):
            inverse[image[a]]=a
            for i in range(18):
                moved[image[a]][move[i]]=potentials[a][i]
        moved_support={image[a] for a in selected}
        _,transported,_=allocate(signatures,targets,edges,moved,moved_support,inverse)
        assert all(transported[image[a]]==coefficient[a] for a in range(480))
        terms=[[a,value//divisor] for a,value in enumerate(transported) if value]
        expected={'core_action_index':action_index,'signed_coefficients':terms,'transported_selection_gap':26}
        assert lifted['transported_cuts'][action_index]==expected
        assert sum(value for a,value in terms if a in moved_support)==26

    # Independent rounding controls include negative half-integers.
    rounding_controls=0
    for numerator in range(-41,42):
        for denominator in range(1,12):
            value=Fraction(numerator,denominator)
            assert nearest_even(value)==round(value)
            rounding_controls+=1
    result={'status':'PASS: independent exact repaired ray, complete fixed box and all 12 global transports',
        'audit_source_sha256':digest(Path(__file__)),'subject_source_sha256':BINDINGS[SOURCE],
        'certificate_sha256':BINDINGS[CERT],'domain_sha256':BINDINGS[DOMAIN],
        'frozen_terminal_result_sha256':certificate['frozen_terminal_result_sha256'],
        'fixed_incidence_columns':60,'equality_rows':m,'fixed_eligible_edges':n,
        'all_primary_and_slack_column_coefficients_checked':2*n,
        'equality_multipliers_reconstructed_from_exact_dyadics':m,
        'upper_multipliers_computed_from_exact_deficits':n,
        'rhs_dot_product':rhs,'weighted_demand':demand,'positive_capacity':capacity,
        'potential_gap':demand-capacity,'global_signatures':480,'global_eligible_edges':len(edges),
        'global_positive_edge_allocations_checked':len(positive),
        'transported_cut_count':12,'normalized_selection_gap':26,
        'rounding_controls':rounding_controls,
        'source_review':[
            'Free equality multipliers may be rounded arbitrarily; exact upper deficits make both dual column blocks nonnegative.',
            'The complete independent RHS check, not numerical infeasibility or closeness, certifies the fixed box obstruction.',
            'Degree elimination uses sum(q)=24 and signature size 3; multiplying by 3 preserves the strict gap.',
            'Each positive global edge weight is assigned to one endpoint, using edge activation to bound it by that endpoint selector.',
            'The saved design selects potentials and allocation only; it is not a hypothesis of the resulting 480-selector inequality.',
            'The inverse label order preserves internal endpoint choices under every verified core action.'],
        'fixed_candidate_excluded':True,'whole_component_excluded':False,
        'subject_modules_imported':False,'CNF_rebuilt':False,'optimizer_or_solver_called':False,
        'original_frozen_outputs_modified':False,'seconds':time.monotonic()-started}
    output=LOGS/'f0-carry-row-loop-run01-shared-ray-repair-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));print('output_sha256',digest(output))


if __name__=='__main__':
    audit()
