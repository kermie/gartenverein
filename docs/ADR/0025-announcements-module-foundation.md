# Announcements module (foundation)

**One canonical content record, delivered to three channels, rather
than three separately-authored pieces of content.** The obvious trap
with "blog post + newsletter + printed notice" is treating them as
three things to write three times. Instead there is one
`Announcement` (title, Markdown body, image, optional print override)
and a separate `AnnouncementDelivery` row per (announcement, channel)
tracking send status -- the content lives once, the channels are just
different renderings of it. See `docs/module-announcements.md` for the
full data model.

**Email and blog share the exact same text; print is the one channel
allowed to diverge.** Per explicit product decision, there is no
per-channel text override for email -- `body_markdown`/`body_html` is
used as-is for both the blog draft and the member email. Print is
different: it has a real physical constraint (fit on one page) that
the other two don't, so `print_text_override` exists specifically for
it -- starting empty, auto-filled with a shortened version plus a QR
code once the PDF channel exists and the text doesn't fit, but always
freely hand-editable rather than a locked computed value.

**Markdown as the authoring format, not WYSIWYG rich text.** Both
Quill (BSD-3-Clause) and TipTap core (MIT) would have been
AGPL-compatible options. Markdown was chosen instead: smaller
dependency footprint, keeps `body_html` genuinely derived rather than
canonical, and is more portable if the content ever needs to move
outside Parcella. Editor is EasyMDE (MIT), CDN-loaded only on the
announcement form.

**A dedicated sanitizer profile, distinct from the ticket-email
sanitizer.** `sanitize_email_html()` (`app/html_sanitizer.py`) strips
all images because that content arrives from an untrusted external
sender. Announcement content is authored by a logged-in board member
and images are core to the format (the whole point is "an image and
some rich text"), so `app/announcement_utils.py` defines its own
allow-list permitting `<img>`, while still stripping
script/style/on*-handlers -- trusted authorship narrows the threat
model but doesn't eliminate it, since the rendered HTML still gets
pushed to a public blog and to every member's inbox.

**Off by default, restricted to admin/board.** Same reasoning as
`public_signup_api`: this module will eventually hold outbound
credentials (a WordPress application password) and can email every
member once the email channel exists, so `MODULE_DEFAULTS["announcements"]`
is `False` rather than the usual `True`, and the router requires
`require_admin` rather than being open to every logged-in member.

**Foundation only -- no channel sending yet.** This first delivery is
authoring and the data model only. The blog publisher (WordPress REST
API via application password), the email send, and the PDF
generation/shortening pipeline are each separate follow-up phases,
each building on `Announcement`/`AnnouncementDelivery` rather than
changing their shape.

