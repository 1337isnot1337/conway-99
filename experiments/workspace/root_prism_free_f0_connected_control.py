"""Exact connected36-shell control with three central edge partitions33."""
import argparse
import hashlib
import json
from pathlib import Path

import root_prism_free_f0_components as components


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record():
    first = [i ^ 1 for i in range(12)]
    other = components.partner([(6*b+2*i+1, 6*b+(2*i+2) % 6)
                                for b in range(2) for i in range(3)], 12)
    q = [6*(1-i//6)+(i % 6+1) % 6 for i in range(12)]
    rows = components.core(first, other, other, q)
    types = [components.alternating(first, other), components.alternating(first, other),
             components.alternating(other, components.transported(other, q))]
    assert types == [[3,3]]*3
    assert [row.bit_count() for row in rows] == [14]*3+[4]*36
    assert components.component_sizes([row >> 3 for row in rows[3:]]) == [36]
    assert components.caps(rows) and components.prism_count(rows) == 0
    # A copy of F has two degree5 centers, so both would be central here.
    # For each central edge, copies are exactly its alternating size4 blocks.
    assert sum(parts.count(2) for parts in types) == 0
    return {'status': 'exact local control, not a99-vertex graph',
            'source_sha256': digest(Path(__file__)),
            'helper_source_sha256': digest(Path(components.__file__)),
            'first_matching': first, 'other_two_matchings': other, 'cross_permutation': q,
            'core_rows': [str(row) for row in rows], 'shell_components': [36],
            'three_central_edge_partitions': types, 'visible_caps_hold': True,
            'internal_prisms': 0, 'internal_F_motifs': 0,
            'consequence': 'Three central edge partitions33 do not locally force a split18+18 shell.',
            'full_graph_completion_claimed': False, 'optimizer_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    result = record()
    if args.replay:
        assert json.loads(args.certificate.read_text()) == result
        print(json.dumps({'status': 'PASS: connected all33 local control replay'}, indent=2))
    else:
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
