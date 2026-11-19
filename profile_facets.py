"""Intersect translated shell flag counts with the exact hulls of eligible coordinate profiles."""
from fractions import Fraction as F
from pathlib import Path
from math import isqrt
import json,subprocess,argparse

def facets(points):
    n=len(points[0])
    source=f'V-representation\nbegin\n{len(points)} {n+1} integer\n'
    source+=''.join('1 '+' '.join(map(str,p))+'\n' for p in points)+'end\n'
    proc=subprocess.run(['cddexec_gmp','--rep'],input=source,capture_output=True,text=True,check=True)
    lines=proc.stdout.splitlines();eq=set()
    for l in lines:
        if l.startswith('linearity'):eq=set(map(int,l.split()[2:]))
    idx=next(i for i,l in enumerate(lines) if l.strip()=='begin');k=int(lines[idx+1].split()[0])
    for i,l in enumerate(lines[idx+2:idx+2+k],1):
        row=list(map(F,l.split()))
        vals=[row[0]+sum(v*x for v,x in zip(row[1:],p)) for p in points]
        assert min(vals)>=0 and (i not in eq or max(vals)==0)
        yield row
        if i in eq:yield [-v for v in row]

def apply(file,out,profiles):
    with open(file+'.coordinates') as f:
        names=json.loads(next(f));n=len(names);coords={}
        for l in f:
            name,_,rest=l.partition(' ')
            if name.startswith(('c0_','f0_')):coords[name]=list(map(F,rest.split()))
    zero=[F(0)]*n;const=zero.copy();const[-1]=99;add=set()
    for key,plist in profiles.items():
        j,d=map(int,key.split('_'));name=f'c0_{j}_{d}'
        if name not in coords:continue
        count=coords[name]
        if not plist:add.add(tuple(-v for v in count));continue
        lim=isqrt(8*d);ts=[t for t in range(-lim,lim+1) if t%9==j]
        xs=[]
        for t in ts:
            r=min(t%28,(-t)%28);z=d-7*((t*t-r*r)//56)
            xs.append(const if z==r==0 else coords.get(f'f0_{z}_{r}',zero))
        points=[[p.get(str((t-j)//9),0) for t in ts] for p in plist]
        for form in facets(points):
            co=[sum(v*row[k] for v,row in zip(form,[count]+xs)) for k in range(n)]
            a=next((abs(x) for x in co if x),None)
            if a:add.add(tuple(x/a for x in co))
    with open(file) as f,open(out,'w') as g:
        g.write(next(f));g.write(next(f));m,n,kind=next(f).split()
        print(int(m)+len(add),n,kind,file=g)
        for _ in range(int(m)):g.write(next(f))
        for row in sorted(add):print(row[-1],*row[:-1],file=g)
        g.write(f.read())
    Path(out+'.coordinates').symlink_to(Path(file+'.coordinates').resolve())
    print('exact profile-hull inequalities',len(add),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('output');p.add_argument('profiles');a=p.parse_args()
    apply(a.base,a.output,json.loads(Path(a.profiles).read_text()))
