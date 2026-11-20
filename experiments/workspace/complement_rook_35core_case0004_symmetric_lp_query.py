"""One bounded symmetric case4 LP query with a separate exact ray gate.

Preparation first constructs and hashes the integer row stream, then
stores exact CSC arrays. A solver receives floating coefficients only
after these bindings pass. No follow-up query or SAT search is exposed.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from math import gcd, isfinite, lcm
from pathlib import Path
import resource
import struct
import time

import complement_rook_35core_case0004_symmetric_lp as sizing


ROOT, LOGS = sizing.ROOT, sizing.LOGS
SIZING_SOURCE_SHA = '458e6306ba9c1efe09d7ce9b13e26554c48b3fa1083bffbc0ef0f0ff2601af52'
SIZING = LOGS / 'complement-rook-35core-case0004-symmetric-lp-preparation.json.gz'
SIZING_SHA = '7172f8e1eea2944d768f54e3acb4e9ef9401b79c2757d309cb9fde6e05978189'
digest, canonical, portable = sizing.digest, sizing.canonical, sizing.portable
ARRAY_NAMES = ('data', 'indices', 'indptr', 'sense', 'rhs')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, record):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.replace(path)


def array_bindings(arrays):
    return {name: {'dtype': arrays[name].dtype.str, 'shape': list(arrays[name].shape),
                   'sha256': sha(arrays[name].tobytes(order='C'))} for name in ARRAY_NAMES}


def exact_arrays():
    import numpy as np
    from scipy import sparse
    assert digest(Path(sizing.__file__)) == SIZING_SOURCE_SHA and digest(SIZING) == SIZING_SHA
    expected = json.loads(gzip.decompress(SIZING.read_bytes()))
    original, row_model, cuts = sizing.load_inputs()
    n = len(row_model['column_masks35'])
    edges, incident = sizing.shared_edges(row_model['eligible_neighbor_column_ids'], n)
    assert sha(canonical(edges)) == expected['edge_domain_sha256']
    m = expected['counts']['physical_rows']
    total = expected['counts']['physical_matrix_nonzeros']
    nv = expected['total_LP_variables_without_explicit_slacks']
    assert (n, len(edges), m, total, nv) == (1214, 275578, 590165, 4121379, 276792)
    rr, cc = np.empty(total, dtype=np.int32), np.empty(total, dtype=np.int32)
    vv = np.empty(total, dtype=np.int64)
    sense, rhs = np.empty(m, dtype=np.uint8), np.empty(m, dtype=np.int64)
    stream, labels = hashlib.sha256(), hashlib.sha256()
    offset = 0
    for row, (kind, label, sign, bound, terms) in enumerate(sizing.row_stream(original, row_model, cuts, edges, incident)):
        assert row < m and sign in (0, 1) and type(bound) is int
        assert [b for b, w in terms] == sorted({b for b, w in terms})
        assert all(type(b) is int and 0 <= b < nv and type(w) is int and w != 0 for b, w in terms)
        values = [sign, bound, len(terms)]
        for b, w in terms:
            values.extend((b, w))
        assert all(-(1 << 63) <= v < 1 << 63 for v in values)
        stream.update(struct.pack('<' + 'q' * len(values), *values))
        labels.update(canonical([kind, label]) + b'\n')
        stop = offset + len(terms)
        assert stop <= total
        rr[offset:stop] = row
        cc[offset:stop] = [b for b, w in terms]
        vv[offset:stop] = [w for b, w in terms]
        sense[row], rhs[row] = sign, bound
        offset = stop
    assert row + 1 == m and offset == total
    assert stream.hexdigest() == expected['integer_row_stream_sha256']
    assert labels.hexdigest() == expected['row_label_stream_sha256']
    assert int(np.count_nonzero(sense)) == 552658
    assert int(np.max(np.abs(vv))) == 1217
    # No floating conversion has occurred before either exact stream hash.
    matrix = sparse.coo_matrix((vv, (rr, cc)), shape=(m, nv)).tocsc()
    assert matrix.nnz == total and matrix.has_canonical_format
    arrays = {'data': matrix.data.astype('<i8', copy=False),
              'indices': matrix.indices.astype('<i4', copy=False),
              'indptr': matrix.indptr.astype('<i4', copy=False),
              'sense': sense, 'rhs': rhs.astype('<i8', copy=False)}
    assert all(arrays[name].dtype.kind in 'iu' for name in ARRAY_NAMES)
    return arrays, expected


def check_ray(arrays, sparse_ray, seconds):
    """Check every physical variable coefficient and every virtual slack."""
    assert 0 < seconds <= 60
    start = time.monotonic()
    assert sparse_ray == sorted(sparse_ray)
    assert all(type(i) is int and type(v) is int and v != 0 for i, v in sparse_ray)
    ray = dict(sparse_ray)
    assert len(ray) == len(sparse_ray)
    m = len(arrays['rhs'])
    assert all(0 <= i < m for i in ray)
    rhs_dot = 0
    for k, (i, value) in enumerate(sparse_ray):
        if k % 1024 == 0 and time.monotonic() - start > seconds:
            raise TimeoutError('exact sparse-ray/bound check budget')
        if int(arrays['sense'][i]) == 1:
            assert value >= 0, ('negative upper-row slack coefficient', i)
        rhs_dot += value * int(arrays['rhs'][i])
    assert rhs_dot < 0, ('nonnegative right-hand product', rhs_dot)
    data, indices, pointers = arrays['data'], arrays['indices'], arrays['indptr']
    minimum = None
    strictly_positive = 0
    for column in range(len(pointers) - 1):
        if column % 1024 == 0 and time.monotonic() - start > seconds:
            raise TimeoutError('exact complete column check budget')
        value = 0
        for p in range(int(pointers[column]), int(pointers[column + 1])):
            value += int(data[p]) * ray.get(int(indices[p]), 0)
        assert value >= 0, ('negative physical variable coefficient', column, value)
        minimum = value if minimum is None else min(minimum, value)
        strictly_positive += value > 0
    return {'right_hand_side_dot_product': rhs_dot, 'minimum_physical_variable_coefficient': minimum,
            'physical_variable_columns_checked': len(pointers) - 1,
            'upper_row_slack_coefficients_checked': sum(int(s) == 1 for s in arrays['sense']),
            'nonzero_ray_support': len(ray), 'strictly_positive_variable_coefficients': strictly_positive,
            'orientation': 'physical_A^T r>=0, r_upper>=0 and rhs^T r<0; every variable lower bound is0'}


def controls():
    toy = {'data': [1, 1], 'indices': [0, 1], 'indptr': [0, 2], 'sense': [0, 1], 'rhs': [2, 1]}
    assert check_ray(toy, [[0, -1], [1, 1]], 1)['right_hand_side_dot_product'] == -1
    rejected = 0
    for ray in ([[0, 1], [1, -1]], [[0, -2], [1, 1]], [[0, 1], [1, 1]]):
        try:
            check_ray(toy, ray, 1)
        except AssertionError:
            rejected += 1
    assert rejected == 3
    return {'exact_Farkas_positive_control': True, 'bad_sign_or_column_controls_rejected': rejected,
            'optimizer_or_solver_called': False}


def prepare(model_path, matrix_path):
    import numpy as np
    assert not model_path.exists() and not matrix_path.exists()
    start = time.monotonic()
    arrays, expected = exact_arrays()
    bindings = array_bindings(arrays)
    np.savez_compressed(matrix_path, **arrays)
    model = {'status': 'one-query symmetric case4 driver prepared; no optimizer called',
             'source_sha256': digest(Path(__file__)), 'sizing_source_sha256': SIZING_SOURCE_SHA,
             'sizing_preparation_sha256': SIZING_SHA,
             'integer_row_stream_sha256': expected['integer_row_stream_sha256'],
             'row_label_stream_sha256': expected['row_label_stream_sha256'],
             'variables': 276792, 'rows': 590165, 'nonzeros': 4121379,
             'selector_variables': 1214, 'shared_edge_variables': 275578,
             'matrix_cache': str(matrix_path), 'matrix_cache_sha256': digest(matrix_path),
             'matrix_cache_bytes': matrix_path.stat().st_size, 'exact_array_bindings': bindings,
             'integer_hash_bound_before_float_conversion': True,
             'column_lower_bounds': 0, 'column_upper_bounds': 'infinite; finite upper bounds are explicit rows',
             'limits': {'queries': 1, 'threads': 1, 'solve_seconds': 60,
                        'ray_construction_seconds': 15, 'combined_exact_ray_check_seconds': 60,
                        'maximum_common_denominator_bits': 4096},
             'controls': controls(), 'initialization_seconds': time.monotonic() - start,
             'preparation_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'exact_feasibility_claimed': False, 'LP_or_SAT_query_called': False,
             'scope': 'Only indexed35-core case4; numerical feasibility remains unverified, '
                      'and an exclusion requires a complete exact Farkas check and cold replay.'}
    save(model_path, model)
    print(json.dumps(model, indent=2), flush=True)


def load_model(path, need_cache):
    import numpy as np
    model = json.loads(path.read_text())
    assert model['source_sha256'] == digest(Path(__file__))
    assert model['sizing_source_sha256'] == digest(Path(sizing.__file__)) == SIZING_SOURCE_SHA
    assert model['sizing_preparation_sha256'] == digest(SIZING) == SIZING_SHA
    arrays = None
    if need_cache:
        cache = Path(model['matrix_cache'])
        assert digest(cache) == model['matrix_cache_sha256']
        with np.load(cache, allow_pickle=False) as archive:
            assert set(archive.files) == set(ARRAY_NAMES)
            arrays = {name: archive[name] for name in ARRAY_NAMES}
        assert array_bindings(arrays) == model['exact_array_bindings']
        assert len(arrays['data']) == model['nonzeros'] and len(arrays['indptr']) == model['variables'] + 1
        assert len(arrays['rhs']) == model['rows'] and len(arrays['sense']) == model['rows']
    return model, arrays


def candidate_from_support(support, method, parameter, seconds):
    start = time.monotonic()
    largest = max(abs(value) for i, value in support)
    normalized = [(i, value / largest) for i, value in support]
    if method == 'scale':
        candidate = []
        for k, (i, value) in enumerate(normalized):
            if k % 256 == 0 and time.monotonic() - start > seconds:
                raise TimeoutError('ray integer construction budget')
            integer = round(parameter * value)
            if integer:
                candidate.append([i, integer])
    else:
        fractions, denominator = [], 1
        for k, (i, value) in enumerate(normalized):
            if k % 128 == 0 and time.monotonic() - start > seconds:
                raise TimeoutError('ray rational construction budget')
            rational = Fraction(value).limit_denominator(parameter)
            if not rational:
                continue
            denominator = lcm(denominator, rational.denominator)
            if denominator.bit_length() > 4096:
                raise OverflowError('bounded common denominator exceeded4096 bits')
            fractions.append((i, rational))
        candidate = [[i, int(value * denominator)] for i, value in fractions]
    common = gcd(*(abs(v) for i, v in candidate))
    return [[i, v // common] for i, v in candidate] if common else []


def reconstruct_ray(arrays, numerical):
    assert all(isfinite(float(v)) for v in numerical)
    support = [(i, float(v)) for i, v in enumerate(numerical) if v != 0]
    report = {'numerical_nonzero_support': len(support), 'attempts': [],
              'construction_seconds': 0.0, 'exact_check_seconds': 0.0,
              'exact_certificate_found': False}
    if not support:
        return report
    methods = [('scale', n) for n in (1, 2, 4, 8, 16, 64, 256, 4096, 65536)]
    methods += [('denominator', n) for n in (1, 2, 4, 16, 64, 256, 4096, 1000000)]
    seen = set()
    for method, parameter in methods:
        available = 15 - report['construction_seconds']
        if available <= 0 or report['exact_check_seconds'] >= 60:
            break
        start = time.monotonic()
        attempt = {'method': method, 'parameter': parameter}
        try:
            candidate = candidate_from_support(support, method, parameter, available)
        except (TimeoutError, OverflowError) as error:
            attempt['construction_status'] = str(error)
            candidate = []
        finally:
            report['construction_seconds'] += time.monotonic() - start
        report['attempts'].append(attempt)
        if not candidate:
            continue
        key = sha(canonical(candidate))
        if key in seen:
            attempt['duplicate_candidate'] = True
            continue
        seen.add(key)
        attempt['integer_nonzero_support'] = len(candidate)
        attempt['maximum_integer_bits'] = max(abs(v).bit_length() for i, v in candidate)
        for sign in (1, -1):
            available = 60 - report['exact_check_seconds']
            if available <= 0:
                break
            proposed = [[i, sign * v] for i, v in candidate]
            start = time.monotonic()
            try:
                check = check_ray(arrays, proposed, available)
            except (AssertionError, TimeoutError) as error:
                attempt[f'orientation_{sign}_rejection'] = str(error)
            else:
                report.update(exact_certificate_found=True, sparse_integer_ray=proposed, exact_check=check)
                return report
            finally:
                report['exact_check_seconds'] += time.monotonic() - start
    return report


def save_float_array(path, values):
    import numpy as np
    array = np.asarray(values, dtype='<f8')
    raw = array.tobytes(order='C')
    path.write_bytes(gzip.compress(raw, mtime=0))
    return {'path': portable(path), 'sha256': digest(path), 'raw_sha256': sha(raw),
            'dtype': '<f8', 'shape': list(array.shape)}


def solve(model_path, directory, seconds):
    import highspy
    import numpy as np
    from scipy import sparse
    assert not directory.exists() and 0 < seconds <= 60
    directory.mkdir(parents=True)
    started = time.monotonic()
    result = {'status': 'initializing one bounded symmetric case4 LP',
              'source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path),
              'requested_solve_seconds': seconds, 'queries': 1, 'threads': 1,
              'exact_feasibility_claimed': False, 'exact_case4_exclusion_claimed': False,
              'whole_local_set_or_graph_excluded': False, 'SAT_queries': 0}
    output = directory / 'result.json'
    save(output, result)
    try:
        model, arrays = load_model(model_path, True)
        assert int(np.max(np.abs(arrays['data']))) == 1217
        matrix = sparse.csc_matrix((arrays['data'], arrays['indices'], arrays['indptr']), shape=(model['rows'], model['variables']))
        lp = highspy.HighsLp()
        lp.num_col_, lp.num_row_ = model['variables'], model['rows']
        lp.col_cost_, lp.col_lower_ = np.zeros(model['variables']), np.zeros(model['variables'])
        lp.col_upper_ = np.full(model['variables'], highspy.kHighsInf)
        lp.row_upper_ = arrays['rhs'].astype(float)
        lp.row_lower_ = np.where(arrays['sense'] == 0, arrays['rhs'], -highspy.kHighsInf).astype(float)
        lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = arrays['indptr'], arrays['indices'], arrays['data'].astype(float)
        solver = highspy.Highs()
        for name, value in [('output_flag', False), ('threads', 1), ('presolve', 'on'), ('time_limit', seconds)]:
            assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
        assert solver.passModel(lp) == highspy.HighsStatus.kOk
        result['initialization_seconds'] = time.monotonic() - started
        result['initialization_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['status'] = 'running the single bounded symmetric case4 LP'
        save(output, result)
        solve_start = time.monotonic()
        solver.run()
        result['solve_seconds'] = time.monotonic() - solve_start
        status = solver.getModelStatus()
        result['numerical_status'] = str(status)
        if status == highspy.HighsModelStatus.kOptimal:
            values = np.asarray(solver.getSolution().col_value, dtype=float)
            assert len(values) == model['variables'] and np.all(np.isfinite(values))
            result['numerical_primary_values'] = save_float_array(directory / 'numerical-primary-f64le.bin.gz', values)
            residual = matrix @ values - arrays['rhs']
            result['maximum_equality_residual'] = float(np.max(np.abs(residual[arrays['sense'] == 0])))
            result['maximum_upper_row_violation'] = max(0.0, float(np.max(residual[arrays['sense'] == 1])))
            result['maximum_lower_bound_violation'] = max(0.0, -float(np.min(values)))
            result['status'] = 'numerical optimum only; no exact feasibility or graph completion claim'
        elif status == highspy.HighsModelStatus.kInfeasible:
            result['status'] = 'numerical infeasibility; exact ray not yet verified'
            save(output, result)
            extraction_start = time.monotonic()
            _, exists, values = solver.getDualRay()
            result['numerical_ray_extraction_seconds'] = time.monotonic() - extraction_start
            if exists:
                assert len(values) == model['rows']
                result['numerical_ray'] = save_float_array(directory / 'numerical-ray-f64le.bin.gz', values)
                reconstructed = reconstruct_ray(arrays, values)
                if reconstructed['exact_certificate_found']:
                    ray = reconstructed.pop('sparse_integer_ray')
                    certificate = {'sparse_integer_ray': ray, 'check': reconstructed['exact_check'],
                                   'source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path)}
                    path = directory / 'integer-farkas-certificate.json.gz'
                    path.write_bytes(gzip.compress(canonical(certificate) + b'\n', mtime=0))
                    result.update(status='exact integer case4 Farkas certificate checked; cold replay required',
                                  exact_case4_exclusion_claimed=True,
                                  integer_certificate={'path': portable(path), 'sha256': digest(path)})
                else:
                    result['status'] = 'numerical infeasibility only; no exact certificate, case4 unresolved'
                result['ray_reconstruction'] = reconstructed
            else:
                result['status'] = 'numerical infeasibility without ray; case4 unresolved'
        else:
            result['status'] = 'LP limit or other numerical status; case4 unresolved'
    except Exception as error:
        result.update(status='error; no unchecked conclusion promoted', error_type=type(error).__name__,
                      error_message=str(error), exact_case4_exclusion_claimed=False)
        raise
    finally:
        result['elapsed_seconds'] = time.monotonic() - started
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output, result)
    print(json.dumps(result, indent=2), flush=True)


def replay(model_path, result_path, output, seconds):
    assert not output.exists() and 0 < seconds <= 60
    model, _ = load_model(model_path, False)
    arrays, expected = exact_arrays()
    assert array_bindings(arrays) == model['exact_array_bindings']
    assert expected['integer_row_stream_sha256'] == model['integer_row_stream_sha256']
    report = {'status': 'cold exact integer stream and full CSC array replay PASS',
              'source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path),
              'variables': model['variables'], 'rows': model['rows'], 'nonzeros': model['nonzeros'],
              'optimizer_or_solver_called': False, 'exact_feasibility_claimed': False,
              'exact_case4_exclusion_verified': False, 'whole_local_set_or_graph_excluded': False}
    if result_path:
        result = json.loads(result_path.read_text())
        assert result['source_sha256'] == digest(Path(__file__)) and result['model_sha256'] == digest(model_path)
        report['result_sha256'] = digest(result_path)
        for name in ('numerical_primary_values', 'numerical_ray'):
            if name in result:
                item = result[name]
                path = ROOT / item['path']
                assert digest(path) == item['sha256']
                raw = gzip.decompress(path.read_bytes())
                assert sha(raw) == item['raw_sha256'] and len(raw) == 8 * item['shape'][0]
        if result['exact_case4_exclusion_claimed']:
            item = result['integer_certificate']
            path = ROOT / item['path']
            assert digest(path) == item['sha256']
            certificate = json.loads(gzip.decompress(path.read_bytes()))
            assert certificate['source_sha256'] == digest(Path(__file__)) and certificate['model_sha256'] == digest(model_path)
            check = check_ray(arrays, certificate['sparse_integer_ray'], seconds)
            assert check == certificate['check']
            report.update(status='cold complete integer matrix and exact case4 Farkas replay PASS',
                          exact_case4_exclusion_verified=True, exact_Farkas_check=check)
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--matrix', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=60)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--check-seconds', type=float, default=60)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(), args.matrix.resolve())
    elif args.command == 'solve':
        solve(args.model.resolve(), args.directory.resolve(), args.seconds)
    else:
        replay(args.model.resolve(), args.result.resolve() if args.result else None, args.output.resolve(), args.check_seconds)
