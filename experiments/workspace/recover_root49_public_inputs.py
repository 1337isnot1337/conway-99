import gzip, hashlib, io, json, pickle, urllib.request
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.sparse import csr_matrix

BASE = "https://raw.githubusercontent.com/1337isnot1337/conway-99/a20ec755c7364c4b7a6e40317e5a7a745224679d/experiments/logs/moments-and-counts/"
FILES = {
 "order10-high-mask-packing-other-roots-scope01-arrays.npz": "4af4af187681c33af2ce0d64fc1e7c3e7afb30e37eec181c741776883d602533",
 "prism-zero-order10-r6s2-blocks.pickle.gz": "84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c"
}
TARGET = Path(__file__).resolve().parent
bindings = {}
raws = {}
for name, expected in FILES.items():
    raw = urllib.request.urlopen(BASE + name, timeout=25).read()
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == expected, (name, actual)
    (TARGET / name).write_bytes(raw)
    raws[name] = raw
    bindings[name] = {"sha256": actual, "bytes": len(raw)}

arrays = {}
with np.load(io.BytesIO(raws["order10-high-mask-packing-other-roots-scope01-arrays.npz"]), allow_pickle=False) as saved:
    for name in saved.files:
        if name.startswith("r49_"):
            value = saved[name]
            assert not value.dtype.hasobject
            arrays[name] = {"dtype": str(value.dtype), "shape": list(value.shape), "data": value.tolist()}
assert arrays

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
        key = (module, name)
        if key not in allowed:
            raise ValueError("unapproved pickle global: " + repr(key))
        return allowed[key]

payload = RestrictedUnpickler(io.BytesIO(gzip.decompress(raws["prism-zero-order10-r6s2-blocks.pickle.gz"]))).load()
assert isinstance(payload, dict) and "blocks" in payload
matches = [row for row in payload["blocks"] if row[0] == 49]
assert len(matches) == 1
root, flags, tensor = matches[0]
assert isinstance(tensor, csr_matrix) and not tensor.dtype.hasobject and tensor.shape[1] == 48965
result = {
    "status": "public root49 input extraction only; no mathematical query or solver",
    "source_commit": "a20ec755c7364c4b7a6e40317e5a7a745224679d",
    "input_bindings": bindings,
    "root_type": int(root),
    "scope_arrays": arrays,
    "flags": flags,
    "tensor": {"shape": list(tensor.shape), "dtype": str(tensor.dtype),
       "data": tensor.data.tolist(), "indices": tensor.indices.tolist(), "indptr": tensor.indptr.tolist()},
    "pickle_global_policy": "only numeric ndarray/CSR constructors and basic containers",
    "optimizer_called": False
}
def scalar(value):
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, np.ndarray):
        assert not value.dtype.hasobject
        return value.tolist()
    if isinstance(value, (set, frozenset)): return sorted(value)
    raise TypeError(type(value).__name__)
output = json.dumps(result, default=scalar, separators=(",", ":"))
path = TARGET / "root49-public-inputs.json"
path.write_text(output + "\n")
if len(output) < 450000:
    print(output)
else:
    print(json.dumps({"output_path": str(path), "bytes": path.stat().st_size,
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))
