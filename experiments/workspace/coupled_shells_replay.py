"""Replay the entire high/low template census without doing a new SAT search."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from coupled_shells import four_high_obstruction
from coupled_shells_certificate import verify as verify_certificate
from coupled_shells_filter import row_domains
from coupled_shells_low import verify as verify_partial
from coupled_shells_zero import zero_domains


def main():
    p = argparse.ArgumentParser()
    p.add_argument('orbits', type=Path); p.add_argument('results', type=Path)
    p.add_argument('--proof-directory', type=Path, default=Path(__file__).parent)
    p.add_argument('--drat-trim', type=Path, required=True)
    a = p.parse_args()
    blocks = {d['core']: d for d in json.loads(a.orbits.read_text())}
    data = json.loads(a.results.read_text())
    expected = {(c, i) for c, d in blocks.items() for i in range(len(d['orbits']))}
    keys = [(r['core'], r['orbit']) for r in data]
    assert len(keys) == len(set(keys)) and set(keys) == expected
    counts = Counter()
    labeled = Counter()
    for r in data:
        block = blocks[r['core']]; orbit = block['orbits'][r['orbit']]
        if r['status'] == 'counting_obstruction':
            assert four_high_obstruction(orbit['high']) is not None
        elif r['status'] == 'sat':
            hd, cc = row_domains(block['rows'], orbit['high'], orbit['single'])
            zd = set(zero_domains(orbit['high'], orbit['single']))
            verify_partial(block['rows'], orbit, r['edges'], r['low_edges'], hd, zd, cc)
        elif r['status'] == 'unsat':
            manifest = a.proof_directory / f"coupled-shells-low-{r['core']}-{r['orbit']}-certificate.json"
            cert = json.loads(manifest.read_text())
            assert cert['rows'] == block['rows']
            assert cert['template']['high'] == orbit['high'] and cert['template']['single'] == orbit['single']
            verify_certificate(manifest.resolve(), a.drat_trim.resolve())
        else:
            raise AssertionError(f"unresolved census entry {r['core']}, {r['orbit']}: {r['status']}")
        counts[r['status']] += 1
        weight = orbit['labeled_templates']
        assert isinstance(weight, int) and weight > 0
        labeled[r['status']] += weight
    print(f"all {len(data)} template classes replayed: {dict(counts)}", flush=True)
    assert sum(labeled.values()) == 4985
    print(f"labeled template counts: {dict(labeled)}", flush=True)
    print('SAT entries certify only the represented partial adjacency and incidence constraints.', flush=True)


if __name__ == '__main__': main()
