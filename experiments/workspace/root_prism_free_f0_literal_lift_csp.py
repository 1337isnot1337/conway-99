"""Exact finite binary CSP kernel and replayable deletion/branch certificates.

This module has no graph inputs and launches no optimizer. A UNSAT result
requires a complete checked tree. A deadline or node limit yields UNKNOWN.
"""
from itertools import combinations, product
import time


def canonical_problem(problem):
    sizes = problem["domain_sizes"]
    assert isinstance(sizes, list) and sizes
    assert all(type(x) is int and x >= 0 for x in sizes)
    pairs = list(combinations(range(len(sizes)), 2))
    relations = problem["relations"]
    assert len(relations) == len(pairs)
    for relation, (i, j) in zip(relations, pairs):
        assert relation["variables"] == [i, j]
        rows = relation["rows"]
        assert len(rows) == sizes[i]
        assert all(type(x) is int and 0 <= x < (1 << sizes[j]) for x in rows)
    return sizes, relations


def adjacency(problem):
    sizes, relations = canonical_problem(problem)
    allowed = {}
    for relation in relations:
        i, j = relation["variables"]
        rows = relation["rows"]
        allowed[i, j] = rows
        allowed[j, i] = [
            sum(1 << a for a, row in enumerate(rows) if row >> b & 1)
            for b in range(sizes[j])
        ]
    return sizes, allowed


