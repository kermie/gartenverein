# Module system: toggleable feature areas

**Context:** not every allotment garden association needs mandatory work
hours, water management, or electricity management. An association
without its own water supply shouldn't be bothered with it in the UI.

**Decision:** instead of a full-blown plugin system (external packages,
hooks, sandboxing) -- which would be an unnecessary risk for a single team
without a security-review process -- there is a lightweight feature-flag
system:

- Every module has a key `modul_<name>` in the `club_settings` table
  (boolean as the string `"true"`/`"false"`)
- `app/module_flags.py` loads these flags **once per request** via a
  middleware and stores them under `request.state.module_flags`
- Router dependencies (`require_module("<name>")`) lock entire routers if
  disabled (404 instead of the page)
- Templates conditionally hide navigation blocks
- **No migration needed for new modules** -- the flags live in the
  existing key-value table

The REST API is the real extensibility surface for external integrations
(independently programmable, in any language) -- no in-process plugin
system needed.

