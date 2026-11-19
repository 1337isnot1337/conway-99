P˚äXèµ`ÿ¢hÀÿÚ≠pè—ëlyÏ„H77·e@ÅöJ]77·e@â©!†iW3v@¿“ÈU
Starting CP-SAT solver v9.15.6755
Parameters: random_seed: 0 max_time_in_seconds: 175 log_search_progress: true cp_model_presolve: true linearization_level: 0 num_search_workers: 1 cp_model_probing_level: 0 symmetry_level: 0 log_to_stdout: true log_to_response: true

Initial satisfaction model '': (model_fingerprint: 0x64052b6617b60e0a)
#Variables: 68'934 (60'179 primary variables)
  - 68'874 Booleans in [0,1]
  - 24 in [-482,482]
  - 36 in [0,1073741823]
#kLinear0: 756
#kLinear1: 1'956
#kLinear2: 138'102
#kLinear3: 64'986
#kLinearN: 51'794 (#terms: 3'029'358)

Starting presolve at 0.22s
  1.52e-01s  0.00e+00d  [DetectDominanceRelations] 
  1.24e+00s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1 
  5.70e-03s  0.00e+00d  [ExtractEncodingFromLinear] #potential_supersets=65'340 
[SAT presolve] num removable Booleans: 0 / 66'918
[SAT presolve] num trivial clauses: 0
[SAT presolve] [0s] clauses:143'809 literals:565'938 vars:66'918 one_side_vars:66276 simple_definition:156 singleton_clauses:0
[SAT presolve] [0.0113126s] clauses:143'797 literals:563'370 vars:66'918 one_side_vars:66276 simple_definition:156 singleton_clauses:0
[SAT presolve] [0.0135521s] clauses:143'797 literals:563'370 vars:66'918 one_side_vars:66276 simple_definition:156 singleton_clauses:0
[MaxClique] Merged 195198 with 475740 literals) into 153790(393340 literals) at_most_ones.
  3.19e+00s  0.00e+00d  [ProcessAtMostOneAndLinear] #num_changes=20'641 
  2.10e-02s  0.00e+00d  [DetectDuplicateConstraints] 
  1.61e-02s  0.00e+00d  [DetectDuplicateConstraintsWithDifferentEnforcements] #without_enforcements=48 
  1.50e-01s  1.00e-01d  [DetectDominatedLinearConstraints] #relevant_constraints=41'353 #num_inclusions=5'487 #num_redundant=162 
  7.46e-03s  0.00e+00d  [DetectDifferentVariables] 
  7.08e-01s  6.11e-02d  [ProcessSetPPC] #relevant_constraints=209'082 #num_inclusions=272'722 
  2.86e-02s  1.28e-03d  [TransformClausesToExactlyOne] #num_amos=64'748 #num_clauses=9'175 #num_checked=9'175 
  6.03e-03s  0.00e+00d  [DetectEncodedComplexDomains] 
  6.50e-03s  1.77e-04d  [FindAlmostIdenticalLinearConstraints] #num_tested_pairs=559 
  2.98e-01s  1.00e+00d *[FindBigAtMostOneAndLinearOverlap] #blocks=8 #saved_nz=4'829 
  2.66e-01s  1.00e+00d *[FindBigVerticalLinearOverlap] 
  3.42e-01s  1.00e+00d *[FindBigHorizontalLinearOverlap] #linears=41'353 
  1.30e-02s  1.21e-03d  [MergeClauses] 
  1.40e-01s  0.00e+00d  [DetectDominanceRelations] 
  5.26e-01s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1 
  1.39e-01s  0.00e+00d  [DetectDominanceRelations] 
  4.71e-01s  0.00e+00d  [PresolveToFixPoint] #num_loops=1 #num_dual_strengthening=1 
[SAT presolve] num removable Booleans: 0 / 66'926
[SAT presolve] num trivial clauses: 0
[SAT presolve] [0s] clauses:12'922 literals:259'968 vars:11'553 one_side_vars:10911 simple_definition:168 singleton_clauses:0
[SAT presolve] [0.00590655s] clauses:12'917 literals:257'783 vars:11'553 one_side_vars:10911 simple_definition:168 singleton_clauses:0
[SAT presolve] [0.00842577s] clauses:12'917 literals:257'783 vars:11'553 one_side_vars:10911 simple_definition:168 singleton_clauses:0
  3.51e+00s  0.00e+00d  [ProcessAtMostOneAndLinear] #num_changes=868 
  1.76e-02s  0.00e+00d  [DetectDuplicateConstraints] 
  1.44e-02s  0.00e+00d  [DetectDuplicateConstraintsWithDifferentEnforcements] #without_enforcements=48 
  1.49e-01s  1.00e-01d  [DetectDominatedLinearConstraints] #relevant_constraints=41'334 #num_inclusions=5'259 
  8.10e-03s  0.00e+00d  [DetectDifferentVariables] 
  1.04e-01s  3.74e-02d  [ProcessSetPPC] #relevant_constraints=119'624 #num_inclusions=142'026 
  2.56e-02s  1.32e-03d  [TransformClausesToExactlyOne] #num_amos=64'746 #num_clauses=9'192 #num_checked=9'192 
  4.42e-03s  0.00e+00d  [DetectEncodedComplexDomains] 
  5.21e-03s  1.82e-04d  [FindAlmostIdenticalLinearConstraints] #num_tested_pairs=589 
  2.96e-01s  1.00e+00d *[FindBigAtMostOneAndLinearOverlap] #blocks=8 #saved_nz=3'316 
  2.74e-01s  1.00e+00d *[FindBigVerticalLinearOverlap] 
  3.51e-01s  1.00e+00d *[FindBigHorizontalLinearOverlap] #linears=41'332 
  1.36e-02s  1.24e-03d  [MergeClauses] 
  1.39e-01s  0.00e+00d  [DetectDominanceRelations] 
  5.07e-01s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1 
  1.40e-01s  0.00e+00d  [DetectDominanceRelations] 
  4.67e-01s  0.00e+00d  [PresolveToFixPoint] #num_loops=1 #num_dual_strengthening=1 
[SAT presolve] num removable Booleans: 0 / 66'934
[SAT presolve] num trivial clauses: 0
[SAT presolve] [0s] clauses:12'904 literals:256'243 vars:11'547 one_side_vars:10905 simple_definition:168 singleton_clauses:0
[SAT presolve] [0.00549399s] clauses:12'904 literals:256'243 vars:11'547 one_side_vars:10905 simple_definition:168 singleton_clauses:0
[SAT presolve] [0.00802445s] clauses:12'904 literals:256'243 vars:11'547 one_side_vars:10905 simple_definition:168 singleton_clauses:0
  3.22e+00s  0.00e+00d  [ProcessAtMostOneAndLinear] 
  1.80e-02s  0.00e+00d  [DetectDuplicateConstraints] 
  1.59e-02s  0.00e+00d  [DetectDuplicateConstraintsWithDifferentEnforcements] #without_enforcements=48 
  1.49e-01s  1.00e-01d  [DetectDominatedLinearConstraints] #relevant_constraints=41'334 #num_inclusions=5'033 
  9.75e-03s  0.00e+00d  [DetectDifferentVariables] 
  1.05e-01s  3.69e-02d  [ProcessSetPPC] #relevant_constraints=119'619 #num_inclusions=139'129 
  2.71e-02s  1.32e-03d  [TransformClausesToExactlyOne] #num_amos=64'745 #num_clauses=9'192 #num_checked=9'192 
  5.38e-03s  0.00e+00d  [DetectEncodedComplexDomains] 
  5.84e-03s  2.00e-04d  [FindAlmostIdenticalLinearConstraints] #num_tested_pairs=627 
  2.92e-01s  1.00e+00d *[FindBigAtMostOneAndLinearOverlap] #blocks=5 #saved_nz=2'128 
  2.71e-01s  1.00e+00d *[FindBigVerticalLinearOverlap] 
  3.52e-01s  1.00e+00d *[FindBigHorizontalLinearOverlap] #linears=41'332 
  1.47e-02s  1.24e-03d  [MergeClauses] 
  1.43e-01s  0.00e+00d  [DetectDominanceRelations] 
  5.02e-01s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1 
  2.93e-03s  0.00e+00d  [MergeNoOverlap] 
  2.79e-03s  0.00e+00d  [MergeNoOverlap2D] 

Presolve summary:
  - 0 affine relations were detected.
  - rule 'TODO dual: only one blocking constraint?' was applied 76 times.
  - rule 'TODO linear matrix: reuse defining constraint' was applied 5 times.
  - rule 'at_most_one: size one' was applied 5 times.
  - rule 'at_most_one: transformed into max clique' was applied 1 time.
  - rule 'bool_or: implications' was applied 134'274 times.
  - rule 'bool_or: removed enforcement literal' was applied 26 times.
  - rule 'linear + amo: extracted enforcement literal' was applied 29'531 times.
  - rule 'linear + amo: fixed literal implied by enforcement' was applied 20'932 times.
  - rule 'linear inclusion: sparsify superset' was applied 162 times.
  - rule 'linear matrix: common amo rectangle' was applied 21 times.
  - rule 'linear1: x in domain' was applied 1'956 times.
  - rule 'linear2: convert ax + by != cte to clauses' was applied 134'274 times.
  - rule 'linear2: implied ax + by = cte has only one solution' was applied 16 times.
  - rule 'linear: advanced coefficient strenghtening' was applied 1'814 times.
  - rule 'linear: always true' was applied 5'064 times.
  - rule 'linear: divide by GCD' was applied 48 times.
  - rule 'linear: extracted enforcement literal' was applied 385'923 times.
  - rule 'linear: fixed or dup variables' was applied 9'342 times.
  - rule 'linear: negative at most one' was applied 61'008 times.
  - rule 'linear: negative clause' was applied 7'104 times.
  - rule 'linear: negative equal one' was applied 4'248 times.
  - rule 'linear: never in domain' was applied 12 times.
  - rule 'linear: positive clause' was applied 2'491 times.
  - rule 'linear: positive equal one' was applied 84 times.
  - rule 'linear: reduced variable domains' was applied 36 times.
  - rule 'linear: reduced variable domains in derived constraint' was applied 99 times.
  - rule 'linear: singleton column' was applied 36 times.
  - rule 'linear: small Boolean expression' was applied 3 times.
  - rule 'new_bool: with clause' was applied 21 times.
  - rule 'presolve: 1956 unused variables removed.' was applied 1 time.
  - rule 'presolve: iteration' was applied 3 times.
  - rule 'setppc: exactly_one included in linear' was applied 14'355 times.
  - rule 'setppc: reduced linear coefficients' was applied 14'355 times.
  - rule 'setppc: removed dominated constraints' was applied 89'486 times.

Presolved satisfaction model '': (model_fingerprint: 0x76dc792d05622449)
#Variables: 66'963 (60'144 primary variables)
  - 66'939 Booleans in [0,1]
  - 3 in [-64,15]
  - 9 in [-64,16]
  - 12 in [-57,7]
#kAtMostOne: 61'033 (#literals: 207'675)
#kBoolAnd: 589 (#enforced: 589) (#literals: 4'299)
#kBoolOr: 9'192 (#literals: 248'819)
#kExactlyOne: 4'353 (#literals: 196'727)
#kLinearN: 41'334 (#enforced: 34'622 #multi: 10'183) (#terms: 1'985'068)

Preloading model.

Starting search at 19.69s with 1 workers.
1 full problem subsolver: [main]


Task timing           n [     min,      max]      avg      dev     time         n [     min,      max]      avg      dev    dtime
      'main':         1 [   2.59m,    2.59m]    2.59m   0.00ns    2.59m         1 [   5.76m,    5.76m]    5.76m   0.00ns    5.76m

Search stats     Bools  Conflicts  Branches  Restarts  BacktrackToRoot  Backtrack   BoolPropag  IntegerPropag
       'main':  66'939    137'871   414'040        17            4'744    144'902  633'121'867    226'781'327

SAT formula    Fixed  Equiv   Total  VarLeft  BinaryClauses  PermanentClauses  TemporaryClauses
      'main':      0      0  66'939   66'939        122'470            14'291            15'632

SAT stats    ClassicMinim  LitRemoved  LitRemovedBinary  LitLearned  LitForgotten  Subsumed
    'main':       111'920   4'975'997         4'197'592  14'341'947    11'466'946    12'767

Vivification    Clauses  Decisions  LitTrue  Subsumed  LitRemoved  DecisionReused  Conflicts
       'main':    3'747    158'724        0         0           0             669          0

Clause deletion    at_true  l_and_not(l)  to_binary  sub_conflict  sub_extra  sub_decisions  sub_eager  sub_vivify  sub_probing  sub_inpro  blocked  eliminated  forgotten  promoted  conflicts
          'main':        0             0          0        12'412      1'307              0        355           0            0         45        0           0    107'373   456'326    137'871

Solution repositories    Added  Queried  Synchro
    'alternative_path':      0        0        0
      'best_solutions':      0        0        0
   'fj solution hints':      0        0        0

LRAT_status: NA
CpSolverResponse summary:
status: UNKNOWN
objective: NA
best_bound: NA
integers: 67624
booleans: 66939
conflicts: 137871
branches: 414040
propagations: 633121867
integer_propagations: 226781327
restarts: 17
lp_iterations: 0
walltime: 175.038
usertime: 175.038
deterministic_time: 355.209
gap_integral: 0

®ê