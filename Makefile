WORKSPACE := experiments/workspace
PYTHON ?= $(or $(wildcard $(CURDIR)/.venv/bin/python),python3)
CERTIFICATES := $(addprefix $(WORKSPACE)/level-seven-certificate-,28.json 30.json 32.json)

.PHONY: verify
verify: $(CERTIFICATES)
	cd $(WORKSPACE) && "$(PYTHON)" hoffman_singleton_double.py
	cd $(WORKSPACE) && "$(PYTHON)" involution_six_axis_cover.py
	cd $(WORKSPACE) && "$(PYTHON)" grid_intersections.py
	cd $(WORKSPACE) && "$(PYTHON)" grid_agreements.py
	cd $(WORKSPACE) && "$(PYTHON)" grid_leaf.py
	cd $(WORKSPACE) && "$(PYTHON)" incomplete_grid_profiles.py
	cd $(WORKSPACE) && "$(PYTHON)" root_cell_profiles.py
	cd $(WORKSPACE) && "$(PYTHON)" thirteen_grid_supports.py
	cd $(WORKSPACE) && "$(PYTHON)" parallel_triangle_cores.py
	cd $(WORKSPACE) && "$(PYTHON)" full_triangle_components.py
	cd $(WORKSPACE) && "$(PYTHON)" rook_nine_covers.py
	cd $(WORKSPACE) && "$(PYTHON)" rook_eight_covers.py
	cd $(WORKSPACE) && "$(PYTHON)" double_partner_cores.py
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

.PHONY: verify-eight-triangle-cover
verify-eight-triangle-cover:
	"$(PYTHON)" $(WORKSPACE)/rook_eight_covers.py --control
	"$(PYTHON)" $(WORKSPACE)/rook_eight_covers.py --verify --solver "$(CADICAL)" --checker "$(DRAT_TRIM)"

.PHONY: verify-double-partner
verify-double-partner:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/check" "$$build_dir/cores"; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/double_partner_check.cpp -o "$$build_dir/check"; \
	"$(PYTHON)" $(WORKSPACE)/double_partner_cores.py --emit > "$$build_dir/cores"; \
	"$$build_dir/check" < "$$build_dir/cores"

GAP ?= gap
.PHONY: verify-triangle-exterior
verify-triangle-exterior:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/triangle-exterior.actions"; rmdir "$$build_dir"' EXIT; \
	cd "$$build_dir"; \
	"$(GAP)" -q -b --quitonbreak "$(CURDIR)/$(WORKSPACE)/triangle_exterior_actions.g"; \
	"$(PYTHON)" "$(CURDIR)/$(WORKSPACE)/triangle_exterior_transitive.py" triangle-exterior.actions

.PHONY: verify-incomplete-corners
verify-incomplete-corners:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/corner-groups.txt"; rmdir "$$build_dir"' EXIT; \
	cd "$$build_dir"; \
	"$(GAP)" -q -b --quitonbreak "$(CURDIR)/$(WORKSPACE)/incomplete_corner_groups.g"; \
	"$(PYTHON)" "$(CURDIR)/$(WORKSPACE)/incomplete_corner_check.py" corner-groups.txt

.PHONY: verify-grid-diagonals
verify-grid-diagonals:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/diagonal-cuts"; rmdir "$$build_dir"' EXIT; \
	"$(CXX)" -std=c++20 -O3 "$(WORKSPACE)/grid_diagonal_cuts.cpp" -o "$$build_dir/diagonal-cuts"; \
	"$(PYTHON)" "$(WORKSPACE)/grid_diagonal_halves.py" "$$build_dir/diagonal-cuts"

.PHONY: verify-involution-axis-frame
verify-involution-axis-frame:
	cd $(WORKSPACE) && "$(PYTHON)" involution_axis_frame.py

.PHONY: certify-involution-axis-frame
certify-involution-axis-frame:
	cd $(WORKSPACE) && "$(PYTHON)" involution_axis_frame.py --certify "$(CADICAL)" "$(DRAT_TRIM)"

.PHONY: verify-aligned-grid-subfamilies
verify-aligned-grid-subfamilies:
	cd $(WORKSPACE) && "$(PYTHON)" aligned_grid_subfamilies.py

.PHONY: verify-central-grid-neighborhood
verify-central-grid-neighborhood:
	cd $(WORKSPACE) && "$(PYTHON)" central_grid_neighborhood.py
