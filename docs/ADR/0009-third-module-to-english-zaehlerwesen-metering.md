# Third module to English: Zaehlerwesen -> Metering

Structurally different from the previous modules: one router factory
produces two instances (water/electricity) from the same codebase. This
time no fundamentally new classes of bugs appeared, but the known ones in
even greater numbers, because the substring "Zaehler" is contained within
"Zaehlerstand" -- replacement order (longest term first) was especially
important here.

**Discovered a completely orphaned utility module.** `zaehler_utils.py`
imported `from app.models import Zaehler, Zaehlerstand` -- classes that had
already been renamed by that point. This file is imported by BOTH router
factories (`metering.py`, `api_metering.py`) -- overlooking this would
have made the entire app fail to start. Found by systematically cross-
referencing every `from app.models import` line in the whole project
against the classes actually defined -- this time also checked in files
that aren't routers themselves, just utility functions.

**Two more constructor-keyword bugs of the exact same pattern as in the
core module.** `MeterReading(zaehler_id=...)` in two different files (HTML
and API routers) -- the column has been called `meter_id` since the
rename. The same class of bug as the very first one found in
`api_versicherungen.py` months earlier: a constructor call with a field
name that missed the rename because it wasn't findable via a word-boundary
regex, only through targeted manual review.

**Inconsistent intermediate naming as a symptom, not just a bug.** On
closer inspection, several half-translated schema fields turned up
(`fruehere_zaehler` next to `current_meter`, `zaehler_nummer` next to
`meter_number`, `VerbrauchZeileOut` next to `EvaluationRowOut`-style names
in other modules). These aren't functional bugs -- the app would run
technically correctly with them -- but exactly the kind of inconsistency
that undermines the point of a rigorous conversion if left unaddressed.
Whenever a schema section is opened up again, it's worth a second look not
just at "is the code correct" but also "does the name fit the rest of the
converted module".

