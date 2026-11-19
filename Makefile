WORKSPACE := experiments/workspace
PYTHON ?= $(or $(wildcard $(CURDIR)/.venv/bin/python),python3)
CERTIFICATES := $(addprefix $(WORKSPACE)/level-seven-certificate-,28.json 30.json 32.json)

.PHONY: verify verify-grid-free-relaxation verify-grid-free-projectors verify-current-grid-bounds verify-general-rook-interfaces verify-rook-partner-bound verify-rook-pair-completion verify-rook-tip-boundary verify-complement-rook-incidence verify-complement-rook-a2-completion verify-root-matching-coverage verify-red-grid-bound verify-seven-red-residual verify-rook-interfaces verify-rook-interfaces-drat verify-global-constraints verify-coupled-shells
.PHONY: verify-order-ten-count-cut verify-root-anchor-max
.PHONY: verify-order-ten-moment-cuts verify-complement-rook-schur
.PHONY: verify-prism-zero-counts verify-prism-zero-psd verify-incidence-master-cut-orbits
.PHONY: verify-root-prism-free-structure verify-incidence-core-simplification verify-refined-pattern-orbits
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
verify-global-constraints: verify-red-grid-bound verify-seven-red-residual verify-grid-free-relaxation verify-grid-free-projectors verify-rook-pair-completion verify-order-ten-count-cut
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

verify-grid-free-relaxation:
	"$(PYTHON)" $(WORKSPACE)/grid_free_core9_certificate.py --verify experiments/logs/moments-and-counts/grid-free-core9-certificate.json.gz

verify-grid-free-projectors:
	"$(PYTHON)" $(WORKSPACE)/grid_free_projector_certificate.py --certificate experiments/logs/moments-and-counts/grid-free-projector-certificate.json.gz

verify-order-ten-count-cut:
	"$(PYTHON)" $(WORKSPACE)/grid_free_order10_scaled_cut.py replay experiments/logs/moments-and-counts/grid-free-order10-scaled-fixed-cut.json

verify-order-ten-moment-cuts:
	"$(PYTHON)" $(WORKSPACE)/grid_free_order10_moments.py replay experiments/logs/moments-and-counts/grid-free-order10-moments.json
	"$(PYTHON)" $(WORKSPACE)/grid_free_order10_moments.py replay experiments/logs/moments-and-counts/grid-free-order10-moments-loop-round0-separation.json

verify-complement-rook-schur:
	"$(PYTHON)" $(WORKSPACE)/complement_rook_projector_schur.py --certificate experiments/logs/grids-and-triangles/complement-rook-projector-schur.json
	@set -eu; \
	audit_file=$$(mktemp); \
	trap 'rm -f "$$audit_file"' EXIT; \
	"$(PYTHON)" $(WORKSPACE)/audit_complement_rook_schur_clauses.py --certificate experiments/logs/grids-and-triangles/complement-rook-projector-schur.json --output "$$audit_file"

verify-root-anchor-max:
	"$(PYTHON)" $(WORKSPACE)/root_full_caps_anchor_max.py --certificate experiments/logs/root-full-caps-anchor-max/anchor-max-certificate.json

verify-prism-zero-counts:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/catalogue.pickle" "$$build_dir/audit.json"; rmdir "$$build_dir"' EXIT; \
	"$(PYTHON)" -c 'import pickle,sys; sys.path.insert(0,"experiments/workspace"); from subgraph_counts import build; pickle.dump(build(10),open(sys.argv[1],"wb"),protocol=4)' "$$build_dir/catalogue.pickle"; \
	"$(PYTHON)" $(WORKSPACE)/audit_prism_zero_count_witness.py --witness experiments/logs/moments-and-counts/prism-zero-repair-witness.json --catalogue "$$build_dir/catalogue.pickle" --output "$$build_dir/audit.json"

verify-prism-zero-psd:
	"$(PYTHON)" $(WORKSPACE)/grid_free_order10_prism_zero_psd.py replay --certificate experiments/logs/moments-and-counts/prism-zero-psd-certificate.json.gz

verify-incidence-master-cut-orbits:
	"$(PYTHON)" $(WORKSPACE)/complement_rook_incidence_master_cut_orbits.py --pilot experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.json --replay experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-full-replay.json --certificate experiments/logs/grids-and-triangles/complement-rook-incidence-master-cut-orbits.json

verify-root-prism-free-structure:
	"$(PYTHON)" $(WORKSPACE)/root_prism_free_structure.py --certificate experiments/logs/root-prism-free/structure-certificate.json --clauses experiments/logs/root-prism-free/near-axis-clauses.cnf.gz --replay
	"$(PYTHON)" $(WORKSPACE)/root_prism_free_anchor_min.py --lex-analysis experiments/logs/root-full-caps-lex/analysis.json --certificate experiments/logs/root-prism-free/anchor-min-certificate.json --replay

