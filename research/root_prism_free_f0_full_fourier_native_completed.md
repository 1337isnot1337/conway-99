# Completed full Fourier and literal native preparation

The combined native model and its separate cold replay pass. The target contains 32,296 variables and 58,957 constraints. The initial prefix has 58,840 constraints, with the same 117 inherited linear rows retained in the external pool. There are 16,280 exact product constraints and 44 allowed-assignment tables. No solver was constructed or called.

The model replaces exactly 42 old local tables by their full Fourier extensions. Their complete projections recover the old tables. The two joint tables remain unchanged. It appends the full Fourier products and coefficient equations, all 151 nonempty original selector equations, 480 literal-selector inverse links, and native encodings of all 4,416 original literal cuts. The 21 remaining original selector equations are certified literal zero identities. Removing the appended variables and constraints and restoring the 42 table messages reproduces both complete original Y-parent protobuf hashes.

## Exact native results

The preparation report is experiments/logs/root-prism-free/f0-full-fourier-literal-native02/report.json, SHA256 d2cc38f284420c461fd191ce4ebfb9dbc16cf6cfd03f8ca1d2e00842bb92e9c4. The cold report is experiments/logs/root-prism-free/f0-full-fourier-literal-native02-cold/report.json, SHA256 5433cc1765e164f6c9df603cb0bfff6c62b5c6779c8f7e5391fff3c8e68a654c.

Public CP-SAT 9.15.6755 constructors produced the complete initial model. Its native validator returned no error, and its exported bytes exactly match the prepared initial protobuf. Exact Python-integer checks covered every variable domain, coefficient, constraint and product range. The target has 1,864,954 linear terms; the initial prefix has 798,592. Their largest absolute row activity bounds are 7,358,236,196,893 and 783,727,900,923 respectively, within signed 64-bit arithmetic.

The initial raw protobuf SHA256 is cf4c7cf7cb21087f443f5bdd6f2781a02e13091b7329d7f05fe78820182e179d. The published initial.pb.gz is 3f8833a098695b058a70841757ffb7e20bcb86531027eeef3c55c586ecd5d6ac. Decompression restores all 16,811,411 bytes of the actual native export. The redundant raw export remains locally and is omitted from the publication upload only under that explicit restoration binding. The target archive is 277449dc6d999207fbc77d452d1f351011791b1093cdda7875fc309d972381dd; its raw hash is 4e0ec33cb363299a9e199ce33a30a937a85d2f96969965f54833ed38464a911b.

## Preserved failure and revised owner

The first 60-second preparation did not finish. Its source, configuration, empty logs, final stages and owned termination are preserved in f0-full-fourier-native-attempt01-artifacts.json. The final stages show successful imports and specification binding before termination. The earlier live snapshot had not yet recorded those stages. No accepted model report or infeasibility result came from that attempt.

The separate v2 changes only the owned phase limit from 60 to 180 seconds and removes the duplicate owner-side definition/configuration hashing. The worker retains every complete binding check before construction. A complete text and AST comparison verifies those two changes; the other 26 functions are unchanged. Both source gates and the actual literal producer/cold proof are bound in the unchanged configuration.

V2 preparation finished in 159.557 owner seconds, with no deadline overrun. Peak RSS was 515,652 KiB. The observed stage intervals include 68.541 seconds for the specification-load/check span, 29.226 seconds for the literal/suffix span, and 4.293 seconds for public initial construction, native validation and export. These are wall-clock intervals, with no separate causal attribution to storage, scheduling or computation.

The independently owned cold replay finished in 17.654 seconds with no overrun. It rebuilt the append from the certified records and reproduced the complete plan and both protobufs. It did not repeat the public native construction or any ancestor mathematical census.

## Scope and next prepared step

These records establish the intended finite native encoding. They provide no feasible count point, literal incidence, exterior-edge realization or exclusion.

The earlier query-design note used a 180-second total owner. The subsequently authorized preparation scope is a separate query adapter with a 300-second total owner and at most 180 seconds of cumulative native solver time. Worker count one, seed zero, probing zero, no LP linearization, at most 12 calls and at most 16 newly violated external rows per returned candidate remain unchanged. This note does not authorize that query. The source and its concrete preparation must pass their own gate.

Every returned 32,296-integer vector must be saved before expensive checks. Full-target success is provisional until the restored original-parent arithmetic receipt and independent Fourier-to-literal decoder pass. The explicit 480 native selector bits must equal the decoded bits. Exterior Y realization remains separate.
