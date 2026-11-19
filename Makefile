WORKSPACE := experiments/workspace
PYTHON ?= $(or $(wildcard $(CURDIR)/.venv/bin/python),python3)
CERTIFICATES := $(addprefix $(WORKSPACE)/level-seven-certificate-,28.json 30.json 32.json)

.PHONY: verify verify-red-grid-bound verify-seven-red-residual verify-global-constraints verify-coupled-shells
verify: $(CERTIFICATES)
	cd $(WORKSPACE) && "$(PYTHON)" grid_intersections.py
	cd $(WORKSPACE) && "$(PYTHON)" root_cover_audit.py
	cd $(WORKSPACE) && "$(PYTHON)" level_seven_check.py
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/grid_support"; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/grid_support.cpp -o "$$build_dir/grid_support"; \
	"$$build_dir/grid_support"

# Exact certificate replay for the global-constraints research branch.
# This target performs no new SAT or mixed-integer search.
verify-global-constraints: verify-red-grid-bound verify-seven-red-residual
	"$(PYTHON)" $(WORKSPACE)/transversal_constraints_certificates.py
	"$(PYTHON)" $(WORKSPACE)/transversal_constraints_hemisphere_verify.py
	"$(PYTHON)" $(WORKSPACE)/verify_coupled_counting.py
	"$(PYTHON)" $(WORKSPACE)/coupled_zero_replay.py
	"$(PYTHON)" $(WORKSPACE)/coupled_zero_gram.py --verify
	"$(PYTHON)" $(WORKSPACE)/coupled_zero_row_certificate.py --verify
	"$(PYTHON)" $(WORKSPACE)/coupled_shells_linear.py --replay $(WORKSPACE)/coupled-shells-linear-certificates.json --orbits experiments/logs/eigenlattices/coupled-shells-orbits.json
	"$(PYTHON)" $(WORKSPACE)/coupled_shells_theta.py --verify $(WORKSPACE)/coupled-shells-zero-theta.json
	"$(PYTHON)" $(WORKSPACE)/completion_constraints_rows.py --replay $(WORKSPACE)/completion-rows-case5-certificate.json
	"$(PYTHON)" $(WORKSPACE)/completion_constraints_edges.py --replay $(WORKSPACE)/completion-core5-edge-certificate.json
	"$(PYTHON)" $(WORKSPACE)/completion_constraints_propagation.py --replay $(WORKSPACE)/completion-propagation-certificate.json
	"$(PYTHON)" $(WORKSPACE)/global_grid_flags.py --verify experiments/logs/session-ab2f/global-grid-flags-integral.json

verify-red-grid-bound:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/"*.json "$$build_dir/"*.log; rmdir "$$build_dir"' EXIT; \
	"$(PYTHON)" $(WORKSPACE)/grid_nine_red_covers.py --output "$$build_dir/double.json" > /dev/null; \
	"$(PYTHON)" $(WORKSPACE)/grid_eight_red_covers.py --output "$$build_dir/triple.json" > /dev/null; \
	"$(PYTHON)" $(WORKSPACE)/eight_red_cycle_spectra.py --output "$$build_dir/spectra.json" > /dev/null; \
	cmp "$$build_dir/double.json" experiments/logs/grids-and-triangles/grid-nine-red-covers.json; \
	cmp "$$build_dir/triple.json" experiments/logs/grids-and-triangles/grid-eight-red-covers.json; \
	cmp "$$build_dir/spectra.json" experiments/logs/grids-and-triangles/eight-red-cycle-spectra.json; \
	"$(PYTHON)" $(WORKSPACE)/eight_red_hamming_spectral_audit.py "$$build_dir/spectra.json"; \
	"$(PYTHON)" $(WORKSPACE)/red_grid_cubic_trace.py --spectra "$$build_dir/spectra.json" --output "$$build_dir/cubic.json" > /dev/null; \
	cmp "$$build_dir/cubic.json" experiments/logs/grids-and-triangles/red-grid-cubic-trace.json

verify-seven-red-residual:
	"$(PYTHON)" $(WORKSPACE)/seven_red_nine_audit.py

# Supply the path to the separately built, pinned drat-trim executable.
verify-coupled-shells:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/orbits.json"; rmdir "$$build_dir"' EXIT; \
	"$(PYTHON)" $(WORKSPACE)/coupled_shells.py --independent --orbits "$$build_dir/orbits.json"; \
	cmp "$$build_dir/orbits.json" experiments/logs/eigenlattices/coupled-shells-orbits.json; \
	"$(PYTHON)" $(WORKSPACE)/coupled_shells_replay.py "$$build_dir/orbits.json" experiments/logs/eigenlattices/coupled-shells-low-all.json --drat-trim "$(DRAT_TRIM)"
	"$(PYTHON)" $(WORKSPACE)/coupled_zero_fixed_proof.py --verify --drat-trim "$(DRAT_TRIM)"
