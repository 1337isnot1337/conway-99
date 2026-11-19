WORKSPACE := experiments/workspace
PYTHON ?= $(or $(wildcard $(CURDIR)/.venv/bin/python),python3)
CERTIFICATES := $(addprefix $(WORKSPACE)/level-seven-certificate-,28.json 30.json 32.json)

.PHONY: verify
verify: $(CERTIFICATES)
	cd $(WORKSPACE) && "$(PYTHON)" grid_intersections.py
	cd $(WORKSPACE) && "$(PYTHON)" root_cover_audit.py
	cd $(WORKSPACE) && "$(PYTHON)" level_seven_check.py
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/grid_support"; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/grid_support.cpp -o "$$build_dir/grid_support"; \
	"$$build_dir/grid_support"
