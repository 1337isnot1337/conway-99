"""Exact elimination of modular equalities before rational linear feasibility."""
from fractions import Fraction as F
from functools import cache
from flint import fmpq_mat,fmpq
import z3,re,time
from level_seven_exact import expr

def reduce_solver(s,seconds,save=None):
    const='$constant'
    @cache
    def linear(t):
        if z3.is_rational_value(t):return {const:F(t.as_fraction())}
        if z3.is_int_value(t):return {const:F(t.as_long())}
        if z3.is_const(t):return {str(t):F(1)}
        if z3.is_add(t):
            a={}
            for v in t.children():
                for k,x in linear(v).items():a[k]=a.get(k,0)+x
            return a
        if z3.is_mul(t):
            q=F(1);v=None
            for c in t.children():
                if z3.is_rational_value(c):q*=c.as_fraction()
                else:assert v is None;v=c
            return {k:q*x for k,x in linear(v).items()}
        raise ValueError(t)
    eq=[];ge=[];names=set()
    for a in s.assertions():
        if z3.is_true(a):continue
        if z3.is_false(a):return 'unsat (constant)'
        lhs,rhs=a.children();row=linear(z3.simplify(lhs-rhs if not z3.is_le(a) else rhs-lhs,som=True))
        (eq if z3.is_eq(a) else ge).append(row);names.update(row)
    names.discard(const)
    if save and str(save).endswith('.lp'):
        from pathlib import Path
        with open(save,'w') as ff:
            print('Minimize\n obj: 0 %s\nSubject To'%min(names),file=ff)
            for suffix,rr,sign in [('e',eq,'='),('g',ge,'>=')]:
                for i,row in enumerate(rr):
                    a={k:x for k,x in row.items() if k!=const and x}
                    rhs=-row.get(const,0)
                    if not a:
                        assert (rhs==0 if sign=='=' else rhs<=0)
                        continue
                    scale=max(abs(v) for v in a.values())
                    print(' '+suffix+str(i)+':',*('%s %s %s'%('+' if x>0 else '-',abs(x)/scale,k.replace('_-','_m')) for k,x in a.items()),sign,F(rhs)/scale,file=ff)
            print('Bounds',file=ff)
            for k in names:print(' '+k.replace('_-','_m')+' free',file=ff)
            print('End',file=ff)
        print('raw LP',len(names),len(eq),len(ge),flush=True)
        return 'exported raw'

    def key(k):
        if 'v' in k:return (0,0,k)
        nums=re.findall(r'\d+',k)
        if k[:1] in ('t','T') and len(nums)>3:return (1,-int(nums[1]),k)
        if k.startswith('m') and len(nums)>3:return (2,-int(nums[1]),k)
        if k.startswith('l') and len(nums)>3:return (3,-int(nums[2]),k)
        if k.startswith(('pedge','pnonedge')):return (2,-int(nums[1]),k)
        if k.startswith('f'):return (3,-int(nums[1]),k)
        if k.startswith('c'):return (4,-int(nums[-1]),k)
        return (5,0,k)
    cols=sorted(names,key=key)+[const];ix={k:i for i,k in enumerate(cols)}
    def mat(rows):
        M=fmpq_mat(len(rows),len(cols))
        for i,row in enumerate(rows):
            for k,x in row.items():M[i,ix[k]]=fmpq(x.numerator,x.denominator)
        return M
    A,rank=mat(eq).rref();piv=[];p=0
    for i in range(rank):
        while not A[i,p]:p+=1
        piv.append(p);p+=1
    if len(cols)-1 in piv:return 'unsat (inconsistent equations)'
    free=[i for i in range(len(cols)) if i not in set(piv)]
    print('eliminated',rank,'of',len(cols)-1,'variables;',len(free)-1,'free',len(ge),'inequalities',flush=True)
    T=fmpq_mat(len(cols),len(free))
    for j,k in enumerate(free):
        T[k,j]=1
        for i,pi in enumerate(piv):T[pi,j]=-A[i,k]
    M=mat(ge)*T;vv=[z3.Real('z'+str(i)) for i in free[:-1]];ss=z3.SolverFor('QF_LRA')
    if seconds:ss.set(timeout=seconds*1000)
    if save:
        from pathlib import Path
        output=Path(save)
        import json
        with open(str(output)+'.coordinates','w') as txt:
            print(json.dumps([cols[i] for i in free]),file=txt)
            for i,name in enumerate(cols[:-1]):
                if 'v' not in name:print(name,*[T[i,j] for j in range(T.ncols())],file=txt)
        with output.open("w") as ff:
            print("H-representation","begin",f"{M.nrows()} {M.ncols()} rational",sep="\n",file=ff)
            for i in range(M.nrows()):print(M[i,M.ncols()-1],*[M[i,j] for j in range(M.ncols()-1)],file=ff)
            print("end",file=ff)
        print("wrote reduced system",save,flush=True)
        return "exported"
    for i in range(M.nrows()):
        row=[F(str(M[i,j])) for j in range(M.ncols())]
        if not any(row[:-1]):
            if row[-1]<0:return 'unsat (constant inequality)'
            continue
        ss.add(expr(row[:-1],vv)>=z3.RealVal(str(-row[-1])))
    return str(ss.check())
