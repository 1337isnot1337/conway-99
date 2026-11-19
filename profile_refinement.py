"""Apply the second-walk equations at every surviving local neighborhood type."""
from itertools import combinations_with_replacement
from collections import Counter
from pathlib import Path
import argparse,json,z3
from shell_profiles import neighborhoods

def refine(j,p,seconds=3,degree=14,neg=4):
    vals=tuple(sorted(p));n=[p[v] for v in vals]
    types=[(i,r) for i,a in enumerate(vals) for r in neighborhoods(a,vals,n,j,degree,neg)]
    q=z3.Reals(' '.join('q'+str(i) for i in range(len(types))))
    table=[[(v,r) for v,(k,r) in zip(q,types) if k==i] for i in range(len(n))]
    s=z3.SolverFor('QF_LRA');s.set(timeout=int(seconds*1000));s.add(*(v>=0 for v in q))
    for i,t in enumerate(table):s.add(sum(v for v,r in t)==n[i])
    def e(i,k):return sum(v*r[k] for v,r in table[i] if r[k])
    for i,k in combinations_with_replacement(range(len(n)),2):
        s.add(e(i,k)==e(k,i))
        s.add(sum(v*r[i]*r[k] for v,(_,r) in zip(q,types) if r[i]*r[k])+e(i,k)==2*n[i]*n[k]+((degree-2)*n[i] if i==k else 0))
    # Union of supports of feasible real solutions. Unknowns are retained.
    active=set()
    while True:
        res=s.check()
        if res==z3.unknown:
            active.update(range(len(q)));break
        if res==z3.unsat:
            if not active:return 'unsat'
            break
        m=s.model()
        active.update(i for i,v in enumerate(q) if m.eval(v).as_fraction()>0)
        missing=[v for i,v in enumerate(q) if i not in active]
        if not missing:break
        s.push();s.add(sum(missing)>0)
    s=z3.SolverFor('QF_LRA');s.set(timeout=int(seconds*1000))
    idx=sorted(active);s.add(*(q[i]>=0 for i in idx))
    for k in range(len(n)):s.add(sum(q[i] for i in idx if types[i][0]==k)==n[k])
    adj={i:[] for i in idx}
    for off,i in enumerate(idx):
        a,r=types[i]
        for k in idx[off:]:
            b,t=types[k]
            if not r[b] or not t[a] or (a==b and n[a]<2):continue
            if sum(max(0,x+y-z) for x,y,z in zip(r,t,n))>1:continue
            if sum(min(x-int(h==b),y-int(h==a)) for h,(x,y) in enumerate(zip(r,t)))<1:continue
            v=z3.Real(f'e{i}_{k}');s.add(v>=0)
            adj[i].append((k,v))
            if i!=k:adj[k].append((i,v))
    for i in idx:
        a,r=types[i]
        for b,mult in enumerate(r):
            s.add(sum(v for k,v in adj[i] if types[k][0]==b)==q[i]*mult)
            s.add(sum(v*types[k][1][b] for k,v in adj[i] if types[k][1][b])==q[i]*((degree-2)*(a==b)+2*n[b]-mult))
    return str(s.check())

def run(file,cap,seconds):
    input=json.loads(Path(file).read_text());out={};counts=Counter()
    for key,ps in input.items():
        j,d=map(int,key.split('_'))
        if d>cap:out[key]=ps;continue
        kept=[]
        for profile in ps:
            p={int(a):n for a,n in profile.items()};r=refine(j,p,seconds)
            counts[r]+=1
            if r!='unsat':kept.append(profile)
        out[key]=kept
        if len(kept)!=len(ps):print(j,d,'kept',len(kept),'of',len(ps),flush=True)
    Path('shell-profiles-refined-'+str(cap)+'.json').write_text(json.dumps(out)+'\n')
    print(dict(counts),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--limit',type=int,default=140);p.add_argument('--seconds',type=float,default=2);a=p.parse_args();run(a.file,a.limit,a.seconds)
