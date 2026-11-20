"""Deterministic lossless bundle for the frozen lazy-loop transcript.

Only the 253 hash-bound JSON or gzipped JSON records are bundled. The large final CNF is
rebuildable and is not bundled. Restore refuses to overwrite any unequal
existing file and cannot write outside the one fixed transcript prefix.
"""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
PREFIX = 'experiments/logs/root-prism-free/f0-bounded-lazy-continuation-run01'
RESULT = ROOT/PREFIX/'result.json'
RESULT_SHA = '88c4858aa36aaf3af15f4b53ce41be5c1fee3d8f2c237a49e2df026f1228bd86'
LOOP_SHA = '361484188521fc5c741be4aa8a7e1a10a9b4e76116ae51d8d9e76b272bc78dd2'
PREPARATION = LOGS/'f0-bounded-lazy-continuation-preparation.json.gz'
PREPARATION_SHA = 'a6a5e69927400cca6f469141d44b2ee6f8e2500ac680d9ddf82d13aa2538f91b'
ARCHIVE = LOGS/'f0-bounded-lazy-continuation-run01-transcript.tar.gz'
MANIFEST = LOGS/'f0-bounded-lazy-continuation-run01-transcript-bundle.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def allowed(name):
    path = Path(name)
    return (not path.is_absolute() and '..' not in path.parts and
            str(path).startswith(PREFIX+'/') and
            (path.name.endswith('.json') or path.name.endswith('.json.gz')))


def records_from_result():
    assert sha(RESULT.read_bytes()) == RESULT_SHA
    result = read(RESULT)
    records = {str(RESULT.relative_to(ROOT)): RESULT_SHA}
    for key in ('individual-registry', 'symmetric-registry', 'explanation-registry'):
        records[result[key]] = result[key+'_sha256']
    for step in result['iterations']:
        for key in ('candidate', 'individual_rows', 'shared_rows', 'symmetric_lift', 'explanation_batch'):
            if key in step:
                records[step[key]] = step[key+'_sha256']
    phase_records = 0
    for step in result['iterations']:
        if 'shared_rows' not in step:
            continue
        wrapper_path = ROOT/step['shared_rows']
        assert sha(wrapper_path.read_bytes()) == step['shared_rows_sha256']
        wrapper = read(wrapper_path)
        for key in ('original_feasibility', 'bounded_potential'):
            if key in wrapper:
                path = ROOT/wrapper[key+'_path']
                assert sha(path.read_bytes()) == wrapper[key+'_sha256']
                assert read(path) == wrapper[key]
                records[wrapper[key+'_path']] = wrapper[key+'_sha256']
                phase_records += 1
    assert phase_records == 9
    assert len(records) == 253
    inventory = []
    for name, expected in sorted(records.items()):
        assert allowed(name)
        data = (ROOT/name).read_bytes()
        assert sha(data) == expected
        json.loads(gzip.decompress(data) if name.endswith('.gz') else data)
        inventory.append({'path': name, 'sha256': expected, 'bytes': len(data)})
    return inventory, result


def build():
    assert not ARCHIVE.exists() and not MANIFEST.exists()
    inventory, result = records_from_result()
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for entry in inventory:
            data = (ROOT/entry['path']).read_bytes()
            info = tarfile.TarInfo(entry['path'])
            info.size = len(data)
            info.mode = 0o644
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ''
            archive.addfile(info, io.BytesIO(data))
    compressed = io.BytesIO()
    with gzip.GzipFile(filename='', fileobj=compressed, mode='wb', mtime=0, compresslevel=9) as stream:
        stream.write(raw.getvalue())
    ARCHIVE.write_bytes(compressed.getvalue())
    manifest = {'status': 'deterministic exact frozen transcript bundle; raw records unchanged',
        'source_sha256': sha(Path(__file__).read_bytes()),
        'loop_source_sha256': LOOP_SHA, 'preparation_sha256': PREPARATION_SHA,
        'result_sha256': RESULT_SHA, 'frozen_status': result['status'],
        'archive': str(ARCHIVE.relative_to(ROOT)), 'archive_sha256': sha(ARCHIVE.read_bytes()),
        'archive_bytes': ARCHIVE.stat().st_size, 'tar_sha256': sha(raw.getvalue()),
        'gzip_mtime': 0, 'tar_members_have_zero_owner_and_time': True,
        'records': inventory, 'record_count': len(inventory),
        'uncompressed_record_bytes': sum(entry['bytes'] for entry in inventory),
        'raw_JSON_records_committed': False, 'raw_JSON_records_preserved_locally': True,
        'raw_CNF_included': False, 'raw_CNF_sha256': result['final_cnf_sha256'],
        'no_solver_or_optimizer_called': True}
    MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
    return verify(False)


