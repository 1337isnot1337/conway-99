# First external-row execution: setup failure before search

The first authorized execution of the frozen external-row count driver
ended `ERROR_CHILD_EXIT`. The owned child exited with return code `-9`
after 3.739 seconds; total owner time was 3.786 seconds. This was before
the 180-second deadline.

The last durable child record is `UNKNOWN_BEFORE_INITIALIZATION`, with
zero native calls and no added rows. No `call000` directory was created.
The hash-bound runner creates that directory and a durable pre-call record
before every native solve. Both child output logs are empty. No candidate,
native infeasibility status, or mathematical certificate was produced.

Signal 9 does not identify the cause. An out-of-memory kill is possible,
but no accessible cgroup event record or per-stage RSS log establishes it.
The available-memory snapshot taken afterward is not a measurement of the
failed child's peak. No unchanged retry was performed.

## What remains checked

The full target and initial native models had passed construction,
validation, exact protobuf comparison, and cold replay before execution.
The separate query preflight had also passed. Those records are unchanged.
The execution failure is not a counterexample to the mathematical model
and is not evidence of feasibility or infeasibility.

Root paused the planned full reconstruction replay while resource use was
investigated. A narrower standard-library checker was then authorized and
passed. It binds the prior complete preflight, the reviewed runner and
owner, and all five failed-run files. It checks the owner/child status,
zero-call progress, exact artifact set, empty logs, and absence of any
accepted outcome. It does not decompress a model archive, reconstruct the
mathematics, or invoke a solver.

The preserved terminal files are in
`experiments/logs/root-prism-free/f0-character-pool-query-run01/`.
The narrow replay is
`f0-character-pool-query-run01-narrow-replay.json`, checked by
`root_prism_free_f0_character_pool_zero_call_replay.py`.

## Separate initialization result

A new runtime path was prepared and checked separately. It loads only the already
checked plan and two protobuf archives, releases decompression buffers,
and constructs the initial native model through the same reviewed public
constructors. It records current and peak RSS at each stage. It does not
load the large mathematical specification or call the original builder's
`load_inputs()` or `derive()` functions.

The separately authorized initialization passed in 4.443 seconds of owner
time. Its constructed 18,444-variable, 34,281-constraint protobuf has exactly
the frozen initial-model hash. The final recorded current and peak RSS were
191,316 KiB. No solver was constructed or called. This establishes a working
initialization path; it does not establish why the earlier child was killed.

The complete stage records, child and owner results, and logs are in
`f0-character-pool-runtime-initialization01/`. Its source is
`root_prism_free_f0_character_pool_runtime.py`. The initialization uses the
old unchanged mathematical target and initial archives.

Any later production query requires a new execution gate. A vector satisfying
the native full target will remain provisional until a separately owned
exact check also passes the restored original parent. The earlier failed
run remains `ERROR_CHILD_EXIT` throughout. A later certified Z-domain overlay
is a separate preparation and is outside this completed package.
