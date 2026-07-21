# Announcements module: pacing, background send, and test email

**Sending is paced (a handful per minute) rather than firing every
email at once, per explicit request.** An SMTP relay rate-limiting or
flagging the account is a real risk at a few hundred recipients sent
in one burst. `EMAIL_BATCH_SIZE` / `EMAIL_BATCH_PAUSE_SECONDS` in
`app/announcement_mailer.py` control this; both are read at call time
rather than baked into a closure, so an admin-configurable pacing
setting can replace them later without touching the pacing logic
itself.

**Pacing means the send has to run outside the request/response
cycle.** At 8 per minute, 800 recipients take well over an hour --
far too long to hold an HTTP connection open, and well past any
reasonable request timeout. The router marks the delivery `SENDING`
and returns immediately; the actual paced loop runs as a FastAPI
`BackgroundTasks` job. This is the first use of `BackgroundTasks` in
the project. Because the background task keeps running after the
request's DB session has already closed, it opens its own
(`AsyncSessionLocal`) -- exactly the pattern `app.main`'s ticket-inbox
polling loop already uses for the same reason.

**A `SENDING` status, not just PENDING/SENT/FAILED, so "in progress"
is visible rather than indistinguishable from "not started" or
silently blocking the UI.** Since Postgres can't add an enum value and
use it in the same transaction, the migration
(`0030_announcement_sending_status`) wraps the `ALTER TYPE ... ADD
VALUE` in Alembic's `autocommit_block()`. `error_message` is repurposed
during `SENDING` to hold a running progress note rather than an error
-- documented as a deliberate dual-use field rather than adding a
dedicated progress column for something that's only ever needed
transiently.

**A server-side guard against double-sends, not just a disabled
button.** The "Send now" button is hidden client-side while a send is
`SENDING`, but the router also rejects a second `POST .../send/email`
outright (409) if the delivery is already `SENDING` -- a stale tab, a
double click racing the first response, or someone re-submitting a
cached page shouldn't be able to trigger the roster being emailed
twice.

**Test email is a genuinely separate code path, not a "send to one
person" flag on the real send.** It isn't paced (it's exactly one
email so pacing is moot), it never touches `AnnouncementDelivery`
(a test was never a delivery attempt), and the email itself carries a
visible "this is a test" banner -- so a board member previewing the
content can never mistake it for, or have it counted as, the real
send.

**The main form's Save button was clarified rather than restructured,
after a board member reasonably read "Save" as "this might send
something."** The save action was already, and remains, purely
persistence -- title/body/print-override to the database, nothing
else. Rather than rename or restructure it, a one-line hint was added
under the button making that explicit, since the actual send actions
already live in their own clearly-separate "Delivery channels" panel
below the form.

