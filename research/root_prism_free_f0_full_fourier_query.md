# Full Fourier and literal no-LP query preparation

The query is prepared against the completed 32,296-variable native target. No production query has run when this note is frozen. The source, control ledger and optimizer-free preflight are separately bound; production still requires the coordinator's execution gate.

## Frozen target and query

The target has 58,957 constraints: 42,633 linear rows, 16,280 exact product constraints and 44 allowed-assignment tables. The initial model contains 58,840 constraints. The same 117 inherited dense linear rows form the external pool. All original rows, coefficient scales, variable domains and literal-cut encodings are retained. The query does not load or reconstruct the full Fourier specification or an ancestor mathematical model.

Native target SHA256: 4e0ec33cb363299a9e199ce33a30a937a85d2f96969965f54833ed38464a911b. Initial SHA256: cf4c7cf7cb21087f443f5bdd6f2781a02e13091b7329d7f05fe78820182e179d. The preparation is f0-full-fourier-query-preparation01/preparation.json, SHA256 2e773adb61fae348e5bd5def5fdf4472a37ba391cf9ca99eec0cf935cc84054d.

The query source is root_prism_free_f0_full_fourier_query.py, SHA256 a8eff9c09fdd2a31482d23e3c83b11424fab32462e9b1431c3d899b6b8034955. The separate replay is root_prism_free_f0_full_fourier_replay.py, SHA256 9a072b04151e4a150d1627171c16c7dd33d87a49a6817157d1766aeddab062a1. Complete text substitutions and function AST inventories are saved in f0-full-fourier-query-reuse-controls.json, SHA256 d32bbacfe4c2801b8f019340cc61d2fdcf934b24a4b52dc59a60a3cc2becb1df.

## Finite search protocol

One owner has a 300-second total deadline. Native solver calls share a cumulative 180-second wall-time allowance. Each call's native time parameter is the smaller of the unused native allowance and the actual remaining owner time after an eight-second finalization reserve. The initial construction, imports, archive reads, row checks, serialization and writes are inside the owner limit. The owner binds the small preparation and source; the worker performs every complete archive/configuration check before construction. It does not duplicate those large reads in the owner.

There is one worker, seed zero, probing level zero and linearization level zero. There are at most 12 calls. After an exact returned candidate violates the full target, the next prefix can append only the first at most 16 violated rows in the frozen 117-row pool order. A further call requires this strict prefix growth. No objective, hint, independent phase choice, selector fixing or visitation clause is introduced.

The solver's time parameter is cooperative; the outer process watchdog is authoritative. Actual native call time and cumulative overrun are recorded. A call that overruns the cumulative native allowance leaves its integer vector saved, but this driver gives no provisional success for that call. A hard owner termination preserves the current files and has no accepted outcome. Native INFEASIBLE is explicitly unproved.

Every returned vector is saved atomically as a plain JSON root array of 32,296 integers before response formatting or expensive exact checks. File SHA256 and canonical integer-vector SHA256 are distinct and both are retained. A full-target pass is provisional. A separate exact restored-parent check and independent Fourier-to-literal decoder must pass before final acceptance; exterior Y realization remains separate.

## Controls and preflight

The exact integer protobuf evaluator, external-pool scanner and violated-row selector retain their original ASTs. The native parameter comparison explicitly accounts for the unchanged no-LP setting and the renamed cumulative-cap constant. Nine concrete owner/native-budget cases and three invalid-time rejection cases pass. Installed OR-Tools 9.15.6755 parameter text and wire roundtrips pass without constructing a solver or model.

The separate owned preflight checks all 32,296 domains, every initial row against the complete target and all 117 pool records and hashes. It passed in 10.921 owner seconds, with no overrun and peak RSS 272,068 KiB. The report is f0-full-fourier-query-preflight01/report.json, SHA256 f8ebff68ce10fcd9f252077e674fe618c2531da7a7bb19e3249e2e60e0572033; its accepted owner record is 78e150121c6fd717cd60a0507a38abae7cd0375a7f68403a23b79b8d51eaae04.

The terminal checker uses a separate 60-second owner. It independently replays chronological prefixes, all saved exact row checks, cumulative native-time accounting and any provisional full-target check. It never promotes a saved partial vector or numerical status into a mathematical claim.
