"""Harmonic positivity on the 13- and 18-dimensional residual eigenspaces of a book."""
import argparse
from itertools import combinations,product
import numpy as np
import scipy.sparse as sp
from scipy.linalg import qr
from scipy.optimize import linprog
from triangle_ball import local_ball
from triple_moments import tmp

class Relax:
    def __init__(self,degree):
        D=np.load(tmp/'book-graph-orbits.npz');self.D=D
        O,W,keys,s,rep,rev=[D[n] for n in ('O','W','keys','sizes','rep','rev')]
        n=len(s);orbit=O[0].astype(np.int32).ravel();diag=int(orbit[0])
        self.s=s;self.n=n
        H=[];cols=[];vals=[]
        for i,r in enumerate(rep):
            labels=O[r//64][:,np.arange(64)^(r%64)].ravel()
            cnt=np.bincount(orbit*n+labels,minlength=n*n).reshape((n,n))
            j,k=np.nonzero(cnt);H.extend(i*n+j);cols.extend(k);vals.extend(cnt[j,k]*np.sqrt(s[i]/s[j]))
        self.mul=sp.csr_matrix((vals,(H,cols)),shape=(n*n,n))
        word=2*np.repeat(W,64,axis=0)+((np.arange(5760)%64)[:,None]>>np.arange(6)&1)
        B=local_ball(12,[np.arange(12)^1]*3,range(12))
        N=np.zeros((n,39));u=word[rep]
        N[np.arange(n)[:,None],3+12*(u//2)+2*np.arange(6)+u%2]=1
        off=1-(np.arange(n)==diag)
        inner=[]
        for a,c,b,dimension in [(-1,1/9,3,13),(1,-2/11,4,18)]:
            M=b*np.eye(39)+a*B+c;X=a*N+c
            g=b*(1-off)+c-X@np.linalg.pinv(M,rcond=1e-11,hermitian=True)@X[diag]
            norm=g[diag];assert np.isclose(norm,7*dimension/60)
            inner.append(np.column_stack((g/norm,(g+a)/norm)))
        agree=np.sum(keys[:,[0,4,8]],axis=1)
        valid=np.column_stack((np.ones(n,bool),agree<=1))&(agree[:,None]<=2)&(np.max(keys[:,[0,4,8]],axis=1)[:,None]<=1)
        for G in inner:valid&=abs(G)<=1+1e-7
        valid[diag]=[True,False]
        self.types=[];self.chan={}
        for h,e in zip(*np.nonzero(valid)):
            t=(min(h,int(rev[h])),e)
            if t not in self.chan:self.chan[t]=len(self.chan)
            self.types.append((h,e,self.chan[t]))
        m=len(self.chan)
        self.m=m;self.diag=diag
        def factor(f):
            C=np.zeros((n,m))
            for h,e,j in self.types:C[h,j]+=f[h,e]
            return C
        def lin(x):return np.array([sum(x[h,e] for h,e,j in self.types if j==i) for i in range(m)])
        ones=np.ones((n,2));sel=np.zeros((n,2));sel[:,1]=1
        A=[];b=[]
        def add(row,target):A.append(lin(row));b.append(target)
        v=ones.copy()*0;v[diag,0]=1;add(v,1)
        for i,j in combinations(range(6),2):
            for a,c in product(range(6),repeat=2):
                cnt=np.bincount(orbit[(word[:,i]==a)&(word[:,j]==c)],minlength=n)
                add(cnt[:,None]*ones,1 if a//2==c//2 else 2)
        for i,a in product(range(6),range(6)):
            cnt=np.bincount(orbit[word[:,i]==a],minlength=n);v=word[0,i]
            prism=(v//2==a//2 and v!=a) or (v//2!=a//2 and v%2==a%2)
            add(cnt[:,None]*sel,2-int(v==a)-int(prism))
            for g in inner:add(cnt[:,None]*g,0)
        for g,d,lmb in zip(inner,(13,18),(-4,3)):
            add(s[:,None]*g*g,60/d);add(s[:,None]*sel*g,lmb)
        add(s[:,None]*inner[0]*inner[1],0)
        A=np.array(A);b=np.array(b)
        Q,R,p=qr(A.T,mode='economic',pivoting=True);rank=sum(abs(R.diagonal())>1e-7)
        assert np.max(np.abs(A@np.linalg.lstsq(A,b,rcond=1e-10)[0]-b))<1e-6
        self.A=A[p[:rank]];self.b=b[p[:rank]]
        polys=[]
        for g,d in zip(inner,(13,18)):
            z=[ones,g]
            for k in range(2,degree+1):z.append(((2*k+d-4)*g*z[-1]-(k-1)*z[-2])/(k+d-3))
            polys.append(z)
        self.kernels=[(i,j,factor(polys[0][i]*polys[1][j])) for i in range(degree+1) for j in range(degree+1-i)]
        print('orbitals',n,'orbit and adjacency variables',m,'marginal rank',rank,'harmonic blocks',len(self.kernels),flush=True)

    def solve(self,rounds):
        A,b=self.A,self.b;n=self.n;cuts=[];rng=np.random.default_rng(736)
        for step in range(rounds):
            res=linprog(np.zeros(self.m) if step else rng.normal(size=self.m),A_eq=A,b_eq=b,A_ub=np.array(cuts) if cuts else None,b_ub=np.zeros(len(cuts)) if cuts else None,bounds=(0,1),method='highs')
            if not res.success:print('LP status',res.status,'iteration',step,'cuts',len(cuts),flush=True);return
            bad=0;low=0
            for i,j,C in self.kernels:
                M=(self.mul@(C@res.x)).reshape(n,n)
                assert np.max(abs(M-M.T))<1e-7
                eig,U=np.linalg.eigh(M);low=min(low,eig[0])
                for v in U[:,eig<-2e-6].T:
                    cuts.append(-(self.mul.T@np.outer(v,v).ravel())@C);bad+=1
            if step%10==0 or not bad:print(step,'lowest',low,'cuts',len(cuts),flush=True)
            if not bad:np.save(tmp/'book-harmonic-point.npy',res.x);return

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=4);p.add_argument('--rounds',type=int,default=100);a=p.parse_args();Relax(a.degree).solve(a.rounds)
