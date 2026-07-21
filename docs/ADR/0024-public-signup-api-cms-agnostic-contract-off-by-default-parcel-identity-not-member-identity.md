# Public signup API: CMS-agnostic contract, off-by-default, parcel identity not Member identity

**Context:** clubs need external websites (typically WordPress, but
potentially TYPO3, Contao, or anything else) to be able to create
work-session signups in Parcella. The obvious anti-pattern to avoid: a
WordPress-specific plugin that reimplements capacity checks, validation,
and data storage on its own, with Parcella as an afterthought synced by
hand.

**Decision: a CMS-agnostic public HTTP contract; the WordPress plugin is
just the first (and reference) client.** Three endpoints
(`GET .../work-sessions/upcoming`, `GET .../parcels`,
`POST .../work-sessions/signup`) under `/api/v1/public/`, documented in
`docs/module-public-api.md`. All business logic -- capacity, matching,
storage -- lives in Parcella. Any future CMS connector implements the
same three calls; nothing about Parcella's side changes.

**Off by default, unlike every other optional module.** Every entry in
`MODULE_DEFAULTS` (`app/module_flags.py`) defaults to `True` so an
upgrade doesn't silently remove functionality an existing club already
relies on. `public_signup_api` is the one exception, defaulting to
`False`: it's the only module that opens a public, unauthenticated-write
HTTP endpoint, which is a security-relevant choice a club should make
consciously, not one that should appear pre-enabled after a version
bump.

**Public signups identify by parcel, not by matching an existing
Member.** *(Superseded below -- kept for context.)* Considered requiring
the submitted name to match a real Member (which would let the signup
become a proper `SessionParticipation`). Rejected: a partner, tenant, or
helping neighbor filling out a public form isn't necessarily a Member
record, and requiring a match would silently reject legitimate signups
from exactly the people a work session most wants to reach. Tradeoff,
originally documented in `docs/module-public-api.md`: these hours
wouldn't automatically count toward any individual's annual work-hours
total -- a board member would have to enter that manually if a club
wanted it credited. In practice this meant a signup landed in a table
nobody but the board thought to check, separate from the normal
participants list -- the wrong tradeoff for something that should just
work like a normal signup. Superseded by the decision directly below.

**Superseding decision: signups create real `SessionParticipation`
rows directly, matched against the parcel's current residents.** The
public website must never expose which members live on which parcel
(explicit requirement), so the form still only ever collects a parcel
number, not a member picked from a list. But instead of storing that as
a separate, disconnected record, Parcella now does the matching
server-side: an optionally-submitted free-text name is checked against
the parcel's current residents (`MemberParcel.assigned_until IS NULL`),
and if it matches exactly one, only that member is registered
(`status=REGISTERED`). If it doesn't match confidently -- no name, no
match, or more than one plausible match -- *every* current resident of
the parcel is registered instead, each with a note flagging the
ambiguity and asking the board to remove whoever didn't actually sign
up. Overregistering and letting the board delete extras from a table
they already use every session is a far smaller failure mode than a
signup that silently registered nobody, or one sitting in a separate
table nobody checks. This removed the `public_session_signups`/
`public_session_signup_sessions` tables entirely (migration
`0028_drop_signup_tables`) in favor of folding the submission details
into each participation's `note` field. See
`docs/module-public-api.md` ("Matching logic") for the full behavior.

**A dedicated shared API token, reusing the ICS-token shape rather than
the member API's JWTs.** A CMS plugin is a server-side script, not a
logged-in user -- there's no account for it to authenticate as. One
regenerable shared secret per installation, mirroring
`get_or_create_ics_token` almost exactly (see `app/public_api_auth.py`),
keeps the auth story consistent across the whole codebase instead of
inventing a fourth pattern.

