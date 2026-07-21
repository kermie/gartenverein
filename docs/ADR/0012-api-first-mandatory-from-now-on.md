# API-first mandatory from now on

**The gap that was found:** after building work hours, metering, and
insurance, it turned out that only the original phase-1 modules (members,
parcels) had REST API endpoints -- the three newer modules existed as web
UI only. This contradicted the actual idea that the REST API should be
the central extensibility surface for external integrations (see the
discussion of the plugin system).

**Rule from now on:** every new module gets both a web UI (Jinja2 router)
and REST API endpoints (`app/routers/api_<module>.py`) from the start, not
one after the other. Existing gaps (work hours, metering, insurance) were
caught up.

