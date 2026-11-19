"""Exact necessary spectra for the two/three-triangle split at eight red grids.

This enumerates rational invariant-subspace spectra of I+cycle adjacency.
It is a necessary spectral relaxation, not a graph construction.
"""
from collections import Counter
from functools import lru_cache
import argparse
import json
from pathlib import Path
import sympy as sp

X=sp.Symbol('x')

@lru_cache(None)
def factors(length):
    a,b=sp.Integer(2),X
    for _ in range(2,length+1):
        a,b=b,sp.expand(X*b-a)
    polynomial=sp.Poly((b-2).subs(X,X-1),X)
    answer=[]
    for f,m in sp.factor_list(polynomial)[1]:
        coefficients=tuple(map(int,f.all_coeffs()))
        if coefficients==(1,-3):
            continue
        answer.append((coefficients,int(m)))
    return tuple(answer)

def partitions(total,minimum=6):
    if total==0:
        yield ()
    for first in range(minimum,total+1,3):
        for rest in partitions(total-first,first):
            yield (first,)+rest

def statistics(coeff):
    d=len(coeff)-1
    s1=-coeff[1]
    s2=s1*s1-(2*coeff[2] if d>=2 else 0)
    return d,s1,s2,12*d-s1-s2

def enumerate_spectra(cycles):
    n=sum(cycles)
    counts=Counter({(1,0):27-n})
    for length in cycles:
        counts.update(dict(factors(length)))
    # im(T) is orthogonal to the all-one vector. With no eigenvalue3,
    # its zero-eigenspace must also be orthogonal to 1 on the type3 sites.
    if n<27:
        counts[(1,0)]-=1
    data=[(c,m,statistics(c)) for c,m in sorted(counts.items()) if m]
    answer=[]
    def visit(k,energy,r,s1,s2,chosen):
        if energy>96 or r>26:
            return
        if k==len(data):
            if energy!=96 or (160-3*r+s1)%7:
                return
            p=(160-3*r+s1)//7
            if not 0<=p<=32-r:
                return
            answer.append({'rank':r,'trace':s1,'trace_square':s2,
                           'delta':s2-3*s1,'kernel_positive_multiplicity':p,
                           'factors':[{'polynomial':list(c),'multiplicity':m}
                                      for c,m in chosen if m]})
            return
        c,m,(d,t1,t2,e)=data[k]
        assert e>0
        for multiplicity in range(min(m,(96-energy)//e)+1):
            visit(k+1,energy+multiplicity*e,r+multiplicity*d,
                  s1+multiplicity*t1,s2+multiplicity*t2,
                  chosen+[(c,multiplicity)])
    visit(0,0,0,0,0,[])
    return answer

def run():
    cases=[]
    for n in range(0,28,3):
        for cycles in partitions(n):
            spectra=enumerate_spectra(cycles)
            cases.append({'type2_vertices':n,'cycles':list(cycles),'spectra':spectra})
    survivors=[r for r in cases if r['spectra']]
    return {'partitions_checked':len(cases),'surviving_partitions':len(survivors),
            'spectrum_count':sum(len(r['spectra']) for r in survivors),
            'survivors':survivors,'all_cases':cases}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=run()
    if args.output:
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='all_cases'},indent=2))