verify-incidence-core-simplification:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/"*.cnf; rmdir "$$build_dir"' EXIT; \
	"$(PYTHON)" $(WORKSPACE)/complement_rook_incidence_core_simplification.py --pilot experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01.json --full-replay experiments/logs/grids-and-triangles/complement-rook-incidence-master-pilot01-full-replay.json --directory "$$build_dir" --certificate experiments/logs/grids-and-triangles/complement-rook-incidence-core-simplification.json --drat-trim "$(DRAT_TRIM)"

verify-refined-pattern-orbits:
	"$(PYTHON)" $(WORKSPACE)/complement_rook_refined_pattern_orbits.py --certificate experiments/logs/grids-and-triangles/complement-rook-refined-pattern-orbits.json

verify-root-matching-coverage:
	"$(PYTHON)" $(WORKSPACE)/root_full_caps_coverage.py --certificate experiments/logs/root-full-caps/matching-coverage.json
	"$(PYTHON)" $(WORKSPACE)/root_full_caps_matching_audit.py --certificate experiments/logs/moments-and-counts/root-full-caps-matching-audit-certificate.json.gz
	"$(PYTHON)" $(WORKSPACE)/root_full_caps_matching_orbit_audit.py --certificate experiments/logs/grids-and-triangles/root-full-caps-matching-orbit-audit.json

verify-complement-rook-incidence:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	"$(PYTHON)" $(WORKSPACE)/complement_rook_a_incidence.py --replay --prefix $(WORKSPACE)/complement-rook-a-incidence --output experiments/logs/grids-and-triangles/complement-rook-a-incidence.json --drat-trim "$(DRAT_TRIM)"
	"$(PYTHON)" $(WORKSPACE)/complement_rook_a_incidence_census.py --replay --output experiments/logs/grids-and-triangles/complement-rook-a2-incidence-census.json --cnf $(WORKSPACE)/complement-rook-a2-incidence-census.cnf --proof $(WORKSPACE)/complement-rook-a2-incidence-census.drat --drat-log experiments/logs/grids-and-triangles/complement-rook-a2-incidence-census-drat-replay.log --drat-trim "$(DRAT_TRIM)"

verify-complement-rook-a2-completion:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	@set -eu; \
	for case_index in 0 1 2 3; do \
	  "$(PYTHON)" $(WORKSPACE)/complement_rook_a2_fixed_certificate.py replay \
	    --certificate experiments/logs/grids-and-triangles/complement-rook-a2-fixed-case$$case_index-certificate.json \
	    --log experiments/logs/grids-and-triangles/complement-rook-a2-fixed-case$$case_index-retained-drat-replay.log \
	    --drat-trim "$(DRAT_TRIM)"; \
	done

verify-rook-pair-completion:
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_pair_integer_replay.py experiments/logs/grids-and-triangles/two-rook-iso-pair-integer.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_pair_integer_lex_replay.py experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-lex.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_hall_audit.py --certificate experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_psd_audit.py --input experiments/logs/grids-and-triangles/two-rook-iso-pair-integer.json --certificate experiments/logs/grids-and-triangles/two-rook-tip-psd-certificate.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_pair_integer_hall_replay.py experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-hall.json.gz
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_psd_hall_audit.py --input experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-hall.json.gz --certificate experiments/logs/grids-and-triangles/two-rook-tip-psd-hall-certificate.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_near_edge.py --replay --hall experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json --cnf $(WORKSPACE)/two-rook-tip-near-edge.cnf --proof $(WORKSPACE)/two-rook-tip-near-edge.drat --output experiments/logs/grids-and-triangles/two-rook-tip-near-edge.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_rook_boundary.py --hall experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json --certificate experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-certificate.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_rook_boundary_export.py --boundary-certificate experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-certificate.json --hall experiments/logs/moments-and-counts/two-rook-tip-hall-certificate.json --output experiments/logs/grids-and-triangles/two-rook-tip-rook-boundary-domains.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_pair_structural.py --certificate experiments/logs/grids-and-triangles/two-rook-pair-structural-certificate.json

verify-current-grid-bounds:
	"$(PYTHON)" $(WORKSPACE)/three_red_boundary.py --verify experiments/logs/grids-and-triangles/three-red-boundary.json --translation-certificate experiments/logs/grids-and-triangles/three-red-translation-incidence.json
	"$(PYTHON)" $(WORKSPACE)/three_red_translation_incidence.py --verify experiments/logs/grids-and-triangles/three-red-translation-incidence.json
	"$(PYTHON)" $(WORKSPACE)/global_grid_flag_certificate.py --verify experiments/logs/grids-and-triangles/global-grid-flag-certificate.json

verify-general-rook-interfaces:
	"$(PYTHON)" $(WORKSPACE)/two_rook_interfaces.py --verify experiments/logs/grids-and-triangles/two-rook-interfaces.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_interfaces.py --witness experiments/logs/grids-and-triangles/two-rook-interfaces-incidence-second.json
	"$(PYTHON)" $(WORKSPACE)/rook_interface_star.py --verify experiments/logs/grids-and-triangles/rook-interface-star.json
	"$(PYTHON)" $(WORKSPACE)/rook_interface_five_cycle.py --verify experiments/logs/grids-and-triangles/rook-interface-five-cycle.json
	"$(PYTHON)" $(WORKSPACE)/rook_interface_dense_audit.py --verify experiments/logs/grids-and-triangles/rook-interface-dense-audit.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_completion.py --two-grid-audit --fixed-certificate experiments/logs/grids-and-triangles/two-rook-iso-completion-case48-ray.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_joint_incidence.py --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_joint_incidence.py --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence-packing.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_joint_incidence.py --space-only --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-incidence-space.json

