"""Exact two-column prism and F witnesses for the66 eighteen-components.

Each recorded pair creates the indicated forbidden motif using only
known core incidences. No edge between the two new vertices is assumed.
No solver is called. The first Gram pilot uses both motif families.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path

import root_prism_free_f0_components as components


ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT/'experiments/logs/root-prism-free/f0-components-certificate.json.gz'
DOMAIN_SHA = 'dc8aad926550cef6a8ee39aa8f4efbd056773950183b9e0ac86b195e8057c3fd'
canonical = components.canonical


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    assert digest(DOMAIN) == DOMAIN_SHA
    saved = json.loads(gzip.decompress(DOMAIN.read_bytes()))
    assert saved['source_sha256'] == digest(Path(components.__file__))
    assert len(saved['representatives']) == 66
    return saved


def partial(domain, first, second):
    rows = list(domain['core_rows'])+[0,0]
    for new, column in ((21,first),(22,second)):
        for vertex in domain['signature_domain'][column]:
            components.edge(rows,new,3+vertex)
    return rows


def induced(rows, sites):
    assert len(set(sites)) == len(sites)
    return [sum((rows[v] >> w & 1) << j for j,w in enumerate(sites)) for v in sites]


def is_F(rows):
    if len(rows) != 10 or [r.bit_count() for r in rows] != [5,5]+[3]*8:
        return False
    if not rows[0] >> 1 & 1:
        return False
    if any((rows[v] & 3).bit_count() != 1 for v in range(2,10)):
        return False
    shell = [row >> 2 for row in rows[2:]]
    if components.component_sizes(shell) != [8]:
        return False
    for v in range(2,10):
        color = rows[v] & 3
        if sum((rows[v] >> w & 1) for w in range(2,10) if rows[w] & 3 == color) != 1:
            return False
    return True


def is_prism(rows):
    if len(rows) != 6 or any(row.bit_count() != 3 for row in rows):
        return False
    first,second = range(3),range(3,6)
    return (all(rows[a] >> b & 1 for triangle in (first,second) for a,b in combinations(triangle,2))
            and all(sum(rows[a] >> b & 1 for b in second) == 1 for a in first)
            and all(sum(rows[b] >> a & 1 for a in first) == 1 for b in second))


def clauses_for(domain):
    shell, gram = domain['shell_rows'],domain['Gram']
    lookup = {tuple(t):i for i,t in enumerate(domain['signature_domain'])}
    f_records, prism_records = {},{}

    def add(first,second,kind,family,sites):
        a,b = lookup.get(tuple(sorted(first))),lookup.get(tuple(sorted(second)))
        if a is None or b is None:
            return
        assert a != b
        shared = set(first)&set(second)
        if any(gram[i][j] < 2 for i,j in combinations(shared,2)):
            # This pair is already excluded by a Gram quota-one equation.
            return
        rows = partial(domain,a,b)
        assert components.caps(rows)
        motif = induced(rows,sites)
        assert (is_F if kind == 'F' else is_prism)(motif)
        # If an A--B edge were added, it would violate an adjacent-pair cap.
        joined = rows[:]
        components.edge(joined,21,22)
        assert not components.caps(joined)
        key = tuple(sorted((a,b)))
        record = {'columns':list(key),'ordered_columns':[a,b], 'family':family,
                  'motif_sites':sites,'induced_motif_rows':motif,
                  'known_partial_caps_hold':True,'new_vertex_edge_forbidden_by_caps':True}
        (f_records if kind == 'F' else prism_records).setdefault(key,record)

    mate = [next(v for v in range(6*(u//6),6*(u//6)+6) if shell[u] >> v & 1)
            for u in range(18)]
    for u in range(18):
        fi = u//6
        v,w = [v for v in range(18) if shell[u] >> v & 1 and v//6 != fi]
        for x in range(6*fi,6*fi+6):
            if x in (u,mate[u]):
                continue
            y = mate[x]
            add((u,v,x),(u,w,y),'F','central-shell edge',
                [fi,3+u,v//6,w//6,3+x,3+y,3+v,3+w,21,22])
    for u,v in combinations(range(18),2):
        if not shell[u] >> v & 1 or u//6 == v//6:
            continue
        mu,mv = mate[u],mate[v]
        w = next(x for x in range(18) if shell[u] >> x & 1 and x//6 not in (u//6,v//6))
        z = next(x for x in range(18) if shell[v] >> x & 1 and x//6 not in (u//6,v//6))
        sites = [3+u,3+v,u//6,3+mu,3+w,21,v//6,3+mv,3+z,22]
        if shell[mu] >> z & 1:
            add((u,w,mv),(v,z,w),'F','cross-shell edge, first chord',sites)
        if shell[w] >> mv & 1:
            add((u,w,z),(v,z,mu),'F','cross-shell edge, second chord',sites)
        if shell[w] >> z & 1:
            add((u,w,mv),(v,z,mu),'F','cross-shell edge, third-fiber mate',sites)
    for a in range(18):
        for b in range(18):
            if not shell[a] >> b & 1:
                continue
            for c in range(18):
                if c == a or not shell[b] >> c & 1:
                    continue
                for d in range(18):
                    if d in (a,b) or not shell[c] >> d & 1:
                        continue
                    add((a,b,d),(a,c,d),'prism','four-vertex shell path',
                        [21,3+a,3+b,22,3+c,3+d])
    return {'F_conflicts':[f_records[key] for key in sorted(f_records)],
            'prism_conflicts':[prism_records[key] for key in sorted(prism_records)],
            'F_conflict_count':len(f_records),'prism_conflict_count':len(prism_records),
            'F_family_counts':dict(sorted(Counter(r['family'] for r in f_records.values()).items()))}


def result():
    domain = load()
    records = [{'representative':i, **clauses_for(record['domain'])}
               for i,record in enumerate(domain['representatives'])]
    return {'status':'explicit necessary two-selector motif clauses; no solver called',
            'source_sha256':digest(Path(__file__)), 'domain_certificate_sha256':DOMAIN_SHA,
            'domain_source_sha256':domain['source_sha256'],'representatives':records,
            'scope':domain['scope'], 'no_graph_automorphism_assumption':True,
            'all_unknown_exterior_edges_unspecified':True,
            'pilot_enforces_prism_conflicts':True, 'optimizer_called':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate',required=True,type=Path)
    parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    actual=result()
    if args.replay:
        assert json.loads(gzip.decompress(args.certificate.read_bytes())) == actual
    else:
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(actual)+b'\n',mtime=0))
    print(json.dumps({'status':'PASS: all motif incidences and clause witnesses checked',
                      'mode':'replay' if args.replay else 'generation',
                      'representatives':len(actual['representatives']),
                      'F_conflict_range':[min(r['F_conflict_count'] for r in actual['representatives']),
                                          max(r['F_conflict_count'] for r in actual['representatives'])],
                      'prism_conflict_range':[min(r['prism_conflict_count'] for r in actual['representatives']),
                                              max(r['prism_conflict_count'] for r in actual['representatives'])],
                      'representative0_F_conflicts':actual['representatives'][0]['F_conflict_count'],
                      'optimizer_called':False},indent=2),flush=True)
