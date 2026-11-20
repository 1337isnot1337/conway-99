# First bounded parity cycle: partial scan

The single authorized v4 cycle stopped during its first parity scan. The owned
scan child reached its 60-second hard limit before it finalized the declared
123,123-word family. The cycle returned `UNRESOLVED: scan child incomplete;
durable prefix retained` after 60.750715991 seconds. It made no LP call, performed
no new exact basis solve, and accepted no new cut into its registry.

The scan's last checkpoint records 103,936 raw words, 98,140 distinct equations,
5,796 duplicates, and two retained cut records. This checkpoint deliberately
remains `RUNNING`, with `complete: false`, because the hard guard terminated the
child. The evaluation file also preserves a later tail: 98,156 physical records,
ending at raw ID 103,958. Neither that tail nor the checkpoint has received the
separate scan replay. These are recorded search positions, not an exhaustion
certificate.

Both complete cut records are retained in `scan-00/cuts.jsonl`. Their owner-side
records describe odd-support covers with right-hand side one. The first uses ten
original Gram equations with total right-hand side 13; the second uses twenty
with total right-hand side 27. Their recorded point deficits are respectively
41,397,422 and 38,044,002 over the accepted point denominator 337,510,679. The
cycle did not promote these records because its frozen contract required a
completed scan and its cold replay first. A separate original-row proof checker
can test the individual cuts without claiming that the searched family was
exhausted. That follow-up is outside this terminal package.

The one prescribed bindings-only verifier passed. It checked the chronological
result, supervisor, preparation, preflight, and seven stage-artifact hashes. The
accepted registry was empty, so it checked zero new cut witnesses. It did not
repeat a parity scan, RREF, exact elimination, or optimizer call. Its success
certifies artifact bindings; it does not turn the partial scan into a completed
mathematical search.

The frozen preparation and v4 source remain unchanged. This package includes
both independent source gates that preceded production. The previously accepted
positive rational point remains valid for the existing complete real model.
This run proves no new coordinate zero, no case-4 exclusion, and no conclusion
about the existence of the 99-vertex graph.
