"""Test a fixed Z forest against actual high-signature overlap classes."""
from __future__ import annotations
import argparse,json
from itertools import combinations
from pathlib import Path
import pynauty
from coupled_zero_structure import forests,solve


def catalog(data):
    classes={}
    for block in data:
        for i,o in enumerate(block['orbits']):
            sig=[set(p)|{n+8 for n in ns} for p,ns in o['high']]
            C=[[0 if j==k else len(a&b) for k,b in enumerate(sig)] for j,a in enumerate(sig)]
            seen={0}
            while True:
                new=seen|{j for i in seen for j in range(8) if C[i][j]}
                if new==seen:break
                seen=new
            if len(seen)<8:continue
            adj={j:[] for j in range(8)};double=set()
            for j,k in combinations(range(8),2):
                if C[j][k]:adj[j].append(k);adj[k].append(j)
                if C[j][k]==2:
                    v=len(adj);double.add(v);adj[v]=[j,k];adj[j].append(v);adj[k].append(v)
            colors=[set(range(8))]+([double] if double else [])
            g=pynauty.Graph(len(adj),adjacency_dict=adj,vertex_coloring=colors)
            cert=pynauty.certificate(g)
            if cert not in classes:
                classes[cert]={'common':C,'source_core':block['core'],'source_orbit':i,
                               'generators':[v[:8] for v in pynauty.autgrp(g)[0]]}
    return list(classes.values())


def edge_orbits(record):
    C=record['common'];left={(i,j) for i,j in combinations(range(8),2) if C[i][j]<=1};out=[]
    while left:
        e=min(left);seen={e}
        while True:
            extra={tuple(sorted((g[i],g[j]))) for i,j in seen for g in record['generators']}
            if extra<=seen:break
            seen|=extra
        out.append(e);left-=seen
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('orbits',type=Path);p.add_argument('forest')
    p.add_argument('--seconds',type=float,default=5);p.add_argument('--output',type=Path)
    a=p.parse_args();C=catalog(json.loads(a.orbits.read_text()));print('connected overlap classes',len(C),flush=True)
    f=next(x for x in forests() if x['id']==a.forest)
    results=[]
    for ci,c in enumerate(C):
        candidates=edge_orbits(c) if f['high_edges'] else [()]
        for edge in candidates:
            r=solve(f,a.seconds,common_matrix=c['common'],endpoints=edge)
            r.update(overlap_class=ci,source_core=c['source_core'],source_orbit=c['source_orbit'])
            results.append(r)
            print(ci,edge,r['status'],r['seconds'],flush=True)
            if a.output:a.output.write_text(json.dumps(results,indent=2)+'\n')
            if r['status']=='sat':return


if __name__=='__main__':main()
