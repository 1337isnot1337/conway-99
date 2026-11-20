"""Export the complete two surviving 27-core incidence domains.

The export does not select an incidence witness. Forced/rejected selectors
come only from the frozen exact propagation certificate.
"""

import argparse
import hashlib
import json
from pathlib import Path

import two_rook_tip_rook_boundary as boundary


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(certificate_path, hall_path):
    certificate = json.loads(certificate_path.read_text())
    assert boundary.verify(certificate, hall_path)['remaining_labelled_cases'] == 19
    cases = []
    for case in certificate['cases']:
        propagation = case['propagation']
        if not propagation['status'].startswith('survives'):
            continue
        code, domain = case['representative'], case['domain']
        adjacency, gram = boundary.core(code)
        signatures = domain['signatures']
        shifted = [[p, 9+q, 18+t] for p, q, t in signatures]
        mixed_need = [[2-(row & sum(1 << i for i in signature)).bit_count()
                       -int(vertex in signature) for vertex, row in enumerate(adjacency)]
                      for signature in shifted]
        assert all(min(row) >= 0 and sum(row) == 33 for row in mixed_need)
        cases.append({'representative': code, 'labelled_orbit_size': len(case['orbit']),
                      'core_rows': adjacency, 'core_gram': gram,
                      'signature_coordinates': signatures, 'core_signatures': shifted,
                      'mixed_need': mixed_need, 'outside_degree_if_selected': 11,
                      'selected_vertex_count': 72,
                      'pair_margin_equations': domain['equations'],
                      'forced_one_indices': propagation['forced_one_variables'],
                      'forced_zero_indices': propagation['forced_zero_variables'],
                      'unresolved_indices': propagation['unassigned_variables']})
    assert [(c['representative'], len(c['core_signatures'])) for c in cases] == [
        (3679836361, 188), (3943553752, 252)]
    return {'scope': 'complete Gram-compatible domains; no fixed incidence selection',
            'boundary_source_sha256': digest(Path(boundary.__file__)),
            'boundary_certificate_sha256': digest(certificate_path),
            'hall_certificate_sha256': digest(hall_path), 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boundary-certificate', type=Path, required=True)
    parser.add_argument('--hall', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    expected = generate(args.boundary_certificate, args.hall)
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2)+'\n')
    assert json.loads(args.output.read_text()) == expected
    print(json.dumps({'status': 'complete surviving domains exported and independently rebuilt',
                      'cases': [{'representative': c['representative'],
                                 'signatures': len(c['core_signatures']),
                                 'forced_one': len(c['forced_one_indices']),
                                 'forced_zero': len(c['forced_zero_indices'])}
                                for c in expected['cases']]}, indent=2))
