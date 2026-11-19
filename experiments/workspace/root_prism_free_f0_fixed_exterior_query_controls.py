"""Small exact gates for the fixed-exterior wrapper; no native model or solver."""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SUBJECT = ROOT / "experiments/workspace/root_prism_free_f0_fixed_selection_exterior_query.py"
EXPECTED = "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"
NAMES = {"sha", "canonical", "save", "verified_checker", "controls", "exact_candidate", "retained_subset", "supervise"}


def main(directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    raw = SUBJECT.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    functions = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    assert {n.name for n in functions} == NAMES
    namespace = dict(globals())
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SUBJECT), "exec"), namespace)
    report = {"status": "RUNNING", "source_sha256": EXPECTED,
              "control_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "checker_controls": namespace["controls"](), "production_solver_calls": 0,
              "native_imported": False, "case_CNF_read": False}
    cnf = SimpleNamespace(nv=2, clauses=[[1], [-1, 2]])
    model = {"formula": {"primary_variables": 2}, "data": {}}
    api = {"inspect": lambda chosen, data: chosen}
    assert namespace["exact_candidate"](api, cnf, model, [1, 2]) == [0, 1]
    bad_assignments = [[1, -2], [1], [1, -1], [True, 2], [1, 3]]
    for assignment in bad_assignments:
        try:
            namespace["exact_candidate"](api, cnf, model, assignment)
        except AssertionError:
            pass
        else:
            raise AssertionError("invalid complete assignment was accepted")
    report["complete_assignment_cases"] = 1 + len(bad_assignments)
    sample = directory / "retained.json"
    api = {"read_clauses": lambda p: json.loads(p.read_text())}
    sample.write_text(json.dumps([[2, 1], [-1]]))
    assert namespace["retained_subset"](api, [[1, 2], [-1], [3]], sample) == 2
    for rows in ([[4]], [[1, 2], [2, 1]]):
        sample.write_text(json.dumps(rows))
        try:
            namespace["retained_subset"](api, [[1, 2], [-1]], sample)
        except AssertionError:
            pass
        else:
            raise AssertionError("unjustified retained clause was accepted")
    report["retained_multiset_cases"] = 3
    stages = []
    for label, code, budget, expected in (
        ("exit0", "print('owned exit')", 2, "CHILD_EXITED"),
        ("exit3", "raise SystemExit(3)", 2, "ERROR_CHILD_EXIT"),
        ("deadline", "import time; time.sleep(30)", 0.15, "UNKNOWN_HARD_DEADLINE"),
    ):
        sub = directory / label
        sub.mkdir()
        outcome = namespace["supervise"]([sys.executable, "-c", code], sub, time.monotonic() + budget)
        assert outcome["status"] == expected and outcome["child_reaped"] and outcome["owned_process_group_stopped"]
        stages.append({"name": label, **outcome})
    sub = directory / "descendant"
    sub.mkdir()
    pidfile = sub / "descendant.json"
    code = ("import subprocess,sys,time,json; from pathlib import Path; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid})); time.sleep(30)")
    outcome = namespace["supervise"]([sys.executable, "-c", code, str(pidfile.resolve())], sub, time.monotonic() + 1)
    assert outcome["status"] == "UNKNOWN_HARD_DEADLINE" and outcome["child_reaped"]
    pid = json.loads(pidfile.read_bytes())["pid"]
    stat = Path("/proc") / str(pid) / "stat"
    state = stat.read_text().split(") ", 1)[1].split()[0] if stat.exists() else "absent"
    assert state in ("absent", "Z", "X"), state
    stages.append({"name": "owned_descendant_deadline", **outcome, "descendant_terminal_state": state})
    report.update(status="PASS_EXACT_AND_OWNED_GROUP_CONTROLS", supervisor_controls=stages)
    namespace["save"](directory / "report.json", report)
    print(json.dumps({"status": report["status"], "report_sha256": hashlib.sha256((directory / "report.json").read_bytes()).hexdigest()}))


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    main(Path(sys.argv[1]))
