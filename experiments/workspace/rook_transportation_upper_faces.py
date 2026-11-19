"""Exact forced-upper-cell certificates from a saved transportation flow.

There is no max-flow call in upper_faces(). Only the exhaustive tiny
controls invoke the previously checked integer max-flow helper.
"""
from collections import deque
from itertools import product
import time

import rook_transportation_faces as original


def parents_from(residual,start):
    parents=[-1]*len(residual)
    parents[start]=start
    queue=deque([start])
    while queue:
        u=queue.popleft()
        for v,k in enumerate(residual[u]):
            if k>0 and parents[v]<0:
                parents[v]=u
                queue.append(v)
    return parents


def upper_faces(r,c,capacities,flow):
    n,m=len(r),len(c)
    assert set(flow)==set(capacities)
    assert all(type(k)is int and 0<=flow[key]<=k for key,k in capacities.items())
    assert all(type(f)is int for f in flow.values())
    assert all(sum(f for (u,v),f in flow.items()if u==a)==r[a]for a in range(n))
    assert all(sum(f for (u,v),f in flow.items()if v==b)==c[b]for b in range(m))
    residual=[[0]*(n+m)for _ in range(n+m)]
    for (u,v),k in capacities.items():
        residual[u][n+v]=k-flow[u,v]
        residual[n+v][u]=flow[u,v]
    trees=[parents_from(residual,u)for u in range(n)]
    records=[]
    for (u,v),k in sorted(capacities.items()):
        entry={'cell':[u,v],'capacity':k,'saved_flow':flow[u,v]}
        if not k:
            entry.update(kind='forced_zero_capacity',forced_upper=True)
        elif flow[u,v]<k:
            entry.update(kind='strict_saved_slack',forced_upper=False,
                         strict_slack=k-flow[u,v])
        elif trees[u][n+v]>=0:
            path=[n+v]
            while path[-1]!=u:path.append(trees[u][path[-1]])
            path.reverse()
            assert len(path)==len(set(path))
            delta=min([flow[u,v]]+[residual[a][b]for a,b in zip(path,path[1:])])
            assert delta>0 and residual[n+v][u]>=delta
            entry.update(kind='decreasing_residual_cycle',forced_upper=False,
                         row_to_column_path=path,positive_cycle_amount=delta)
        else:
            P=[a for a in range(n)if trees[u][a]>=0]
            Q=[b for b in range(m)if trees[u][n+b]>=0]
            cut=original.cut_data(r,c,capacities,P,Q)
            assert cut['rhs']==0 and [u,v]in cut['capacity_cells']
            assert all(flow[a,b]==capacities[a,b]for a,b in cut['capacity_cells'])
            assert all(flow[a,b]==0 for a,b in cut['incoming_cells'])
            entry.update(kind='forced_positive_upper',forced_upper=True,cut=cut)
        records.append(entry)
    return records


def verify_cell_inequality(r,c,capacities,record):
    target=tuple(record['cell'])
    assert record['forced_upper']and capacities[target]==record['capacity']
    if record['kind']=='forced_zero_capacity':
        assert capacities[target]==0
        return {'negative_target_lower_row':[list(target),-1],
                'lower_rhs':0,'uses_only_nonnegativity_and_zero_upper_bound':True}
    cut=record['cut']
    assert cut==original.cut_data(r,c,capacities,cut['rows'],cut['columns'])
    assert cut['rhs']==0 and target in map(tuple,cut['capacity_cells'])
    P,Q=set(cut['rows']),set(cut['columns'])
    other={tuple(e)for e in cut['capacity_cells']if tuple(e)!=target}
    rhs=sum(c[v]for v in Q)-sum(r[u]for u in P)+sum(capacities[e]for e in other)
    coefficients={e:int(e[1]in Q)-int(e[0]in P)+int(e in other)for e in capacities}
    remainder={e:v+int(e==target)for e,v in coefficients.items()}
    assert rhs==-capacities[target]and set(remainder.values())<={0,1}
    return {'combined_upper_rhs':rhs,'all_cell_remainder_coefficients_nonnegative':True}


def controls():
    deadline=time.monotonic()+60
    cases=feasible=certificates=positive_certificates=flexible=0
    cells=[(0,0),(0,1),(1,0),(1,1)]
    for cap in product(range(3),repeat=4):
        capacities=dict(zip(cells,cap))
        minima={}
        for values in product(*(range(k+1)for k in cap)):
            r=(values[0]+values[1],values[2]+values[3])
            c=(values[0]+values[2],values[1]+values[3])
            key=(r,c)
            minima[key]=[min(a,b)for a,b in zip(minima.get(key,values),values)]
        for r in product(range(5),repeat=2):
            for c in product(range(5),repeat=2):
                if sum(r)!=sum(c):continue
                original.tick(deadline)
                result=original.transport(r,c,capacities,deadline)
                assert result['feasible']==((r,c)in minima)
                cases+=1
                if not result['feasible']:continue
                feasible+=1
                records=upper_faces(r,c,capacities,result['flow'])
                forced={tuple(e['cell'])for e in records if e['forced_upper']}
                truth={e for e,v,k in zip(cells,minima[r,c],cap)if v==k}
                assert forced==truth
                for entry in records:
                    if entry['forced_upper']:
                        verify_cell_inequality(r,c,capacities,entry)
                        certificates+=1
                        positive_certificates+=entry['capacity']>0
                    else:flexible+=1
    complete={(u,v):1 for u in range(3)for v in range(3)}
    r=c=[1,1,1]
    result=original.transport(r,c,complete,deadline)
    assert not any(e['forced_upper']for e in upper_faces(r,c,complete,result['flow']))
    diagonal={(u,u):1 for u in range(3)}
    result=original.transport(r,c,diagonal,deadline)
    assert all(e['forced_upper']for e in upper_faces(r,c,diagonal,result['flow']))
    return {'complete_two_by_two_cases':cases,'feasible_cases':feasible,
        'full_integer_box_flow_truth_enumerated':True,
        'forced_upper_certificates_checked':certificates,
        'positive_capacity_certificates_checked':positive_certificates,
        'flexible_cell_classifications':flexible,
        'complete_three_by_three_has_no_forced_upper':True,
        'diagonal_three_by_three_all_cells_forced_upper':True,
        'case4_flow_or_optimizer_called':False}