def bits(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def check_assignment(problem, assignment):
    sizes, relations = canonical_problem(problem)
    assert len(assignment) == len(sizes)
    assert all(type(a) is int and 0 <= a < sizes[i] for i, a in enumerate(assignment))
    for relation in relations:
        i, j = relation["variables"]
        assert relation["rows"][assignment[i]] >> assignment[j] & 1
    return True


def solve(problem, seconds=1.0, maximum_nodes=100000):
    """Deterministic exact arc consistency and exhaustive finite branching."""
    assert seconds >= 0 and type(maximum_nodes) is int and maximum_nodes >= 0
    sizes, allowed = adjacency(problem)
    initial = [(1 << n) - 1 for n in sizes]
    started = time.monotonic()
    deadline = started + seconds
    statistics = {"nodes": 0, "deletions": 0, "split_nodes": 0}

    def visit(domains):
        node = {"deletions": []}
        if statistics["nodes"] >= maximum_nodes or time.monotonic() >= deadline:
            node["terminal"] = {"kind": "unknown", "reason": "declared_time_or_node_limit"}
            return "UNKNOWN", node, None
        statistics["nodes"] += 1
        while True:
            empty = next((i for i, mask in enumerate(domains) if mask == 0), None)
            if empty is not None:
                node["terminal"] = {"kind": "empty_domain", "variable": empty}
                return "UNSAT", node, None
            changed = False
            for i in range(len(sizes)):
                for a in list(bits(domains[i])):
                    if time.monotonic() >= deadline:
                        node["terminal"] = {"kind": "unknown", "reason": "declared_time_or_node_limit"}
                        return "UNKNOWN", node, None
                    other = next((j for j in range(len(sizes)) if j != i
                                  and allowed[i, j][a] & domains[j] == 0), None)
                    if other is not None:
                        domains[i] ^= 1 << a
                        node["deletions"].append([i, a, other])
                        statistics["deletions"] += 1
                        changed = True
                        if domains[i] == 0:
                            node["terminal"] = {"kind": "empty_domain", "variable": i}
                            return "UNSAT", node, None
            if not changed:
                break
        if all(mask.bit_count() == 1 for mask in domains):
            assignment = [next(bits(mask)) for mask in domains]
            check_assignment(problem, assignment)
            node["terminal"] = {"kind": "sat", "assignment": assignment}
            return "SAT", node, assignment
        variable = min((i for i, mask in enumerate(domains) if mask.bit_count() > 1),
                       key=lambda i: (domains[i].bit_count(), i))
        values = list(bits(domains[variable]))
        statistics["split_nodes"] += 1
        node["terminal"] = {"kind": "split", "variable": variable,
                            "values": values, "children": []}
        children = node["terminal"]["children"]
        for value in values:
            restricted = list(domains)
            restricted[variable] = 1 << value
            status, child, assignment = visit(restricted)
            children.append({"value": value, "node": child})
            if status == "SAT":
                return "SAT", node, assignment
            if status == "UNKNOWN":
                return "UNKNOWN", node, None
        return "UNSAT", node, None

    status, tree, assignment = visit(initial)
    result = {"status": status, "statistics": statistics, "tree": tree,
              "limits": {"seconds": seconds, "maximum_nodes": maximum_nodes},
              "seconds": time.monotonic() - started}
    if assignment is not None:
        result["assignment"] = assignment
    return result


def replay(problem, result):
    """Check the saved tree without running propagation or choosing branches."""
    sizes, allowed = adjacency(problem)
    counts = {"nodes": 0, "deletions": 0, "split_nodes": 0, "unknown_leaves": 0}

    def visit(domains, node):
        counts["nodes"] += 1
        for deletion in node["deletions"]:
            assert isinstance(deletion, list) and len(deletion) == 3
            i, value, j = deletion
            assert all(type(x) is int for x in deletion)
            assert 0 <= i < len(sizes) and 0 <= j < len(sizes) and i != j
            assert 0 <= value < sizes[i] and domains[i] >> value & 1
            assert allowed[i, j][value] & domains[j] == 0
            domains[i] ^= 1 << value
            counts["deletions"] += 1
        terminal = node["terminal"]
        kind = terminal["kind"]
        if kind == "empty_domain":
            i = terminal["variable"]
            assert type(i) is int and 0 <= i < len(sizes) and domains[i] == 0
            return "UNSAT"
        if kind == "unknown":
            counts["unknown_leaves"] += 1
            return "UNKNOWN"
        assert all(domains)
        if kind == "sat":
            assignment = terminal["assignment"]
            check_assignment(problem, assignment)
            assert all(domains[i] >> a & 1 for i, a in enumerate(assignment))
            return "SAT"
        assert kind == "split"
        counts["split_nodes"] += 1
        variable = terminal["variable"]
        assert type(variable) is int and 0 <= variable < len(sizes)
        values = list(bits(domains[variable]))
        assert len(values) > 1 and terminal["values"] == values
        children = terminal["children"]
        assert 0 < len(children) <= len(values)
        status = "UNSAT"
        for position, child in enumerate(children):
            assert child["value"] == values[position]
            restricted = list(domains)
            restricted[variable] = 1 << child["value"]
            status = visit(restricted, child["node"])
            if status != "UNSAT":
                assert position == len(children) - 1
                break
        if status == "UNSAT":
            assert len(children) == len(values)
        return status

    status = visit([(1 << n) - 1 for n in sizes], result["tree"])
    assert status == result["status"]
    if status == "SAT":
        check_assignment(problem, result["assignment"])
    if status == "UNSAT":
        assert counts["unknown_leaves"] == 0
    return {"status": "PASS: finite CSP certificate checked", "certified_outcome": status,
            "trace_counts": counts, "solver_or_optimizer_called": False}


def controls():
    """All 4,096 binary three-variable relation systems and boundary cases."""
    cases = sat = unsat = split_unsat = 0
    for encoded in product(range(16), repeat=3):
        relations = [{"variables": [i, j], "rows": [code & 3, code >> 2]}
                     for (i, j), code in zip(combinations(range(3), 2), encoded)]
        problem = {"domain_sizes": [2, 2, 2], "relations": relations}
        witnesses = [list(a) for a in product(range(2), repeat=3)
                     if all(r["rows"][a[r["variables"][0]]] >> a[r["variables"][1]] & 1
                            for r in relations)]
        result = solve(problem, seconds=1, maximum_nodes=64)
        assert result["status"] == ("SAT" if witnesses else "UNSAT")
        replay(problem, result)
        cases += 1
        sat += bool(witnesses)
        unsat += not witnesses
        split_unsat += not witnesses and result["statistics"]["split_nodes"] > 0
    assert cases == 4096 and split_unsat > 0
    empty = {"domain_sizes": [0, 2], "relations": [{"variables": [0, 1], "rows": []}]}
    assert solve(empty)["status"] == "UNSAT"
    replay(empty, solve(empty))
    singleton = {"domain_sizes": [1], "relations": []}
    assert solve(singleton)["assignment"] == [0]
    replay(singleton, solve(singleton))
    unknown = solve(singleton, maximum_nodes=0)
    assert unknown["status"] == "UNKNOWN"
    replay(singleton, unknown)
    # A deletion with an available support cannot be certified.
    bad = {"status": "UNSAT", "tree": {"deletions": [[0, 0, 1]],
            "terminal": {"kind": "empty_domain", "variable": 0}}}
    supported = {"domain_sizes": [1, 1],
                 "relations": [{"variables": [0, 1], "rows": [1]}]}
    caught = False
    try:
        replay(supported, bad)
    except AssertionError:
        caught = True
    assert caught
    return {"exhaustive_three_binary_variable_systems": cases, "SAT": sat, "UNSAT": unsat,
            "UNSAT_requiring_a_branch": split_unsat, "empty_domain_checked": True,
            "singleton_checked": True, "zero_node_budget_is_UNKNOWN": True,
            "false_deletion_rejected": True,
            "external_solver_calls": 0, "optimizer_calls": 0}
