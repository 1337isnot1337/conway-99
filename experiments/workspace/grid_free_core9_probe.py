"""Bounded grid-free probe of the existing order-nine count/moment model.

All files written by this probe have a grid-free-specific name. Existing
catalogues, moment blocks, cuts, and witnesses are read only. A numerical
PSD candidate is not an exact semidefinite certificate or a graph.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import pickle
import re
import time

import numpy as np
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits

from flag_moments import BASE, cache9
from flag_separate import cuts, prim


def load_blocks(prefix):
    blocks = []
    files = sorted(BASE.glob(prefix+'moments-?-?-512.pickle'))
    for path in files:
        with path.open('rb') as stream:
            blocks.extend(pickle.load(stream))
    return blocks, [path.name for path in files]


def run(rounds, seconds, out):
    start = time.monotonic()
    graphs, levels, aut, cores, scale, inj_object, induced = cache9()
    zero_types = [i for i, graph in enumerate(graphs)
                  if len(graph) == 9 and sum(row.bit_count() for row in graph) >= 34]
    assert len(zero_types) == 2
    fixed = [cores.index(i) for i in zero_types]
    free = [i for i in range(len(cores)) if i not in fixed]
    assert fixed == [55, 56]
    forms = {prim(row) for row in induced}
    forms.discard(())
    saved = {tuple(row) for row in json.loads((BASE/'flag-cuts.json').read_text())}
    forms |= saved
    ordinary, ordinary_files = load_blocks('')
    induced_blocks, induced_files = load_blocks('induced-')
    assert np.max(abs(inj_object)) < 2**63
    inj = np.asarray(inj_object, dtype=np.int64)
    assert not np.any(induced % scale)
    rated_object = (induced//scale)*np.array(aut, dtype=object)[:, None]
    assert np.max(abs(rated_object)) < 2**63
    rated = np.asarray(rated_object, dtype=np.int64)
    result = {'scope': 'order-nine counts plus finite ordinary and induced moment blocks',
              'fixed_zero_core_coordinates': fixed, 'fixed_zero_catalogue_types': zero_types,
              'ordinary_blocks': len(ordinary), 'induced_blocks': len(induced_blocks),
              'ordinary_cache_files': ordinary_files, 'induced_cache_files': induced_files,
              'archived_exact_cuts': len(saved), 'rounds': []}
    added = set()
    status = 'round_limit'
    candidate = None
    for iteration in range(rounds):
        if time.monotonic()-start >= seconds:
            status = 'time_limit'
            break
        rows = sorted(forms)
        active = [row for row in rows if any(row[1+i] for i in free)]
        for row in rows:
            if not any(row[1+i] for i in free):
                assert row[0] >= 0
        raw = np.array(active, dtype=float)
        a = raw[:, [1+i for i in free]]
        norms = np.maximum(np.max(abs(a), axis=1), 1)
        goal = np.zeros(len(free)+1)
        goal[-1] = -1
        solution = linprog(goal, A_ub=np.column_stack((-a/norms[:, None], np.ones(len(a)))),
                           b_ub=raw[:, 0]/norms,
                           bounds=[(0, None)]*len(free)+[(None, None)], method='highs',
                           options={'time_limit': max(1, seconds-(time.monotonic()-start))})
        if not solution.success:
            status = 'lp_requires_audit'
            result['lp_message'] = solution.message
            break
        x = np.zeros(len(cores)+1)
        x[0] = 1
        x[[1+i for i in free]] = solution.x[:-1]
        candidate = x
        ordinary_worst, ordinary_cuts = cuts(ordinary, inj, x)
        induced_worst, induced_cuts = cuts(induced_blocks, rated, x)
        fresh = {row for _, row in ordinary_cuts+induced_cuts if row not in forms}
        record = {'round': iteration, 'normalized_linear_margin': float(solution.x[-1]),
                  'ordinary_minimum_scaled_eigenvalue': float(ordinary_worst),
                  'induced_minimum_scaled_eigenvalue': float(induced_worst),
                  'new_exact_cuts': len(fresh), 'seconds': time.monotonic()-start}
        result['rounds'].append(record)
        print(json.dumps(record), flush=True)
        if solution.x[-1] < -1e-6:
            status = 'linear_infeasibility_candidate_requires_exact_audit'
            break
        if not fresh:
            status = 'numerical_psd_candidate' if min(ordinary_worst, induced_worst) >= -1e-7 else 'separation_stalled'
            break
        forms |= fresh
        added |= fresh
    result['status'] = status
    result['new_exact_cut_count'] = len(added)
    result['new_exact_cuts'] = [list(row) for row in sorted(added)]
    result['core_values'] = candidate.tolist() if candidate is not None else None
    result['seconds'] = time.monotonic()-start
    if out:
        out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': status, 'rounds': len(result['rounds']),
                      'new_exact_cut_count': len(added), 'seconds': result['seconds']}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rounds', type=int, default=80)
    parser.add_argument('--seconds', type=float, default=90)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.rounds, args.seconds, args.output)
