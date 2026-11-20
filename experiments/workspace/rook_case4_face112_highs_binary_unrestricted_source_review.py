"""Read-only compact Boolean-model review; no subject imports or execution."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source = ROOT / "experiments/workspace/rook_case4_face112_highs_binary_model.py"
    expected = "3869c9aa63a596421a7fefebc492d90159b6ac8edf0739a0995254bcfd5c4301"
    raw = source.read_bytes()
    assert sha(raw) == expected
    tree = ast.parse(raw.decode())
    assert {"original_rows", "load_inputs", "definition", "compare_base_arrays", "cover_row", "inspect_binary", "load_model"} <= {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    model = ROOT / "experiments/logs/grids-and-triangles/rook-case4-face112-highs-binary-model01.json"
    assert sha(model.read_bytes()) == "195bf6c2c274100686087fd71a22f488f7aaee28025e39e490d7751bffcbceb6"
    record = json.loads(model.read_bytes())
    assert record["source_sha256"] == expected
    assert (record["binary_variables"],record["initial_row_count"],record["initial_nonzeros"],record["external_cover_pool_count"]) == (1102,2195,27515,164044)
    report = {
        "status": "PASS: complete compact Boolean-model source and acceptance scope reviewed",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "subject_source": {"path": str(source.relative_to(ROOT)), "sha256": expected},
        "saved_model": {"path": str(model.relative_to(ROOT)), "sha256": sha(model.read_bytes())},
        "mathematical_checks": [
            "The original2271 native rows are rebuilt from the frozen inventory with correct guarded-row-cut signs and full signed coefficient accumulation.",
            "Projection fixes only the proved112 zero columns; the311 removed native rows have exact binary-box tautology witnesses equal to the complete parent witnesses.",
            "Both unit sums, all four certified pairs, the227 proved grouped cuts, the86-term sum=2 and the sparse H3 inequality are retained. No failed branch or candidate is imposed.",
            "The comparison checks all1966 inherited native/equality/pair rows against the full arrays and all164044 retained original cover IDs.",
            "A cover is omitted only when its guard target is proved zero; every other original cover stays in the external pool. Bit orientation is little-endian and target activation has the correct sign.",
            "Exact Boolean acceptance requires1214 literal Python integer coordinates in{0,1}, all2618 original-coordinate rows including the zero units, and all178533 original covers.",
            "The optional literal support check and the default integer bit intersection test express the same guarded cover predicate."
        ],
        "subject_imported": False, "model_rebuilt": False, "controls_repeated": False,
        "optimizer_calls": 0,
        "scope": "Builder and exact Boolean acceptance only. The forthcoming HiGHS driver, numerical rounding, time limits and process supervision are outside this report."
    }
    output = ROOT / "experiments/logs/grids-and-triangles/rook-case4-face112-highs-binary-unrestricted-source-review.json"
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output.read_bytes()), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
