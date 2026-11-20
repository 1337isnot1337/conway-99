# Terminal binary search on the 112-zero case4 face

The single authorized HiGHS binary search ended UNKNOWN at the owned
180-second deadline. It returned no integral proposal and proves no
exclusion.

The [production record](../../experiments/logs/grids-and-triangles/rook-case4-face112-highs-binary-run01/result.json)
has SHA256 cd6cdf9f9cd6e2ac5ff058112ab30a31bc1bb6426ef560143dd053326fc2d8bc.
One native call started and none completed. No cover was appended.
The supervisor killed and reaped the child; that supervision took
180.028 seconds. The child checkpoint retains the last active-call
state. The outer supervisor record is the terminal status.

The frozen model has 1,102 binary variables, 2,195 initial rows, and
27,515 nonzero coefficients. Its 164,044 retained coordinate covers
remained in the external pool. The exact acceptance gate would check
all 2,618 original-coordinate integer rows and all 178,533 original
covers, but no proposed Boolean point reached that gate.

The one prescribed [cold replay](../../experiments/logs/grids-and-triangles/rook-case4-face112-highs-binary-run01-cold/result.json)
passed in 25.95 seconds, with SHA256
70795b320acda8007bebfb5065c3c68367c9f354ab51fbf73e0e593cd1f6194a.
It rechecked the source, model, input, and terminal-record bindings.
There were zero saved numerical points or appended-cover decisions to
replay. It made no optimizer call.

The full preparation is preserved by publication map
d6ee67276c4a4eab28862e4a6b7b6de0f40bf4f3. It includes the exact
compact model, native readback, tiny backend controls, source reviews,
the H3 branch-interval diagnostic, and the preserved preflight failures.
The production and cold outcome files are separate immutable artifacts.

This attempt neither supplies an incidence witness nor excludes case4.
No automatic repeat, longer search, or second backend invocation was
started.
