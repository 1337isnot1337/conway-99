"""Read-only source review and direct integer replay of two case4 cuts.

No subject source is imported, no optimizer or SAT solver is called,
and no complete attachment-domain or CNF reconstruction is attempted.
Each retained target's eligibility is independently enumerated over
all1,214 columns of the bound complete domain.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATHS = {
    'experiments/workspace/complement_rook_35core_case0004_exterior_rows.py':'db88ab6af3b151dc233519efb052d1fc20bd40b251e01a61558a3c93ac709977',
    'experiments/workspace/complement_rook_35core_case0004_row_separation.py':'a5a7f1a950de22e310484ec17c098eaaf19915b556d71cec67b191c4a1a79339',
    'experiments/logs/grids-and-triangles/complement-rook-35core-case0004-exterior-rows.json.gz':'10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628',
    'experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-separation-run01.json':'e758fffa8bbeb80f0fc2edd3bdb9b9fc8b992a27303679df9d9658f0c9aa18f3'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review():
    for name,value in PATHS.items():
        assert digest(ROOT/name) == value
    model = json.loads(gzip.decompress((ROOT/list(PATHS)[2]).read_bytes()))
    result = json.loads((ROOT/list(PATHS)[3]).read_text())
    core,masks = model['core_adjacency_rows'],model['column_masks35']
    assert len(core) == 35 and len(masks) == len(set(masks)) == 1214
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) and not(core[i] >> i & 1)
               for i in range(35) for j in range(35))
    gram = [[12*int(i == j)+2-(core[i]&core[j]).bit_count()-(core[i] >> j & 1)
             for j in range(35)] for i in range(35)]
    assert gram == model['Gram']
    targets = [[2-int(mask >> i & 1)-(core[i]&mask).bit_count() for i in range(35)]
               +[14-mask.bit_count()] for mask in masks]
    assert targets == model['row_targets36']
    assert all(min(row) >= 0 for row in targets)
    zero = [sum(1 << i for i in range(35) if row[i] == 0) for row in targets]
    checked = []
    for row in result['rows']:
        if 'integer_certificate' not in row:
            continue
        certificate = row['integer_certificate']
        a = row['target_column']
        assert certificate['target_column'] == a
        eligible = [b for b in range(1214) if b != a and (masks[a]&masks[b]).bit_count() <= 1
                    and not(masks[b]&zero[a]) and not(masks[a]&zero[b])]
        assert eligible == model['eligible_neighbor_column_ids'][a]
        vector = certificate['integer_vector']
        assert len(vector) == 36 and all(type(v) is int for v in vector)
        demand = sum(v*q for v,q in zip(vector,targets[a]))
        assert demand == certificate['positive_demand'] and demand > 0
        products = [[b,vector[35]+sum(vector[i] for i in range(35) if masks[b] >> i & 1)] for b in eligible]
        assert products == certificate['all_eligible_neighbor_products']
        positive = [[b,w] for b,w in products if w > 0]
        assert positive == certificate['positive_terms']
        checked.append({'target':a,'eligible_columns_checked':len(eligible),
                        'positive_terms':len(positive),'positive_integer_demand':demand,
                        'maximum_absolute_integer_coordinate':max(map(abs,vector))})
    assert [record['target'] for record in checked] == [85,628]
    return {'status':'independent source/necessity review and both complete integer row-cut checks PASS',
        'review_source_sha256':digest(Path(__file__)),'checked_hashes':PATHS,
        'all1214_mixed_and_degree_targets_independently_recomputed':True,
        'checked_inequalities':checked,
        'source_review':[
            'Actual exterior adjacency gives H D=2J-H-BH and degree14-column_weight.',
            'The35 mixed coordinates plus one degree coordinate are necessary.',
            'Overlap at most1 and both endpoint zero-quota tests remove only impossible edges.',
            'Neighbor activation y_ab<=x_b proves the positive-part weighted selector inequality.',
            'Numeric proposal ranking/sanitization does not enter universal cut validity.',
            'Positive demand is checked exactly; numerical proposal gaps are not exact infeasibility certificates.',
            'No incidence or graph automorphism is imposed; nonoptimal rows stop the bounded pilot.'
        ],
        'numerical_proposal_used_in_integer_validation':False,
        'exact_numerical_proposal_violation_claimed':False,
        'full_attachment_domain_or_CNF_rebuilt':False,
        'subject_source_imported':False,'optimizer_or_SAT_solver_called':False,
        'whole_case_or_graph_exclusion_claimed':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = review()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
