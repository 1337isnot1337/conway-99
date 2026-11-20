"""Exact transportation feasibility and zero-cell certificates.

This module uses only integer augmenting paths. It calls no LP/SAT optimizer.
A cell is forced zero precisely when it has capacity zero, or it has zero
flow and belongs to no positive residual cycle. Cut certificates use
c(Q)-r(P)+cap(P,Qbar), with nonnegative incoming flows and outgoing slacks.
"""
from collections import deque
from itertools import product
import time


def tick(deadline):
    if deadline is not None and time.monotonic()>deadline:
        raise TimeoutError('exact transportation budget')


def reach(residual,start):
    seen={start}
    queue=deque([start])
    while queue:
        u=queue.popleft()
        for v,capacity in enumerate(residual[u]):
            if capacity>0 and v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


def transport(row_margins,column_margins,capacities,deadline=None):
    r,c=list(row_margins),list(column_margins)
    n,m=len(r),len(c)
    assert n and m and all(type(v)is int and v>=0 for v in r+c)
    assert sum(r)==sum(c)
    assert all(type(u)is type(v)is type(k)is int and 0<=u<n and 0<=v<m and k>=0
               for (u,v),k in capacities.items())
    source,sink=n+m,n+m+1
    residual=[[0]*(n+m+2)for _ in range(n+m+2)]
    for u,k in enumerate(r):residual[source][u]=k
    for (u,v),k in capacities.items():residual[u][n+v]=k
    for v,k in enumerate(c):residual[n+v][sink]=k
    total=0
    augmentations=0
    while True:
        tick(deadline)
        parents=[-1]*(n+m+2)
        parents[source]=source
        queue=deque([source])
        while queue and parents[sink]<0:
            u=queue.popleft()
            for v,k in enumerate(residual[u]):
                if k>0 and parents[v]<0:
                    parents[v]=u
                    queue.append(v)
                    if v==sink:break
        if parents[sink]<0:break
        v=sink
        delta=sum(r)+1
        while v!=source:
            u=parents[v]
            delta=min(delta,residual[u][v])
            v=u
        assert delta>0
        v=sink
        while v!=source:
            u=parents[v]
            residual[u][v]-=delta
            residual[v][u]+=delta
            v=u
        total+=delta
        augmentations+=1
        assert total<=sum(r) and augmentations<=sum(r)
    flow={key:k-residual[key[0]][n+key[1]] for key,k in capacities.items()}
    assert all(0<=flow[key]<=k for key,k in capacities.items())
    assert sum(flow.values())==total
    if total==sum(r):
        assert all(sum(f for (a,b),f in flow.items()if a==u)==r[u]for u in range(n))
        assert all(sum(f for (a,b),f in flow.items()if b==v)==c[v]for v in range(m))
        cut=None
    else:
        reachable=reach(residual,source)
        assert sink not in reachable
        P=sorted(u for u in range(n)if u in reachable)
        Q=sorted(v for v in range(m)if n+v in reachable)
        cut=cut_data(r,c,capacities,P,Q)
        assert cut['rhs']==total-sum(r)<0
    return {'feasible':total==sum(r),'total':total,'augmentations':augmentations,
            'flow':flow,'infeasible_cut':cut}


def cut_data(r,c,capacities,P,Q):
    assert P==sorted(set(P)) and Q==sorted(set(Q))
    ps,qs=set(P),set(Q)
    outgoing=sorted(key for key in capacities if key[0]in ps and key[1]not in qs)
    incoming=sorted(key for key in capacities if key[0]not in ps and key[1]in qs)
    bound=sum(c[v]for v in Q)-sum(r[u]for u in P)+sum(capacities[key]for key in outgoing)
    return {'kind':'transport_cut','rows':P,'columns':Q,
            'capacity_cells':[list(k)for k in outgoing],
            'incoming_cells':[list(k)for k in incoming],'rhs':bound}