verify-rook-partner-bound:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	"$(PYTHON)" $(WORKSPACE)/two_rook_interfaces.py --verify experiments/logs/grids-and-triangles/two-rook-interfaces.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_joint_integer_independent_audit.py --verify experiments/logs/grids-and-triangles/two-rook-iso-joint-integer-independent-audit.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_iso_joint_integer_certificate.py $(WORKSPACE)/two-rook-iso-joint-integer-certificate.json --drat-trim "$(DRAT_TRIM)"

verify-rook-tip-boundary:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_boundary_joint_certificate.py $(WORKSPACE)/two-rook-tip-boundary-joint-3679836361-certificate.json --drat-trim "$(DRAT_TRIM)"
	"$(PYTHON)" $(WORKSPACE)/two_rook_tip_edge_bound.py --boundary-proof $(WORKSPACE)/two-rook-tip-boundary-joint-3679836361-certificate.json --certificate experiments/logs/grids-and-triangles/two-rook-tip-edge-bound-certificate.json
	"$(PYTHON)" $(WORKSPACE)/two_rook_a0_fixed_certificate.py $(WORKSPACE)/two-rook-a0-fixed-certificate.json --drat-trim "$(DRAT_TRIM)"

verify-red-grid-bound: verify-current-grid-bounds verify-general-rook-interfaces verify-rook-interfaces
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

verify-rook-interfaces:
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/"*; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/seven_red_interfaces_backtrack.cpp -o "$$build_dir/census"; \
	"$$build_dir/census" 60 "$$build_dir/5.json" "$$build_dir/6.json"; \
	for bases in 5 6; do \
	  "$(PYTHON)" -c 'import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); a.pop("seconds"); b.pop("seconds"); assert a==b' "$$build_dir/$$bases.json" "experiments/logs/grids-and-triangles/seven-red-interfaces-b$$bases-backtrack.json"; \
	done; \
	"$(PYTHON)" $(WORKSPACE)/seven_red_interfaces_backtrack_replay.py --five "$$build_dir/5.json" --six "$$build_dir/6.json" --four-output "$$build_dir/4.json"; \
	cmp "$$build_dir/4.json" experiments/logs/grids-and-triangles/seven-red-interfaces-b4-backtrack.json
	"$(PYTHON)" $(WORKSPACE)/rook_interface_small_spectra.py --verify $(WORKSPACE)/rook-interface-small-spectral-certificates.json
	"$(PYTHON)" $(WORKSPACE)/four_red_boundary.py --verify experiments/logs/grids-and-triangles/four-red-boundary.json
	"$(PYTHON)" $(WORKSPACE)/petersen_red_core_boundary.py

verify-rook-interfaces-drat:
	@test -x "$(DRAT_TRIM)" || { echo 'Set DRAT_TRIM to the drat-trim executable path.' >&2; exit 1; }
	"$(PYTHON)" $(WORKSPACE)/seven_red_interfaces_certificate.py $(WORKSPACE)/seven-red-interfaces-b6-certificate.json --drat-trim "$(DRAT_TRIM)"

verify-seven-red-residual:
	"$(PYTHON)" $(WORKSPACE)/seven_red_nine_audit.py
	@set -eu; \
	build_dir=$$(mktemp -d); \
	trap 'rm -f "$$build_dir/"*; rmdir "$$build_dir"' EXIT; \
	$(CXX) -O3 -std=c++20 $(WORKSPACE)/seven_red_four_cover_scout.cpp -o "$$build_dir/covers"; \
	"$$build_dir/covers" 3 > "$$build_dir/three.json" 2> "$$build_dir/three.log"; \
	"$$build_dir/covers" 4 > "$$build_dir/four.json" 2> "$$build_dir/four.log"; \
	cmp "$$build_dir/three.json" experiments/logs/grids-and-triangles/seven-red-four-cover-control.json; \
	cmp "$$build_dir/four.json" experiments/logs/grids-and-triangles/seven-red-four-cover-scout.json; \
	"$(PYTHON)" $(WORKSPACE)/seven_red_four_cover_projections.py --source "$$build_dir/four.json" --verify-colorings $(WORKSPACE)/seven-red-four-cover-colorings.json; \
	"$(PYTHON)" $(WORKSPACE)/seven_red_four_cover_independent_audit.py --source "$$build_dir/four.json"; \
	"$(PYTHON)" $(WORKSPACE)/seven_red_four_rook_exclusion.py --output "$$build_dir/rook.json"; \
	cmp "$$build_dir/rook.json" experiments/logs/grids-and-triangles/seven-red-four-rook-exclusion.json

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
