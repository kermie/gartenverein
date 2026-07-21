# Announcements module: blog channel (WordPress)

**A small `BlogPublisher` interface with one implementation, not a
WordPress-specific router.** `WordPressPublisher` is the only class
today, but every method it exposes (`test_connection`,
`publish_draft`) is generic enough that a TYPO3 or Joomla connector
later is a new class, not a change to the router or to
`AnnouncementDelivery`.

**WordPress's own built-in mechanisms, no custom plugin needed for
this direction.** The public-signup connector needed a WordPress
plugin because Parcella was *receiving* data from an external site
with no way to authenticate that inbound call except a shared token.
Here Parcella is the one *calling out*, using WordPress's REST API
(`wp-json/wp/v2/posts`, `/media`) and its own Application Password
authentication (WP 5.6+) -- nothing to install on the WordPress side.

**Credentials reuse the exact same storage mechanism as SMTP, not a
bespoke Integrations-page form.** Adding
`wordpress_site_url`/`wordpress_username`/`wordpress_app_password` to
the existing `SETTINGS_FIELDS` list means they get encrypted storage,
the "blank = unchanged" convention, and the masked-password placeholder
UI for free -- all already built for SMTP. A "Test connection" button
was added alongside (calling `wp-json/wp/v2/users/me`), since getting
Application Password auth wrong is easy to do and better caught before
a real draft attempt than after.

**Every post is created as a draft; the publisher never gets a
"publish immediately" option.** This was the scope from the original
ask ("draft that we can enrich... and publish as we like it") and
stays a hard behavior, not a configurable one -- there's no code path
in `WordPressPublisher.publish_draft` that sets any other `status`.

**`AnnouncementDelivery.external_reference` stores the WordPress edit
URL, not a public post URL.** There isn't a public URL yet for a
draft. This is a known constraint for the not-yet-built print channel:
its QR code needs something actually public to point at, so it can
only be generated after a board member publishes the WordPress draft
themselves -- documented as a real ordering dependency between blog
and print, not silently papered over.

