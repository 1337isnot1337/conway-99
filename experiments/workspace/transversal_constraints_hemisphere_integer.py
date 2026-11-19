"""Bounded Boolean signature selection for the H21 exterior relaxation."""

import argparse
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model

from transversal_constraints_hemisphere_incidence import build


def run(labeling_file, seconds=45, output=None):
    labeling = json.loads(Path(labeling_file).read_text())['result']['labels']
    start = time.monotonic()
    A, b, signatures, labels, row_labels, info = build(labeling)
    print(json.dumps({'build': info}), flush=True)
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f'x{c}') for c in range(A.shape[1])]
    for r in range(A.shape[0]):
        indices = A.indices[A.indptr[r]:A.indptr[r+1]]
        if b[r] == 1:
            model.add_exactly_one(variables[c] for c in indices)
        else:
            model.add(sum(variables[c] for c in indices) == int(b[r]))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 2
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = 1
    status = solver.solve(model)
    result = {'status': solver.status_name(status), 'seconds': time.monotonic()-start,
              'conflicts': solver.num_conflicts, 'branches': solver.num_branches}
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        selected = [int(solver.value(v)) for v in variables]
        assert all(A @ selected == b)
        result['selection'] = [{'label': list(labels[label]), 'mask': mask}
                               for c, (label, mask) in enumerate(signatures) if selected[c]]
    print(json.dumps(result), flush=True)
    if output:
        Path(output).write_text(json.dumps({'build': info, 'result': result}, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labeling', default='experiments/logs/independent-sets/transversal-hemisphere-minimal21-spectral.json')
    parser.add_argument('--seconds', type=int, default=45)
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.labeling, args.seconds, args.output)
