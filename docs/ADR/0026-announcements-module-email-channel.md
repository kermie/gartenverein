# Announcements module: email channel

**Recipients are current parcel residents, not "all members".**
Mirrors the definition already used elsewhere (e.g. insurance
household grouping): `MemberParcel.assigned_until IS NULL`, not
soft-deleted, membership not lapsed, `email_notifications = True`.
Someone who used to garden here but has moved on shouldn't get club
news; someone currently gardening but who opted out of email shouldn't
either.

**A member with no stored email address is skipped, not treated as a
failure.** That's a data-completeness gap that belongs to Members
admin, not something an announcement send should surface as an error
per attempt.

**Channel-level delivery status, not per-recipient.** Consistent with
`AnnouncementDelivery`'s original design: a partial failure (some
recipients unreachable) is still recorded as `SENT`, with the failure
count folded into `error_message`, since the announcement genuinely
went out. Only a *total* failure -- zero successful sends, including
the zero-recipients case -- is recorded as `FAILED`, so it stands out
visually and invites a retry rather than being buried in a list of
mostly-successful sends.

**Reuses `app/email_service.py`'s existing `sende_email()` rather than
introducing a second SMTP pathway.** The announcement content is
wrapped in a minimal branded HTML shell (club name, header image,
`body_html`) and sent per-recipient through the same SMTP
configuration the rest of the app already uses.

