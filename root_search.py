"""Exact rooted 99-graph search by incremental common-neighbor constraints.

Every complete solution is independently checked on its ordinary adjacency
matrix. Exhaustion requires external proof replay before a nonexistence claim.
"""
import argparse
from itertools import combinations
import json
from pathlib import Path
import time
from pysat.formula import IDPool
from pysat.solvers import Solver


def partitions(n, floor=1):
    if not n:
        yield ()
    for first in range(floor,n+1):
        for tail in partitions(n-first,first):
            yield (first,)+tail


def verify(rows,k):
    n=len(rows)
    assert n==1+k*k//2
    assert all(x.bit_count()==k and not x>>i&1 for i,x in enumerate(rows))
    for i,j in combinations(range(n),2):
        assert (rows[i]>>j&1)==(rows[j]>>i&1)
        assert (rows[i]&rows[j]).bit_count()==2-(rows[i]>>j&1)


class Instance:
    def __init__(self,k,solver):
        self.k=k
        self.s=solver
        self.pool=IDPool()
        self.labels=[(a,b) for a,b in combinations(range(k),2) if a^1!=b]
        self.n=len(self.labels)
        self.pairs=list(combinations(range(self.n),2))
        self.var={p:self.pool.id() for p in self.pairs}
        self.full=set()
        self.signatures=[]
        for i,e in enumerate(self.labels):
            for a in range(k):
                support=[self.edge(i,j) for j,f in enumerate(self.labels) if a in f and i!=j]
                degree=2-int(a in e)-int((a^1) in e)
                self.s.add_atmost(support,degree)
                self.s.add_atmost([-z for z in support],len(support)-degree)
        # Relabel the axes other than {0,1}. At coordinate 0 the induced
        # perfect matching and the preassigned mate matching have alternating
        # cycles of lengths 2*p, including doubled edges when p=1.
        for parts in partitions((k-2)//2):
            selector=self.pool.id()
            self.signatures.append(selector)
            cur=2
            for p in parts:
                for j in range(p):
                    a=cur+2*j+1
                    b=cur+2*((j+1)%p)
                    u=self.labels.index((0,a))
                    v=self.labels.index((0,b))
                    self.s.add_clause([-selector,self.edge(u,v)])
                cur+=2*p
        self.s.add_clause(self.signatures)

    def edge(self,i,j):
        return self.var[min(i,j),max(i,j)]

    def rows(self,model):
        on={z for z in model if z>0}
        rows=[0]*self.n
        for (i,j),lit in self.var.items():
            if lit in on:
                rows[i]|=1<<j
                rows[j]|=1<<i
        return rows

    def bad_pairs(self,rows):
        for i,j in self.pairs:
            count=(rows[i]&rows[j]).bit_count()+((rows[i]>>j)&1)
            cap=2-len(set(self.labels[i])&set(self.labels[j]))
            if count>cap:
                yield (count-cap,i,j,cap)

    def add_pair(self,i,j,cap):
        lits=[self.edge(i,j)]
        for z in range(self.n):
            if z==i or z==j:continue
            cherry=self.pool.id()
            self.s.add_clause([-self.edge(i,z),-self.edge(j,z),cherry])
            lits.append(cherry)
        self.s.add_atmost(lits,cap)
        self.full.add((i,j))

    def simple_cut(self,i,j,cap,rows):
        shared=rows[i]&rows[j]
        active=[]
        if rows[i]>>j&1:
            active.append([self.edge(i,j)])
        while shared and len(active)<=cap:
            bit=shared&-shared
            z=bit.bit_length()-1
            active.append([self.edge(i,z),self.edge(j,z)])
            shared ^= bit
        assert len(active)==cap+1
        self.s.add_clause([-x for term in active for x in term])

    def complete(self,rows):
        k=self.k
        allrows=[0]*(1+k+self.n)
        def join(x,y):
            allrows[x]|=1<<y
            allrows[y]|=1<<x
        for a in range(k):
            join(0,1+a)
            join(1+a,1+(a^1))
        for i,(a,b) in enumerate(self.labels):
            z=1+k+i
            join(1+a,z)
            join(1+b,z)
            allrows[z]|=rows[i]<<(k+1)
        verify(allrows,k)
        return allrows


def run(k,time_limit,out):
    with Solver(name='mc') as s:
        instance=Instance(k,s)
        print('degree',k,'outer variables',len(instance.var),'cycle partitions',len(instance.signatures),flush=True)
        start=time.monotonic()
        iteration=0
        seed_file=Path(__file__).with_name('anchor-seed.json')
        seed=None
        if k==14 and seed_file.exists():
            seed=list(map(int,json.loads(seed_file.read_text())))
            s.set_phases([lit if seed[i]>>j&1 else -lit for (i,j),lit in instance.var.items()])
        while time.monotonic()-start<time_limit:
            s.conf_budget(100000)
            result=True if seed is not None else s.solve_limited()
            if result is None:
                print('cumulative conflicts',s.accum_stats()['conflicts'],'at iteration',iteration,flush=True)
                continue
            if not result:
                print('infeasible relaxation; independent proof required',flush=True)
                return
            iteration+=1
            rows=seed if seed is not None else instance.rows(s.get_model())
            seed=None
            bad=sorted(instance.bad_pairs(rows),reverse=True)
            if not bad:
                verified=instance.complete(rows)
                out.write_text(json.dumps({'degree':k,'adjacency_bits':[str(x) for x in verified]})+'\n')
                print('complete verified construction',out,flush=True)
                return
            for _,i,j,cap in bad[:8]:
                assert (i,j) not in instance.full
                instance.add_pair(i,j,cap)
            for _,i,j,cap in bad[8:]:
                instance.simple_cut(i,j,cap,rows)
            print('linear model',iteration,'violating pairs',len(bad),'activated full pair constraints',len(instance.full),flush=True)
        print('bounded search ended',s.accum_stats(),'models',iteration,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('degree',type=int)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    run(a.degree,a.seconds,a.out)
