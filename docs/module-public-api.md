# Public signup API module

Lets an external CMS (WordPress, TYPO3, Contao, or a hand-rolled site --
anything that can make an HTTP request) submit work-session signups to
Parcella without a Parcella login. Built to solve a concrete problem:
clubs already have a public website (usually WordPress) with its own
"sign up for a work session" form, and that form's list of dates
inevitably drifts out of sync with what's actually scheduled in
Parcella, because someone has to update it by hand in two places.

A reference WordPress connector plugin lives in
`integrations/wordpress/parcella-work-signup/` -- see its own README
for installation. Writing an equivalent connector for another CMS means
implementing the same three-endpoint contract below; none of the logic
needs to be reimplemented per CMS.

## Off by default

Unlike every other optional module (`app/module_flags.py`), this one
defaults to **disabled**. Every other module gates functionality that's
only reachable by an already-authenticated user; this one opens a public
HTTP endpoint that accepts writes from anyone with the API token. That's
a meaningfully different risk profile, so a board/admin has to
explicitly turn it on (Administration -> Settings) rather than it
silently being available after an upgrade.

## Data model

```
public_session_signups          -- one row per form submission
                                    (parcel_id, optional name/phone/email/remarks)
public_session_signup_sessions  -- join table: one submission can cover
                                    several work sessions (checkbox list)
```

Deliberately **not** `SessionParticipation`: that model requires a real
`Member`, but the public form only asks for a parcel number. The
submitter might be a tenant, a partner, or a helping neighbor who isn't
necessarily a `Member` record -- see "Key decisions" below.

`WorkSession.available_spots` (used everywhere capacity is checked or
displayed) counts both real `SessionParticipation` rows and
`PublicSessionSignupSession` links, so a session filled half by members
signing up internally and half by the public form still enforces one
shared capacity correctly.

## Endpoints

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/public/work-sessions/upcoming` | none |
| GET | `/api/v1/public/parcels` | none |
| POST | `/api/v1/public/work-sessions/signup` | `X-Parcella-API-Token` header |

The two GET endpoints are intentionally unauthenticated -- the same
posture as the public community ICS feed (`app/ics_utils.py`): an
external site's frontend can't send this app's session cookie, and the
data exposed (session dates/times, plot numbers) isn't sensitive on its
own.

The POST endpoint requires the installation's shared API token (see
`app/public_api_auth.py`, same shared-secret pattern as the private ICS
feeds) plus a lightweight honeypot field and a per-IP rate limit (20
requests/hour, in-memory, see `app/routers/api_public.py`) as
defense-in-depth on top of the token.

`POST .../signup` accepts multiple `session_ids` in one submission and
evaluates each independently -- a full session is rejected with a
`reason` while other sessions in the same submission can still succeed.
See the admin "Integrations" page (Administration -> Integrations) for
the current token, endpoint URLs, and a regenerate button.

## Key decisions

**Parcel number is enough; no Member match required.** Considered
requiring the submitted name to match an existing Member on that parcel,
which would allow linking straight to `SessionParticipation`. Rejected
per an explicit product decision: someone helping out on behalf of a
parcel (a partner, a neighbor) should be able to sign up without being a
Member record themselves. The tradeoff is that public signups don't
show up in a member's own work-hours history -- they're recorded
against the parcel, not a person. Public signups for a session are
shown in a dedicated "Public Signups" card on the session's detail page
(`app/templates/work_hours/session_detail.html`), separate from the
regular participations table, and can be removed from there once
processed. If a club wants those hours credited to a specific member's
annual total, a board member currently has to add that member as a
regular participant as well from the same page -- there's no automatic
link between a public signup and a `SessionParticipation`.

**A dedicated token, not the member API's JWT.** The existing REST API
(`app/api_auth.py`) issues per-user JWTs from a login -- there's no
"user" for a CMS plugin to log in as. A single shared, regenerable
token per installation (mirroring `app/ics_utils.py`'s ICS feed tokens)
is simple to document in one settings screen and easy to rotate if a
site's credentials leak.

**Capacity check is not fully race-safe.** Two submissions arriving at
nearly the same moment could both read `available_spots > 0` before
either commits, both succeeding when only one spot existed. Accepted as
a known limitation for a small club's traffic volume rather than adding
row-level locking; worth revisiting if a club's usage pattern makes
this a real problem in practice.

**Blank optional fields must be treated as absent, not validated as-is.**
Found via the WordPress connector: an HTML form submits an untouched
`<input type="email">` as `""`, not as a missing field, and `EmailStr`
rejects `""` outright (`@-sign` missing) -- every real-world submission
with an empty email field returned a 422 that the connector's generic
error handler couldn't distinguish from an actual server error.
`PublicSignupCreate` now coerces blank strings to `None` for all
optional fields (`name`, `phone`, `email`, `remarks`, `website`) before
validation runs (`app/schemas.py`). Worth remembering for any future
public-facing form schema: assume every optional field arrives as `""`,
not absent, unless the client is JSON-native and deliberately omits it.

**In-memory rate limiting, not a new dependency.** No Redis/`slowapi` --
a per-process sliding-window counter keyed by IP is enough deterrence
layered on top of the actual access control (the token), and adding
infrastructure for this felt disproportionate. Resets on deploy and
doesn't share state across multiple workers if the app is ever run with
more than one; acceptable for now, revisit if that changes.

## Extending to another CMS

Any connector needs to, in order:
1. `GET /work-sessions/upcoming` and `GET /parcels` to render a form
   (cache both briefly -- see the WordPress plugin's use of transients).
2. Collect parcel number (required), optional name/phone/email/remarks,
   and one or more chosen session IDs.
3. `POST /work-sessions/signup` with the API token in
   `X-Parcella-API-Token`, server-side only.
4. Handle a per-session `accepted`/`reason` in the response -- a
   submission can partially succeed.

New module checklist entries in `docs/README.md` apply here too if this
module gets extended (new translation keys go in all 7 language files).
