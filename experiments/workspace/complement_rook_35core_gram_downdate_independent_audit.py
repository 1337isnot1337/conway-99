"""Independent complete-domain and direct-integer audit of886 pair cuts.

This does not import the downdate source or use its inverse, Schur tests,
or quotient. Each full35-dimensional negative vector is checked directly.
No CNF is rebuilt and no solver is called.
"""
from itertools import combinations
import gzip
import hashlib
import json
from pathlib import Path

import complement_rook_projector_schur as base


ROOT=Path(__file__).resolve().parents[2]
LOGS=ROOT/'experiments/logs/grids-and-triangles'
CERT=LOGS/'complement-rook-35core-case0002-gram-downdate.json.gz'
FRAGMENT=LOGS/'complement-rook-35core-case0002-gram-downdate-clauses.cnf'
CERT_SHA='de5cbe02ea5cda392b139bed8e7468fc75e6e37bb7619aad8e743a396c859294'
FRAGMENT_SHA='a86af34800a77f1a07f72d823e02d2832fecb39eb8775ce2526c0a7f5806d25e'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert digest(CERT)==CERT_SHA and digest(FRAGMENT)==FRAGMENT_SHA
    saved=json.loads(gzip.decompress(CERT.read_bytes()))
    for name,expected in saved['source_hashes'].items():
        assert digest(Path(__file__).with_name(name))==expected
    index_path=ROOT/saved['bindings']['complete_core_index']
    assert digest(index_path)==saved['bindings']['complete_core_index_sha256']
    assert json.loads(index_path.read_text())['cases'][2]==saved['case']
    rows,_,_,signatures,masks,_,domain_hash=base.domain()
    assert domain_hash==saved['bindings']['base_domain_sha256']
    case=saved['case']
    core=list(rows)+[0]*8
    for i,source in enumerate(case['selected_signatures'],27):
        for j in signatures[source]:
            core[i] |= 1<<j
            core[j] |= 1<<i
    for a,b in case['matching']:
        a,b=27+a,27+b
        core[a] |= 1<<b
        core[b] |= 1<<a
    assert core==saved['core_adjacency_bit_rows']
    gram=[[12*(i==j)+2-(core[i]&core[j]).bit_count()-(core[i]>>j&1)
           for j in range(35)] for i in range(35)]
    assert gram==saved['Gram']
    columns=[]
    raw_count=0
    for source,sites in enumerate(signatures):
        if 0 in sites:
            continue
        degree=2-(rows[0]&masks[source]).bit_count()
        for attachment in range(256):
            if attachment.bit_count()!=degree:
                continue
            raw_count+=1
            support=list(sites)+[27+i for i in range(8) if attachment>>i&1]
            if any(gram[i][j]<=0 for i in support for j in support):
                continue
            if any(sum((core[i]>>j&1)+(i==j) for j in support)>2 for i in range(35)):
                continue
            columns.append([source,attachment])
    columns.sort()
    assert raw_count==3120 and len(columns)==1287 and columns==saved['attachment_columns']
    full_masks=[masks[source]|(attachment<<27) for source,attachment in columns]
    witnesses=saved['scan']['additional_binary_exclusion_witnesses']
    assert len(witnesses)==886
    pairs=[]
    largest=0
    for witness in witnesses:
        a,b=witness['columns']
        assert 0<=a<b<len(columns)
        assert columns[a][0]!=columns[b][0]
        common=[i for i in range(35) if (full_masks[a]&full_masks[b])>>i&1]
        assert len(common)<=2 and all(gram[i][j]!=1 for i,j in combinations(common,2))
        vector=witness['negative_vector']
        assert len(vector)==35 and all(type(value) is int for value in vector)
        value=sum(vector[i]*gram[i][j]*vector[j] for i in range(35) for j in range(35))
        for column in (a,b):
            dot=sum(vector[i] for i in range(35) if full_masks[column]>>i&1)
            value-=dot*dot
        assert value==witness['negative_quadratic_value'] and value<0
        largest=max(largest,max(abs(x) for x in vector))
        pairs.append([a,b])
    assert len({tuple(pair) for pair in pairs})==886
    expected=(f'p cnf 1287 886\n'+''.join(f'{-a-1} {-b-1} 0\n' for a,b in pairs)).encode()
    assert FRAGMENT.read_bytes()==expected
    report={'status':'PASS: independent complete attachment domain and886 direct negative-vector inequalities',
            'audit_source_sha256':digest(Path(__file__)),'subject_source_hashes':saved['source_hashes'],
            'certificate_sha256':CERT_SHA,'clause_fragment_sha256':FRAGMENT_SHA,
            'raw_attachment_columns':raw_count,'complete_admitted_columns':len(columns),
            'full35_Gram_entries_reconstructed':1225,'direct_integer_negative_vectors_checked':886,
            'largest_absolute_vector_coordinate':largest,
            'all_clauses_use_the_complete_primary_column_order':True,
            'quotient_inverse_or_Schur_formula_used':False,
            'complete827541_pair_census_recomputed':False,'CNF_rebuilt':False,'solver_called':False,
            'necessity':'If both columns occur, G-hh^T-kk^T is a sum of remaining incidence outer products and must be PSD.',
            'scope':'Necessary binary clauses for indexed35-core case2; no case exclusion claimed.'}
    output=LOGS/'complement-rook-35core-case0002-gram-downdate-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