def restore_entries(entries, root):
    written = existing = 0
    for name, data in entries:
        assert allowed(name)
        target = root/name
        assert target.resolve().is_relative_to(root.resolve())
        assert target.resolve().is_relative_to((root/PREFIX).resolve())
        if target.exists():
            assert target.is_file() and target.read_bytes() == data
            existing += 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            written += 1
    return written, existing


def verify(restore):
    manifest = read(MANIFEST)
    assert manifest['source_sha256'] == sha(Path(__file__).read_bytes())
    assert manifest['loop_source_sha256'] == LOOP_SHA and manifest['preparation_sha256'] == PREPARATION_SHA
    assert manifest['result_sha256'] == RESULT_SHA and manifest['record_count'] == 253
    assert manifest['archive'] == str(ARCHIVE.relative_to(ROOT))
    blob = ARCHIVE.read_bytes()
    assert len(blob) == manifest['archive_bytes'] and sha(blob) == manifest['archive_sha256']
    uncompressed = gzip.decompress(blob)
    assert sha(uncompressed) == manifest['tar_sha256']
    entries = []
    with tarfile.open(fileobj=io.BytesIO(uncompressed), mode='r:') as archive:
        members = archive.getmembers()
        assert [m.name for m in members] == [r['path'] for r in manifest['records']]
        for member, record in zip(members, manifest['records']):
            assert member.isfile() and allowed(member.name)
            assert member.uid == member.gid == member.mtime == 0 and member.mode == 0o644
            data = archive.extractfile(member).read()
            assert len(data) == record['bytes'] == member.size and sha(data) == record['sha256']
            json.loads(gzip.decompress(data) if member.name.endswith('.gz') else data)
            entries.append((member.name, data))
    assert sum(len(data) for _, data in entries) == manifest['uncompressed_record_bytes']
    assert sha(dict(entries)[PREFIX+'/result.json']) == RESULT_SHA
    # Exercise missing-file restoration, exact reuse, and mismatch refusal
    # inside a disposable directory, never by deleting a frozen record.
    with tempfile.TemporaryDirectory(prefix='conway-lazy-bundle-control-') as directory:
        temporary = Path(directory)
        sample = [(PREFIX+'/control.json', b'{"control":1}\n')]
        assert restore_entries(sample, temporary) == (1, 0)
        assert restore_entries(sample, temporary) == (0, 1)
        try:
            restore_entries([(sample[0][0], b'changed')], temporary)
        except AssertionError:
            pass
        else:
            raise AssertionError('unequal existing file was overwritten')
    written, existing = restore_entries(entries, ROOT) if restore else (0, 0)
    return {'status': 'all253 exact transcript records and narrow restore controls PASS',
        'source_sha256': sha(Path(__file__).read_bytes()),
        'manifest_sha256': sha(MANIFEST.read_bytes()), 'archive_sha256': sha(blob),
        'archive_bytes': len(blob), 'uncompressed_record_bytes': manifest['uncompressed_record_bytes'],
        'record_count': len(entries), 'restoration_requested': restore,
        'missing_files_written': written, 'equal_existing_files_preserved': existing,
        'unequal_existing_files_never_overwritten': True,
        'frozen_result_status': manifest['frozen_status'], 'solver_or_optimizer_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'check', 'restore', 'cold-replay'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    if args.mode == 'build':
        report = build()
    else:
        report = verify(args.mode in ('restore', 'cold-replay'))
        if args.mode == 'cold-replay':
            import root_prism_free_f0_bounded_lazy_continuation as loop
            assert sha(Path(loop.__file__).read_bytes()) == LOOP_SHA
            assert sha(PREPARATION.read_bytes()) == PREPARATION_SHA
            _, _, _, cold = loop.reconstruct(PREPARATION, RESULT)
            report['complete_cold_mathematical_and_CNF_replay'] = cold
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
