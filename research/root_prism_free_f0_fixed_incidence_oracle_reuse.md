# Reuse of fixed-incidence shared-edge oracles

The existing repository already has an exact Boolean partial-exterior encoder and inspector for a fixed selection of sixty signatures. It is stronger than eighteen separate core matching tests and stronger than the shared fractional row-box oracle.

This note records a source and saved-record inspection. No model, census, optimizer or proof checker was run for this assessment.

## Boolean shared-edge model

The pure functions build(data) and inspect(chosen, data) in root_prism_free_f0_first_design_exterior.py have source SHA256 f0c5105526b9374935b4ba961859261249f44f2b311d98138ac3c8aeb5ed56cd.

One variable is used for each eligible unordered pair, so symmetry is explicit. The encoder imposes all 60 degree-eight equations, all 1,080 mixed equations and all 1,770 exterior-pair common-neighbor caps. Conjunction variables represent two incident exterior edges exactly.

For selected signatures h_a and fixed component adjacency D, the equations are W A = 2J - (D+I)W. The pair caps are A_ab + (A squared)_ab + h_a dot h_b <= 2. The source inspector independently reconstructs the symmetric Boolean adjacency, verifies exactly 240 edges and degree eight, checks the 1,080 mixed equations and checks all 1,770 caps.

The first historical incidence is already a useful separation between local and shared conditions. Its source result is f0-incidence-case00-run01/result.json, SHA256 64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf. The exterior model directly binds that same result. It has 1,224 primary edges and 426,090 clauses. Its model SHA256 is d98d817a7e9410f6fd88186adacdf23b886e543f3e18f7a9ec98af07e6558078.

The saved exterior run is UNSAT, and f0-first-design-exterior-run01-cold-replay.json has status cold complete domain/CNF rebuild, retained inclusion and DRAT PASS, SHA256 6240d173c5f15919a74e0062f8a81f3b25bd55a3928f3bd9e94b0531ed5a4847. Root separately found all eighteen local core matching tests feasible on this same old incidence. No contradiction is present: independent local matchings need not combine into one shared edge assignment.

A second fixed incidence with all individual row boxes feasible was already prepared using the same pure encoder by root_prism_free_f0_row_box_design_exterior.py, SHA256 ee064ece3bde366809e23837b75a5aaa8c480421532004049e90671d8e5fd6cf. Its cold preparation binds 1,220 primary edges and 423,130 clauses, with the same complete equation and cap coverage.

## Fractional shared-edge receipt

The reusable wrapper root_prism_free_f0_shared_reserved_fallback.py has SHA256 0685fc162e91a466ed033becb7d01259c4869f2afd9214474b4b0eae7dfcd066. It shares one bounded budget between an original shared feasibility call and, if needed, a distinct bounded-potential call.

Its exact outcomes are either a rational symmetric row-box point or a strict integer support separator. The primitive verifiers in root_prism_free_f0_row_box_design_linear.py, SHA256 c0d9e70f98e94176bf78bc518b41270940b930ab69cf34b26f42b71ff31a0871, check all rational bounds and 1,140 equations, or an integer Farkas identity with strictly negative right side. The exact-deficit reconstruction is in root_prism_free_f0_shared_deficit_separator.py, SHA256 6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf.

The fractional model omits the nonlinear exterior-pair caps. Its feasible point is therefore a weaker receipt than a Boolean witness from the encoder and inspector above. A numerical infeasible status without an exact separator remains unresolved.

## Narrow reuse recommendation

For a future accepted direct-selector candidate, supply its sorted sixty IDs and the current exact domain to a new bound adapter for the existing pure Boolean encoder and inspector. Do not call the historical fixed-candidate inputs() or coupling.load() chain. A modern owned supervisor and current proof-checker binding can surround the unchanged encoder.

The current 162 proved-zero Y orbits require explicit provenance if removed from the edge domain or added as units. The old global selector-cut lift asserts the complete 68,394-edge domain. It must not silently receive a filtered neighbor graph. The fixed-domain point/ray arithmetic can be reused, but any stronger filtered-domain universal lift needs its own premise binding.

A Boolean witness from this model is a partial exterior graph. The second shell component remains unspecified, and the encoder does not enforce every further global prism-absence condition. It is not a completed SRG. A checked UNSAT proof excludes only the fixed sixty-signature selection.
