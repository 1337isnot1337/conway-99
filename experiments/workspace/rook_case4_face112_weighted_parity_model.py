"""Append two proved parity rows to the exact cached complete H3 matrix.

The inherited166011 rows are bound to their passed complete cold replay.
No original cover support is reconstructed. All cached array prefixes are
compared exactly, and both new original-coordinate Gram proofs are replayed.
The two suffix rows are equivalent to the70/50-term odd covers under the
inherited equations. No candidate, extra zero or optimizer is introduced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import numpy as np

import rook_case4_face112_h3_model_v2 as parent
import rook_case4_face112_weighted_parity_covers as covers

ROOT, BASE = parent.ROOT, parent.BASE
recovery, closure = parent.recovery, parent.closure
PARENT_SHA = "d06dfcadee54deeb81c244c9e11c80bd8687fdc682dcd01e274130fab1a0e2b7"
COVERS_SHA = "71062b0c84e637016a74b8d2df267e4e1e87893ca30221b6906f20ea7b4b844b"
INPUTS = {
    "bound_audit": parent.INPUTS["bound_audit"],
    "parent_model": (BASE+"rook-case4-face112-h3-model02/model.json", "1928eb76274865e219747f631fee2d7a327ed7acd3a845986844be13c9e34265"),
    "parent_arrays": (BASE+"rook-case4-face112-h3-model02/arrays.npz", "4e2de2786d3036cf995953791192500cb4aaa5b0c5079f3d97ea465a4cf64e46"),
    "parent_complete_cold": (BASE+"rook-case4-face112-h3-model02-cold-replay.json", "56864810924bacb6b331db728a4ce32810d8e6f2dfe7c196e0a73e0b2f583a97"),
    "weighted_covers": (BASE+"rook-case4-face112-weighted-parity-covers-certificate.json", "c0c06b09c0aa79fafc2901d2bfd2b82e4da0e666baf05f853f75ac27ed7b76ce"),
    "weighted_covers_cold": (BASE+"rook-case4-face112-weighted-parity-covers-replay.json", "4a3a74688ae8f51670ff59cdbfa07030ca17177c02877d6424962f9d5c8ee9ed"),
}
SELECTORS, PARENT_ROWS, ROWS = 1102, 166011, 166013
PARENT_NONZEROS, NONZEROS = 10767194, 10767292
NATIVE_ROWS, COVERS = 1960, 164044
SECONDS, RSS_KIB = 60, 1048576


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return recovery.canonical(value)


def source_bindings():
    assert digest(Path(parent.__file__).read_bytes()) == PARENT_SHA
    assert digest(Path(covers.__file__).read_bytes()) == COVERS_SHA
    old = parent.source_bindings()
    return dict(old, builder_sha256=digest(Path(__file__).read_bytes()),
                unchanged_H3_parent_builder_sha256=PARENT_SHA,
                direct_weighted_covers_verifier_sha256=COVERS_SHA)


def inputs(root):
    source_bindings()
    for name,(path,expected) in INPUTS.items():
        assert digest((root/path).read_bytes()) == expected,name
    saved,arrays = parent.load(root/INPUTS["parent_model"][0],root/INPUTS["parent_arrays"][0])
    cold = json.loads((root/INPUTS["parent_complete_cold"][0]).read_bytes())
    assert cold["status"].startswith("PASS:")
    assert cold["source_bindings"] == parent.source_bindings()
    assert cold["model_sha256"] == INPUTS["parent_model"][1]
    assert cold["arrays"]["sha256"] == INPUTS["parent_arrays"][1]
    assert cold["canonical_integer_stream_sha256"] == saved["canonical_integer_stream_sha256"]
    assert (cold["columns"],cold["rows"],cold["nonzeros"]) == (SELECTORS,PARENT_ROWS,PARENT_NONZEROS)
    assert cold["all_omission_witnesses_replayed"] and cold["all_row_column_transports_checked"]
    proof = covers.build(root)
    assert proof == json.loads((root/INPUTS["weighted_covers"][0]).read_bytes())
    replay = json.loads((root/INPUTS["weighted_covers_cold"][0]).read_bytes())
    assert replay["certificate_sha256"] == INPUTS["weighted_covers"][1]
    assert replay["all_original_coordinates_checked"] == 1214
    assert proof["current112_zero_columns"] == saved["fixed_zero_columns"]
    assert set(proof["prior99_zero_columns"]) <= set(saved["fixed_zero_columns"])
    return saved,arrays,proof


def integer_stream(arrays,stop):
    return parent.integer_stream(arrays,stop)


def append(old,base,proof):
    kept = list(map(int,base["original_column_ids"]))
    position = {a:j for j,a in enumerate(kept)}
    assert len(kept) == SELECTORS
    chosen = [cut["chosen_equivalent_append_row"] for cut in proof["cuts"]]
    assert len(chosen) == 2
    assert [r["representation"] for r in chosen] == ["rounded_capacity","odd_cover"]
    assert [len(r["terms"]) for r in chosen] == [48,50]
    assert [[r["lower"],r["upper"]] for r in chosen] == [[0,4],[1,17]]
    suffix_indices,suffix_coefficients,ends = [],[],[]
    for row in chosen:
        terms = [[position[a],c] for a,c in row["terms"]]
        assert terms == sorted(terms) and len({a for a,c in terms}) == len(terms)
        assert all(c == 1 for a,c in terms)
        suffix_indices.extend(a for a,c in terms)
        suffix_coefficients.extend(c for a,c in terms)
        ends.append(PARENT_NONZEROS+len(suffix_indices))
    assert len(suffix_indices) == 98 and ends[-1] == NONZEROS
    suffix = {
        "coefficients":np.asarray(suffix_coefficients,dtype="<i8"),
        "column_indices":np.asarray(suffix_indices,dtype="<i4"),
        "row_pointers":np.asarray(ends,dtype="<i8"),
        "row_lower":np.asarray([0,1],dtype="<i8"),
        "row_upper":np.asarray([4,17],dtype="<i8"),
        "row_origin_kind":np.asarray([5,5],dtype="u1"),
        "row_origin_index":np.asarray([0,1],dtype="<i4"),
        "current_row_to_previous":np.asarray([-1,-1],dtype="<i4"),
    }
    arrays = {name:(np.concatenate((value,suffix[name])) if name in suffix else value.copy())
              for name,value in base.items()}
    for name,value in base.items():
        assert arrays[name].dtype == value.dtype
        assert arrays[name][:len(value)].tobytes() == value.tobytes(),("parent prefix",name)
        if name not in suffix:
            assert arrays[name].tobytes() == value.tobytes()
    assert len(arrays["coefficients"]) == len(arrays["column_indices"]) == NONZEROS
    assert len(arrays["row_pointers"]) == ROWS+1 and arrays["row_pointers"][-1] == NONZEROS
    assert integer_stream(arrays,PARENT_ROWS) == old["canonical_integer_stream_sha256"]
    record = {k:v for k,v in old.items() if k not in ("arrays","controls","preparation_seconds","peak_rss_kib")}
    record.update({
        "status":"complete cached H3 selector LP plus two proved equivalent parity rows prepared; no optimizer",
        "source_bindings":source_bindings(),
        "inherited_H3_parent_input_bindings":old["parent_input_bindings"],
        "parent_input_bindings":{k:list(v) for k,v in INPUTS.items()},
        "rows":ROWS,"nonzeros":NONZEROS,
        "unchanged_parent_rows":PARENT_ROWS,"unchanged_parent_nonzeros":PARENT_NONZEROS,
        "unchanged_parent_stream_sha256":old["canonical_integer_stream_sha256"],
        "new_rows_without_previous_origin":old["new_rows_without_previous_origin"]+2,
        "weighted_parity_row_ids":[PARENT_ROWS,PARENT_ROWS+1],
        "weighted_parity_rows":chosen,
        "weighted_parity_cover_supports":[c["cover_support"] for c in proof["cuts"]],
        "weighted_parity_original_Gram_rows":[c["original_Gram_rows"] for c in proof["cuts"]],
        "weighted_parity_equivalent_under_inherited_Gram_equations":True,
        "new_zero_or_positive_selector_assumption":False,
        "new_rows_necessary_for_nonnegative_integer_incidences":True,
        "parent_real_feasible_set_preservation_claimed":False,
        "scope":"Every actual case4 incidence satisfies the cached complete H3 parent and both new odd covers. The48-term capacity is exactly equivalent to its70-term cover under original Gram equations. All prior rows and columns remain unchanged.",
        "row_inventory":dict(old["row_inventory"],retained_weighted_integer_parity_rows=2),
        "canonical_integer_stream_sha256":integer_stream(arrays,ROWS),
        "canonical_integer_stream_format":old["canonical_integer_stream_format"]+"; kind5 is a weighted-basis parity row",
        "inherited_array_prefix_lengths":{name:len(value) for name,value in base.items()},
        "inherited_array_prefix_sha256":old["array_sha256"],
        "array_sha256":{name:digest(value.tobytes()) for name,value in arrays.items()},
        "uncompressed_array_bytes":sum(value.nbytes for value in arrays.values()),
        "all_parent_array_prefixes_equal":True,
        "prior_complete_cold_replay_bound":INPUTS["parent_complete_cold"][1],
        "original_cover_supports_reconstructed":False,
    })
    return record,arrays


def build(root):
    # Exact cached-prefix replay, deliberately not parent.build(root).
    old,base,proof = inputs(root)
    return append(old,base,proof)


def load(model_path,arrays_path=None):
    model = json.loads(model_path.read_bytes())
    assert model["source_bindings"] == source_bindings()
    assert model["parent_input_bindings"] == {k:list(v) for k,v in INPUTS.items()}
    assert (model["columns"],model["rows"],model["nonzeros"]) == (SELECTORS,ROWS,NONZEROS)
    assert model["weighted_parity_row_ids"] == [PARENT_ROWS,PARENT_ROWS+1]
    assert model["prior_complete_cold_replay_bound"] == INPUTS["parent_complete_cold"][1]
    assert not model["original_cover_supports_reconstructed"]
    arrays_path = arrays_path or model_path.parent/model["arrays"]["path"]
    assert digest(arrays_path.read_bytes()) == model["arrays"]["sha256"]
    with np.load(arrays_path,allow_pickle=False) as archive:
        arrays = {name:archive[name] for name in archive.files}
    assert {name:digest(value.tobytes()) for name,value in arrays.items()} == model["array_sha256"]
    assert all(value.dtype.kind in "iu" for value in arrays.values())
    for name,size in model["inherited_array_prefix_lengths"].items():
        assert digest(arrays[name][:size].tobytes()) == model["inherited_array_prefix_sha256"][name]
    assert list(map(int,arrays["original_column_ids"])) == [a for a in range(1214) if a not in set(model["fixed_zero_columns"])]
    assert len(model["fixed_zero_columns"]) == 112 and not model["fixed_one_columns"]
    assert len(arrays["coefficients"]) == len(arrays["column_indices"]) == NONZEROS
    assert len(arrays["row_pointers"]) == ROWS+1 and arrays["row_pointers"][-1] == NONZEROS
    assert all(len(arrays[k]) == ROWS for k in ("row_lower","row_upper","row_origin_kind","row_origin_index","current_row_to_previous"))
    assert list(map(int,arrays["row_origin_kind"][-9:])) == [2,2,3,3,3,3,4,5,5]
    assert list(map(int,arrays["row_origin_index"][-2:])) == [0,1]
    assert list(map(int,arrays["row_pointers"][-3:])) == [PARENT_NONZEROS,PARENT_NONZEROS+48,NONZEROS]
    for k,row in enumerate(model["weighted_parity_rows"]):
        a,b = map(int,arrays["row_pointers"][PARENT_ROWS+k:PARENT_ROWS+k+2])
        terms = [[int(arrays["original_column_ids"][j]),int(c)]
                 for j,c in zip(arrays["column_indices"][a:b],arrays["coefficients"][a:b])]
        assert terms == row["terms"]
        assert [int(arrays["row_lower"][PARENT_ROWS+k]),int(arrays["row_upper"][PARENT_ROWS+k])] == [row["lower"],row["upper"]]
    assert list(map(int,arrays["current_row_to_previous"][-2:])) == [-1,-1]
    assert np.count_nonzero(arrays["current_row_to_previous"] < 0) == model["new_rows_without_previous_origin"] == 7
    return model,arrays


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("prepare","replay"))
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--directory",type=Path)
    p.add_argument("--model",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    started=time.monotonic()
    def expired(_signum,_frame):
        raise TimeoutError("bounded60second cached parity append preparation/replay")
    handler=signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        if args.mode == "prepare":
            assert args.directory is not None and not args.directory.exists()
            args.directory.mkdir(parents=True)
            model,arrays=build(args.root.resolve())
            path=args.directory/"arrays.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream,**arrays)
            model["arrays"]={"path":"arrays.npz","sha256":digest(path.read_bytes()),"bytes":path.stat().st_size}
            model["preparation_seconds"]=time.monotonic()-started
            model["peak_rss_kib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert model["peak_rss_kib"] <= RSS_KIB
            model_path=args.directory/"model.json"
            recovery.write_json(model_path,model)
            loaded,stored=load(model_path,path)
            for name,value in arrays.items():
                assert np.array_equal(value,stored[name])
            output=args.directory/"preparation.json"
        else:
            assert args.model is not None and args.output is not None and not args.output.exists()
            model_path=args.model
            model,stored=load(model_path)
            current,arrays=build(args.root.resolve())
            for key,value in current.items():
                if key not in ("numpy_version","python_version"):
                    assert model[key] == value,("cold parity field",key)
            for name,value in arrays.items():
                assert np.array_equal(value,stored[name]),("cold parity array",name)
            output=args.output
        report={"status":"PASS: cached complete H3 prefix and two exact Gram parity rows "+args.mode,
            "source_bindings":source_bindings(),"model_sha256":digest(model_path.read_bytes()),
            "columns":SELECTORS,"rows":ROWS,"nonzeros":NONZEROS,
            "unchanged_parent_rows":PARENT_ROWS,"appended_weighted_parity_rows":2,
            "appended_row_sizes":[48,50],"appended_ranges":[[0,4],[1,17]],
            "canonical_integer_stream_sha256":model["canonical_integer_stream_sha256"],
            "arrays":model["arrays"],"all_parent_array_prefixes_equal":True,
            "all_original_coordinate_cut_coefficients_checked":True,
            "prior_complete_cold_replay_bound":INPUTS["parent_complete_cold"][1],
            "all_omission_witnesses_replayed_in_this_run":False,
            "all_inherited_row_column_transport_arrays_preserved":True,
            "original_cover_supports_reconstructed":False,
            "optimizer_calls":0,"case4_excluded":False,
            "seconds":time.monotonic()-started,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        assert report["peak_rss_kib"] <= RSS_KIB
        recovery.write_json(output,report)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,handler)
    print(json.dumps(report,indent=2),flush=True)


if __name__ == "__main__":
    main()
