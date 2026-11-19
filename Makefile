WORKSPACE := experiments/workspace
PYTHON ?= $(or $(wildcard $(CURDIR)/.venv/bin/python),python3)
CERTIFICATES := $(addprefix $(WORKSPACE)/level-seven-certificate-,28.json 30.json 32.json)

.PHONY: verify
verify: $(CERTIFICATES)
	cd $(WORKSPACE) && "$(PYTHON)" grid_intersections.py
	cd $(WORKSPACE) && "$(PYTHON)" grid_agreements.py
	cd $(WORKSPACE) && "$(PYTHON)" grid_leaf.py
	cd $(WORKSPACE) && "$(PYTHON)" root_cell_profiles.py
	cd $(WORKSPACE) && "$(PYTHON)" thirteen_grid_supports.py
	cd $(WORKSPACE) && "$(PYTHON)" parallel_triangle_cores.py
	cd $(WORKSPACE) && "$(PYTHON)" full_triangle_components.py
	cd $(WORKSPACE) && "$(PYTHON)" rook_nine_covers.py
	cd $(WORKSPACE) && "$(PYTHON)" root_cover_audit.py
	cd $(WORKSPACE) && "$(PYTHON)" level_seven_check.py
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/grid_support" "$$build_dir/aligned_spokes" "$$build_dir/mixed_spokes" "$$build_dir/domains"; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/grid_support.cpp -o "$$build_dir/grid_support"; \
	"$$build_dir/grid_support"; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/aligned_spokes.cpp -o "$$build_dir/aligned_spokes"; \
	"$$build_dir/aligned_spokes"; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/mixed_spokes.cpp -o "$$build_dir/mixed_spokes"; \
	"$(PYTHON)" $(WORKSPACE)/mixed_spoke_templates.py > "$$build_dir/domains"; \
	"$$build_dir/mixed_spokes" < "$$build_dir/domains"

.PHONY: verify-full-axes
verify-full-axes:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/mixed_spokes"; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/mixed_spokes.cpp -o "$$build_dir/mixed_spokes"; \
	"$(PYTHON)" $(WORKSPACE)/two_full_verify.py "$$build_dir/mixed_spokes"

CADICAL ?= cadical
DRAT_TRIM ?= drat-trim
.PHONY: verify-nine-triangle-cover
verify-nine-triangle-cover:
	"$(PYTHON)" $(WORKSPACE)/rook_nine_covers.py --control
	"$(PYTHON)" $(WORKSPACE)/rook_nine_covers.py --verify --solver "$(CADICAL)" --checker "$(DRAT_TRIM)"