def zero_cuts(r,c,capacities,flow):
    n,m=len(r),len(c)
    assert set(flow)==set(capacities)
    assert all(type(f)is int and 0<=f<=capacities[key]for key,f in flow.items())
    assert all(sum(f for (a,b),f in flow.items()if a==u)==r[u]for u in range(n))
    assert all(sum(f for (a,b),f in flow.items()if b==v)==c[v]for v in range(m))
    residual=[[0]*(n+m)for _ in range(n+m)]
    for (u,v),k in capacities.items():
        residual[u][n+v]=k-flow[u,v]
        residual[n+v][u]=flow[u,v]
    cuts=[]
    forced=set()
    for key in sorted(capacities):
        if capacities[key]==0:
            cuts.append({'kind':'zero_capacity','cell':list(key),'rhs':0})
            forced.add(key)
    seen=set()
    for v in range(m):
        reachable=reach(residual,n+v)
        P=sorted(u for u in range(n)if u in reachable)
        Q=sorted(w for w in range(m)if n+w in reachable)
        key=(tuple(P),tuple(Q))
        if key in seen:continue
        seen.add(key)
        candidate=cut_data(r,c,capacities,P,Q)
        assert candidate['rhs']==0
        for u,w in candidate['capacity_cells']:
            assert flow[u,w]==capacities[u,w]
        for u,w in candidate['incoming_cells']:
            assert flow[u,w]==0
        new={tuple(k)for k in candidate['incoming_cells']}-forced
        if new:
            cuts.append(candidate)
            forced.update(new)
    # Completeness for this projection: an unsaturated positive-capacity
    # zero-flow edge can become positive iff its reverse endpoint reaches
    # its forward endpoint, closing a residual cycle.
    for (u,v),k in capacities.items():
        possible=(flow[u,v]>0 or (k>0 and u in reach(residual,n+v)))
        assert ((u,v)not in forced)==possible
    return cuts,forced


def verify_cut_on_cells(r,c,capacities,cut):
    if cut['kind']=='zero_capacity':
        key=tuple(cut['cell'])
        assert key in capacities and capacities[key]==cut['rhs']==0
        return {key:1},0
    assert cut==cut_data(r,c,capacities,cut['rows'],cut['columns'])
    P,Q=set(cut['rows']),set(cut['columns'])
    outgoing={tuple(k)for k in cut['capacity_cells']}
    coefficient={key:int(key[1]in Q)-int(key[0]in P)+int(key in outgoing)
                 for key in capacities}
    assert set(coefficient.values())<={0,1}
    assert {key for key,k in coefficient.items()if k}=={tuple(k)for k in cut['incoming_cells']}
    return coefficient,cut['rhs']


def controls():
    deadline=time.monotonic()+60
    cases=feasible=zero_certificates=infeasible_certificates=0
    keys=[(0,0),(0,1),(1,0),(1,1)]
    for capacity_values in product(range(3),repeat=4):
        capacities=dict(zip(keys,capacity_values))
        truth={}
        for values in product(*(range(k+1)for k in capacity_values)):
            r=(values[0]+values[1],values[2]+values[3])
            c=(values[0]+values[2],values[1]+values[3])
            truth.setdefault((r,c),set()).update(key for key,f in zip(keys,values)if f)
        for r in product(range(5),repeat=2):
            for c in product(range(5),repeat=2):
                if sum(r)!=sum(c):continue
                tick(deadline)
                result=transport(r,c,capacities,deadline)
                assert result['feasible']==((r,c)in truth)
                cases+=1
                if not result['feasible']:
                    _,rhs=verify_cut_on_cells(r,c,capacities,result['infeasible_cut'])
                    assert rhs<0
                    infeasible_certificates+=1
                    continue
                feasible+=1
                cuts,forced=zero_cuts(r,c,capacities,result['flow'])
                assert forced==set(keys)-truth[r,c]
                for cut in cuts:
                    coeff,rhs=verify_cut_on_cells(r,c,capacities,cut)
                    assert rhs==0 and any(coeff.values())
                    assert {key for key,v in coeff.items()if v}<=forced
                    zero_certificates+=1
    # A nontrivial3x3 flow has all nine cells in residual cycles.
    capacities={(u,v):1 for u in range(3)for v in range(3)}
    result=transport([1,1,1],[1,1,1],capacities,deadline)
    assert result['feasible'] and not zero_cuts([1,1,1],[1,1,1],capacities,result['flow'])[1]
    return {'exhaustive_two_by_two_cases':cases,'feasible_cases':feasible,
        'exact_infeasible_cut_controls':infeasible_certificates,
        'exact_zero_cut_controls':zero_certificates,
        'all_integer_box_flows_enumerated_for_truth':True,
        'positive_three_by_three_residual_cycle_control':True,
        'LP_or_SAT_optimizer_calls':0}
