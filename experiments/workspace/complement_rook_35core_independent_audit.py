"""Read-only independent attachment/row audit of the first35-core model.

Uses the previously certified27-core signature universe, but does not
import the attachment builder, construct CNF, or call a solver.
"""
from collections import defaultdict
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path

import complement_rook_projector_schur as base

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    model_path = LOGS/'complement-rook-35core-incidence-case0000-model.json'
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    prefix = ROOT/model['prefix_certificate']
    assert digest(prefix) == model['prefix_certificate_sha256']
    certificate = json.loads(prefix.read_text())
    archive = ROOT/certificate['archive']
    assert digest(archive) == certificate['archive_sha256']
    raw = gzip.decompress(archive.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == certificate['decompressed_jsonl_sha256']
    saved = next(item for item in map(json.loads, raw.splitlines()) if item['index'] == 0)
    old, old_gram, triples, signatures, masks, edges, domain_hash = base.domain()
    assert domain_hash == certificate['base_domain_sha256']
    case = model['case']
    core = list(old)+[0]*8
    for i, source in enumerate(case['selected_signatures'], 27):
        for j in signatures[source]:
            core[i] |= 1 << j
            core[j] |= 1 << i
    for a, b in case['matching']:
        a, b = 27+a, 27+b
        core[a] |= 1 << b
        core[b] |= 1 << a
    assert core == saved['core_rows'] and core[0].bit_count() == 14
    gram = [[12*(i == j)+2-(core[i] & core[j]).bit_count()-(core[i] >> j & 1)
             for j in range(35)] for i in range(35)]
    assert all(v >= 0 for row in gram for v in row)
    columns, raw_count = [], 0
    for source, sites in enumerate(signatures):
        if 0 in sites:
            continue
        required = 2-sum(old[0] >> v & 1 for v in sites)
        for attachment in range(256):
            if attachment.bit_count() != required:
                continue
            raw_count += 1
            support = list(sites)+[27+i for i in range(8) if attachment >> i & 1]
            if any(gram[i][j] == 0 for i in support for j in support):
                continue
            if any(sum((core[i] >> j & 1)+(i == j) for j in support) > 2 for i in range(35)):
                continue
            columns.append([source, attachment])
    columns.sort()
    assert raw_count == 3120 and columns == saved['columns'] and len(columns) == 1206
    supports = [set(signatures[s]) | {27+i for i in range(8) if a >> i & 1} for s,a in columns]
    pairs = list(combinations(range(35),2))+[(i,i) for i in range(35)]
    pairs.sort()
    rows = {(i,j): [c for c,h in enumerate(supports) if i in h and j in h] for i,j in pairs}
    distinct, coverage = {}, []
    for i,j in pairs:
        key = tuple(rows[i,j]), gram[i][j]
        if key not in distinct:
            distinct[key] = len(distinct)
        coverage.append([i,j,distinct[key]])
    formula = model['formula']
    assert coverage == formula['Gram_equation_coverage']
    assert len(distinct) == formula['distinct_Gram_equations_including_empty_zero']
    originals, triple_rows = defaultdict(list), defaultdict(list)
    for c, ((s,a), support) in enumerate(zip(columns,supports)):
        originals[s].append(c)
        for triple in combinations(sorted(support),3):
            triple_rows[triple].append(c)
    multiplicity = [[s,members] for s,members in sorted(originals.items()) if len(members)>1]
    assert multiplicity == formula['original_signature_multiplicity_rows']
    extra, triple_coverage = [], []
    for triple,members in sorted(triple_rows.items()):
        if len(members)<=1:
            continue
        quota_one = [p for p in combinations(triple,2) if gram[p[0]][p[1]]==1]
        if quota_one:
            witness = min(quota_one)
            assert set(members)<=set(rows[witness])
            triple_coverage.append({'triple':list(triple),'support':len(members),
                                    'implied_by_Gram_pair':list(witness)})
        else:
            assert all(gram[i][j]>=2 for i,j in combinations(triple,2))
            extra.append([list(triple),members])
            triple_coverage.append({'triple':list(triple),'support':len(members),
                                    'extra_row_index':len(extra)-1})
    assert extra == formula['additional_triple_rows']
    assert triple_coverage == formula['triple_capacity_coverage']
    assert all({i//9 if i<27 else 3 for i in triple} == {0,1,3} for triple,_ in extra)
    sums = [sum(gram[i][i] for i in range(27)),sum(gram[i][i] for i in range(27,35)),
            sum(gram[i][j] for i in range(27,35) for j in range(i+1,35))]
    assert sums == [192,80,20]
    report = {'status':'PASS: independent full attachment and constraint-support reconstruction',
              'audit_source_sha256':digest(Path(__file__)), 'subject_source_hashes':model['source_hashes'],
              'model_sha256':digest(model_path), 'base_domain_sha256':domain_hash,
              'raw_attachments':raw_count,'admitted_columns':len(columns),
              'original_signatures':len(originals),'all_Gram_positions':len(pairs),
              'positive_Gram_positions':sum(gram[i][j]>0 for i,j in pairs),
              'multiplicity_rows':len(multiplicity),'nontrivial_triple_rows':len(triple_coverage),
              'additional_triple_rows':len(extra),'forced_population':64,
              'forced_attachment_counts':[4,40,20], 'CNF_rebuilt':False,'solver_called':False,
              'scope':'mathematical necessity and domain/row coverage, not an UNSAT claim'}
    output = LOGS/'complement-rook-35core-incidence-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
