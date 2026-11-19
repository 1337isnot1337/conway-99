#!/usr/bin/env bash
set -eu
base=$1
py=/tmp/conway99-tools/venv/bin/python
"$py" ine_to_lp.py "$base.ine"
LD_LIBRARY_PATH=/tmp/conway99-tools/soplex-compat:/tmp/conway99-tools/venv/lib/python3.14/site-packages/scs.libs OPENBLAS_NUM_THREADS=1 /tmp/conway99-tools/soplex/bin/soplex --int:readmode=1 --int:solvemode=2 --int:syncmode=1 --int:checkmode=2 --real:feastol=0 --real:opttol=0 -X -Y "$base.lp" > "$base.spx" 2>&1
rg 'SoPlex status|Solving time|Violation' "$base.spx" | head -8
"$py" verify_theta_lp.py "$base"
