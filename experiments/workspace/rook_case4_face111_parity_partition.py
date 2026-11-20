"""Exact72-pattern partition induced by H1=H2=1; no branch query.

The union of the two live supports has46 coordinates. A nonnegative
integer solution has at most two selected coordinates in this union.
There are32 common-support singletons and40 A-times-B pairs. Coordinates
outside the union remain free subject to the original incidence model.
"""
import argparse
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

import rook_case4_face111_two_parity_equalities as equalities

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = '195b5fc78cb6895ee7797ebf1926f1cd19d990d992d5a9e9638d44f24aa984c6'
CERTIFICATE = 'experiments/logs/grids-and-triangles/rook-case4-face111-two-parity-equalities-certificate.json'
CERTIFICATE_SHA = '6272996ff8c38af719b057dea6f6796efb895fdb678c69b82cc3eaff757ec606'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def prove(root=ROOT):
    assert digest(Path(equalities.__file__).read_bytes()) == SOURCE_SHA
    raw = (root/CERTIFICATE).read_bytes()
    assert digest(raw) == CERTIFICATE_SHA
    proof = equalities.prove(root)
    assert canonical(proof) == canonical(json.loads(raw))
    H1,H2 = map(set,proof['live_cover_supports'])
    common,A,B = sorted(H1&H2),sorted(H1-H2),sorted(H2-H1)
    union = sorted(H1|H2)
    assert list(map(len,(common,A,B,union))) == [32,4,10,46]
    assert A == proof['positive_difference_A'] and B == proof['negative_difference_B']
    selected = [[c] for c in common]+[sorted((a,b)) for a,b in product(A,B)]
    assert len(selected) == len({tuple(s) for s in selected}) == 72
    # Completeness: H1+H2=2 bounds the union population by two. Each
    # union coordinate has coefficient at least one in that sum.
    # Hence enumerating every support of size0,1,2 is exhaustive.
    enumerated,checked = [],0
    for size in range(3):
        for support in combinations(union,size):
            checked += 1
            if sum(a in H1 for a in support) == sum(a in H2 for a in support) == 1:
                enumerated.append(support)
    assert checked == 1082 and set(enumerated) == {tuple(s) for s in selected}
    cases = []
    for i,support in enumerate(selected):
        negative = sorted(set(union)-set(support))
        assert len(negative)+len(support) == 46
        assert sum(a in H1 for a in support) == sum(a in H2 for a in support) == 1
        cases.append({'case_id':i,'kind':'common_singleton' if len(support) == 1 else 'A_B_pair',
            'selected_original_columns':support,'absent_original_columns_in_union':negative})
    outside = [a for a in range(1214) if a not in set(union)|set(proof['proved_zero_columns'])]
    assert len(outside) == 1057
    return {'status':'PASS: complete disjoint72-pattern cover of the two parity equalities; no branch query',
        'source_sha256':digest(Path(__file__).read_bytes()),
        'equality_source_sha256':SOURCE_SHA,'equality_certificate_sha256':CERTIFICATE_SHA,
        'proved_zero_columns':proof['proved_zero_columns'],'live_H1':sorted(H1),'live_H2':sorted(H2),
        'common_support':common,'A':A,'B':B,'support_union':union,
        'common_singleton_cases':32,'A_B_pair_cases':40,'cases':cases,
        'independent_bounded_population_supports_checked':checked,
        'completeness_reason':'H1+H2=2 gives union population<=2. Every admissible support is either one common coordinate or one A and one B coordinate.',
        'mutual_disjointness_reason':'Different cases specify different complete0/1 assignments on the entire46-coordinate union.',
        'outside_union_surviving_columns':outside,'outside_union_columns_fixed_by_this_partition':[],
        'all_original_constraints_still_required_within_a_case':True,
        'branch_cases_claimed_feasible':False,'branch_query_count':0,'optimizer_calls':0,
        'case4_excluded':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','replay'))
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    started = time.monotonic()
    assert not args.output.exists()
    proof = prove(args.root)
    if args.mode == 'prepare':
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(proof,indent=2)+'\n')
    else:
        assert canonical(json.loads(args.certificate.read_bytes())) == canonical(proof)
    report = {'status':proof['status'],'source_sha256':proof['source_sha256'],
        'certificate_sha256':digest(args.certificate.read_bytes()),'equality_certificate_sha256':CERTIFICATE_SHA,
        'case_count':72,'union_columns':46,'outside_survivors_unfixed':1057,
        'all1082_population_at_most_two_supports_checked':True,
        'branch_query_count':0,'optimizer_calls':0,'case4_excluded':False,'seconds':time.monotonic()-started}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
