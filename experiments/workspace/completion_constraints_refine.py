"""Propagate required exterior-neighbor support back into incidence packing.

Every added clause is conditional on the source signature being present.
No sampled incidence failure excludes other incidence assignments.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from threading import Timer
import time

import numpy as np
from pysat.card import CardEnc, EncType

from broken_grid import canonical_cases
from completion_constraints_packing import packing, signatures
from completion_constraints_propagation import prepare, possible_neighbors, replay
from completion_constraints_spectral import pair_exclusions


def refine(case, seconds, propagation_file=None, use_pair_cuts=False, seed_witness=None):
    B = list(canonical_cases())[case][2]
    domains = signatures(B)
    N, Q = prepare(B, domains)
    need = 2 - Q
    live = np.ones(len(domains), dtype=bool)
    forbidden = []
    if propagation_file:
        record = next(r for r in json.loads(propagation_file.read_text()) if r['case'] == case)
        replay(record)
        forbidden = [c['source'] for c in record['certificates']]
        live[forbidden] = False
    pair_cuts = pair_exclusions(B, domains) if use_pair_cuts else []
    print(json.dumps({'case': case, 'signatures': len(domains), 'excluded_signatures': len(forbidden), 'exact_pair_cuts': len(pair_cuts)}), flush=True)

    def search(solver, copies, by_domain):
        for source in forbidden:
            solver.add_clause([-by_domain[source][0]])
        start = time.monotonic()
        timer = Timer(seconds, solver.interrupt)
        timer.start()
        rounds = 0
        cuts = set()
        last = None
        first_assumptions = []
        if seed_witness:
            seed_record = json.loads(seed_witness.read_text())
            seed_count = seed_record.get('native_packing', seed_record)['witness']
            for domain, literals in by_domain.items():
                multiplicity = int(seed_count.get(str(domain), 0))
                first_assumptions.extend(lit if j < multiplicity else -lit for j, lit in enumerate(literals))
        try:
            while True:
                seeded = bool(first_assumptions)
                status = solver.solve_limited(assumptions=first_assumptions, expect_interrupt=True)
                first_assumptions = []
                if seeded and status is False:
                    raise AssertionError('stored incidence witness fails the stated model; no graph exclusion follows')
                if status is None or status is False:
                    return {'case': case, 'status': 'unknown' if status is None else 'solver reported unsat',
                            'rounds': rounds, 'conditional_neighbor_cuts': len(cuts), 'seconds': round(time.monotonic() - start, 3),
                            'neighbor_cut_sources': [list(x) for x in sorted(cuts)],
                            'last_incidence_witness': last}
                on = {x for x in solver.get_model() if 0 < x <= len(copies)}
                count = Counter(copies[x - 1] for x in on)
                cols = [domains[i] for i, multiplicity in count.items() for _ in range(multiplicity)]
                incidence = np.array([[int(i in S) for S in cols] for i in range(len(B))], dtype=int)
                assert incidence.shape == (27, 72)
                assert np.array_equal(incidence @ incidence.T, 12 * np.eye(27, dtype=int) + 2 - B - B @ B)
                intersections = incidence.T @ incidence
                np.fill_diagonal(intersections, 0)
                assert np.max(intersections) <= 2
                last = {str(i): int(x) for i, x in count.items()}
                rounds += 1
                selected = np.zeros(len(domains), dtype=bool)
                selected[list(count)] = True
                added = 0
                for source in count:
                    possible = possible_neighbors(N, Q, source, live)
                    current = possible & selected
                    available = N[current].sum(axis=0)
                    bad = list(map(int, np.flatnonzero(available < need[source])))
                    if current.sum() < 14 - len(domains[source]):
                        bad.append(-1)
                    for coordinate in bad:
                        key = source, coordinate
                        assert key not in cuts
                        cuts.add(key)
                        if coordinate < 0:
                            choices = np.flatnonzero(possible)
                            required = 14 - len(domains[source])
                        else:
                            choices = np.flatnonzero(possible & N[:, coordinate].astype(bool))
                            required = int(need[source, coordinate])
                        support = [by_domain[int(i)][0] for i in choices]
                        source_lit = by_domain[source][0]
                        if required == 1:
                            solver.add_clause([-source_lit, *support])
                        elif required > len(support):
                            solver.add_clause([-source_lit])
                        else:
                            encoded = CardEnc.atleast(support, bound=required, top_id=solver.nof_vars(), encoding=EncType.kmtotalizer)
                            for clause in encoded.clauses:
                                solver.add_clause([-source_lit, *clause])
                        added += 1
                print(json.dumps({'case': case, 'round': rounds, 'new_neighbor_cuts': added, 'total_neighbor_cuts': len(cuts),
                                  'seconds': round(time.monotonic() - start, 3)}), flush=True)
                if not added:
                    return {'case': case, 'status': 'integer incidence with neighbor supports feasible',
                            'rounds': rounds, 'conditional_neighbor_cuts': len(cuts), 'seconds': round(time.monotonic() - start, 3),
                            'neighbor_cut_sources': [list(x) for x in sorted(cuts)],
                            'witness': last}
        finally:
            timer.cancel()

    return packing(B, domains, seconds=seconds, exclusions=pair_cuts, refinement=search)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', type=int, default=5)
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--propagation-certificate', type=Path)
    p.add_argument('--pair-cuts', action='store_true')
    p.add_argument('--seed-witness', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = refine(a.case, a.seconds, a.propagation_certificate, a.pair_cuts, a.seed_witness)
    if a.out:
        a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if 'witness' not in k}), flush=True)
