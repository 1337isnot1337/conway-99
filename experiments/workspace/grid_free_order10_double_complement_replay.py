"""Cold regeneration with JSON normalization of integer dictionary keys.

The original frozen constructor's embedded replay compared integer keys
with JSON string keys. This wrapper fixes only that comparison boundary.
It changes neither the constructor nor the saved domain certificate.
"""

import argparse
import gzip
import json
from pathlib import Path
import time

import grid_free_order10_double_complement_domains as domains


SOURCE_SHA = '1283b15c44f408e0baf2cb1f9abd1c59b4ebee8717ca099c39e52b55c56ea935'
CERTIFICATE_SHA = '166c66d9b990f5806ee5fcd729eb90a6e073a98a890a348f12450908f5235eac'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--certificate',type=Path,default=domains.ROOT/'experiments/logs/moments-and-counts/order10-double-complement-domains.json.gz')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert domains.files.digest(Path(domains.__file__)) == SOURCE_SHA
    assert domains.files.digest(args.certificate) == CERTIFICATE_SHA
    started = time.monotonic()
    saved = json.loads(gzip.decompress(args.certificate.read_bytes()))
    rebuilt = json.loads(json.dumps(domains.build(args.catalogue)))
    for value in (saved,rebuilt):
        value.pop('seconds')
        value.pop('peak_rss_kib')
    assert saved == rebuilt
    result = {'status':'complete cold double-complement domain and coefficient replay PASS',
              'replay_source_sha256':domains.files.digest(Path(__file__)),
              'constructor_source_sha256':SOURCE_SHA,'certificate_sha256':CERTIFICATE_SHA,
              'summary':saved['summary'],
              'integer_dictionary_keys_normalized_at_JSON_boundary':True,
              'original_constructor_and_certificate_unchanged':True,
              'count_point_or_optimizer_used':False,'seconds':time.monotonic()-started}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
