# Calendar ICS feeds: public for the community calendar, token-protected for everything else

**Context:** the calendar module needs to export four different kinds
of information as ICS feeds -- meetings/inspections/work sessions,
member birthdays, council presence, and council absence. One of these
(the community calendar) has an explicit requirement to be embeddable
on the club's public WordPress site. The other three contain
meaningfully more sensitive information: birth dates are personal data
in the fullest sense, and staff schedules/absences are internal
coordination info, not public announcements.

**Decision: two different privacy postures, not one blanket policy.**
- The community calendar's ICS feed (`/calendar/community.ics`) is
  fully public with zero authentication, by design -- an external
  WordPress site cannot send this app's session cookie, so "public" was
  the only option that could satisfy the actual requirement. This is
  fine because the feed only contains information that's already
  intended to be public (meeting announcements, work session
  schedules) -- nothing here is more sensitive than a printed notice
  board.
- Birthdays, council presence, and council absence all require a
  secret token passed as a query parameter
  (`/calendar/birthdays.ics?token=...`), checked with
  `secrets.compare_digest` (constant-time, not a plain `==`). Calendar
  apps subscribing to a feed URL generally can't do session-cookie
  authentication either, so a long random token in the URL is the
  practical equivalent of "logging in" for a subscription feed -- the
  same mechanism used by, for instance, Google Calendar's own "secret
  address" feature for private calendar sharing.

**One shared token per installation, not per user.** Simpler to
implement, simpler to explain to users ("here's the private calendar
link"), and matches the actual trust model of a small volunteer-run
association where everyone with a login is already a trusted party.
Explicitly flagged in `docs/module-calendar.md` as a place to revisit if
a much larger association ever needs per-user revocation.

**Never conflate the two.** It would be a real privacy incident for the
birthday feed to accidentally become reachable without the token (e.g.
if someone reused `build_community_calendar`'s public route pattern for
a private feed by mistake) -- worth remembering if this module is
extended: check which category any new feed belongs to *before* writing
the route, not after.

