"""SHA-bound exact blossom row evaluation for a future 32296-integer vector.

No production candidate has been supplied. Passing these rows is not count,
literal incidence, exterior edge, or graph acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/workspace/root_prism_free_f0_core_matching_blossom_inventory.py"
SOURCE_SHA = "6455d5c3967eb4f7aa22c690ab89f7572cf31ab9c5f7975927c6096caa39513c"
DIRECTORY = ROOT / "experiments/logs/root-prism-free/f0-core-matching-blossom-inventory01"
REPORT_SHA = "5e5ba4687a85c30d75647c54e76b5713caa295f2a9e77f8722f10c3e8dd4382d"


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    assert hashlib.sha256((DIRECTORY / "report.json").read_bytes()).hexdigest() == REPORT_SHA
    spec = importlib.util.spec_from_file_location("frozen_blossom_inventory", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.scan(DIRECTORY, args.candidate, args.output)
    print(json.dumps({"status": result["status"], "checked_rows": result["checked_rows"],
                      "violated_rows": len(result["violations"]), "minimum_slack": result["minimum_slack"],
                      "full_count_acceptance_claimed": False, "optimizer_calls": 0}))


if __name__ == "__main__":
    main()
