"""Bounded exact spectral/cubic pass on the complete nine-type2 core list."""

import argparse
import json
from pathlib import Path
import time

from seven_red_core_catalog import permitted
from seven_red_residual_spectra import factor_information, matrix, spectra


def run(catalogue, seconds=50, start=0, count=None, output=None):
    source = json.loads(Path(catalogue).read_text())
    assert source['complete'] and source['completed_order'] == 9
    graphs = source['graphs']
    assert len(graphs) == 408
    stop = len(graphs) if count is None else min(len(graphs),start+count)
    begin = time.monotonic()
    records = []
    for case in range(start,stop):
        if time.monotonic()-begin > seconds:
            break
        rows = graphs[case]
        assert len(rows) == 9 and permitted(rows)
        edges = [(a,b) for a in range(9) for b in range(a+1,9) if rows[a] >> b & 1]
        information = factor_information(matrix(9,edges),use_krylov=False)
        survivors = spectra(9,information,True)
        record = {'case': case, 'edges': [list(edge) for edge in edges],
                  'factor_information': information, 'surviving_spectra': survivors}
        records.append(record)
        if survivors or len(records) % 25 == 0:
            print(json.dumps({'case': case, 'processed': len(records),
                              'surviving_spectra': len(survivors),
                              'seconds': time.monotonic()-begin}),flush=True)
    summary = {'complete_catalogue': True, 'catalogue_cores': len(graphs),
               'krylov_filter_used': False,
               'start': start, 'requested_stop': stop, 'processed': len(records),
               'complete_requested_range': len(records) == stop-start,
               'surviving_cores': sum(bool(row['surviving_spectra']) for row in records),
               'surviving_spectra': sum(len(row['surviving_spectra']) for row in records),
               'seconds': time.monotonic()-begin}
    print(json.dumps({'summary': summary}),flush=True)
    result = {**summary,'cores': records}
    if output:
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--catalogue',default='experiments/logs/grids-and-triangles/seven-red-type2-core-catalog.json')
    parser.add_argument('--seconds',type=int,default=50)
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--count',type=int)
    parser.add_argument('--output')
    args=parser.parse_args()
    run(args.catalogue,args.seconds,args.start,args.count,args.output)
