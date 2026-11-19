WORKSPACE := experiments/workspace
PYTHON ?= $(or $(wildcard $(CURDIR)/.venv/bin/python),python3)
LEAN ?= lean
CERTIFICATES := $(addprefix $(WORKSPACE)/level-seven-certificate-,28.json 30.json 32.json)

.PHONY: verify verify-level-seven-standalone verify-level-seven-lean
verify: $(CERTIFICATES)
	cd $(WORKSPACE) && "$(PYTHON)" grid_intersections.py
	cd $(WORKSPACE) && "$(PYTHON)" root_cover_audit.py
	cd $(WORKSPACE) && "$(PYTHON)" level_seven_check.py
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/grid_support"; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/grid_support.cpp -o "$$build_dir/grid_support"; \
	"$$build_dir/grid_support"

verify-level-seven-standalone: $(CERTIFICATES)
	"$(PYTHON)" -O -B -W error "$(WORKSPACE)/level_seven_standalone_verify.py"

verify-level-seven-lean:
	"$(LEAN)" --trust=0 lean/Conway99LevelSeven.lean
