"""Check only the unvisited suffix of the frozen principal-projector scan.

The certificate source field retains the frozen checker binding. A separate
continuation source field binds this generator. No previous matrix is
classified again, and all previously certified removals are retained.
"""

import argparse
import copy
import time

import grid_free_order10_high_mask_graph_projectors as base


SOURCE_SHA = '6582189b3d6f541bb46aec5e86123a507e8622e023e1f6f73093ab86cf53660d'
PARENT = base.LOGS/'order10-high-mask-graph-projectors-scan01.json.gz'
PARENT_SHA = '280ba40a6a67370f0e4d2a9dbc9c0c67381051b4a9ee87b5f0c2f39dcf32f200'
COLD = base.LOGS/'order10-high-mask-graph-projectors-scan01-replay.json'
MAX_SECONDS = 15


def finish(output):
    assert base.digest(base.Path(base.__file__)) == SOURCE_SHA
    assert base.digest(PARENT) == PARENT_SHA
    parent, cold = base.read(PARENT), base.read(COLD)
    assert cold['result_sha256'] == PARENT_SHA and cold['status'].startswith('PASS:')
    assert parent['source_sha256'] == SOURCE_SHA and not parent['complete']
    start = parent['checked_full_columns']
    assert start == 153727 and parent['unvisited_columns_retained'] == 3984
    assert len(parent['rejection_witnesses']) == cold['removed_graphs_checked'] == 20601
    record, arrays = base.load_domain()
    result = copy.deepcopy(parent)
    rejects, ranks = result['rejection_witnesses'], result['accepted_projector_rank_histograms']
    started, checked = time.monotonic(), start
    for full in range(start, 157711):
        if time.monotonic()-started >= MAX_SECONDS:
            break
        atom, masks, edges, rows = base.graph(record, arrays, full)
        for kind in (0, 1):
            check = base.exact_psd(base.schur(masks, edges, kind))
            if check['psd']:
                ranks[kind][check['rank']] += 1
                continue
            z = check['negative_vector']
            v = base.full_vector(masks, z, kind)
            value = base.quadratic(base.principal(rows, kind), v)
            assert value == (891 if kind == 0 else 704)*check['quadratic_value'] < 0
            rejects.append({'full_column': full, 'atom_orbit': atom, 'projector': kind,
                            'integer_schur_vector': z, 'schur_quadratic': check['quadratic_value'],
                            'full_quadratic': value})
            break
        checked += 1
    assert rejects[:20601] == parent['rejection_witnesses']
    removed = {r['full_column'] for r in rejects}
    assert len(removed) == len(rejects)
    kept = [j for j in range(157711) if j not in removed]
    result.update(status='complete exact principal-projector filter' if checked == 157711 else
                  'partial exact filter; unvisited columns retained', complete=checked == 157711,
                  continuation_source_sha256=base.digest(base.Path(__file__)),
                  parent_result_sha256=PARENT_SHA, parent_cold_replay_sha256=base.digest(COLD),
                  continuation_start_column=start, continuation_maximum_seconds=MAX_SECONDS,
                  continuation_columns_checked=checked-start,
                  continuation_seconds=time.monotonic()-started,
                  checked_full_columns=checked, rejected_full_columns=len(rejects),
                  retained_full_columns=len(kept), retained_columns=kept,
                  unvisited_columns_retained=157711-checked,
                  previous_matrices_classified_again=False,
                  seconds=parent['seconds']+time.monotonic()-started)
    base.save(output, result)
    print(base.json.dumps({k: v for k, v in result.items() if k not in
                          ('retained_columns', 'rejection_witnesses', 'accepted_projector_rank_histograms')}, indent=2))
    print('result_sha256', base.digest(output), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=base.Path, required=True)
    args = parser.parse_args()
    finish(args.output)
