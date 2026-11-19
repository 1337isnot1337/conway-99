import base64, gzip, hashlib, io, json, pickle, sys, urllib.request
from collections import Counter
import numpy as np
from scipy.sparse import csr_matrix

COMMIT = "a20ec755c7364c4b7a6e40317e5a7a745224679d"
REQUEST_BLOB = "768bf542248d214b6e74412e35780233604d1986"
BASE = "https://raw.githubusercontent.com/1337isnot1337/conway-99/" + COMMIT + "/experiments/logs/moments-and-counts/"
FILES = {
 "order10-high-mask-packing-other-roots-scope01-arrays.npz": "4af4af187681c33af2ce0d64fc1e7c3e7afb30e37eec181c741776883d602533",
 "prism-zero-order10-r6s2-blocks.pickle.gz": "84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c"
}
def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "conway99-public-record-extraction"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()
blob = json.loads(get("https://api.github.com/repos/1337isnot1337/conway-99/git/blobs/" + REQUEST_BLOB))
assert blob["encoding"] == "base64"
request_raw = base64.b64decode(blob["content"])
assert hashlib.sha1(b"blob " + str(len(request_raw)).encode() + b"\0" + request_raw).hexdigest() == REQUEST_BLOB
request = json.loads(request_raw)
assert request["source_commit"] == COMMIT and len(request["roots"]) == 1
assert request["source_archives"]["arrays_sha256"] == FILES["order10-high-mask-packing-other-roots-scope01-arrays.npz"]
assert request["source_archives"]["tensor_sha256"] == FILES["prism-zero-order10-r6s2-blocks.pickle.gz"]
root_requests = {item["root_type"]: item for item in request["roots"]}
assert len(root_requests) == 1 and set(root_requests) == {42}
bindings, raws = {}, {}
for name, expected in FILES.items():
    raw = get(BASE + name)
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == expected, (name, actual)
    raws[name] = raw
    bindings[name] = {"sha256": actual, "bytes": len(raw)}

allowed = {
    ("collections", "Counter"): Counter,
    ("builtins", "set"): set,
    ("builtins", "frozenset"): frozenset,
    ("numpy", "dtype"): np.dtype,
    ("numpy", "ndarray"): np.ndarray,
    ("scipy.sparse._csr", "csr_matrix"): csr_matrix,
    ("scipy.sparse.csr", "csr_matrix"): csr_matrix
}
for prefix in ["numpy.core", "numpy._core"]:
    allowed[(prefix + ".multiarray", "_reconstruct")] = np.core.multiarray._reconstruct
    allowed[(prefix + ".multiarray", "scalar")] = np.core.multiarray.scalar
    allowed[(prefix + ".numeric", "_frombuffer")] = np.core.numeric._frombuffer
class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in allowed:
            raise ValueError("unapproved pickle global: " + repr((module, name)))
        return allowed[module, name]

payload = RestrictedUnpickler(io.BytesIO(gzip.decompress(raws["prism-zero-order10-r6s2-blocks.pickle.gz"]))).load()
assert isinstance(payload, dict) and "blocks" in payload
block_by_root = {}
for root, flags, tensor in payload["blocks"]:
    assert root not in block_by_root
    assert isinstance(tensor, csr_matrix) and not tensor.dtype.hasobject
    assert not tensor.data.dtype.hasobject and not tensor.indices.dtype.hasobject and not tensor.indptr.dtype.hasobject
    block_by_root[int(root)] = (flags, tensor)

records = []
with np.load(io.BytesIO(raws["order10-high-mask-packing-other-roots-scope01-arrays.npz"]), allow_pickle=False) as saved:
    for root, spec in root_requests.items():
        assert root in block_by_root
        flags, tensor = block_by_root[root]
        assert len(flags) == spec["expected_flag_count"]
        assert list(tensor.shape) == spec["expected_tensor_shape"]
        arrays = {}
        for suffix in request["array_suffixes"]:
            name = "r" + str(root) + "_" + suffix
            value = saved[name]
            assert not value.dtype.hasobject
            arrays[name] = {"dtype": str(value.dtype), "shape": list(value.shape), "data": value.tolist()}
        row_ids = spec["requested_tensor_rows"]
        assert all(type(row) is int and 0 <= row < tensor.shape[0] for row in row_ids)
        assert row_ids == sorted(set(row_ids))
        selected_rows = []
        for row in row_ids:
            start, end = int(tensor.indptr[row]), int(tensor.indptr[row + 1])
            selected_rows.append({"row": row, "indices": tensor.indices[start:end].tolist(), "data": tensor.data[start:end].tolist()})
        selected_flags = [{field: flag[field] for field in request["flags_fields"]} for flag in flags]
        records.append({"root_type": root, "scope_arrays": arrays, "flags": selected_flags,
                        "tensor": {"shape": list(tensor.shape), "dtype": str(tensor.dtype), "rows": selected_rows}})

result = {
    "status": "public selected input extraction only; no moment evaluation, census, or optimizer",
    "source_commit": COMMIT,
    "extraction_request_git_blob": REQUEST_BLOB,
    "input_bindings": bindings,
    "root_count": len(records), "roots": records,
    "pickle_global_policy": "same numeric ndarray/CSR and basic-container allowlist as root49; no object arrays",
    "count_point_loaded": False, "optimizer_called": False,
    "mathematical_reconstruction_performed": False
}
def scalar(value):
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, np.ndarray):
        assert not value.dtype.hasobject
        return value.tolist()
    if isinstance(value, (set, frozenset)): return sorted(value)
    raise TypeError(type(value).__name__)
output = json.dumps(result, default=scalar, separators=(",", ":")) + "\n"
encoded = output.encode("utf-8")
print(json.dumps({"projected_utf8_bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(), "output_limit": 450000}), file=sys.stderr)
if len(encoded) >= 450000:
    raise RuntimeError("Compact public extraction exceeds the predeclared stdout limit")
sys.stdout.write(output)
