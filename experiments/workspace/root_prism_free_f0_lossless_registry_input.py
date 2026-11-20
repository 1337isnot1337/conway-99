"""Lossless integer-only JSON transfer for the recovered F0 selector registries.

This performs file parsing and serialization only. It does not normalize cuts,
rebuild a model, or call an optimizer. The V8 consumer independently checks
each original canonical hash and reconstructs the mathematical coefficients.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

TAG = "__f0_exact_json_integer__"
MAX_SAFE = (1 << 53) - 1
INPUTS = {
    "individual": ("individual-registry.json.gz", "6acd86b609230632c42b345ba0d1742ca3a3155cf216271f74508acaa71f1e41"),
    "shared": ("symmetric-registry.json.gz", "6ea36f93085ab07e641e5148fb9a297b9d9bdd9abd6ff36922fde5f112ccd71d"),
    "quadratic": ("quadratic-registry.json.gz", "29610083a8ce62eca87fb53e9cadbcdc5cca94cb8c24952a213cc19e876a8871"),
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def reject_numeric(value):
    raise ValueError("fractional, exponential or nonfinite JSON token refused: "+value)

def unique_object(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON object key")
        output[key] = value
    return output

def parse(raw):
    return json.loads(raw, parse_int=int, parse_float=reject_numeric,
                      parse_constant=reject_numeric, object_pairs_hook=unique_object)

def transfer(value, statistics):
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        statistics["integer_values"] += 1
        statistics["maximum_integer_bits"] = max(statistics["maximum_integer_bits"], abs(value).bit_length())
        if -MAX_SAFE <= value <= MAX_SAFE:
            return value
        statistics["tagged_large_integers"] += 1
        return {TAG: str(value)}
    if type(value) is list:
        return [transfer(item, statistics) for item in value]
    if type(value) is dict:
        if TAG in value:
            raise ValueError("reserved integer tag in original object")
        return {key: transfer(item, statistics) for key, item in value.items()}
    raise TypeError("non-integer JSON value type")

def statistics():
    return {"integer_values": 0, "tagged_large_integers": 0, "maximum_integer_bits": 0}

def controls():
    values = [
        [0, True, False, None, MAX_SAFE, -MAX_SAFE, MAX_SAFE+1, -MAX_SAFE-1],
        [-(1 << 200), (1 << 200)+3, "9007199254740992", "-123", "1e3", "1.5"],
        {"escaped": "quote\" backslash\\ tab\t newline\n slash/", "unicode": "\u007f\u2028\U0001f600",
         "numeric-looking": "-9007199254740993"},
        {"\uffff": 1, "\U0001f600": 2, "a": 3},
    ]
    fixtures=[]
    for value in values:
        count=statistics()
        wire=transfer(value,count)
        fixtures.append({"wire":wire,"expected_python_canonical":canonical(value).decode("ascii"),
                         "expected_python_canonical_sha256":sha(canonical(value)),"statistics":count})
    rejected=[]
    for raw in ("1.5","-0.5","1e3","1E-2","NaN","Infinity","-Infinity",'{"a":1,"a":2}'):
        try:
            parse(raw)
        except (ValueError,TypeError):
            rejected.append(raw)
        else:
            raise AssertionError("unwanted JSON token accepted")
    try:
        transfer({TAG:"7"},statistics())
    except ValueError:
        pass
    else:
        raise AssertionError("reserved tag collision accepted")
    for raw in ('"1e3"','"-0.5"','"9007199254740992"'):
        assert type(parse(raw)) is str
    assert parse("-0") == 0
    return {"status":"PASS: lossless integer transfer and lexical rejection controls",
            "fixtures":fixtures,"rejected_json_inputs":rejected,
            "reserved_tag_collision_rejected":True,
            "numeric_looking_strings_preserved":True,
            "negative_zero_canonicalized_as_integer_zero":True,
            "optimizer_called":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    base=args.root/"experiments/logs/root-prism-free/f0-allocated-lazy-continuation-run01"
    inputs={}
    for label,(name,expected) in INPUTS.items():
        raw=(base/name).read_bytes()
        assert sha(raw)==expected
        body=gzip.decompress(raw)
        original=parse(body)
        count=statistics()
        wire=transfer(original,count)
        inputs[label]={"path":"experiments/logs/root-prism-free/f0-allocated-lazy-continuation-run01/"+name,
                       "compressed_sha256":sha(raw),"compressed_bytes":len(raw),
                       "uncompressed_sha256":sha(body),"uncompressed_bytes":len(body),
                       "canonical_original_sha256":sha(canonical(original)),
                       "record_count":len(original),"statistics":count,"wire":wire}
    result={"schema":"f0-lossless-final-registry-input-v1",
            "source_sha256":sha(Path(__file__).read_bytes()),"integer_tag":TAG,
            "maximum_untagged_integer":MAX_SAFE,"inputs":inputs,"controls":controls(),
            "raw_registries_modified":False,"mathematical_normalization_performed":False,
            "optimizer_called":False}
    body=canonical(result)+b"\n"
    raw=gzip.compress(body,mtime=0) if args.output.suffix==".gz" else body
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(raw)
    report={"status":"PASS: lossless final registry serialization; no mathematical model/query",
            "source_sha256":result["source_sha256"],"output":str(args.output),
            "output_sha256":sha(raw),"output_bytes":len(raw),
            "canonical_sha256":sha(canonical(result)),
            "records":{label:entry["record_count"] for label,entry in inputs.items()},
            "integer_statistics":{label:entry["statistics"] for label,entry in inputs.items()},
            "optimizer_called":False}
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
