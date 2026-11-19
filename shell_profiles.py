"""Enumerate coordinate profiles and apply the common-neighbor equations to each one."""
from collections import Counter
from functools import cache
from itertools import combinations_with_replacement
from math import comb
from pathlib import Path
import argparse,json,z3

def profiles(j,d):
    slack,rem=divmod(d-11*j*(9-j)//2,9)
    if slack<0 or rem:return
    labels=[]
    for a in range(-slack-2,slack+2):
        cost=a*(a+1)//2
        if 0<cost<=slack and (9*a+j)**2<=8*d:
            labels.append((cost,a))
    labels.sort(reverse=True)
    def rec(idx,k,c):
        if idx==len(labels):
            if k:return
            neg=11*j+sum(i*v for i,v in c.items())
            zero=99-neg-sum(c.values())
            if min(neg,zero)<0:return
            p=dict(c)
            if neg:p[-1]=neg
            if zero:p[0]=zero
            yield dict(sorted(p.items()))
            return
        cost,a=labels[idx]
        for b in range(k//cost+1):
            if b:c[a]=b
            yield from rec(idx+1,k-b*cost,c)
        c.pop(a,None)
    yield from rec(0,slack,{})

def neighborhoods(a,vals,counts,j,degree=14,neg=4):
    target=-neg*a-2*j
    def rec(i,num,s,row):
        if i==len(vals):
            if num==s==0:yield tuple(row)
            return
        if s<num*vals[i] or s>num*vals[-1]:return
        for u in range(min(num,counts[i]-int(a==vals[i]))+1):
            yield from rec(i+1,num-u,s-u*vals[i],row+[u])
    return list(rec(0,degree,target,[]))

def solve(j,p,seconds,integer=False,degree=14,neg=4):
    vals=tuple(p);n=list(p.values());s=z3.SolverFor('QF_LIA' if integer else 'QF_LRA')
    s.set(timeout=int(seconds*1000))
    tables=[];var=z3.Int if integer else z3.Real
    for i,a in enumerate(vals):
        rows=neighborhoods(a,vals,n,j,degree,neg)
        if not rows:return 'unsat',0
        table=[(var(f'q{i}_{k}'),row) for k,row in enumerate(rows)]
        tables.append(table);s.add(sum(q for q,row in table)==n[i],*(q>=0 for q,row in table))
    def edges(i,h):return sum(q*row[h] for q,row in tables[i] if row[h])
    for i,h in combinations_with_replacement(range(len(vals)),2):
        e=edges(i,h)
        if i!=h:s.add(e==edges(h,i))
        elif integer:s.add(e%2==0)
        lhs=sum(q*(row[i]*row[h]) for table in tables for q,row in table if row[i]*row[h])
        s.add(lhs+e==2*n[i]*n[h]+((degree-2)*n[i] if i==h else 0))
    return str(s.check()),sum(map(len,tables))

def run(cap,seconds,integer):
    out={}
    for d in range(cap+1):
        for j in range(5):
            if d%9!=8*j*j%9:continue
            kept=[];status=Counter()
            for p in profiles(j,d):
                result,_=solve(j,p,seconds,integer)
                status[result]+=1
                if result!='unsat':kept.append(p)
            out[f'{j}_{d}']=kept
            if status:print(j,d,dict(status),flush=True)
    name='shell-profiles-'+('integral' if integer else 'real')+'-'+str(cap)+'.json'
    Path(name).write_text(json.dumps(out)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=126);p.add_argument('--seconds',type=float,default=1);p.add_argument('--integer',action='store_true');a=p.parse_args();run(a.limit,a.seconds,a.integer)
