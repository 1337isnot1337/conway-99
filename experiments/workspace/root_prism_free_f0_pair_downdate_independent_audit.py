"""Independent integer-matrix/vectorized replay of the full type census.

No subject builder or classifier is imported. Rebuild all480 triples and
230,400 component-pair types, then compare every complete two-column
classification total. The alternative homogeneous inverse formula uses
profile dot products rather than centered-profile corrections.
"""

import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
INPUTS = {
    'f0-pair-gram-certificate.json.gz':'edb85ff422222961e6bc9b36322b74bcfce455bca262d6e189d7768f9ac91c98',
    'f0-pair-gram-model-preparation.json.gz':'7b870a9df98c855f75fcd0191b5fe03589d9458ad1e3f985ba77edb066be0c59',
    'f0-pair-clauses.json.gz':'47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f',
    'f0-pair-downdate-bounds.json':'443c87ca561fa28c343d0446afa6d65ad87ad7d1f754a54a1756e5fcca7b6dfb'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(output,seconds):
    assert not output.exists() and 0 < seconds <= 120
    started = time.monotonic()
    loaded = {}
    for name,value in INPUTS.items():
        path = LOGS/name
        assert digest(path) == value
        raw = path.read_bytes()
        loaded[name] = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    g = loaded['f0-pair-gram-certificate.json.gz']
    prepared = loaded['f0-pair-gram-model-preparation.json.gz']
    bounds = loaded['f0-pair-downdate-bounds.json']
    assert bounds['conservative_determinant_absolute_upper'] < 2**63-1
    rows = list(map(int,g['joined_core_rows']))
    gram = [[12*int(i == j)+2-(rows[i]&rows[j]).bit_count()-(rows[i] >> j & 1)
             for j in range(39)] for i in range(39)]
    assert gram == g['Gram']
    local = [row[3:21] for row in gram[3:21]]
    triples = []
    for h in combinations(range(18),3):
        profile = [sum(v//6 == f for v in h) for f in range(3)]
        if max(profile) > 2 or any(local[i][j] == 0 for i,j in combinations(h,2)):
            continue
        if any(sum(int(i == v or rows[3+i] >> (3+v) & 1) for v in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == g['component_triples'] and len(triples) == 480
    Q = g['bilinear_reduction']['component_inverse_numerator']
    denominator = g['bilinear_reduction']['component_inverse_denominator']
    assert denominator == 2288520
    assert all(sum(local[i][k]*Q[k][j] for k in range(18)) == denominator*int(i == j)
               for i in range(18) for j in range(18))
    assert 9*max(abs(v) for row in Q for v in row) < 2**63-1
    incidence = np.array([[int(i in h) for i in range(18)] for h in triples],dtype=np.int64)
    products = incidence @ np.array(Q,dtype=np.int64) @ incidence.T
    profiles = [tuple(map(int,row)) for row in incidence.reshape(480,3,6).sum(axis=2)]
    overlap = np.stack([incidence[:,6*f:6*f+6] @ incidence[:,6*f:6*f+6].T for f in range(3)],axis=2)
    local_flag = np.zeros((480,480),dtype=np.bool_)
    for i,j in combinations(range(18),2):
        if local[i][j] == 1:
            ids = np.flatnonzero(incidence[:,i]&incidence[:,j])
            local_flag[np.ix_(ids,ids)] = True
    motif_flag = np.zeros((480,480),dtype=np.bool_)
    record = loaded['f0-pair-clauses.json.gz']['representatives'][0]
    for family in ('F_conflicts','prism_conflicts'):
        for witness in record[family]:
            a,c = witness['columns']
            motif_flag[a,c] = motif_flag[c,a] = True
    histogram = Counter()
    diagonal = products.diagonal()
    for a in range(480):
        for c in range(480):
            key = (profiles[a],profiles[c],int(diagonal[a]),int(diagonal[c]),int(products[a,c]),
                   tuple(map(int,overlap[a,c])),int(local_flag[a,c]),int(motif_flag[a,c]))
            histogram[key] += 1
    types = [[list(k[0]),list(k[1]),k[2],k[3],k[4],list(k[5]),k[6],k[7],count]
             for k,count in sorted(histogram.items())]
    assert types == prepared['bilinear_table_preparation']['type_histogram']
    groups = defaultdict(list)
    for i,t in enumerate(types):
        groups[tuple(t[0]),tuple(t[1])].append(i)
    # Homogeneous formula: 2*(R_left+R_right)+D/15-(D/36)*profile_dot.
    D = 4577040
    aa = np.array([t[2] for t in types],dtype=np.int64)
    cc = np.array([t[3] for t in types],dtype=np.int64)
    ac = np.array([t[4] for t in types],dtype=np.int64)
    intersections = np.array([t[5] for t in types],dtype=np.int64)
    local_bits = np.array([t[6] for t in types],dtype=np.bool_)
    motif_bits = np.array([t[7] for t in types],dtype=np.bool_)
    weight = np.array([t[8] for t in types],dtype=np.int64)
    all_counts = np.zeros(32,dtype=np.int64)
    bad_counts = np.zeros(32,dtype=np.int64)
    all_type_counts = np.zeros(32,dtype=np.int64)
    bad_type_counts = np.zeros(32,dtype=np.int64)
    total = self_count = self_types = bad_self = 0
    allowed_minimum = None
    allowed_minimum_ids = None
    allowed_zero_weight = 0
    for (p,q),left_ids in sorted(groups.items()):
        right_ids = np.array(groups[tuple(2-x for x in p),tuple(2-x for x in q)],dtype=np.int64)
        r = right_ids[None,:]
        for start in range(0,len(left_ids),128):
            assert time.monotonic()-started < seconds
            l = np.array(left_ids[start:start+128],dtype=np.int64)[:,None]
            nh = 2*(aa[l]+aa[r])+D//15-(D//36)*sum(x*x for x in p)
            nk = 2*(cc[l]+cc[r])+D//15-(D//36)*sum(x*x for x in q)
            cross = 2*(ac[l]+ac[r])+D//15-(D//36)*sum(x*y for x,y in zip(p,q))
            assert int(nh.min()) >= 2240036 and int(nh.max()) <= 3242772
            assert int(nk.min()) >= 2240036 and int(nk.max()) <= 3242772
            assert np.all(cross*cross <= nh*nk)
            determinant = (D-nh)*(D-nk)-cross*cross
            assert int(np.abs(determinant).max()) <= bounds['conservative_determinant_absolute_upper']
            w = weight[l]*weight[r]
            ls = intersections[l].sum(axis=2)
            rs = intersections[r].sum(axis=2)
            same = (ls == 3)|(rs == 3)
            self_mask = (ls == 3)&(rs == 3)
            triple = ls+rs >= 3
            local_one = local_bits[l]|local_bits[r]
            cross_one = (intersections[l]*intersections[r]).sum(axis=2) > 0
            motif = motif_bits[l]|motif_bits[r]
            mask = same.astype(np.int8)+2*triple+4*local_one+8*cross_one+16*motif
            negative = determinant < 0
            total += determinant.size
            self_count += int(w[self_mask].sum(dtype=np.int64))
            self_types += int(np.count_nonzero(self_mask))
            bad_self += int(w[self_mask&negative].sum(dtype=np.int64))
            for flag in np.unique(mask[~self_mask]):
                selected = (mask == flag)&~self_mask
                bad = selected&negative
                all_counts[int(flag)] += w[selected].sum(dtype=np.int64)
                bad_counts[int(flag)] += w[bad].sum(dtype=np.int64)
                all_type_counts[int(flag)] += np.count_nonzero(selected)
                bad_type_counts[int(flag)] += np.count_nonzero(bad)
            allowed = ~triple
            allowed_zero_weight += int(w[allowed&(determinant == 0)].sum(dtype=np.int64))
            if np.any(allowed):
                masked = np.where(allowed,determinant,np.iinfo(np.int64).max)
                loc = np.unravel_index(int(masked.argmin()),masked.shape)
                value = int(masked[loc])
                if allowed_minimum is None or value < allowed_minimum:
                    allowed_minimum = value
                    allowed_minimum_ids = [int(l[loc[0],0]),int(r[0,loc[1]])]
    subject_path = LOGS/'f0-pair-downdate-run01/certificate.json'
    subject = json.loads(subject_path.read_text())
    native = subject['native']['native_summary']
    assert total == native['type_combinations'] == 33578176
    assert self_count == native['self_ordered_pairs'] == 39168
    assert self_types == native['self_type_combinations'] and bad_self == native['negative_duplicate_self_columns']
    for name,actual in [('all_nonself_ordered_counts_by_mask',all_counts),('negative_nonself_ordered_counts_by_mask',bad_counts),
                        ('all_nonself_type_counts_by_mask',all_type_counts),('negative_nonself_type_counts_by_mask',bad_type_counts)]:
        assert list(map(int,actual)) == native[name]
    assert sum(map(int,all_counts))+self_count == 39168**2
    assert all(int(v)%2 == 0 for v in all_counts) and all(int(v)%2 == 0 for v in bad_counts)
    assert sum(int(v) for i,v in enumerate(bad_counts) if not i&2) == 0
    predicate = ROOT/subject['predicate_file']
    assert digest(predicate) == subject['predicate_file_sha256'] and gzip.decompress(predicate.read_bytes()) == b''
    report = {'status':'PASS: independent complete integer type census and vectorized two-column classification',
              'audit_source_sha256':digest(Path(__file__)),'subject_certificate_sha256':digest(subject_path),
              'input_hashes':INPUTS,'independent_component_triples':len(triples),'independent_component_types':len(types),
              'ordered_type_combinations':total,'self_full_columns':self_count,
              'distinct_unordered_full_column_pairs':int(all_counts.sum())//2,
              'negative_unordered_pairs':int(bad_counts.sum())//2,
              'negative_pairs_with_intersection_at_most_two':0,
              'all_negative_pairs_already_violate_triple_packing':True,
              'allowed_pair_minimum_determinant_numerator':allowed_minimum,
              'allowed_pair_minimum_type_ids':allowed_minimum_ids,
              'allowed_pair_zero_determinant_unordered_count':allowed_zero_weight//2,
              'all32_count_and_type_categories_match_native_result':True,
              'empty_new_predicate_archive_checked':True,
              'subject_builder_or_classifier_imported':False,'native_classifier_called':False,'solver_called':False,
              'integer_arithmetic':'NumPy int64 with independently checked integer bounds; no float reductions',
              'elapsed_seconds':time.monotonic()-started}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=120)
    args = parser.parse_args()
    main(args.output.resolve(),args.seconds)
