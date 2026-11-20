"""Bounded catalogue of triangle-free subcubic cores with codegree at most2.

Uses the repository's existing exact extension checks and pynauty
isomorphism certificates. Every level through order7 is independently
compared with the complete NetworkX graph atlas.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import time

import networkx as nx
import pynauty

from subgraph_counts import extensions, nauty


def permitted(rows):
    if any(row.bit_count() > 3 for row in rows):
        return False
    return all((rows[i] & rows[j]).bit_count() <= (0 if rows[i] >> j & 1 else 2)
               for i,j in combinations(range(len(rows)), 2))


def atlas_certificates(order):
    certificates = set()
    for G in nx.graph_atlas_g():
        if len(G) != order:
            continue
        rows = tuple(sum(1 << j for j in G[i]) for i in range(order))
        if permitted(rows):
            certificates.add(pynauty.certificate(nauty(rows)))
    return certificates


def run(order=9, seconds=60, maximum_types=10000, output=None):
    start = time.monotonic()
    current = [()]
    levels = [{'order': 0, 'types': 1, 'atlas_verified': True}]
    complete = True
    for n in range(1,order+1):
        found = {}
        for rows in current:
            if time.monotonic()-start > seconds:
                complete = False
                break
            for mask,child in extensions(rows):
                if mask.bit_count() > 3 or not permitted(child):
                    continue
                certificate = pynauty.certificate(nauty(child))
                found.setdefault(certificate,child)
            if len(found) > maximum_types:
                complete = False
                break
        if not complete:
            break
        if n <= 7:
            assert set(found) == atlas_certificates(n)
        current = [found[key] for key in sorted(found)]
        row = {'order': n, 'types': len(current), 'atlas_verified': n <= 7,
               'seconds': time.monotonic()-start}
        levels.append(row)
        print(json.dumps(row),flush=True)
    result = {'requested_order': order, 'completed_order': levels[-1]['order'],
              'complete': complete, 'levels': levels,
              'graphs': [list(rows) for rows in current]}
    if output:
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--order',type=int,default=9)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--maximum-types',type=int,default=10000)
    parser.add_argument('--output')
    args=parser.parse_args()
    run(args.order,args.seconds,args.maximum_types,args.output)
